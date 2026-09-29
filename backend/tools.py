"""Catalogue/inventory database access and the tools the shop agent can call.

Every tool is read-only and re-reads SQLite on each call, so prices and stock are always live.
"""

from __future__ import annotations

import difflib
import json
import re
import sqlite3
from contextlib import closing
from pathlib import Path

from pydantic_ai import RunContext

import memory
from models import (
    MAX_PAGE_RESULTS,
    AlternativeSuggestions,
    CatalogueOverview,
    CustomerProfile,
    PastConversation,
    ProductCard,
    ProductDetails,
    ProductNotFound,
    ProductSnapshot,
    ProductSnapshotResult,
    ProductSummary,
    SearchResults,
    ShopDeps,
    SizeStock,
    StockLevel,
    StockReport,
    StockStatus,
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DATA_DIR / "campus_customs.db"
IMAGES_DIR = DATA_DIR / "products"
SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]
LOW_STOCK_THRESHOLD = 5
MAX_SNAPSHOT_PRODUCTS = 6

# Customer words -> spellings used in the catalogue (garment_type values are inconsistent).
SYNONYMS: dict[str, list[str]] = {
    "hoodie": ["hood"],
    "hoodies": ["hood"],
    "hoody": ["hood"],
    "hoodys": ["hood"],
    "hooded": ["hood"],
    "tee": ["t-shirt", "tee"],
    "tees": ["t-shirt", "tee"],
    "tshirt": ["t-shirt"],
    "shirt": ["shirt"],
    "quarter": ["quarter-zip", "1/4", "quarter"],
    "quarterzip": ["quarter-zip"],
    "crewneck": ["crewneck", "crew-neck", "crew neck"],
    "sweatshirt": ["sweatshirt", "crewneck", "hoodie"],
    "sweater": ["sweater", "sweatshirt", "crewneck", "fleece"],
    "jacket": ["jacket", "fleece", "bomber"],
    "grey": ["gray", "grey"],
    "gray": ["gray", "grey"],
    "longsleeve": ["long-sleeve", "long sleeve"],
}
STOPWORDS = {"a", "an", "the", "and", "or", "for", "with", "in", "of", "any", "some", "yale", "merch", "item", "items"}
# How close a misspelling must be to a catalogue word to be corrected (difflib ratio, 0-1).
FUZZY_CUTOFF = 0.75
MIN_FUZZY_LENGTH = 4

# Spoken sizes -> the size codes stored in the inventory table.
SIZE_ALIASES: dict[str, str] = {
    "xs": "XS", "x-small": "XS", "xsmall": "XS", "extra small": "XS", "extra-small": "XS",
    "s": "S", "sm": "S", "small": "S",
    "m": "M", "med": "M", "medium": "M",
    "l": "L", "lg": "L", "large": "L",
    "xl": "XL", "x-large": "XL", "xlarge": "XL", "extra large": "XL", "extra-large": "XL",
    "xxl": "XXL", "2xl": "XXL", "xx-large": "XXL", "xxlarge": "XXL", "2x": "XXL", "double xl": "XXL",
}


# ---------------------------------------------------------------------------
# Database access (also used by main.py)
# ---------------------------------------------------------------------------


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _size_rank(size: str) -> int:
    return SIZE_ORDER.index(size) if size in SIZE_ORDER else len(SIZE_ORDER)


def load_products(product_id: str | None = None, db_path: Path = DB_PATH) -> list[ProductCard]:
    """Read catalogue rows joined with their per-size inventory."""
    where, params = ("WHERE product_id = ?", (product_id,)) if product_id else ("", ())
    with closing(get_connection(db_path)) as conn:
        rows = conn.execute(f"SELECT * FROM catalogue {where} ORDER BY name", params).fetchall()
        stock_rows = conn.execute(f"SELECT product_id, size, quantity FROM inventory {where}", params).fetchall()

    stock: dict[str, list[StockLevel]] = {}
    for s in stock_rows:
        stock.setdefault(s["product_id"], []).append(StockLevel(size=s["size"], quantity=s["quantity"]))

    products = []
    for r in rows:
        levels = sorted(stock.get(r["product_id"], []), key=lambda lvl: _size_rank(lvl.size))
        products.append(
            ProductCard(
                product_id=r["product_id"],
                name=r["name"],
                garment_type=r["garment_type"],
                description=r["description"],
                colors=json.loads(r["colors"]),
                search_tags=json.loads(r["search_tags"]),
                image_file_path=r["image_file_path"],
                image_url=f"/media/{r['image_file_path']}",
                price=r["price"],
                inventory=levels,
                total_stock=sum(lvl.quantity for lvl in levels),
            )
        )
    return products


