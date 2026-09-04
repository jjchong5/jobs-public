# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: Claude Code
# Prompt: written during the 2026-07-03 ranking-rework session (07199978...) --
#   automated reconstruction couldn't isolate a verbatim trigger; the real
#   prompt exists in the raw transcript at docs/ai_usage/transcripts/07199978-1387-498f-a20c-9216f23549a2.jsonl,
#   see docs/ai_usage/prompt_log.md#src-pipeline-ranker-scorespy
# Usage: Implements the ranker's three score formulas (preference_score,
#   urgency_score, general_score) per the 5-weight-table design described in
#   CLAUDE.md's ranking-rework section.
# -------------------------------------------------------------------------

"""Pure scoring functions: tagged item fields + preference-profile weight
tables -> a handful of named scores. No DB access, no sorting -- that's
rank.py's job. Kept separate so the scoring formulas can be read/tweaked/
tested in isolation from orchestration (see relevance_ranking_rework memory
for the design rationale: three named scores instead of one "relevance").
"""
from datetime import datetime, timezone


def deadline_urgency_boost(deadline: str | None) -> float:
    """Small boost for items with a near-term deadline; 0 if no deadline or unparseable."""
    if not deadline:
        return 0.0
    try:
        days_left = (datetime.fromisoformat(deadline).replace(tzinfo=timezone.utc)
                     - datetime.now(timezone.utc)).days
    except ValueError:
        return 0.0
    if days_left < 0:
        return 0.0
    if days_left <= 7:
        return 1.0
    if days_left <= 21:
        return 0.5
    return 0.0


def preference_multiplier(item: dict, profile: dict) -> float:
    """Product of every personal-preference weight table over this item's
    tagged fields. This is the ONLY place preference weighting happens --
    content_quality itself is deliberately preference-blind (see
    tagger/schema.py). spam_risk is intentionally excluded here: reported for
    visibility only, not folded into any score until validated in use."""
    engagement_weights = profile.get("engagement_weights") or {}
    seniority_weights = profile.get("seniority_weights") or {}
    location_weights = profile.get("location_weights") or {}
    sector_weights = profile.get("sector_weights") or {}
    stage_weights = profile.get("stage_weights") or {}
    category_weights = profile.get("category_weights") or {}
    role_category_weights = profile.get("role_category_weights") or {}

    multiplier = category_weights.get(item.get("category"), 0.5)
    multiplier *= engagement_weights.get(item.get("engagement_type"), 1.0)
    multiplier *= seniority_weights.get(item.get("seniority"), 1.0)
    multiplier *= location_weights.get(item.get("remote_type"), 1.0)
    multiplier *= sector_weights.get(item.get("industry"), 1.0)
    multiplier *= stage_weights.get(item.get("company_stage"), 1.0)
    # Default 1.0 (neutral) for every role_category except the entries
    # explicitly set low in DEFAULT_ROLE_CATEGORY_WEIGHTS (see storage/db.py) --
    # this is a narrow derank, not a general role_category preference weight.
    multiplier *= role_category_weights.get(item.get("role_category"), 1.0)
    return multiplier


def compute_scores(item: dict, profile: dict) -> dict:
    """Returns {urgency_score, preference_score, general_score} for one
    tagged item under the given preference profile.

    - general_score: preference-UNweighted -- roughly "how good does this
      look to a generic viewer", content_quality plus deadline only.
    - preference_score: full personal-preference weight stack applied on top
      of content_quality. The main "does this match MY preferences" sort.
    - urgency_score: same as preference_score, but the deadline boost is
      amplified so a high-preference item with a looming deadline surfaces
      to the top even if a slightly-higher-preference item has no deadline.
    """
    quality = item.get("content_quality") or 0.0
    boost = deadline_urgency_boost(item.get("deadline"))
    pref_multiplier = preference_multiplier(item, profile)

    general_score = quality + boost
    preference_score = quality * pref_multiplier + boost
    urgency_score = quality * pref_multiplier + boost * 3

    return {
        "general_score": round(general_score, 3),
        "preference_score": round(preference_score, 3),
        "urgency_score": round(urgency_score, 3),
    }
