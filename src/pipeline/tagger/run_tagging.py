# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: Claude Code
# Prompt: Built/refined across 7 sessions (2026-06-24 to 2026-07-05) -- initial scaffold, Wellfound cost/volume tuning, GLM-provider-abstraction groundwork -- see docs/ai_usage/prompt_log.md#src-pipeline-tagger-run_taggingpy for full text
# Usage: Tagging-run orchestration -- concurrency-controlled batch driver over untagged items, lockfile guard against concurrent runs, per-provider model pricing table
# -------------------------------------------------------------------------

"""Batch-tags all untagged rows in `items` and writes results back to the DB.
Run as: python -m pipeline.tagger.run_tagging [--limit N] [--concurrency N]

Concurrency runs independent tag_item() API calls in parallel via a thread
pool; every DB write still happens sequentially on the main thread (SQLite
connections aren't safe to share across threads, and this keeps the same
single-writer discipline used elsewhere in the pipeline -- only the network
calls are parallelized, not the persistence).
"""
import argparse
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from pipeline.storage.db import get_connection, record_run
from pipeline.tagger.batch_tagging import run_batch_tagging
from pipeline.tagger.providers import tagger_available
from pipeline.tagger.tag_item import is_fast_lane, tag_item

logger = logging.getLogger(__name__)

# Prevents two tagging runs from claiming the same untagged rows at once --
# a real incident on 2026-07-03: two overlapping runs against `wellfound_search`
# each read a stale "tagged_at IS NULL" snapshot before the other's commits
# landed, so 717 already-tagged rows got re-tagged for ~$2 of wasted spend.
# A plain existence-check lock is enough here (single-machine, human-triggered
# runs plus one future scheduler job) -- no need for a distributed lock.
LOCK_PATH = Path(__file__).resolve().parents[3] / "data" / "tagging.lock"


class _AlreadyRunningError(Exception):
    pass


