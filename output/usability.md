# Campus Customs — Usability Improvements (Problem 9)

Four improvements: two on the **frontend** (shopper experience) and two on the **backend** (agent speed, cost, and accuracy).

| # | Improvement | Side | Main benefit |
|---|---|---|---|
| 1 | Product pop-up instead of a separate page | Frontend | Shoppers never lose their place |
| 2 | "Return to Full Menu" for chat-filtered results | Frontend | Shoppers stay in control of the page |
| 3 | One-call product snapshot tool | Backend | Faster, cheaper answers |
| 4 | Typo-tolerant search | Backend | More accurate answers |

---

## Frontend 1: Product pop-up that preserves your place

**What was added**
- Clicking any product card opens the product in a **floating window** over the current page instead of navigating away. The window has a large image on the left and the full description, price, colors, and per-size stock on the right.
- The page underneath stays rendered and lightly shaded, so the shopper keeps their exact **scroll position**, filters, search text, or chat results.
- It closes with the **×** button, the **Esc** key, or a click on the shaded area. Each returns to the same spot (`navigate(-1)`).
- The URL still changes to `/products/<id>`, so the item is shareable. Opening that link directly (or refreshing) shows a full product page as a fallback.
- Works the same from the Products grid, the Home page, chat product cards, and chat search results.
- Code: `components/ProductModal.tsx`, `components/ProductView.tsx`, the `backgroundLocation` routing in `App.tsx`, and `useProductModalLink()` in `hooks.ts`.

**Why it helps**
- **Shopper:** browsing 102 products means a lot of scrolling. With the old full-page view, the Back button would send them to the top of the list, and they'd lose their filters. Now they can check sizes on several items quickly and pick up exactly where they left off.
- **Business:** less friction per product view means more items viewed per visit, and more chances to find something to buy. Keeping the context also lowers the chance a shopper gives up mid-browse.

## Frontend 2: "Return to Full Menu" for chat-filtered results

**What was added**
- When the assistant fills the page with search results (e.g., "what t-shirts do you have?"), the Products page shows a clear **"From Your Chat"** banner. It includes the results title, a count, and the shopper's own question: "T-Shirts in Stock · 25 items match 'what t-shirts do you have available'".
- A **"← Return to Full Menu"** button in the banner clears the chat filter and brings back all products with the normal search box and category filters.
- Other exits also work:
  - clicking **Products** in the nav, or any category chip;
  - the browser **Back** button;
  - the results are reachable again from the chat bubble's **"View N Items on Page"** button.
- The results survive a page refresh (`sessionStorage`) and stay behind the product pop-up (Frontend 1).
- Code: `pages/Products.tsx`, `components/ChatResultsProvider.tsx`, `chat-results-context.ts`, `ChatWidget.showOnPage()`.

**Why it helps**
- **Shopper:** an AI that silently changes the page can feel confusing or trapping. The banner explains *why* the page changed, and the button gives a one-click way out, so the shopper stays in control.
- **Business:** shoppers trust and keep using a chat feature they can easily undo. Clear labeling also avoids "where did the other products go?" moments, which could otherwise look like a small catalogue.

---

## Backend 3: One-call product snapshot (`get_product_snapshot`)

**What was added**
- **A new agent tool** in `tools.py`: `get_product_snapshot(product_ids, size=None, include_alternatives=True)`. For **up to 6 products in one call**, it returns a `ProductSnapshot` per product:
  - `details`: full description, category, colors, price, availability, stock by size (with `in_stock` / `low_stock` / `sold_out` status);
  - `stock`: a `StockReport` for the requested size (`requested_size_status`, quantity, and a ready-to-say `note`);
  - `alternatives`: up to 3 similar **in-stock** items (in the requested size), added **only when** the item or size is unavailable.

  It also returns a `not_found` list, with suggestions for any id or name that doesn't match.
- **One database read per batch:** the catalogue is loaded once for all requested products (batch of 3 measured at ~5 ms).
- **Shared building blocks:** `_details()`, `_stock_report()`, and `_alternatives()` are now shared by the snapshot and the older single-purpose tools, so all of them always give the same answers.
- **New return types** in `models.py`: `ProductSnapshot` and `ProductSnapshotResult`.
- **Protocol change** in `prompts/prompt.md`:
  - `get_product_snapshot` is the **default** for any question about specific products.
  - The agent should aim for **at most two tool calls** per answer (`search_products` → `get_product_snapshot`), or one when it already knows the product (e.g., the one being viewed).
  - It should never chain `get_product_details` → `check_stock` → `find_alternatives`.

