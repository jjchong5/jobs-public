# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: Claude Code
# Prompt: milestone-3 task from a /loop-executed sourcing-feature task list --
#   see docs/ai_usage/prompt_log.md#src-pipeline-scrapers-remoteokpy for full text
# Usage: Generated in a single Write call (2026-06-24) implementing the
#   RemoteOK public-API scraper; not edited again afterward.
# -------------------------------------------------------------------------

"""RemoteOK public JSON API scraper (https://remoteok.com/api).

RemoteOK exposes a public, no-auth JSON API. Their API terms ask only for
attribution (link back, mention Remote OK as source) -- no anti-bot blocking
encountered. This module only parses the raw API response into a list of
dicts -- structured field extraction (role_type, seniority, engagement_type,
etc.) is handled downstream by the LLM tagger. RemoteOK has no clean
engagement-type field of its own (tags are freeform, e.g. "full time" shows
up inconsistently); the tagger infers it from raw text + tags.

Standalone run:
    python -m pipeline.scrapers.remoteok
writes raw entries to data/raw/remoteok.json and prints the count fetched.

Attribution per RemoteOK API terms: data sourced from https://remoteok.com
"""

import json
import logging
from pathlib import Path

import requests


from pipeline.scrapers.raw_writer import write_raw_output
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

REMOTEOK_API_URL = "https://remoteok.com/api"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

# Project root is src/pipeline/scrapers/../../.. -> C:\Users\jjcho\code\jobs
PROJECT_ROOT = Path(__file__).resolve().parents[3]
RAW_OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "remoteok.json"


def fetch_raw() -> list[dict]:
    """Fetch raw job entries from the RemoteOK public API.

    Returns a list of dicts with keys: title, url, company, location, tags,
    description, posted_at, source. Returns an empty list (and logs a
    warning/error) on any failure -- this is a scaffold, callers should
    handle empty results gracefully.
    """
    logger.info("Fetching RemoteOK API: %s", REMOTEOK_API_URL)

    items: list[dict] = []
    try:
        resp = requests.get(REMOTEOK_API_URL, headers={"User-Agent": USER_AGENT}, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        # First element is a legal/metadata notice, not a job -- skip it.
        records = data[1:] if data and "legal" in data[0] else data

        if not records:
            logger.warning("RemoteOK API returned 0 job records")

        for rec in records:
            items.append(
                {
                    "title": rec.get("position", ""),
                    "url": rec.get("url", ""),
                    "company": rec.get("company", ""),
                    "location": rec.get("location", ""),
                    "tags": rec.get("tags", []),
                    "description": rec.get("description", ""),
                    "posted_at": rec.get("date", ""),
                    "source": "remoteok",
                }
            )

        logger.info("Fetched %d raw items from RemoteOK", len(items))
    except Exception:
        logger.exception("Failed to fetch/parse RemoteOK API")

    return items


def main() -> None:
    items = fetch_raw()
    history_path = write_raw_output("remoteok", items)
    print(f"Fetched {len(items)} raw entries -> {history_path}")


if __name__ == "__main__":
    main()