def products_by_ids(product_ids: list[str], db_path: Path = DB_PATH) -> list[ProductCard]:
    """Look up products in the given order, silently dropping unknown or duplicate ids."""
    by_id = {p.product_id: p for p in load_products(db_path=db_path)}
    seen: set[str] = set()
    result = []
    for pid in product_ids:
        if pid in by_id and pid not in seen:
            seen.add(pid)
            result.append(by_id[pid])
    return result


def known_product_ids(db_path: Path = DB_PATH) -> set[str]:
    with closing(get_connection(db_path)) as conn:
        return {row[0] for row in conn.execute("SELECT product_id FROM catalogue")}


def category_of(garment_type: str) -> str:
    """Group the database's many garment_type spellings into shop categories (mirrors the frontend)."""
    t = garment_type.lower()
    if "t-shirt" in t:
        return "T-Shirts"
    if "quarter-zip" in t:
        return "Quarter-Zips"
    if "jacket" in t:
        return "Jackets & Fleece"
    if "hood" in t:
        return "Hoodies"
    if "long-sleeve" in t:
        return "Long Sleeve"
    return "Crewnecks & Sweatshirts"


def normalize_size(size: str | None) -> str | None:
    """'medium' -> 'M', '2xl' -> 'XXL'; unknown text is upper-cased so it reports as not offered."""
    if size is None or not size.strip():
        return None
    key = size.strip().lower()
    return SIZE_ALIASES.get(key, key.upper())


def stock_status(quantity: int) -> StockStatus:
    if quantity == 0:
        return "sold_out"
    if quantity <= LOW_STOCK_THRESHOLD:
        return "low_stock"
    return "in_stock"


# ---------------------------------------------------------------------------
# Search helpers (keyword matching + typo correction)
# ---------------------------------------------------------------------------


def _haystack(product: ProductCard) -> str:
    return " ".join(
        [product.name, product.garment_type, product.description, *product.colors, *product.search_tags]
    ).lower()


def matches(product: ProductCard, query: str) -> bool:
    """Every word must appear (used by the Products API search box)."""
    haystack = _haystack(product)
    return all(word in haystack for word in query.lower().split())


def _query_words(query: str) -> list[str]:
    text = query.lower().replace("t shirt", "tshirt").replace("quarter zip", "quarterzip")
    return [w for w in re.findall(r"[a-z0-9/\-]+", text) if w not in STOPWORDS]


def _vocabulary(products: list[ProductCard]) -> set[str]:
    """Every word that appears in the catalogue, plus the synonym keys customers use."""
    words = {w for p in products for w in re.findall(r"[a-z0-9]+", _haystack(p)) if len(w) >= 3}
    return words | set(SYNONYMS)


def _is_known(word: str, haystacks: list[str]) -> bool:
    return word in SYNONYMS or any(opt in h for h in haystacks for opt in _match_options(word))


def _correct(word: str, vocabulary: set[str], haystacks: list[str]) -> str | None:
    """Return the closest catalogue word for a misspelling, or None if the word is fine or too far off."""
    if len(word) < MIN_FUZZY_LENGTH or word.isdigit() or _is_known(word, haystacks):
        return None
    close = difflib.get_close_matches(word, vocabulary, n=1, cutoff=FUZZY_CUTOFF)
    return close[0] if close else None


def _match_options(word: str) -> list[str]:
    """Spellings to look for. Words with a synonym entry match only through it ("tshirt" must not hit "sweatshirt")."""
    if word in SYNONYMS:
        return SYNONYMS[word]
    singular = word[:-1] if word.endswith("s") and len(word) > 3 else word
    return [word, singular]


def _relevance(product: ProductCard, words: list[str], haystack: str | None = None) -> int:
    haystack = haystack if haystack is not None else _haystack(product)
    return sum(1 for word in words if any(opt in haystack for opt in _match_options(word)))


def _first_sentence(text: str) -> str:
    return re.split(r"(?<=\.)\s", text, maxsplit=1)[0]


def _summary(product: ProductCard) -> ProductSummary:
    in_stock = [s.size for s in product.inventory if s.quantity > 0]
    return ProductSummary(
        product_id=product.product_id,
        name=product.name,
        category=category_of(product.garment_type),
        garment_type=product.garment_type,
        price=product.price,
        summary=_first_sentence(product.description),
        colors=product.colors,
        availability="in_stock" if product.total_stock > 0 else "sold_out",
        sizes_in_stock=in_stock,
        total_stock=product.total_stock,
    )