def _acquire_lock() -> None:
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(LOCK_PATH, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        raise _AlreadyRunningError(
            f"Lock file {LOCK_PATH} already exists -- another tagging run is in "
            "progress (or crashed without cleaning up; delete the file manually "
            "if you've confirmed nothing is running)."
        )
    with os.fdopen(fd, "w") as f:
        f.write(str(os.getpid()))


def _release_lock() -> None:
    try:
        LOCK_PATH.unlink()
    except FileNotFoundError:
        pass

# $/1M tokens (input, output). Source: platform.claude.com/docs/en/pricing,
# checked 2026-07-02. Update here if pricing changes -- this is the only
# place per-call cost is computed.
MODEL_PRICING = {
    "claude-haiku-4-5-20251001": (1.00, 5.00),
    "claude-sonnet-4-6": (3.00, 15.00),
    # TODO(glm): confirm real GLM 5.2 pricing before use -- not confidently found
    # via web search as of 2026-07-04 (Zhipu's public pricing pages weren't
    # checked live this pass; no number is invented here). Cost logging for
    # the GLM path will silently compute $0 until this is filled in -- see
    # _call_cost's .get(model, (0.0, 0.0)) fallback below.
}


# Message Batches API is a flat 50% off both input and output tokens vs.
# realtime calls (platform.claude.com/docs/en/pricing, checked 2026-08-26).
BATCH_DISCOUNT = 0.5


def _call_cost(model: str, input_tokens: int, output_tokens: int, is_batch: bool = False) -> float:
    in_rate, out_rate = MODEL_PRICING.get(model, (0.0, 0.0))
    cost = (input_tokens / 1_000_000) * in_rate + (output_tokens / 1_000_000) * out_rate
    return cost * BATCH_DISCOUNT if is_batch else cost


def run(limit: int | None = None, source: str | None = None, concurrency: int = 15) -> dict:
    if not tagger_available():
        # No API key configured -- tagging/ranking are optional add-ons, not a
        # requirement for scraping/ingest/browsing. Skip quietly (one log line,
        # no lock taken, no per-item exceptions) rather than crashing every
        # scheduled cycle. See docs/RUNNING_WITHOUT_ANTHROPIC.md.
        logger.info(
            "Tagging skipped: no tagger provider configured (set ANTHROPIC_API_KEY "
            "or GLM_API_KEY in .env to enable tagging/ranking)."
        )
        return {"tagged": 0, "failed": 0, "skipped_reason": "no_provider_configured"}

    try:
        _acquire_lock()
    except _AlreadyRunningError as e:
        logger.error(str(e))
        return {"tagged": 0, "failed": 0, "skipped_reason": "already_running"}

    try:
        conn = get_connection()
        query = "SELECT id, title, author, raw_text FROM items WHERE tagged_at IS NULL"
        params: list = []
        if source:
            query += " AND source = ?"
            params.append(source)
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        rows = conn.execute(query, params).fetchall()

        # Fast lane (author on FAST_LANE_COMPANY_WHITELIST): realtime per-call
        # API, same as before -- for roles where applying quickly plausibly
        # matters. Everything else: the cheaper/slower Batch API lane (50% off
        # both input/output tokens, fine for a once-nightly job). See
        # tag_item.is_fast_lane / batch_tagging.py module docstrings.
        fast_rows = [row for row in rows if is_fast_lane(row["author"])]
        batch_rows = [row for row in rows if not is_fast_lane(row["author"])]
        logger.info(
            "Tagging split: %d fast-lane (realtime), %d batch-lane item(s)",
            len(fast_rows), len(batch_rows),
        )

        started = time.monotonic()
        tagged, failed = 0, 0
        haiku_calls, sonnet_calls = 0, 0
        input_tokens_total, output_tokens_total = 0, 0
        cost_total = 0.0
        category_counts: dict[str, int] = {}
        engagement_type_counts: dict[str, int] = {}

        def _write_result(row, result, model, calls, is_batch: bool = False) -> None:
            nonlocal tagged, failed, haiku_calls, sonnet_calls, input_tokens_total, output_tokens_total, cost_total
            for call_model, in_tok, out_tok in calls:
                input_tokens_total += in_tok
                output_tokens_total += out_tok
                cost_total += _call_cost(call_model, in_tok, out_tok, is_batch=is_batch)
                if "haiku" in call_model:
                    haiku_calls += 1
                elif "sonnet" in call_model:
                    sonnet_calls += 1
            if result is None:
                failed += 1
                logger.warning("Tagging failed for item id=%d after retries", row["id"])
                return
            conn.execute(
                """UPDATE items SET category=?, role_type=?, role_category=?, industry=?,
                   seniority=?, engagement_type=?, company_stage=?, location=COALESCE(location, ?),
                   deadline=?, content_quality=?, spam_risk=?, role_expectation_delta=?,
                   role_expectation_notes=?, tag_confidence=?, tagged_at=?, tagger_model=?
                   WHERE id=?""",
                (
                    result.category, result.role_type, result.role_category, result.industry,
                    result.seniority, result.engagement_type, result.company_stage,
                    result.location, result.deadline,
                    result.content_quality, result.spam_risk, result.role_expectation_delta,
                    result.role_expectation_notes, result.confidence,
                    datetime.now(timezone.utc).isoformat(), model, row["id"],
                ),
            )
            conn.commit()
            tagged += 1
            category_counts[result.category] = category_counts.get(result.category, 0) + 1
            if result.engagement_type:
                engagement_type_counts[result.engagement_type] = engagement_type_counts.get(result.engagement_type, 0) + 1

        def _tag_row(row):
            # title carries real signal for sources like Luma/Built In where the
            # raw_text snippet alone can be vague filler text -- without it,
            # e.g. a real "Coffee Cupping" event was misclassified as irrelevant.
            text_to_tag = f"{row['title']}\n\n{row['raw_text']}" if row["title"] else row["raw_text"]
            return row, *tag_item(text_to_tag)

        # Only the network calls run concurrently -- every DB write below still
        # happens on the main thread, sequentially, same as before.
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            futures = [pool.submit(_tag_row, row) for row in fast_rows]
            for future in as_completed(futures):
                row, result, model, calls = future.result()
                _write_result(row, result, model, calls)

        # Batch lane: one (or two, with escalation) round-trip submissions
        # instead of one call per item -- see batch_tagging.py.
        if batch_rows:
            batch_results = run_batch_tagging(batch_rows)
            rows_by_id = {row["id"]: row for row in batch_rows}
            for item_id, (result, model, calls) in batch_results.items():
                _write_result(rows_by_id[item_id], result, model, calls, is_batch=True)
        conn.close()

        record_run(
            stage="tag",
            source=source,
            duration_seconds=round(time.monotonic() - started, 3),
            status="ok" if failed == 0 else "error",
            error=f"{failed} item(s) failed after retries" if failed else None,
            metrics={
                "tagged": tagged,
                "failed": failed,
                "fast_lane_count": len(fast_rows),
                "batch_lane_count": len(batch_rows),
                "haiku_calls": haiku_calls,
                "sonnet_calls": sonnet_calls,
                "input_tokens": input_tokens_total,
                "output_tokens": output_tokens_total,
                "cost_usd": round(cost_total, 4),
                "category_counts": category_counts,
                "engagement_type_counts": engagement_type_counts,
            },
        )
        return {"tagged": tagged, "failed": failed}
    finally:
        _release_lock()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--source", type=str, default=None)
    parser.add_argument("--concurrency", type=int, default=15)
    args = parser.parse_args()
    print(run(limit=args.limit, source=args.source, concurrency=args.concurrency))
