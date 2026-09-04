# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: Claude Code
# Prompt: Built 2026-06-24 scaffold; refined 2026-07-03; GLM-5.2 provider-abstraction overnight pass 2026-07-05 (TaggerClient interface, TAGGER_PROVIDER env var) -- see docs/ai_usage/prompt_log.md#src-pipeline-tagger-tag_itempy for full text
# Usage: Per-item LLM tagging call -- builds prompt, calls Haiku/Sonnet via TaggerClient abstraction with confidence-based escalation, validates response against Pydantic schema with retries
# -------------------------------------------------------------------------

"""LLM tagger/verifier. The default tier tags every item; if its self-reported
confidence is < 0.7, we escalate the same item to the escalation tier for a second
pass. "confidence" here is an LLM self-report elicited via prompt instruction, not a
calibrated probability -- treat it as a semantic heuristic (see CLAUDE.md).

Provider (Anthropic vs. GLM) is selected once via TAGGER_PROVIDER (see providers.py);
Anthropic is the live default, GLM is a stub awaiting a real API key -- see
providers.py's module docstring for what's verified vs. assumed there.
"""
import json
import logging
from datetime import date

from dotenv import load_dotenv
from pydantic import ValidationError

from pipeline.tagger.prompts import build_system_prompt, build_user_message
from pipeline.tagger.providers import ModelTier, get_tagger_client
from pipeline.tagger.schema import TagResult

load_dotenv()
logger = logging.getLogger(__name__)

CONFIDENCE_ESCALATION_THRESHOLD = 0.7
MAX_RETRIES = 2

# Companies the author wants tagged immediately (realtime, per-call API) rather
# than queued into the overnight Batch API run -- for roles where applying
# fast plausibly matters (early applicant advantage, fast-moving hiring).
# Match is against items.author, squashed the same way as normalize_dedup_key
# (lowercased, non-alphanumeric stripped) so ATS-slug names ("elevenlabs") and
# human display names ("Eleven Labs") both match. Everything NOT on this list
# goes through the cheaper/slower Batch API lane in run_tagging.py -- edit this
# list directly, it's a short author-curated set, not a DB-editable preference
# like the ranker's weight tables.
FAST_LANE_COMPANY_WHITELIST: set[str] = {
    # e.g. "anthropic", "openai" -- add real entries as needed
}


def _squash_company(name: str) -> str:
    import re
    return re.sub(r"[^a-z0-9]", "", (name or "").lower())


def is_fast_lane(author: str | None) -> bool:
    """True if this item's company matches the fast-lane whitelist and should
    be tagged via realtime per-call API instead of the overnight Batch API."""
    if not author:
        return False
    return _squash_company(author) in FAST_LANE_COMPANY_WHITELIST


def parse_model_json(text: str) -> dict:
    """Shared response-text -> dict parsing for both the realtime path below
    and the Batch API path in run_tagging.py, so a strip-markdown-fence/
    trailing-prose fix only needs to happen in one place."""
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    # The model sometimes appends trailing prose after the JSON object
    # despite being told not to; raw_decode parses just the first object
    # and ignores anything after it instead of failing on "Extra data".
    return json.JSONDecoder().raw_decode(text.strip())[0]


def _call_model(raw_text: str, tier: ModelTier, calls: list) -> dict:
    client = get_tagger_client()
    result = client.complete(
        system_prompt=build_system_prompt(date.today().isoformat()),
        user_message=build_user_message(raw_text),
        tier=tier,
    )
    calls.append((tier.model, result.input_tokens, result.output_tokens))
    return parse_model_json(result.text)


def _tag_with_tier(raw_text: str, tier: ModelTier, calls: list) -> TagResult | None:
    for attempt in range(MAX_RETRIES + 1):
        try:
            data = _call_model(raw_text, tier, calls)
            return TagResult(**data)
        except (json.JSONDecodeError, ValidationError) as e:
            logger.warning("Tag attempt %d failed for model=%s: %s", attempt + 1, tier.model, e)
    return None


def tag_item(raw_text: str) -> tuple[TagResult | None, str, list[tuple[str, int, int]]]:
    """Returns (TagResult or None, model_used, calls). `calls` is a list of
    (model, input_tokens, output_tokens) for every API call made (1 entry,
    or 2 if escalated) -- used by run_tagging.py for cost logging."""
    client = get_tagger_client()
    calls: list[tuple[str, int, int]] = []
    result = _tag_with_tier(raw_text, client.default_tier, calls)
    if result is None:
        return None, client.default_tier.model, calls
    if result.confidence < CONFIDENCE_ESCALATION_THRESHOLD:
        escalated = _tag_with_tier(raw_text, client.escalation_tier, calls)
        if escalated is not None:
            return escalated, client.escalation_tier.model, calls
    return result, client.default_tier.model, calls


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sample = ("Anthropic | Research Engineer | San Francisco, CA | Full-time. "
               "Apply by July 15. Looking for ML engineers with LLM experience.")
    result, model, calls = tag_item(sample)
    print(f"model={model}")
    print(result.model_dump_json(indent=2) if result else "FAILED")