def _size_stock(product: ProductCard) -> list[SizeStock]:
    return [SizeStock(size=s.size, quantity=s.quantity, status=stock_status(s.quantity)) for s in product.inventory]


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _resolve(identifier: str, products: list[ProductCard]) -> ProductCard | ProductNotFound:
    """Find a product by product_id, exact name, or slug; otherwise suggest close matches (typos allowed)."""
    key = identifier.strip()
    for p in products:
        if p.product_id == key or p.name.lower() == key.lower() or p.product_id == _slug(key):
            return p
    haystacks = [_haystack(p) for p in products]
    vocabulary = _vocabulary(products)
    words = [_correct(w, vocabulary, haystacks) or w for w in _query_words(key.replace("-", " "))]
    ranked = sorted(products, key=lambda p: (-_relevance(p, words), p.name))
    suggestions = [_summary(p) for p in ranked[:3] if _relevance(p, words) > 0]
    return ProductNotFound(
        query=identifier,
        message=f"No product matches '{identifier}'. Use a product_id from search_products or the suggestions below.",
        suggestions=suggestions,
    )


# ---------------------------------------------------------------------------
# Building blocks shared by the lookup tools
# ---------------------------------------------------------------------------


def _details(product: ProductCard) -> ProductDetails:
    sizes = _size_stock(product)
    return ProductDetails(
        product_id=product.product_id,
        name=product.name,
        category=category_of(product.garment_type),
        garment_type=product.garment_type,
        description=product.description,
        price=product.price,
        colors=product.colors,
        availability="in_stock" if product.total_stock > 0 else "sold_out",
        total_stock=product.total_stock,
        stock_by_size=sizes,
        in_stock_sizes=[s.size for s in sizes if s.quantity > 0],
        sold_out_sizes=[s.size for s in sizes if s.quantity == 0],
    )


def _stock_report(product: ProductCard, size: str | None) -> StockReport:
    sizes = _size_stock(product)
    in_stock = [s.size for s in sizes if s.quantity > 0]
    sold_out = [s.size for s in sizes if s.quantity == 0]
    requested = normalize_size(size)
    level = next((s for s in sizes if s.size == requested), None)

    if requested is None:
        status, quantity = None, None
        note = (
            f"{product.name} is sold out in every size."
            if not in_stock
            else f"{product.name} is in stock in {', '.join(in_stock)}"
            + (f"; sold out in {', '.join(sold_out)}." if sold_out else ".")
        )
    elif level is None:
        status, quantity = "not_offered", None
        note = f"{product.name} doesn't come in size {requested}. Offered sizes: {', '.join(s.size for s in sizes)}."
    else:
        status, quantity = level.status, level.quantity
        if level.quantity == 0:
            others = f" In stock: {', '.join(in_stock)}." if in_stock else " It is sold out in every size."
            note = f"Size {requested} of {product.name} is sold out.{others}"
        elif level.status == "low_stock":
            note = f"Size {requested} of {product.name} is in stock, but only {level.quantity} left."
        else:
            note = f"Size {requested} of {product.name} is in stock ({level.quantity} available)."

    return StockReport(
        product_id=product.product_id,
        name=product.name,
        price=product.price,
        availability="in_stock" if in_stock else "sold_out",
        total_stock=product.total_stock,
        stock_by_size=sizes,
        in_stock_sizes=in_stock,
        sold_out_sizes=sold_out,
        requested_size=requested,
        requested_size_status=status,
        requested_size_quantity=quantity,
        note=note,
    )


def _alternatives(
    product: ProductCard, size: str | None, limit: int, products: list[ProductCard]
) -> list[ProductSummary]:
    """Similar in-stock items: same category first, then shared keywords, then closest price."""
    wanted_size = normalize_size(size)
    category = category_of(product.garment_type)
    target_words = list(set(_query_words(" ".join([product.name, *product.search_tags]))))
    candidates: list[tuple[int, int, ProductCard]] = []
    for p in products:
        if p.product_id == product.product_id or p.total_stock == 0:
            continue
        if wanted_size and not any(s.size == wanted_size and s.quantity > 0 for s in p.inventory):
            continue
        same_category = 1 if category_of(p.garment_type) == category else 0
        candidates.append((same_category, _relevance(p, target_words), p))
    candidates.sort(key=lambda c: (-c[0], -c[1], abs(c[2].price - product.price), c[2].name))
    return [_summary(p) for _, _, p in candidates[: max(1, min(limit, 6))]]


