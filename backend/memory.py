"""Customer memory: saved chat history (chat_messages table) and the customer profile the agent sees."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from pathlib import Path

from models import ChatResponse, ChatTurn, CustomerProfile, PastMessage, UserOut

PAST_MESSAGE_CHARS = 300


def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_chat_schema(conn: sqlite3.Connection) -> None:
    """Add what Problem 8 needs to the provided chat_messages table (safe to run on every start)."""
    columns = {row[1] for row in conn.execute("PRAGMA table_info(chat_messages)")}
    if "page_results_json" not in columns:
        conn.execute("ALTER TABLE chat_messages ADD COLUMN page_results_json TEXT")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_messages_user ON chat_messages (user_id, id)")


def product_ids_from_json(raw: str | None) -> list[str]:
    """products_json holds a list of product objects; pull out their ids (tolerates bad rows)."""
    if not raw:
        return []
    try:
        return [p["product_id"] for p in json.loads(raw) if isinstance(p, dict) and "product_id" in p]
    except (json.JSONDecodeError, TypeError):
        return []


def build_customer_profile(db_path: Path, user: UserOut) -> CustomerProfile:
    with closing(_connect(db_path)) as conn:
        count = conn.execute("SELECT COUNT(*) FROM chat_messages WHERE user_id = ?", (user.id,)).fetchone()[0]
    return CustomerProfile(
        user_id=user.id,
        first_name=user.first_name or user.name.split()[0],
        last_name=user.last_name,
        email=user.email,
        member_since=user.created_at[:10],
        saved_message_count=count,
        is_returning=count > 0,
    )


def load_recent_turns(db_path: Path, user_id: int, limit: int) -> list[ChatTurn]:
    """The last `limit` saved messages, oldest first, as conversation context for the agent."""
    with closing(_connect(db_path)) as conn:
        rows = conn.execute(
            "SELECT role, content FROM chat_messages WHERE user_id = ? ORDER BY id DESC LIMIT ?", (user_id, limit)
        ).fetchall()
    return [ChatTurn(role=r["role"], content=r["content"][:4000]) for r in reversed(rows)]


def load_history_rows(db_path: Path, user_id: int, limit: int) -> list[sqlite3.Row]:
    with closing(_connect(db_path)) as conn:
        rows = conn.execute(
            "SELECT id, role, content, products_json, page_results_json, created_at FROM chat_messages "
            "WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    return list(reversed(rows))


def load_past_messages(db_path: Path, user_id: int, limit: int) -> tuple[list[PastMessage], int]:
    with closing(_connect(db_path)) as conn:
        total = conn.execute("SELECT COUNT(*) FROM chat_messages WHERE user_id = ?", (user_id,)).fetchone()[0]
    messages = [
        PastMessage(
            date=row["created_at"][:10],
            role=row["role"],
            content=row["content"][:PAST_MESSAGE_CHARS],
            product_ids=product_ids_from_json(row["products_json"]),
        )
        for row in load_history_rows(db_path, user_id, limit)
    ]
    return messages, total


def save_exchange(db_path: Path, user_id: int, message: str, response: ChatResponse) -> None:
    """Store the customer's message and the assistant's reply together (one transaction)."""
    products_json = json.dumps([p.model_dump() for p in response.products]) if response.products else None
    page_json = None
    if response.page_results:
        page_json = json.dumps(
            {
                "title": response.page_results.title,
                "query": response.page_results.query,
                "product_ids": [p.product_id for p in response.page_results.products],
            }
        )
    with closing(_connect(db_path)) as conn:
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content) VALUES (?, 'user', ?)",
            (user_id, message),
        )
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content, products_json, page_results_json) "
            "VALUES (?, 'assistant', ?, ?, ?)",
            (user_id, response.reply, products_json, page_json),
        )
        conn.commit()


def clear_history(db_path: Path, user_id: int) -> int:
    with closing(_connect(db_path)) as conn:
        deleted = conn.execute("DELETE FROM chat_messages WHERE user_id = ?", (user_id,)).rowcount
        conn.commit()
    return deleted
