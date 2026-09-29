"""Pydantic models shared by the API, the agent's tools, and the agent's structured output."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------


class StockLevel(BaseModel):
    size: str
    quantity: int


class ProductCard(BaseModel):
    """Everything the website needs to draw a product card or the product pop-up."""

    product_id: str
    name: str
    garment_type: str
    description: str
    colors: list[str]
    search_tags: list[str]
    image_file_path: str
    image_url: str
    price: float
    inventory: list[StockLevel]
    total_stock: int


# ---------------------------------------------------------------------------
# Chat API
# ---------------------------------------------------------------------------


class ChatTurn(BaseModel):
    """One earlier message in the conversation, sent by the website as context."""

    role: Literal["user", "assistant"]
    content: str = Field(max_length=4000)


PageType = Literal["home", "products", "chat_results", "product", "about", "login", "create_account", "other"]


class PageContext(BaseModel):
    """What the customer is looking at when they send a message (sent by the website; treated as untrusted)."""

    path: str = Field(max_length=300)
    page_type: PageType
    product_id: str | None = Field(default=None, max_length=120, description="Set on a product page or pop-up.")
    category: str | None = Field(default=None, max_length=60, description="Active category filter on the Products page.")
    search: str | None = Field(default=None, max_length=100, description="Text in the Products page search box.")
    results_title: str | None = Field(default=None, max_length=80, description="Heading of chat results on the page.")
    results_count: int | None = Field(default=None, ge=0, le=500)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    history: list[ChatTurn] = Field(
        default_factory=list,
        max_length=40,
        description="Recent turns from the browser; used for guests only (logged-in history comes from the database).",
    )
    page_context: PageContext | None = None


class ProductMatches(BaseModel):
    """Search results the website shows as a full product grid on the Products page."""

    title: str = Field(description="Heading for the results grid, e.g. 'T-Shirts in Stock'.")
    query: str = Field(description="The customer message that produced these results.")
    total: int
    products: list[ProductCard]


class ChatResponse(BaseModel):
    reply: str
    products: list[ProductCard] = Field(default_factory=list)
    page_results: ProductMatches | None = None


class ChatHistoryMessage(BaseModel):
    id: int
    role: Literal["user", "assistant"]
    content: str
    products: list[ProductCard] = Field(default_factory=list)
    page_results: ProductMatches | None = None
    created_at: str


class ChatHistoryResponse(BaseModel):
    messages: list[ChatHistoryMessage]


# ---------------------------------------------------------------------------
# Agent: dependencies, structured output, and tool results
# ---------------------------------------------------------------------------


class CustomerProfile(BaseModel):
    """The logged-in shopper, as the agent sees them. No password hash, no session data."""

    user_id: int
    first_name: str
    last_name: str | None
    email: str
    member_since: str = Field(description="Account creation date (YYYY-MM-DD).")
    saved_message_count: int = Field(description="Chat messages saved from earlier conversations.")
    is_returning: bool = Field(description="True if they have chatted with the assistant before.")


class PastMessage(BaseModel):
    date: str
    role: Literal["user", "assistant"]
    content: str = Field(description="Message text, trimmed to 300 characters.")
    product_ids: list[str] = Field(description="Products shown with this message, if any.")


class PastConversation(BaseModel):
    messages: list[PastMessage]
    total_saved: int


@dataclass
class ShopDeps:
    """Per-request context handed to the agent's instructions and tools."""

    db_path: Path
    customer: CustomerProfile | None = None
    page: PageContext | None = None
    viewing_product: ProductSummary | None = None


MAX_PAGE_RESULTS = 40


class PageResults(BaseModel):
    """Part of the agent's output: the matches to lay out on the Products page."""

    title: str = Field(max_length=80, description="Short heading for the grid, e.g. 'T-Shirts in Stock'.")
    product_ids: list[str] = Field(
        max_length=MAX_PAGE_RESULTS,
        description="Every matching product_id from search_products, best match first.",
    )


class AgentReply(BaseModel):
    """Structured output the agent must return for every chat message."""

    reply: str = Field(description="The message shown to the customer, in the Campus Customs voice.")
    product_ids: list[str] = Field(
        default_factory=list,
        max_length=6,
        description="product_id values (from tool results) to show as small cards inside the chat, in the order mentioned.",
    )
    page_results: PageResults | None = Field(
        default=None,
        description="Set for browse/category searches so the matches appear as a product grid on the page; null otherwise.",
    )


StockStatus = Literal["in_stock", "low_stock", "sold_out"]
SizeStatus = Literal["in_stock", "low_stock", "sold_out", "not_offered"]
Availability = Literal["in_stock", "sold_out"]


class SizeStock(BaseModel):
    """Stock for one size, with a ready-made status so the agent never has to interpret raw numbers."""

    size: str
    quantity: int
    status: StockStatus = Field(description="sold_out = 0 left, low_stock = 1-5 left, in_stock = more than 5.")


