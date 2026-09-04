# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: Claude Code
# Prompt: 2026-07-03 discussion on raw-scrape-file overwrite-safety/
#   retention, resolved as "use a helper" -- see
#   docs/ai_usage/prompt_log.md#src-pipeline-scrapers-raw_writerpy
# Usage: Shared raw-data-writing helper (timestamped writes, not blind
#   overwrite) used by scrapers, following the raw-file retention/safety
#   discussion in this session.
# -------------------------------------------------------------------------

"""Shared raw-output writer for scrapers.

Every scraper's `main()` used to do its own `mkdir` + `open(..., "w")` +
`json.dump` directly against a fixed `data/raw/<source>.json` path. Two
problems with that:

1. A bad run that returns an empty (or much smaller) list silently clobbers
   the last good snapshot -- exactly when you'd want to look at it to debug
   the bad run.
2. No history -- only "last run" is ever on disk, so there's no way to look
   back at what a source returned yesterday.

`write_raw_output()` fixes both: it always writes a timestamped copy under
`data/raw/history/<source>_<UTC-timestamp>.json`, and only refreshes the
stable `data/raw/<source>.json` (what ingest.py and everything else reads)
if `items` is non-empty. An empty result still gets its timestamped copy
(so the failure itself is visible in history) but never overwrites a good
snapshot with nothing.

`purge_old_history()` deletes timestamped files older than a retention
window, called from the scheduler rather than per-scraper.
"""

import json
import logging
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

RAW_DIR = Path(__file__).resolve().parents[3] / "data" / "raw"
HISTORY_DIR = RAW_DIR / "history"
DEFAULT_RETENTION_DAYS = 14


def write_raw_output(source: str, items: list) -> Path:
    """Write `items` for `source` to a timestamped history file, and refresh
    the stable `data/raw/<source>.json` unless `items` is empty.

    Returns the path to the timestamped history file that was written.
    """
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    history_path = HISTORY_DIR / f"{source}_{timestamp}.json"

    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)

    stable_path = RAW_DIR / f"{source}.json"
    if items:
        shutil.copyfile(history_path, stable_path)
    else:
        logger.warning(
            "%s returned 0 items; leaving existing %s untouched (history copy written to %s)",
            source, stable_path, history_path,
        )

    return history_path


def purge_old_history(retention_days: int = DEFAULT_RETENTION_DAYS) -> int:
    """Delete timestamped history files older than `retention_days`. Returns
    the number of files deleted.
    """
    if not HISTORY_DIR.exists():
        return 0

    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    deleted = 0
    for path in HISTORY_DIR.glob("*.json"):
        if datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc) < cutoff:
            path.unlink()
            deleted += 1

    if deleted:
        logger.info("Purged %d raw history file(s) older than %d days", deleted, retention_days)
    return deleted