**Why it helps**
- **Faster:** every tool call costs a full model round trip (the model reads the result, then decides the next step). A question like "Is the Ice Hockey hoodie available in medium?" used to take **3 tool calls in sequence** (details → stock → alternatives, each followed by another model request). Now it's **1 call**. Fewer round trips means a noticeably shorter wait in the chat.
- **Cheaper:** each extra model request re-sends the whole conversation, instructions, and tool definitions. Cutting 2 of those requests per product question cuts input tokens (cost) roughly in proportion. The snapshot payload is also slightly smaller than the three separate results combined (2,718 vs 2,826 characters for the same item), because it doesn't repeat the product header three times.
- **More accurate:** alternatives arrive automatically exactly when something is sold out, so the agent always has an in-stock backup ready. It no longer has to remember to make a separate call.
- **Comparisons:** "Which is cheaper, the Yale Dad hoodie or the crewneck, and do they have XL?" is answered from **one** batched call.

## Backend 4: Typo-tolerant search

**What was added**
- **Automatic correction:** `search_products` now corrects misspellings before searching. Each query word that doesn't appear anywhere in the catalogue is matched to the **closest real catalogue word** with Python's `difflib` (similarity ≥ 0.75; words of 4+ letters; numbers are never "corrected"). The vocabulary is built from product names, types, descriptions, colors, and search tags, plus common shopper words.
- **The color filter is corrected too** ("nvay" → navy).
- **New shopper-word synonyms:** "hoody"/"hoodys" → hoodies, "sweater" → sweaters/crewnecks/fleece.
- **Precision fix:** words with a synonym entry now match **only** through their synonyms. Before, "tshirt" matched inside "swea*tshirt*" and returned 84 items instead of the 25 T-shirts.
- **New result shape** (`SearchResults` in `models.py`):
  - `results`;
  - `total_matches` (before the limit);
  - `corrections` (e.g., `{"sweatshit": "sweatshirt"}`);
  - a friendly `note` ("Showing results for 'sweatshirt' (typed 'sweatshit')").
- **Name typos in the other tools:** the product-lookup tools use the same correction when a product name is misspelled. "Yale Dad Hoddie" suggests `yale-dad-hoodie`.
- **Prompt rules:** pass the customer's words as typed; answer for the corrected word and mention it lightly once; don't lecture about spelling.

**Results (offline, real catalogue)**

| Shopper typed | Corrected to | Matches | Top result |
|---|---|---|---|
| hoody | (synonym) hoodie | 27 | Basic Hoodie Big Yale |
| sweatshit | sweatshirt | 67 | Crewnecks & hoodies |
| quater zip | quarter | 20 | Benjamin Franklin 1/4 Zip |
| Saybrok | saybrook | 3 | Saybrook College Crewneck |
| hocky | hockey | 5 | Ice Hockey Left Chest Hoodie |
| tshrit | tshirt | 25 | 2025 Yale vs Harvard T-Shirt |
| crewnek | crewneck | 39 | Baseball Left Chest Crewneck |
| hoodie + color "nvay" | navy | 25 | Basic Hoodie Big Yale |
| zzzqqq (nonsense) | none | 0 | (correctly nothing) |

Before this change, every misspelled row above returned **0 matches**, except "quater zip", which still matched on the word "zip" alone.

**Why it helps**
- **Shopper:** people type fast on phones and misspell college names, garment words, and colors. They now get the right products on the first try instead of "we don't carry that," which would be both wrong and frustrating.
- **Business:** a false "no results" is a lost sale. Accurate first searches also mean the agent doesn't have to guess, retry with different spellings, or ask clarifying questions, which saves model calls (**cheaper and faster**). The corrections map is also a record of what shoppers commonly mistype, which merchandising could use later.

---

## Verification summary
- **Snapshot:** a batch of `["ice-hockey-left-chest-hoodie", "basic-hoodie-big-yale", "not-a-real-id"]` in size "medium" returned:
  - Ice Hockey: M **sold out**, with 3 hoodie alternatives that have M in stock;
  - Basic Hoodie: M **low stock (5)**, no alternatives needed;
  - the fake id in `not_found`.
- **Typo search:** all cases in the table above.
- **Agent wiring:** 8 tools are registered. `/api/chat` ran with PydanticAI's `TestModel` calling `search_products` + `get_product_snapshot` → 200 (no live LLM call).
- **Backend health:** the server reloaded cleanly with no errors.
