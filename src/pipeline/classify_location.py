# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: Claude Code
# Prompt: 2026-07-03 schema-design discussion covering remote/local/
#   hyperlocal(SF) location categorization -- see
#   docs/ai_usage/prompt_log.md#src-pipeline-classify_locationpy
# Usage: Location-classification helper (remote / local / hyperlocal-SF
#   buckets) used by the tagger/ranker.
# -------------------------------------------------------------------------

"""Deterministic remote/local/hyperlocal bucketing from the `location` field
already captured by every scraper. Not LLM-tagged -- cheap enough to compute
at ingest time and backfill for every existing item for free.
"""
import re

BAY_AREA_CITIES = (
    "oakland", "berkeley", "san jose", "palo alto", "mountain view",
    "sunnyvale", "redwood city", "san mateo", "fremont", "santa clara",
    "menlo park", "south san francisco", "daly city", "burlingame",
    "emeryville", "walnut creek", "san rafael", "cupertino",
)

_SF_RE = re.compile(r"\bsf\b")


def classify_remote_type(location: str | None) -> str:
    if not location:
        return "unknown"
    loc = location.lower()
    if "remote" in loc:
        return "remote"
    if "san francisco" in loc or _SF_RE.search(loc):
        return "hyperlocal_sf"
    if any(city in loc for city in BAY_AREA_CITIES):
        return "bay_area"
    return "other"
