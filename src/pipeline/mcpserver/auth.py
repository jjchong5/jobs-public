"""API key auth + in-memory rate limiting for the MCP server.

v1/single-process only: the rate limiter is a plain in-memory dict, not
Redis/distributed -- fine since the server runs as one process (see plan).
Keys live in their own `mcp_api_keys` table (additive migration in
storage/db.py-style pattern, see init_keys_table below) -- separate from
`items`/`preference_profiles`, nothing existing touched.
"""
import hashlib
import logging
import secrets
import sqlite3
import time
from collections import defaultdict
from datetime import datetime, timezone

from pipeline.storage.db import DB_PATH

logger = logging.getLogger(__name__)

REQUESTS_PER_MINUTE = 60
EXPORT_CALLS_PER_DAY = 5

# in-memory: {key_hash: [timestamps]} for the per-minute limiter,
# {key_hash: [date_str, count]} for the daily export limiter.
_request_log: dict[str, list[float]] = defaultdict(list)
_export_log: dict[str, list] = defaultdict(lambda: ["", 0])


def hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def generate_key() -> str:
    return "jobs_mcp_" + secrets.token_urlsafe(32)


def get_keys_connection() -> sqlite3.Connection:
    """Separate writable connection scoped only to mcp_api_keys -- key
    management is the one legitimate write path this server needs, kept
    apart from db_read.py's strictly-read-only connection used for item
    queries. Always targets the local DB_PATH regardless of
    PIPELINE_DB_REMOTE_PATH: key management is an author-run CLI action on this
    machine, not something the server does against a remote mini copy.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.row_factory = sqlite3.Row
    init_keys_table(conn)
    return conn


def init_keys_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """CREATE TABLE IF NOT EXISTS mcp_api_keys (
             id INTEGER PRIMARY KEY AUTOINCREMENT,
             key_hash TEXT UNIQUE NOT NULL,
             label TEXT,
             created_at TEXT NOT NULL,
             revoked_at TEXT
           )"""
    )
    conn.commit()


def validate_key(conn: sqlite3.Connection, raw_key: str | None) -> tuple[bool, str]:
    """Returns (ok, key_hash_or_error_message)."""
    if not raw_key:
        return False, "missing API key"
    key_hash = hash_key(raw_key)
    row = conn.execute(
        "SELECT id FROM mcp_api_keys WHERE key_hash = ? AND revoked_at IS NULL",
        (key_hash,),
    ).fetchone()
    if not row:
        return False, "invalid or revoked API key"
    return True, key_hash


def check_rate_limit(key_hash: str) -> tuple[bool, str]:
    now = time.time()
    window = _request_log[key_hash]
    window[:] = [t for t in window if now - t < 60]
    if len(window) >= REQUESTS_PER_MINUTE:
        return False, f"rate limit exceeded ({REQUESTS_PER_MINUTE}/min)"
    window.append(now)
    return True, ""


def check_export_limit(key_hash: str) -> tuple[bool, str]:
    today = datetime.now(timezone.utc).date().isoformat()
    entry = _export_log[key_hash]
    if entry[0] != today:
        entry[0], entry[1] = today, 0
    if entry[1] >= EXPORT_CALLS_PER_DAY:
        return False, f"export limit exceeded ({EXPORT_CALLS_PER_DAY}/day)"
    entry[1] += 1
    return True, ""