# ---------------------------------------------------------------------------
# Agent tools
# ---------------------------------------------------------------------------


def search_products(
    ctx: RunContext[ShopDeps],
    query: str = "",
    color: str | None = None,
    size: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    in_stock_only: bool = True,
    limit: int = 8,
) -> SearchResults:
    """Search the catalogue (misspellings are corrected automatically); returns matches with price and in-stock sizes.

    Args:
        query: Keywords such as garment type, sport, college, school, family role, or graphic
            (e.g. "hoodie", "hockey", "Saybrook", "Yale Mom", "bulldog"). Pass the customer's words as typed;
            typos like "hoody" or "sweatshit" are fixed for you. Empty to browse everything.
        color: Only products that come in this color (e.g. "navy", "gray", "white").
        size: Only products with this size in stock (XS, S, M, L, XL, XXL, or words like "medium").
        min_price: Minimum price in USD.
        max_price: Maximum price in USD.
        in_stock_only: Skip products that are sold out in every size.
        limit: Maximum number of results (1-40). Use a high limit (e.g. 40) when listing every match for the page.
    """
    products = load_products(db_path=ctx.deps.db_path)
    haystacks = {p.product_id: _haystack(p) for p in products}
    all_haystacks = list(haystacks.values())
    vocabulary = _vocabulary(products)

    corrections: dict[str, str] = {}
    words = []
    for word in _query_words(query):
        fixed = _correct(word, vocabulary, all_haystacks)
        if fixed:
            corrections[word] = fixed
        words.append(fixed or word)

    color_terms: list[str] = []
    if color:
        color_word = color.lower().strip()
        palette = {c.lower() for p in products for c in p.colors}  # e.g. "heather gray"
        palette |= {word for c in list(palette) for word in c.split()}  # plus "heather", "gray"
        if len(color_word) >= MIN_FUZZY_LENGTH and not any(color_word in c for c in palette) and color_word not in SYNONYMS:
            close = difflib.get_close_matches(color_word, palette, n=1, cutoff=FUZZY_CUTOFF)
            if close:
                corrections[color_word] = close[0]
                color_word = close[0]
        color_terms = SYNONYMS.get(color_word, [color_word])

    wanted_size = normalize_size(size)
    scored: list[tuple[int, ProductCard]] = []
    for product in products:
        if color_terms and not any(term in c.lower() for c in product.colors for term in color_terms):
            continue
        if wanted_size and not any(s.size == wanted_size and s.quantity > 0 for s in product.inventory):
            continue
        if min_price is not None and product.price < min_price:
            continue
        if max_price is not None and product.price > max_price:
            continue
        if in_stock_only and product.total_stock == 0:
            continue
        score = _relevance(product, words, haystacks[product.product_id]) if words else 1
        if score > 0:
            scored.append((score, product))
    scored.sort(key=lambda item: (-item[0], item[1].name))

    note = None
    if corrections:
        fixes = ", ".join(f"'{fixed}' (typed '{typed}')" for typed, fixed in corrections.items())
        note = f"Showing results for {fixes}."
    return SearchResults(
        results=[_summary(p) for _, p in scored[: max(1, min(limit, MAX_PAGE_RESULTS))]],
        total_matches=len(scored),
        corrections=corrections,
        note=note,
    )


def get_product_snapshot(
    ctx: RunContext[ShopDeps],
    product_ids: list[str],
    size: str | None = None,
    include_alternatives: bool = True,
) -> ProductSnapshotResult:
    """ONE call for everything about one or more products: full details, stock by size, the requested size's
    status, and in-stock alternatives when something is unavailable. Prefer this over calling
    get_product_details, check_stock, and find_alternatives separately.

    Args:
        product_ids: Up to 6 product_ids (or exact product names), e.g. to compare items or answer about one item.
        size: Optional size to check for every product (XS-XXL, "medium", "2XL", ...).
        include_alternatives: Add up to 3 similar in-stock items when a product or the requested size is unavailable.
    """
    products = load_products(db_path=ctx.deps.db_path)  # one database read for the whole batch
    snapshots: list[ProductSnapshot] = []
    not_found: list[ProductNotFound] = []
    for identifier in product_ids[:MAX_SNAPSHOT_PRODUCTS]:
        found = _resolve(identifier, products)
        if isinstance(found, ProductNotFound):
            not_found.append(found)
            continue
        stock = _stock_report(found, size)
        unavailable = stock.availability == "sold_out" or stock.requested_size_status in ("sold_out", "not_offered")
        snapshots.append(
            ProductSnapshot(
                details=_details(found),
                stock=stock,
                alternatives=_alternatives(found, size, 3, products) if include_alternatives and unavailable else [],
            )
        )
    return ProductSnapshotResult(snapshots=snapshots, not_found=not_found)


