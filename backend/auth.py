"""Password hashing, login sessions, and login rate limiting for Campus Customs accounts."""

from __future__ import annotations

import hashlib
import hmac
import secrets
import sqlite3
import time
from datetime import datetime, timedelta, timezone

ALGORITHM = "pbkdf2_sha256"
# OWASP's current recommendation for PBKDF2-HMAC-SHA256.
ITERATIONS = 600_000
# Hashes seeded in the provided database use the 3-part format "pbkdf2_sha256$salt$hash" at 120,000 iterations.
LEGACY_ITERATIONS = 120_000
SALT_BYTES = 16

SESSION_COOKIE = "cc_session"
SESSION_DAYS = 7


def hash_password(password: str, *, iterations: int = ITERATIONS, salt: str | None = None) -> str:
    """Return "pbkdf2_sha256$<iterations>$<salt>$<hex digest>" using a fresh random salt."""
    salt = salt or secrets.token_hex(SALT_BYTES)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterations).hex()
    return f"{ALGORITHM}${iterations}${salt}${digest}"


def _parse(stored: str) -> tuple[int, str, str] | None:
    parts = stored.split("$")
    if len(parts) == 3 and parts[0] == ALGORITHM:
        return LEGACY_ITERATIONS, parts[1], parts[2]
    if len(parts) == 4 and parts[0] == ALGORITHM and parts[1].isdigit():
        return int(parts[1]), parts[2], parts[3]
    return None


def verify_password(password: str, stored: str) -> bool:
    """Re-hash the attempt with the stored salt and compare in constant time."""
    parsed = _parse(stored)
    if parsed is None:
        return False
    iterations, salt, expected = parsed
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterations).hex()
    return hmac.compare_digest(digest, expected)


# Checked when an email is unknown, so "no such user" takes as long as "wrong password".
DUMMY_HASH = hash_password(secrets.token_hex(16))


def ensure_sessions_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            token_hash TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            expires_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
    )


def _token_hash(token: str) -> str:
    # Only a SHA-256 of the session token is stored, so a leaked database can't be used to hijack sessions.
    return hashlib.sha256(token.encode()).hexdigest()


def create_session(conn: sqlite3.Connection, user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    expires = (datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS)).strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("DELETE FROM sessions WHERE expires_at <= datetime('now')")
    conn.execute(
        "INSERT INTO sessions (token_hash, user_id, expires_at) VALUES (?, ?, ?)",
        (_token_hash(token), user_id, expires),
    )
    return token


def session_user_id(conn: sqlite3.Connection, token: str) -> int | None:
    row = conn.execute(
        "SELECT user_id FROM sessions WHERE token_hash = ? AND expires_at > datetime('now')",
        (_token_hash(token),),
    ).fetchone()
    return row[0] if row else None


def delete_session(conn: sqlite3.Connection, token: str) -> None:
    conn.execute("DELETE FROM sessions WHERE token_hash = ?", (_token_hash(token),))


class LoginRateLimiter:
    """Blocks a client/email pair after too many failed logins within a time window (in memory)."""

    def __init__(self, max_failures: int = 5, window_seconds: int = 15 * 60) -> None:
        self.max_failures = max_failures
        self.window_seconds = window_seconds
        self._failures: dict[str, list[float]] = {}

    def _recent(self, key: str) -> list[float]:
        now = time.monotonic()
        recent = [t for t in self._failures.get(key, []) if now - t < self.window_seconds]
        self._failures[key] = recent
        return recent

    def is_blocked(self, key: str) -> bool:
        return len(self._recent(key)) >= self.max_failures

    def record_failure(self, key: str) -> None:
        self._recent(key).append(time.monotonic())

    def reset(self, key: str) -> None:
        self._failures.pop(key, None)
