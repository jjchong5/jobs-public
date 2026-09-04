# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: Claude Code
# Prompt: AI-assisted (2026-07-02 multi-scraper session), no clean prompt
#   attribution reconstructed -- see docs/ai_usage/prompt_log.md#src-pipeline-scrapers-eventbritepy
# Usage: Eventbrite API event scraper. Now frozen/mothballed (event
#   tracking de-prioritized 2026-07-02 per CLAUDE.md).
# -------------------------------------------------------------------------

"""Eventbrite event scraper (eventbrite.com public search pages).

Eventbrite deprecated its public `/v3/events/search/` REST endpoint years ago
(confirmed 2026-07-02: it 404s -- keys are only issued now for organizers to
manage their own events, not to search the whole platform). Rather than stop
there, checked whether the public search *website* itself still exposes
results without login: `eventbrite.com/d/<location>/<category>/` embeds the
full first-page result set as JSON in a `window.__SERVER_DATA__ = {...}`
assignment in the initial server-rendered HTML -- no auth, no JS execution
needed to read it. Same "public search page embeds real data, no key
required" shape as this project's Luma and Meetup sources.

Standalone run:
    python -m pipeline.scrapers.eventbrite
writes raw entries to data/raw/eventbrite.json and prints the count fetched.
"""

import json
import logging
from pathlib import Path

import requests


from pipeline.scrapers.raw_writer import write_raw_output
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# SF-area search pages, category slugs matching the seeded DS/ML/AI
# preference profile. Eventbrite's `/d/<region>/<query>/` search page format.
SEARCH_URLS = [
    "https://www.eventbrite.com/d/ca--san-francisco/data-science/",
    "https://www.eventbrite.com/d/ca--san-francisco/machine-learning/",
    "https://www.eventbrite.com/d/ca--san-francisco/artificial-intelligence/",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}

SERVER_DATA_MARKER = "window.__SERVER_DATA__ = "

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RAW_OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "eventbrite.json"


def fetch_raw(search_urls: list[str] = SEARCH_URLS) -> list[dict]:
    """Fetch raw events from each Eventbrite search page's embedded
    `__SERVER_DATA__` JSON. Dedups across pages by event id. Returns
    whatever succeeded if a page fails -- logs a warning rather than
    aborting the whole run."""
    seen_ids: set = set()
    items: list[dict] = []
    decoder = json.JSONDecoder()

    for url in search_urls:
        logger.info("Fetching Eventbrite search page: %s", url)
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            resp.raise_for_status()
            html = resp.text
            marker_idx = html.find(SERVER_DATA_MARKER)
            if marker_idx == -1:
                logger.warning("No __SERVER_DATA__ payload found on %s (page may have changed)", url)
                continue
            data, _ = decoder.raw_decode(html, marker_idx + len(SERVER_DATA_MARKER))
            results = data.get("search_data", {}).get("events", {}).get("results", [])
            if not results:
                logger.warning("Eventbrite search page %s returned 0 events", url)
            for ev in results:
                event_id = ev.get("id")
                if event_id in seen_ids:
                    continue
                seen_ids.add(event_id)
                ev = dict(ev)
                ev["source"] = "eventbrite"
                items.append(ev)
        except Exception:
            logger.exception("Failed to fetch/parse Eventbrite search page %s", url)

    logger.info("Fetched %d raw items from Eventbrite", len(items))
    return items


def main() -> None:
    items = fetch_raw()
    history_path = write_raw_output("eventbrite", items)
    print(f"Fetched {len(items)} raw entries -> {history_path}")


if __name__ == "__main__":
    main()