def get_product_details(ctx: RunContext[ShopDeps], product_id: str) -> ProductDetails | ProductNotFound:
    """Get the full description, price, colors, and stock for every size of one product.

    Args:
        product_id: The product_id from a search result (an exact product name also works).
    """
    found = _resolve(product_id, load_products(db_path=ctx.deps.db_path))
    return found if isinstance(found, ProductNotFound) else _details(found)


def check_stock(ctx: RunContext[ShopDeps], product_id: str, size: str | None = None) -> StockReport | ProductNotFound:
    """Check live stock for one product, optionally for a specific size the customer asked about.

    Args:
        product_id: The product_id from a search result (an exact product name also works).
        size: Optional size to check: XS, S, M, L, XL, XXL (words like "medium" or "2XL" are fine).
    """
    found = _resolve(product_id, load_products(db_path=ctx.deps.db_path))
    return found if isinstance(found, ProductNotFound) else _stock_report(found, size)


def find_alternatives(
    ctx: RunContext[ShopDeps], product_id: str, size: str | None = None, limit: int = 4
) -> AlternativeSuggestions | ProductNotFound:
    """Suggest similar in-stock products (same category first) when an item or size is unavailable.

    Args:
        product_id: The product the customer wanted.
        size: The size they need, if any; alternatives will have this size in stock.
        limit: Maximum number of suggestions (1-6).
    """
    products = load_products(db_path=ctx.deps.db_path)
    found = _resolve(product_id, products)
    if isinstance(found, ProductNotFound):
        return found
    wanted_size = normalize_size(size)
    category = category_of(found.garment_type).lower()
    return AlternativeSuggestions(
        original_product_id=found.product_id,
        original_name=found.name,
        size=wanted_size,
        reason=f"Similar {category} with size {wanted_size} in stock" if wanted_size else f"Similar in-stock {category}",
        alternatives=_alternatives(found, size, limit, products),
    )


def summarize_product(product_id: str, db_path: Path = DB_PATH) -> ProductSummary | None:
    """Used by main.py to describe the product on the customer's current page."""
    found = load_products(product_id, db_path=db_path)
    return _summary(found[0]) if found else None


def get_customer_profile(ctx: RunContext[ShopDeps]) -> CustomerProfile | str:
    """Get the logged-in customer's profile: name, email, member-since date, and whether they've chatted before."""
    if ctx.deps.customer is None:
        return "The customer is a guest (not logged in). There is no profile and nothing from this chat is saved."
    return ctx.deps.customer


def recall_chat_history(ctx: RunContext[ShopDeps], limit: int = 10) -> PastConversation | str:
    """Look back at this customer's saved conversations (e.g. "what was that hoodie you showed me last time?").

    Args:
        limit: How many of the most recent saved messages to return (1-30).
    """
    if ctx.deps.customer is None:
        return "The customer is a guest (not logged in), so there is no saved chat history."
    messages, total = memory.load_past_messages(ctx.deps.db_path, ctx.deps.customer.user_id, max(1, min(limit, 30)))
    return PastConversation(messages=messages, total_saved=total)


def catalogue_overview(ctx: RunContext[ShopDeps]) -> CatalogueOverview:
    """Summarize what the shop carries: categories with counts, sizes, price range, and colors."""
    products = load_products(db_path=ctx.deps.db_path)
    categories: dict[str, int] = {}
    for p in products:
        cat = category_of(p.garment_type)
        categories[cat] = categories.get(cat, 0) + 1
    colors = sorted({c.lower() for p in products for c in p.colors})
    return CatalogueOverview(
        total_products=len(products),
        categories=categories,
        sizes=SIZE_ORDER,
        min_price=min(p.price for p in products),
        max_price=max(p.price for p in products),
        colors=colors,
    )


AGENT_TOOLS = [
    search_products,
    get_product_snapshot,
    get_product_details,
    check_stock,
    find_alternatives,
    catalogue_overview,
    get_customer_profile,
    recall_chat_history,
]