class ProductSummary(BaseModel):
    """Compact search result so the agent can compare many products cheaply."""

    product_id: str
    name: str
    category: str
    garment_type: str
    price: float
    summary: str = Field(description="First sentence of the product description.")
    colors: list[str]
    availability: Availability
    sizes_in_stock: list[str]
    total_stock: int


class ProductDetails(BaseModel):
    """Everything the agent needs to describe one product and answer price/size/stock questions."""

    product_id: str
    name: str
    category: str
    garment_type: str
    description: str
    price: float
    colors: list[str]
    availability: Availability
    total_stock: int
    stock_by_size: list[SizeStock]
    in_stock_sizes: list[str]
    sold_out_sizes: list[str]


class StockReport(BaseModel):
    """Live stock for one product, optionally focused on the size the customer asked about."""

    product_id: str
    name: str
    price: float
    availability: Availability
    total_stock: int
    stock_by_size: list[SizeStock]
    in_stock_sizes: list[str]
    sold_out_sizes: list[str]
    requested_size: str | None = Field(default=None, description="The requested size, normalized (e.g. 'medium' -> 'M').")
    requested_size_status: SizeStatus | None = None
    requested_size_quantity: int | None = Field(
        default=None, description="Units left in the requested size (0 = sold out); null if not offered or not asked."
    )
    note: str = Field(description="One plain-language sentence stating the stock facts; safe to relay to the customer.")


class ProductNotFound(BaseModel):
    """Returned instead of a product when an id or name doesn't match anything in the catalogue."""

    query: str
    message: str
    suggestions: list[ProductSummary] = Field(description="Closest matches by name, to pick the right product_id from.")


class AlternativeSuggestions(BaseModel):
    """Similar in-stock products for when the requested item or size is unavailable."""

    original_product_id: str
    original_name: str
    size: str | None
    reason: str
    alternatives: list[ProductSummary]


class SearchResults(BaseModel):
    """search_products result: matches plus any spelling corrections that were applied."""

    results: list[ProductSummary]
    total_matches: int = Field(description="Matches before the limit was applied.")
    corrections: dict[str, str] = Field(
        default_factory=dict, description="Misspelled word -> the catalogue word it was corrected to."
    )
    note: str | None = Field(default=None, description="e.g. \"Showing results for 'sweatshirt' (you typed 'sweatshit').\"")


class ProductSnapshot(BaseModel):
    """Everything about one product in one object: details, stock, the asked-about size, and backups."""

    details: ProductDetails
    stock: StockReport
    alternatives: list[ProductSummary] = Field(
        default_factory=list,
        description="Similar in-stock items; filled only when the product or requested size is unavailable.",
    )


class ProductSnapshotResult(BaseModel):
    snapshots: list[ProductSnapshot]
    not_found: list[ProductNotFound] = Field(default_factory=list)


class CatalogueOverview(BaseModel):
    total_products: int
    categories: dict[str, int] = Field(description="Shop category -> number of products.")
    sizes: list[str]
    min_price: float
    max_price: float
    colors: list[str]


# ---------------------------------------------------------------------------
# Audit trail (output/audit_trail.json)
# ---------------------------------------------------------------------------

StopReason = Literal["final_output", "usage_limit", "agent_unavailable", "model_error", "error"]


class ToolCallRecord(BaseModel):
    """One tool call inside an agent run, with short, privacy-safe summaries."""

    time: str = Field(description="UTC ISO time the model requested the tool.")
    tool: str
    args: str = Field(description="Arguments as compact JSON, redacted and trimmed to 160 characters.")
    result: str = Field(description="Short summary of what the tool returned (or the retry message).")


class AuditRecord(BaseModel):
    """One agent loop (one chat message) in the append-only audit trail."""

    run_id: str
    started_at: str
    finished_at: str
    duration_ms: int
    model: str
    customer: str = Field(description='"user #<id>" or "guest"; never names or emails.')
    page: str = Field(description="page_type, plus product_id when on a product.")
    message_preview: str = Field(description="Customer message, redacted (emails/long numbers) and trimmed.")
    model_requests: int
    tool_calls: list[ToolCallRecord]
    retries: int = Field(description="Times the model was sent back to fix a tool call or its final answer.")
    input_tokens: int
    output_tokens: int
    stop_reason: StopReason
    stop_detail: str | None = None
    reply_preview: str | None = None
    chat_cards: int = 0
    page_results: int = 0


# ---------------------------------------------------------------------------
# Accounts
# ---------------------------------------------------------------------------


class RegisterRequest(BaseModel):
    first_name: str = Field(max_length=50)
    last_name: str = Field(max_length=50)
    email: str = Field(max_length=254)
    password: str = Field(max_length=128)
    confirm_password: str = Field(max_length=128)


class LoginRequest(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(max_length=128)


class UserOut(BaseModel):
    """Public account fields only; password_hash never leaves the backend."""

    id: int
    email: str
    name: str
    first_name: str | None
    last_name: str | None
    created_at: str


class AuthResponse(BaseModel):
    user: UserOut
