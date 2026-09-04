"""Read-only DB access for the MCP server. Deliberately separate from
storage/db.py's get_connection() (which is read-write and used by the
scheduler/UI/writer queue) -- this module never opens a writable connection,
so a bug here can't corrupt pipeline data no matter what a caller sends.

Path resolution: PIPELINE_DB_REMOTE_PATH env var (Mac mini, once the DB
migration there lands) takes priority; falls back to the existing local
data/pipeline.db used by storage/db.py. Both are opened via the sqlite
read-only URI mode (mode=ro) so even a coding mistake here can't write.
"""
import os
import sqlite3
from pathlib import Path

from pipeline.storage.db import DB_PATH as LOCAL_DB_PATH


_DEFAULT_SNAPSHOT = Path(__file__).resolve().parents[3] / "data" / "pipeline_mini_snapshot.db"


def resolve_db_path() -> Path:
    """PIPELINE_DB_REMOTE_PATH, if set, points at a local snapshot of the
    Mac mini's pipeline.db (see sync_remote_db.py -- SQLite has no live
    remote-file story, so "remote" here means "last synced snapshot", not a
    live network connection). Falls back to the mini snapshot's default path
    if it exists even without the env var set, then to the Windows local
    pipeline.db used by storage/db.py.
    """
    remote = os.getenv("PIPELINE_DB_REMOTE_PATH")
    if remote and Path(remote).exists():
        return Path(remote)
    if _DEFAULT_SNAPSHOT.exists():
        return _DEFAULT_SNAPSHOT
    return LOCAL_DB_PATH


def get_read_connection() -> sqlite3.Connection:
    path = resolve_db_path()
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn
