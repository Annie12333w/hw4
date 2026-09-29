"""Append-only audit trail of agent runs, stored as a JSON array in output/audit_trail.json.

Each chat message becomes one AuditRecord: time, every tool call (short args/result), and the stop reason.
New records are added by rewriting only the file's closing "]"; existing records are never modified or removed.
"""

from __future__ import annotations

import json
import logging
import os
import re
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, RetryPromptPart, ToolCallPart, ToolReturnPart

from models import (
    AlternativeSuggestions,
    AuditRecord,
    CatalogueOverview,
    CustomerProfile,
    PastConversation,
    ProductDetails,
    ProductNotFound,
    ProductSnapshotResult,
    SearchResults,
    StockReport,
    ToolCallRecord,
)

AUDIT_PATH = Path(os.getenv("AUDIT_TRAIL_PATH") or Path(__file__).resolve().parent.parent / "output" / "audit_trail.json")
MAX_TEXT = 160
OUTPUT_TOOL_PREFIX = "final_result"  # PydanticAI's structured-output tool; recorded as the stop, not as a tool

logger = logging.getLogger("campus_customs.audit")
_lock = threading.Lock()
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_LONG_NUMBER = re.compile(r"\d[\d -]{6,}\d")  # card, phone, or ID numbers


def redact(text: str, limit: int = MAX_TEXT) -> str:
    """Hide emails and long digit runs, collapse whitespace, and trim."""
    clean = _LONG_NUMBER.sub("[number]", _EMAIL.sub("[email]", " ".join(str(text).split())))
    return clean if len(clean) <= limit else clean[: limit - 1] + "…"


def summarize_result(content: Any) -> str:
    """A one-line, privacy-safe description of a tool result."""
    if isinstance(content, SearchResults):
        top = ", ".join(r.product_id for r in content.results[:3])
        fixes = f"; corrected {content.corrections}" if content.corrections else ""
        return redact(f"{content.total_matches} matches, returned {len(content.results)} (top: {top}){fixes}")
    if isinstance(content, ProductSnapshotResult):
        parts = [
            f"{s.details.product_id} ${s.details.price:g} "
            f"{s.stock.requested_size or 'all sizes'}={s.stock.requested_size_status or s.stock.availability}"
            f"{f' qty {s.stock.requested_size_quantity}' if s.stock.requested_size_quantity is not None else ''}"
            f"{f' +{len(s.alternatives)} alts' if s.alternatives else ''}"
            for s in content.snapshots
        ]
        if content.not_found:
            parts.append(f"not found: {', '.join(n.query for n in content.not_found)}")
        return redact("; ".join(parts))
    if isinstance(content, StockReport):
        return redact(content.note)
    if isinstance(content, ProductDetails):
        return redact(f"{content.product_id} ${content.price:g} {content.availability}, in stock: {content.in_stock_sizes}")
    if isinstance(content, AlternativeSuggestions):
        return redact(f"{len(content.alternatives)} alternatives for {content.original_product_id}")
    if isinstance(content, ProductNotFound):
        return redact(f"not found: {content.query}; {len(content.suggestions)} suggestions")
    if isinstance(content, CustomerProfile):
        return f"profile for user #{content.user_id} (returning={content.is_returning})"  # no name/email in the log
    if isinstance(content, PastConversation):
        return f"{len(content.messages)} of {content.total_saved} saved messages"
    if isinstance(content, CatalogueOverview):
        return f"{content.total_products} products, ${content.min_price:g}-${content.max_price:g}"
    if isinstance(content, BaseModel):
        return redact(content.model_dump_json())
    if isinstance(content, list):
        return f"{len(content)} items"
    return redact(str(content))


def _args(part: ToolCallPart) -> str:
    try:
        return redact(json.dumps(part.args_as_dict(), separators=(",", ":")))
    except Exception:
        return redact(str(part.args))


def _iso(ts: datetime | None) -> str:
    return ts.isoformat(timespec="seconds") if ts else ""


def tool_calls_from(messages: list[ModelMessage]) -> tuple[list[ToolCallRecord], int, int, int, int]:
    """Pair each tool call with its result. Returns (calls, retries, model_requests, input_tokens, output_tokens)."""
    returns: dict[str, str] = {}
    retries = 0
    for msg in messages:
        if isinstance(msg, ModelRequest):
            for part in msg.parts:
                if isinstance(part, ToolReturnPart):
                    returns[part.tool_call_id] = summarize_result(part.content)
                elif isinstance(part, RetryPromptPart):
                    retries += 1
                    if part.tool_call_id:
                        returns[part.tool_call_id] = "retry: " + redact(str(part.content))

    calls: list[ToolCallRecord] = []
    requests = input_tokens = output_tokens = 0
    for msg in messages:
        if not isinstance(msg, ModelResponse):
            continue
        requests += 1
        input_tokens += msg.usage.input_tokens or 0
        output_tokens += msg.usage.output_tokens or 0
        for part in msg.parts:
            if isinstance(part, ToolCallPart) and not part.tool_name.startswith(OUTPUT_TOOL_PREFIX):
                calls.append(
                    ToolCallRecord(
                        time=_iso(msg.timestamp),
                        tool=part.tool_name,
                        args=_args(part),
                        result=returns.get(part.tool_call_id, "(no result: run stopped)"),
                    )
                )
    return calls, retries, requests, input_tokens, output_tokens


def append_record(record: AuditRecord, path: Path = AUDIT_PATH) -> None:
    """Append one record to the JSON array without touching earlier records. Never raises."""
    entry = "\n".join("  " + line for line in record.model_dump_json(indent=2).splitlines())
    try:
        with _lock:
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists() or path.stat().st_size == 0:
                path.write_text("[\n" + entry + "\n]\n", encoding="utf-8")
                return
            with path.open("r+b") as f:
                # Walk back from the end, past whitespace, to the closing bracket.
                pos = f.seek(0, os.SEEK_END)
                ch = before = b""
                while pos > 0:
                    f.seek(pos - 1)
                    ch = f.read(1)
                    if not ch.isspace():
                        break
                    pos -= 1
                if ch != b"]":
                    raise ValueError("audit trail does not end with ']'; refusing to modify it")
                close = pos - 1
                # Is the array empty? Look at the previous non-space character.
                prev = close
                while prev > 0:
                    f.seek(prev - 1)
                    before = f.read(1)
                    if not before.isspace():
                        break
                    prev -= 1
                separator = "\n" if before == b"[" else ",\n"
                f.seek(close)
                f.write((separator + entry + "\n]\n").encode("utf-8"))
                f.truncate()
    except Exception:
        # Auditing must never break the chat. Keep the record in a side file instead of losing it.
        logger.exception("Could not append to %s", path)
        try:
            with path.with_suffix(".recovery.jsonl").open("a", encoding="utf-8") as side:
                side.write(record.model_dump_json() + "\n")
        except Exception:
            logger.exception("Could not write audit recovery file")
