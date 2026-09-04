# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: Claude Code (sub-agent via Agent tool)
# Prompt: "Build Indeed RSS scraper" sub-agent task (2026-06-24) -- see
#   docs/ai_usage/prompt_log.md#src-pipeline-scrapers-indeed_rsspy
# Usage: Indeed RSS-feed job scraper, built and live-tested entirely by a
#   spawned sub-agent; never edited again. Now confirmed dead/deprecated --
#   Indeed retired public RSS access -- and superseded by indeed_radius.py.
# -------------------------------------------------------------------------

"""Indeed RSS job feed parser.

Fetches raw entries from Indeed's RSS feed (https://www.indeed.com/rss) for a
given search query and location. This module only parses the raw feed into a
list of dicts -- structured field extraction (role_type, seniority, etc.) is
handled downstream by the LLM tagger.

Standalone run:
    python -m pipeline.scrapers.indeed_rss
writes raw entries to data/raw/indeed_rss.json and prints the count fetched.
"""

import json
import logging
import urllib.parse
from pathlib import Path

import feedparser


from pipeline.scrapers.raw_writer import write_raw_output
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

INDEED_RSS_BASE = "https://www.indeed.com/rss"

# Project root is src/pipeline/scrapers/../../.. -> C:\Users\jjcho\code\jobs
PROJECT_ROOT = Path(__file__).resolve().parents[3]
RAW_OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "indeed_rss.json"


def fetch_raw(query: str = "data scientist", location: str = "San Francisco, CA") -> list[dict]:
    """Fetch raw entries from Indeed's RSS feed for the given query/location.

    Returns a list of dicts with keys: title, link, summary, published, source.
    Returns an empty list (and logs a warning) on any failure -- this is a
    scaffold, callers should handle empty results gracefully.
    """
    params = {"q": query, "l": location}
    url = f"{INDEED_RSS_BASE}?{urllib.parse.urlencode(params)}"
    logger.info("Fetching Indeed RSS feed: %s", url)

    entries: list[dict] = []
    try:
        feed = feedparser.parse(url)

        if feed.bozo:
            logger.warning("Feed parse flagged bozo (possibly malformed/blocked): %s", feed.get("bozo_exception"))

        if not feed.entries:
            logger.warning("Indeed RSS returned 0 entries for query=%r location=%r", query, location)

        for entry in feed.entries:
            entries.append(
                {
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "summary": entry.get("summary", ""),
                    "published": entry.get("published", ""),
                    "source": "indeed",
                }
            )

        logger.info("Fetched %d entries from Indeed RSS", len(entries))
    except Exception:
        logger.exception("Failed to fetch/parse Indeed RSS feed")

    return entries


def main() -> None:
    entries = fetch_raw()
    history_path = write_raw_output("indeed_rss", entries)
    print(f"Fetched {len(entries)} raw entries -> {history_path}")


if __name__ == "__main__":
    main()
