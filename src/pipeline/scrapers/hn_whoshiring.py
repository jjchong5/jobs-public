# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: Claude Code
# Prompt: Sub-agent build "Build HN Who's Hiring scraper" (2026-06-24); later touched in a 2026-07-03 multi-file scraper touch-up session -- see docs/ai_usage/prompt_log.md#src-pipeline-scrapers-hn_whoshiringpy for full text
# Usage: Original fetch_raw() HN Algolia API parser built end-to-end by sub-agent and verified against live data; later lightly edited alongside luma_events.py/wellfound.py in a same-day touch-up pass.
# -------------------------------------------------------------------------

"""
Scraper for Hacker News "Who is Hiring?" monthly thread, via the HN Algolia API.

No HTML scraping needed: Algolia indexes HN content as JSON.
  1. Search for the latest "Who is Hiring" story posted by user `whoishiring`.
  2. Fetch the full comment tree for that story.
  3. Flatten top-level (and nested) comments into raw dicts for downstream
     LLM tagging. We deliberately do NOT parse out structured fields here
     (role, location, etc) -- that's the tagger's job.
"""

import json
import logging
import sys
from pathlib import Path

import requests

from pipeline.scrapers.raw_writer import write_raw_output

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

ALGOLIA_SEARCH_URL = "https://hn.algolia.com/api/v1/search_by_date"
ALGOLIA_ITEM_URL = "https://hn.algolia.com/api/v1/items/{item_id}"
HN_PERMALINK = "https://news.ycombinator.com/item?id={item_id}"

DATA_RAW_DIR = Path(__file__).resolve().parents[3] / "data" / "raw"


def _find_latest_thread_id() -> int | None:
    """Search Algolia for the most recent 'Who is Hiring' story by the whoishiring account."""
    try:
        resp = requests.get(
            ALGOLIA_SEARCH_URL,
            params={
                "query": "Who is hiring",
                "tags": "story,author_whoishiring",
                "hitsPerPage": 5,
            },
            timeout=30,
        )
        resp.raise_for_status()
        hits = resp.json().get("hits", [])
    except Exception:
        logger.exception("Failed to search Algolia for Who is Hiring thread")
        return None

    for hit in hits:
        title = (hit.get("title") or "").lower()
        if "who is hiring" in title:
            return int(hit["story_id"]) if "story_id" in hit else int(hit["objectID"])

    if hits:
        # fallback: just take the most recent hit even if title match is loose
        return int(hits[0]["objectID"])

    logger.warning("No 'Who is Hiring' threads found in Algolia search results")
    return None


def _flatten_comments(node: dict, out: list[dict]) -> None:
    """Recursively walk the Algolia item comment tree, collecting comment nodes."""
    children = node.get("children") or []
    for child in children:
        if child.get("text"):
            out.append(
                {
                    "comment_id": child.get("id"),
                    "author": child.get("author"),
                    "text": child.get("text"),
                    "created_at": child.get("created_at"),
                    "url": HN_PERMALINK.format(item_id=child.get("id")),
                }
            )
        # Recurse into replies too -- some job listings get follow-up replies
        # (e.g. clarifications) that may still be relevant raw text.
        _flatten_comments(child, out)


def fetch_raw() -> list[dict]:
    """Fetch the latest HN 'Who is Hiring' thread and return raw comment items."""
    thread_id = _find_latest_thread_id()
    if thread_id is None:
        logger.error("Could not determine latest Who is Hiring thread id")
        return []

    logger.info("Using Who is Hiring thread id=%s", thread_id)

    try:
        resp = requests.get(ALGOLIA_ITEM_URL.format(item_id=thread_id), timeout=60)
        resp.raise_for_status()
        thread = resp.json()
    except Exception:
        logger.exception("Failed to fetch thread item id=%s", thread_id)
        return []

    items: list[dict] = []
    try:
        _flatten_comments(thread, items)
    except Exception:
        logger.exception("Failed to flatten comments for thread id=%s", thread_id)

    logger.info("Fetched %d raw comment items from thread id=%s", len(items), thread_id)
    return items


if __name__ == "__main__":
    raw_items = fetch_raw()
    print(f"Fetched {len(raw_items)} raw items")

    try:
        history_path = write_raw_output("hn_whoshiring", raw_items)
        print(f"Wrote raw items to {history_path}")
    except Exception:
        logger.exception("Failed to write output file")
        sys.exit(1)
