# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: Claude Code
# Prompt: 2026-08-26 cost-cutting pass -- "prompt caching + batch API +
#   fast/slow lane split" -- see docs/ai_usage/prompt_log.md#src-pipeline-tagger-batch_taggingpy
# Usage: Anthropic Message Batches API path for the non-realtime tagging lane
#   -- submits a batch of tag requests, polls for completion, parses results.
#   Only supports the Anthropic provider (GLM's batch equivalent, if any, is
#   out of scope until GLM is verified live -- see providers.py).
# -------------------------------------------------------------------------

"""Batch API tagging for items NOT on the fast-lane company whitelist (see
tag_item.is_fast_lane). The Message Batches API is 50% off both input and
output tokens vs. realtime calls, with up to a 24h turnaround -- fine for
this pipeline since tag_and_rank already runs once nightly (see
scheduler.py), not on a tight latency budget.

Escalation (confidence < threshold -> retry on the escalation tier) still
happens, but as a SECOND batch round-trip after the first batch's results are
in, rather than inline per-item like the realtime path in tag_item.py. Two
sequential batches is still far cheaper than realtime calls for the items
that don't need to be fast.
"""
import json
import logging
import time
from datetime import date

from pipeline.tagger.prompts import build_system_prompt, build_user_message
from pipeline.tagger.providers import AnthropicTaggerClient, get_tagger_client
from pipeline.tagger.schema import TagResult
from pipeline.tagger.tag_item import CONFIDENCE_ESCALATION_THRESHOLD, parse_model_json

logger = logging.getLogger(__name__)

# How often to poll batch status. Batches can take minutes to ~24h; there's no
# push notification, only polling. 60s keeps this responsive for the common
# case (most batches finish in minutes) without hammering the API.
POLL_INTERVAL_SECONDS = 60
# Safety cap so a stuck/pathological batch doesn't poll forever inside a
# scheduled job -- 6h is well under the 24h SLA but generous for a nightly run.
MAX_POLL_SECONDS = 6 * 60 * 60

# The Message Batches API caps a single submission at 256MB total request
# size. Raw item text can run up to RAW_TEXT_CHAR_LIMIT (12000 chars, see
# prompts.py) each, so a single batch of the whole backlog can blow past that
# limit (hit in practice at ~15k items -> 413 Payload Too Large). 500
# items/chunk keeps a worst-case batch (500 * ~12KB text + prompt overhead)
# well under 256MB with plenty of margin.
MAX_BATCH_SIZE = 500


def _custom_id(item_id: int) -> str:
    return f"item-{item_id}"


def _item_id_from_custom_id(custom_id: str) -> int:
    return int(custom_id.removeprefix("item-"))


def _submit_batch(client: AnthropicTaggerClient, rows: list, tier) -> str:
    today = date.today().isoformat()
    system_prompt = build_system_prompt(today)
    requests = [
        {
            "custom_id": _custom_id(row["id"]),
            "params": client.build_message_params(
                system_prompt=system_prompt,
                user_message=build_user_message(row["_text_to_tag"]),
                tier=tier,
            ),
        }
        for row in rows
    ]
    batch = client.raw_client.messages.batches.create(requests=requests)
    logger.info("Submitted batch id=%s for %d item(s), tier=%s", batch.id, len(rows), tier.model)
    return batch.id


def _run_batch_chunked(client: AnthropicTaggerClient, rows: list, tier, tier_model: str) -> dict[int, tuple]:
    """Submits `rows` across one or more MAX_BATCH_SIZE-sized batches
    (sequentially, to keep the polling logic simple) and merges the results."""
    results: dict[int, tuple] = {}
    for start in range(0, len(rows), MAX_BATCH_SIZE):
        chunk = rows[start:start + MAX_BATCH_SIZE]
        batch_id = _submit_batch(client, chunk, tier)
        _wait_for_batch(client, batch_id)
        results.update(_collect_results(client, batch_id, tier_model))
    return results


def _wait_for_batch(client: AnthropicTaggerClient, batch_id: str) -> None:
    waited = 0
    while waited < MAX_POLL_SECONDS:
        batch = client.raw_client.messages.batches.retrieve(batch_id)
        if batch.processing_status == "ended":
            return
        time.sleep(POLL_INTERVAL_SECONDS)
        waited += POLL_INTERVAL_SECONDS
    raise TimeoutError(f"Batch {batch_id} did not finish within {MAX_POLL_SECONDS}s")


def _collect_results(client: AnthropicTaggerClient, batch_id: str, tier_model: str) -> dict[int, tuple]:
    """Returns {item_id: (TagResult or None, model, [(model, in_tok, out_tok)])}."""
    results: dict[int, tuple] = {}
    for entry in client.raw_client.messages.batches.results(batch_id):
        item_id = _item_id_from_custom_id(entry.custom_id)
        calls: list[tuple[str, int, int]] = []
        if entry.result.type != "succeeded":
            logger.warning("Batch item id=%d did not succeed: %s", item_id, entry.result.type)
            results[item_id] = (None, tier_model, calls)
            continue
        message = entry.result.message
        calls.append((tier_model, message.usage.input_tokens, message.usage.output_tokens))
        text = message.content[0].text.strip()
        try:
            data = parse_model_json(text)
            tag_result = TagResult(**data)
        except (json.JSONDecodeError, Exception) as e:
            logger.warning("Batch item id=%d failed to parse/validate: %s", item_id, e)
            results[item_id] = (None, tier_model, calls)
            continue
        results[item_id] = (tag_result, tier_model, calls)
    return results


def run_batch_tagging(rows: list) -> dict[int, tuple]:
    """Tags `rows` (sqlite3.Row objects with id/title/raw_text) via the Batch
    API, including a second-batch escalation pass for low-confidence results.
    Returns {item_id: (TagResult or None, model_used, calls)} matching the
    shape run_tagging.py already expects from tag_item()'s return value, so
    the DB-write loop doesn't need to know which lane produced the result.
    """
    client = get_tagger_client()
    if not isinstance(client, AnthropicTaggerClient):
        raise RuntimeError("Batch tagging is only implemented for the Anthropic provider")
    if not rows:
        return {}

    prepared = [
        {"id": row["id"], "_text_to_tag": f"{row['title']}\n\n{row['raw_text']}" if row["title"] else row["raw_text"]}
        for row in rows
    ]

    final: dict[int, tuple] = _run_batch_chunked(client, prepared, client.default_tier, client.default_tier.model)

    escalate_rows = [
        row for row in prepared
        if final.get(row["id"], (None,))[0] is not None
        and final[row["id"]][0].confidence < CONFIDENCE_ESCALATION_THRESHOLD
    ]
    if escalate_rows:
        escalated = _run_batch_chunked(client, escalate_rows, client.escalation_tier, client.escalation_tier.model)
        for item_id, (esc_result, esc_model, esc_calls) in escalated.items():
            if esc_result is not None:
                prev_result, prev_model, prev_calls = final[item_id]
                final[item_id] = (esc_result, esc_model, prev_calls + esc_calls)
            # else: keep the default-tier result, same fallback behavior as
            # tag_item.py's realtime escalation path.

    return final
