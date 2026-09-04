# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: Claude Code
# Prompt: "do we have notification built in? if not can we wire this to my telegram bot" (2026-08-26)
#   -- scope narrowed by author to: run-summary digest (item counts, tagging
#   cost, errors) after each scrape/tag/rank cycle now; a company-whitelist-
#   gated high-priority-item alert is wanted but explicitly deferred/dormant
#   ("I'll figure this out later -- probably a whitelist of very reputable
#   companies").
# Usage: Built from scratch. Reads existing run_log rows (already written by
#   ingest.py/run_tagging.py/rank.py -- no new instrumentation needed) to build
#   one digest message per nightly run, and pushes it via notifications/telegram.py.
# -------------------------------------------------------------------------

"""Run-summary Telegram digest, plus a dormant high-priority-item alert hook.

`notify_run_summary()` is the live path: call it once after a scrape/tag/rank
cycle (see scheduler.py's _run_tag_and_rank) and it reads that run's `run_log`
rows to build one digest message -- items fetched/inserted per source, tagging
cost, and any errors. No API-credit-remaining figures are included: none of
the providers in use (Anthropic, Apify) expose a reliable remaining-balance
API, and guessing at one would be worse than omitting it.

`notify_high_priority_items()` is a deliberately dormant stub for a future
per-item alert (e.g. "item at a whitelisted top-tier company just got tagged
highly") -- the author wants this eventually but hasn't defined the whitelist
yet, so this raises NotImplementedError rather than silently no-op-ing if
something calls it prematurely. Do not implement the whitelist logic until
the author provides one.
"""
import json
import logging
from datetime import datetime, timedelta, timezone

from pipeline.notifications.telegram import send_telegram_message
from pipeline.storage.db import get_connection

logger = logging.getLogger(__name__)


def _recent_run_log_rows(conn, since: datetime) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM run_log WHERE run_at >= ? ORDER BY run_at ASC",
        (since.isoformat(),),
    ).fetchall()
    return [dict(row) for row in rows]


def build_run_summary_text(since: datetime | None = None) -> str:
    """Builds the digest text from run_log rows newer than `since` (default:
    last 2 hours, wide enough to cover one nightly ingest+tag+rank cycle
    without pulling in the prior night's run)."""
    since = since or (datetime.now(timezone.utc) - timedelta(hours=2))
    conn = get_connection()
    try:
        rows = _recent_run_log_rows(conn, since)
    finally:
        conn.close()

    if not rows:
        return "Jobs pipeline: no run activity in the last 2 hours."

    ingest_rows = [r for r in rows if r["stage"] == "ingest"]
    tag_rows = [r for r in rows if r["stage"] == "tag"]
    rank_rows = [r for r in rows if r["stage"] == "rank"]
    error_rows = [r for r in rows if r["status"] == "error"]

    total_fetched = 0
    total_inserted = 0
    per_source_lines = []
    for r in ingest_rows:
        m = json.loads(r["metrics"])
        fetched = m.get("fetched", 0)
        inserted = m.get("inserted", 0)
        total_fetched += fetched
        total_inserted += inserted
        if r["status"] == "error" or inserted:
            per_source_lines.append(f"  {r['source']}: {inserted} new / {fetched} fetched" + (" [ERROR]" if r["status"] == "error" else ""))

    lines = [f"<b>Jobs pipeline run summary</b> ({since.strftime('%Y-%m-%d')})"]
    if ingest_rows:
        lines.append(f"Scraped: {total_inserted} new items ({total_fetched} fetched) across {len(ingest_rows)} sources")
        lines.extend(per_source_lines[:20])
        if len(per_source_lines) > 20:
            lines.append(f"  ...and {len(per_source_lines) - 20} more sources")

    for r in tag_rows:
        m = json.loads(r["metrics"])
        cost = m.get("cost_usd")
        tagged = m.get("tagged") or m.get("items_tagged")
        cost_str = f", ${cost:.2f}" if cost is not None else ""
        lines.append(f"Tagged: {tagged if tagged is not None else '?'} items{cost_str}")

    for r in rank_rows:
        m = json.loads(r["metrics"])
        ranked = m.get("items_ranked") or m.get("ranked")
        if ranked is not None:
            lines.append(f"Ranked: {ranked} items")

    if error_rows:
        lines.append(f"\n<b>{len(error_rows)} error(s):</b>")
        for r in error_rows[:10]:
            label = r["source"] or r["stage"]
            err = (r["error"] or "unknown error")[:150]
            lines.append(f"  {label}: {err}")
        if len(error_rows) > 10:
            lines.append(f"  ...and {len(error_rows) - 10} more")

    return "\n".join(lines)


def notify_run_summary(since: datetime | None = None) -> bool:
    """Builds and sends the run-summary digest. Returns True/False from the
    underlying send (never raises -- a notification failure shouldn't fail
    the run it's reporting on)."""
    text = build_run_summary_text(since)
    return send_telegram_message(text)


def notify_high_priority_items(*_args, **_kwargs) -> None:
    """Dormant. Intended future behavior: alert on individual items matching a
    company whitelist the author hasn't defined yet ("I'll figure this out
    later -- probably a whitelist of very reputable companies", 2026-08-26).
    Do not implement without that whitelist -- raises rather than silently
    no-op-ing so an accidental call surfaces immediately instead of pushing
    nothing and looking like it worked."""
    raise NotImplementedError(
        "High-priority item alerts are not implemented yet -- pending a "
        "company whitelist from the author. See notifications/notifier.py docstring."
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ok = notify_run_summary()
    print("sent" if ok else "failed (see logs)")
