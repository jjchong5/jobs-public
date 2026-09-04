# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: Claude Code
# Prompt: built 2026-07-02 in a multi-scraper session, extended 2026-07-03 --
#   automated reconstruction couldn't isolate a verbatim trigger; full
#   transcripts at docs/ai_usage/transcripts/, see docs/ai_usage/prompt_log.md#src-pipeline-scrapers-leverpy
# Usage: Lever ATS board scraper, following the project's existing
#   fetch_raw()-style scraper convention.
# -------------------------------------------------------------------------

"""Lever job board scraper (public per-company JSON API).

Lever exposes a public, unauthenticated JSON API per company at
`https://api.lever.co/v0/postings/<company>?mode=json` -- no auth, no
anti-bot, one HTTP GET per company. Same shape/tradeoff as greenhouse.py:
no cross-company search, so this needs a target company list.

`COMPANY_SLUGS` is a placeholder list confirmed live against the real API
(2026-07-02). Fewer confirmed companies use Lever than Greenhouse among the
SF AI/DS/ML candidates tried -- same "seed a reasonable starting set, don't
curate the 'right' list" spirit as greenhouse.py and the default preference
profile.

Standalone run:
    python -m pipeline.scrapers.lever
writes raw entries to data/raw/lever.json and prints the count fetched.
"""

import json
import logging
from pathlib import Path

import requests


from pipeline.scrapers.raw_writer import write_raw_output
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

POSTINGS_API_URL = "https://api.lever.co/v0/postings/{slug}?mode=json"

# Confirmed live (2026-07-02) -- each of these company slugs returned >0 real
# postings from the public API.
COMPANY_SLUGS = [
    "palantir",
    "outreach",
    "wealthfront",
    "articulate",
    # Added 2026-07-03: same live-probe pass as greenhouse.py/ashby.py.
    "zilliz",  # 11 postings -- Zilliz, vector database (Milvus)
]


def fetch_raw(company_slugs: list[str] = COMPANY_SLUGS) -> list[dict]:
    """Fetch raw job postings from each Lever company slug.

    Returns a list of dicts with keys: title, company, url, location,
    created_at, description, source. Returns whatever succeeded if some
    companies fail -- logs a warning per failed company rather than aborting
    the whole run.
    """
    items: list[dict] = []
    for slug in company_slugs:
        url = POSTINGS_API_URL.format(slug=slug)
        logger.info("Fetching Lever postings: %s", slug)
        try:
            resp = requests.get(url, timeout=20)
            resp.raise_for_status()
            postings = resp.json()
            if not isinstance(postings, list) or not postings:
                logger.warning("Lever company %s returned 0 postings", slug)
                continue
            for job in postings:
                categories = job.get("categories") or {}
                items.append(
                    {
                        "title": job.get("text", ""),
                        "company": slug,
                        "url": job.get("hostedUrl", ""),
                        "location": categories.get("location"),
                        "commitment": categories.get("commitment"),
                        "created_at": job.get("createdAt"),
                        "description": job.get("descriptionPlain") or job.get("description", ""),
                        "source": "lever",
                    }
                )
        except Exception:
            logger.exception("Failed to fetch/parse Lever postings for %s", slug)

    logger.info("Fetched %d raw items from Lever (%d companies)", len(items), len(company_slugs))
    return items


PROJECT_ROOT = Path(__file__).resolve().parents[3]
RAW_OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "lever.json"


def main() -> None:
    items = fetch_raw()
    history_path = write_raw_output("lever", items)
    print(f"Fetched {len(items)} raw entries -> {history_path}")


if __name__ == "__main__":
    main()
