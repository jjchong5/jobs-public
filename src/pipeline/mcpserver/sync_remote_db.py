"""Pulls a read-only local snapshot of the Mac mini's pipeline.db over SSH
(scp), since SQLite has no real remote-filesystem story -- a live network
path isn't an option, so PIPELINE_DB_REMOTE_PATH points at this local
snapshot copy instead, refreshed by running this script.

Not wired into a scheduler yet (v1 -- run manually or cron/Task Scheduler
this later if the server needs to stay closer to real-time). db_read.py
falls back to the Windows local pipeline.db automatically if this snapshot
doesn't exist yet.

Usage: python -m pipeline.mcpserver.sync_remote_db
"""
import logging
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

MINI_HOST = "<user>@<mac-mini-tailscale-ip>"
MINI_DB_PATH = "~/code/jobs/data/pipeline.db"
SNAPSHOT_PATH = Path(__file__).resolve().parents[3] / "data" / "pipeline_mini_snapshot.db"


def sync() -> Path:
    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = SNAPSHOT_PATH.with_suffix(".db.tmp")
    result = subprocess.run(
        ["scp", "-o", "ConnectTimeout=10", f"{MINI_HOST}:{MINI_DB_PATH}", str(tmp_path)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"scp failed: {result.stderr}")
    tmp_path.replace(SNAPSHOT_PATH)  # atomic swap so a reader never sees a half-copied file
    logger.info("Synced mini snapshot to %s", SNAPSHOT_PATH)
    return SNAPSHOT_PATH


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        sync()
    except RuntimeError as e:
        logger.error(str(e))
        sys.exit(1)
