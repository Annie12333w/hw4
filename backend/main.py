"""Campus Customs API: products, images, accounts, and the shop assistant chat.

Run from the backend folder:  uvicorn main:app --reload --port 8000
"""

from __future__ import annotations

import json
import logging
import os
import re
import sqlite3
from contextlib import closing

from fastapi import Cookie, FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic_ai.exceptions import UsageLimitExceeded

import auth
import memory
from agent import MAX_HISTORY_TURNS, AgentUnavailableError, run_chat
from models import (
    AgentReply,
    AuthResponse,
    ChatHistoryMessage,
    ChatHistoryResponse,
    ChatRequest,
    ChatResponse,
    LoginRequest,
    ProductCard,
    ProductMatches,
    RegisterRequest,
    ShopDeps,
    UserOut,
)
from tools import DB_PATH, IMAGES_DIR, get_connection, load_products, matches, products_by_ids, summarize_product

logger = logging.getLogger("campus_customs")

MIN_PASSWORD_LENGTH = 8
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
# Set COOKIE_SECURE=true when served over HTTPS so the session cookie is never sent in plain text.
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"
CHAT_HISTORY_LIMIT = 50

app = FastAPI(title="Campus Customs API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# catalogue.image_file_path is "products/<file>.jpg", so images are served at /media/products/<file>.jpg
app.mount("/media/products", StaticFiles(directory=IMAGES_DIR), name="product-images")

with closing(get_connection()) as _conn:
    auth.ensure_sessions_table(_conn)
    memory.ensure_chat_schema(_conn)
    _conn.commit()

login_limiter = auth.LoginRateLimiter()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------


@app.get("/api/products", response_model=list[ProductCard])
def list_products(q: str | None = Query(default=None, description="Keywords to match")) -> list[ProductCard]:
    products = load_products()
    if q and q.strip():
        products = [p for p in products if matches(p, q)]
    return products


@app.get("/api/products/{product_id}", response_model=ProductCard)
def get_product(product_id: str) -> ProductCard:
    found = load_products(product_id)
    if not found:
        raise HTTPException(status_code=404, detail="Product not found")
    return found[0]


# ---------------------------------------------------------------------------
# Accounts
# ---------------------------------------------------------------------------


def _fetch_user(conn: sqlite3.Connection, user_id: int) -> UserOut:
    row = conn.execute(
        "SELECT id, email, name, first_name, last_name, created_at FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    return UserOut(**dict(row))


def _user_from_session(session: str | None) -> UserOut | None:
    if not session:
        return None
    with closing(get_connection()) as conn:
        user_id = auth.session_user_id(conn, session)
        return _fetch_user(conn, user_id) if user_id is not None else None


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        auth.SESSION_COOKIE,
        token,
        max_age=auth.SESSION_DAYS * 24 * 60 * 60,
        httponly=True,  # page scripts can't read it, which limits damage from XSS
        samesite="lax",  # not sent on cross-site form posts (CSRF protection)
        secure=COOKIE_SECURE,
        path="/",
    )


@app.post("/api/auth/register", response_model=AuthResponse, status_code=201)
def register(body: RegisterRequest, response: Response) -> AuthResponse:
    first_name = body.first_name.strip()
    last_name = body.last_name.strip()
    email = body.email.strip().lower()
    if not first_name or not last_name:
        raise HTTPException(400, "Please enter your first and last name.")
    if not EMAIL_PATTERN.match(email):
        raise HTTPException(400, "Please enter a valid email address.")
    if len(body.password) < MIN_PASSWORD_LENGTH:
        raise HTTPException(400, f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
    if body.password != body.confirm_password:
        raise HTTPException(400, "Passwords do not match.")

    password_hash = auth.hash_password(body.password)
    with closing(get_connection()) as conn:
        if conn.execute("SELECT 1 FROM users WHERE lower(email) = ?", (email,)).fetchone():
            raise HTTPException(409, "An account with this email already exists. Try logging in instead.")
        try:
            cur = conn.execute(
                "INSERT INTO users (name, email, password_hash, first_name, last_name) VALUES (?, ?, ?, ?, ?)",
                (f"{first_name} {last_name}", email, password_hash, first_name, last_name),
            )
        except sqlite3.IntegrityError:
            raise HTTPException(409, "An account with this email already exists. Try logging in instead.")
        user_id = cur.lastrowid
        token = auth.create_session(conn, user_id)
        conn.commit()
        user = _fetch_user(conn, user_id)

    _set_session_cookie(response, token)
    return AuthResponse(user=user)


@app.post("/api/auth/login", response_model=AuthResponse)
def login(body: LoginRequest, request: Request, response: Response) -> AuthResponse:
    email = body.email.strip().lower()
    limiter_key = f"{request.client.host if request.client else 'unknown'}|{email}"
    if login_limiter.is_blocked(limiter_key):
        raise HTTPException(429, "Too many failed attempts. Please wait 15 minutes and try again.")

    with closing(get_connection()) as conn:
        row = conn.execute("SELECT id, password_hash FROM users WHERE lower(email) = ?", (email,)).fetchone()
        password_ok = auth.verify_password(body.password, row["password_hash"] if row else auth.DUMMY_HASH)
        if row is None or not password_ok:
            login_limiter.record_failure(limiter_key)
            # Same message either way, so the form can't be used to discover which emails have accounts.
            raise HTTPException(401, "Invalid email or password.")
        login_limiter.reset(limiter_key)
        token = auth.create_session(conn, row["id"])
        conn.commit()
        user = _fetch_user(conn, row["id"])

    _set_session_cookie(response, token)
    return AuthResponse(user=user)


@app.get("/api/auth/me", response_model=AuthResponse)
def current_user(session: str | None = Cookie(default=None, alias=auth.SESSION_COOKIE)) -> AuthResponse:
    user = _user_from_session(session)
    if user is None:
        raise HTTPException(401, "Not logged in.")
    return AuthResponse(user=user)


@app.post("/api/auth/logout", status_code=204)
def logout(response: Response, session: str | None = Cookie(default=None, alias=auth.SESSION_COOKIE)) -> None:
    if session:
        with closing(get_connection()) as conn:
            auth.delete_session(conn, session)
            conn.commit()
    response.delete_cookie(auth.SESSION_COOKIE, path="/")


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------


@app.post("/api/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest, session: str | None = Cookie(default=None, alias=auth.SESSION_COOKIE)
) -> ChatResponse:
    message = body.message.strip()
    if not message:
        raise HTTPException(400, "Please type a message.")
    user = _user_from_session(session)

    # Logged in: the database is the source of truth for history. Guests: only the browser's copy exists.
    history = memory.load_recent_turns(DB_PATH, user.id, MAX_HISTORY_TURNS) if user else body.history
    page = body.page_context
    deps = ShopDeps(
        db_path=DB_PATH,
        customer=memory.build_customer_profile(DB_PATH, user) if user else None,
        page=page,
        # The page only sends an id; resolve it here so the agent gets real catalogue facts about "this" item.
        viewing_product=summarize_product(page.product_id) if page and page.product_id else None,
    )

    try:
        output = await run_chat(message, history, deps)
    except AgentUnavailableError:
        logger.exception("Shop assistant is not configured")
        raise HTTPException(503, "The shop assistant isn't set up yet. Please try again later.")
    except UsageLimitExceeded:
        output = AgentReply(
            reply="Sorry, that one took me too long to look up. Could you ask again a little more specifically?"
        )
    except Exception:
        logger.exception("Shop assistant failed")
        raise HTTPException(502, "The shop assistant is having trouble right now. Please try again in a moment.")

    # Cards come from the database, so prices and stock shown on the page are always real.
    page_results = None
    if output.page_results and output.page_results.product_ids:
        matches_found = products_by_ids(output.page_results.product_ids)
        if matches_found:
            page_results = ProductMatches(
                title=output.page_results.title, query=message, total=len(matches_found), products=matches_found
            )
    response = ChatResponse(
        reply=output.reply, products=products_by_ids(output.product_ids), page_results=page_results
    )
    if user:  # guests' chats are never written to the database
        memory.save_exchange(DB_PATH, user.id, message, response)
    return response


def _stored_page_results(raw: str | None) -> ProductMatches | None:
    if not raw:
        return None
    try:
        data = json.loads(raw)
        products = products_by_ids(list(data["product_ids"]))
        if not products:
            return None
        return ProductMatches(title=data["title"], query=data["query"], total=len(products), products=products)
    except (json.JSONDecodeError, KeyError, TypeError):
        return None


@app.get("/api/chat/history", response_model=ChatHistoryResponse)
def chat_history(session: str | None = Cookie(default=None, alias=auth.SESSION_COOKIE)) -> ChatHistoryResponse:
    user = _user_from_session(session)
    if user is None:
        raise HTTPException(401, "Log in to see your chat history.")
    messages = [
        ChatHistoryMessage(
            id=row["id"],
            role=row["role"],
            content=row["content"],
            # Re-read products so old cards show today's price and stock.
            products=products_by_ids(memory.product_ids_from_json(row["products_json"])),
            page_results=_stored_page_results(row["page_results_json"]),
            created_at=row["created_at"],
        )
        for row in memory.load_history_rows(DB_PATH, user.id, CHAT_HISTORY_LIMIT)
    ]
    return ChatHistoryResponse(messages=messages)


@app.delete("/api/chat/history", status_code=204)
def clear_chat_history(session: str | None = Cookie(default=None, alias=auth.SESSION_COOKIE)) -> None:
    user = _user_from_session(session)
    if user is None:
        raise HTTPException(401, "Log in to manage your chat history.")
    memory.clear_history(DB_PATH, user.id)
