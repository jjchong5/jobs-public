# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: Claude Code
# Prompt: "rename it wellfound_apify_old with documentation somewhere -- and
#   commit" (2026-07-03) -- see docs/ai_usage/prompt_log.md#src-pipeline-scrapers-wellfound_apify_oldpy
# Usage: Renamed from wellfound_apify.py to wellfound_apify_old.py and
#   documented as mothballed (superseded by wellfound_search_apify.py, see
#   CLAUDE.md Current State).
# -------------------------------------------------------------------------

"""ARCHIVED/MOTHBALLED 2026-07-03 -- superseded by wellfound_search_apify.py.

Live-tagging this scraper's 50-item pool found only 14% relevance>=5 against
the project's SF DS/ML/AI profile. Root cause (see wellfound_search_apify.py
docstring for the full investigation): this actor's `maxItems`/`keyword`/
`location` inputs are all client-side filters over one fixed, unauthenticated
~49-job snapshot of wellfound.com/jobs -- not real search. Renamed from
wellfound_apify.py to wellfound_apify_old.py and removed from ingest.py's
default source rotation (added to FROZEN_SOURCES) per author decision, same
reversible mothball pattern used for the frozen event sources. Code and
already-ingested data (`source='wellfound_apify_old'` in the DB) are left
intact, not deleted -- re-enable by passing `sources=["wellfound_apify_old"]`
to `run_ingest()` if ever needed again. See docs/SOURCES.md for full detail.

Wellfound (AngelList) job scraper via the Apify actor `crawlerbros/wellfound-scraper`.

Direct scraping of Wellfound is hard-blocked by DataDome (see wellfound.py and
docs/SOURCES.md -- every job-bearing URL returned 403 despite UA spoofing,
referer warm-up, non-headless, navigator.webdriver masking, and simulated
mouse/scroll). This module goes through a managed Apify actor instead, the
same pattern as linkedin_apify.py.

Picked `crawlerbros/wellfound-scraper` over several other Wellfound actors in
the Apify store after a deliberate evaluation, not just the first result:
description promises a narrow, plausible scope ("HTTP-only, no login" --
job ID, title, compensation, remote status, location, company), it's cheap
($0.005 actor-start + $0.002/result at the FREE tier vs. $0.003+/result for
alternatives), and it was NOT published by `orgupdate` -- that publisher's
`handshake-jobs-scraper` actor was tried and rejected earlier in this project
(see docs/SOURCES.md "Built, hard-blocked" table) for being a mislabeled
generic aggregator, so its other actors get extra scrutiny/avoidance rather
than a pass on reputation alone.

Verified live (2026-07-02) with a 10-item test call before trusting it: every
result had a real, self-consistent `jobUrl` in the form
`wellfound.com/jobs/<jobId>-<slug>` matching the returned title/company (e.g.
"Mechanical Engineer" at "Starfish Space", Seattle, $100k-$170k) -- not the
generic-aggregator junk pattern seen in the rejected Handshake actor (unrelated
domains riding along on a keyword match). Cost for the 10-item test: ~$0.00005
(FREE-tier pricing, well under the $25 session cap).

Required env vars (.env):
    APIFY_API_TOKEN            -- Apify account API token (already set for LinkedIn)
Optional:
    APIFY_WELLFOUND_START_URL  -- Wellfound jobs URL to scrape. Defaults to the
                                   unfiltered https://wellfound.com/jobs listing
                                   (this actor's own client-side filters are
                                   fairly blunt substring matches, so filtering
                                   downstream via the LLM tagger is more
                                   reliable than filtering at fetch time).
    APIFY_WELLFOUND_MAX_ITEMS  -- result cap per run (default 50; cost ~$0.10/run
                                   at the FREE tier's $0.002/result)

Standalone run:
    python -m pipeline.scrapers.wellfound_apify_old
writes raw entries to data/raw/wellfound_apify_old.json and prints the count fetched.
"""

import json
import logging
import os
from pathlib import Path

from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()


from pipeline.scrapers.raw_writer import write_raw_output
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

ACTOR_ID = "crawlerbros~wellfound-scraper"

DEFAULT_START_URL = "https://wellfound.com/jobs"
DEFAULT_MAX_ITEMS = 50

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RAW_OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "wellfound_apify_old.json"


def fetch_raw() -> list[dict]:
    """Run the Wellfound Apify actor and return its raw dataset items.

    Returns an empty list (and logs why) on missing token or actor failure --
    callers should handle empty results gracefully, same as every other
    scraper in this project.
    """
    token = os.environ.get("APIFY_API_TOKEN")
    if not token:
        logger.error("APIFY_API_TOKEN not set; skipping Wellfound Apify fetch")
        return []

    start_url = os.environ.get("APIFY_WELLFOUND_START_URL", DEFAULT_START_URL)
    max_items = int(os.environ.get("APIFY_WELLFOUND_MAX_ITEMS", DEFAULT_MAX_ITEMS))

    logger.info(
        "Running Apify actor %s (max_items=%d, start_url=%s)", ACTOR_ID, max_items, start_url
    )

    items: list[dict] = []
    try:
        client = ApifyClient(token)
        run = client.actor(ACTOR_ID).call(
            run_input={"startUrls": [start_url], "maxItems": max_items}
        )
        run = run.model_dump() if hasattr(run, "model_dump") else dict(run)
        logger.info(
            "Apify run %s finished, status=%s, cost_usd=%s",
            run.get("id"),
            run.get("status"),
            run.get("usage_total_usd"),
        )

        dataset_id = run["default_dataset_id"]
        for rec in client.dataset(dataset_id).iterate_items():
            items.append(rec)

        logger.info("Fetched %d raw items from Wellfound (via Apify)", len(items))
    except Exception:
        logger.exception("Failed to fetch Wellfound jobs via Apify actor %s", ACTOR_ID)

    return items


def main() -> None:
    items = fetch_raw()
    history_path = write_raw_output("wellfound_apify_old", items)
    print(f"Fetched {len(items)} raw entries -> {history_path}")


if __name__ == "__main__":
    main()
