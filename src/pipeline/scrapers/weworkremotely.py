# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: Claude Code
# Prompt: milestone-3 task from a /loop-executed freelance-sourcing
#   sub-feature task list (2026-06-24) -- see
#   docs/ai_usage/prompt_log.md#src-pipeline-scrapers-weworkremotelypy
# Usage: Generated in a single Write call implementing the We Work Remotely
#   RSS-feed scraper (fetch_raw()); not edited again afterward.
# -------------------------------------------------------------------------

"""We Work Remotely RSS feed parser (https://weworkremotely.com).

Fetches raw entries from WWR's public category RSS feeds. No auth, no
anti-bot encountered (plain RSS XML). This module only parses the raw feed
into a list of dicts -- structured field extraction (role_type, seniority,
engagement_type, etc.) is handled downstream by the LLM tagger. WWR is
mostly full-time listings with some contract roles mixed in; the tagger
infers engagement_type from the raw text rather than from a clean source
field, since WWR doesn't expose one.

Standalone run:
    python -m pipeline.scrapers.weworkremotely
writes raw entries to data/raw/weworkremotely.json and prints the count fetched.
"""

import json
import logging
from pathlib import Path

import feedparser


from pipeline.scrapers.raw_writer import write_raw_output
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Category feeds relevant to AI/ML/DS work -- not the full WWR category list.
FEED_URLS = [
    "https://weworkremotely.com/categories/remote-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss",
]

# Project root is src/pipeline/scrapers/../../.. -> C:\Users\jjcho\code\jobs
PROJECT_ROOT = Path(__file__).resolve().parents[3]
RAW_OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "weworkremotely.json"


def fetch_raw() -> list[dict]:
    """Fetch raw entries from WWR's category RSS feeds.

    Returns a list of dicts with keys: title, link, summary, published,
    region, category, source. Returns an empty list (and logs a warning) on
    any failure -- this is a scaffold, callers should handle empty results
    gracefully.
    """
    entries: list[dict] = []
    for feed_url in FEED_URLS:
        logger.info("Fetching We Work Remotely RSS feed: %s", feed_url)
        try:
            feed = feedparser.parse(feed_url)

            if feed.bozo:
                logger.warning("Feed parse flagged bozo (possibly malformed/blocked) for %s: %s", feed_url, feed.get("bozo_exception"))

            if not feed.entries:
                logger.warning("We Work Remotely feed returned 0 entries: %s", feed_url)

            for entry in feed.entries:
                entries.append(
                    {
                        "title": entry.get("title", ""),
                        "link": entry.get("link", ""),
                        "summary": entry.get("summary", ""),
                        "published": entry.get("published", ""),
                        "region": entry.get("region", ""),
                        "category": entry.get("category", ""),
                        "source": "weworkremotely",
                    }
                )
        except Exception:
            logger.exception("Failed to fetch/parse We Work Remotely feed %s", feed_url)

    logger.info("Fetched %d entries from We Work Remotely", len(entries))
    return entries


def main() -> None:
    entries = fetch_raw()
    history_path = write_raw_output("weworkremotely", entries)
    print(f"Fetched {len(entries)} raw entries -> {history_path}")


if __name__ == "__main__":
    main()
