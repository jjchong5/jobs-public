# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: Claude Code
# Prompt: decision to freeze the prior Indeed Apify integration rather than
#   delete it, made in the same 2026-07-03 turn that built indeed_radius.py --
#   see docs/ai_usage/prompt_log.md#src-pipeline-scrapers-indeed_apify_oldpy
# Usage: Renamed/frozen the original Indeed Apify scraper as a deliberate
#   fallback after indeed_radius.py replaced it as the live source.
# -------------------------------------------------------------------------

"""FROZEN/MOTHBALLED 2026-07-03 -- superseded as the default by indeed_radius.py.

Kept in reserve, not deleted, for a different reason than the wellfound
mothball: this actor (`misceres/indeed-scraper`, residential-proxy HTML
scraping) isn't broken or low-quality -- indeed_radius.py is simply cheaper
(~$0.00125/item vs $0.005/item here) and has a native `radius` param that
closes a real coverage gap this actor lacks (no radius/distance input, so
"San Francisco, CA" and "San Jose, CA" searches came back ~92% non-overlapping
in a live comparison -- see docs/SOURCES.md). The tradeoff: indeed_radius.py's
actor authenticates using harvested third-party mobile-app session cookies
against Indeed's private mobile API, a materially different (and less
predictable) mechanism than this actor's residential-proxy approach -- no
personal account-ban risk either way (neither actor uses the author's own
credentials), but the harvested-token pool could get invalidated/blocked at
any time without warning. This actor is kept live in the codebase as a known-
working fallback for exactly that scenario. Renamed from indeed_apify.py to
indeed_apify_old.py and added to FROZEN_SOURCES in ingest.py (same reversible
mothball pattern as the frozen event sources and wellfound_apify_old) --
re-enable by passing sources=["indeed_apify_old"] to run_ingest() if
indeed_radius ever breaks. Already-ingested data was migrated to
source='indeed_apify_old' in the DB for consistency with the rename.

Indeed job scraper via the Apify actor `misceres/indeed-scraper`.

Indeed's public RSS feed is dead (retired by Indeed, confirmed 404 -- see
`indeed_rss.py` and docs/SOURCES.md), so this goes through a managed Apify
actor instead, same pattern as `linkedin_apify.py` and (now-archived)
`wellfound_apify_old.py`.
`misceres/indeed-scraper` was picked over several similarly-named actors in
the Apify store after checking real usage (26k+ users, 1.7M+ runs -- by far
the most established), unlike the mislabeled Handshake actor rejected
earlier in this project (see docs/SOURCES.md). Pricing is pay-per-result
($0.005/result as of this writing), so `maxItemsPerSearch` is a hard cap on
spend per run, not just a result limit -- keep it deliberately low until
cost at this volume is validated against real usage.

Required env vars (.env):
    APIFY_API_TOKEN            -- Apify account API token
Optional:
    APIFY_INDEED_POSITION      -- search keywords (default: generic SF DS/ML/AI)
    APIFY_INDEED_LOCATION      -- search location (default: San Francisco, CA)
    APIFY_INDEED_MAX_ITEMS     -- result cap per run (default 10; cost ~$0.05/run
                                   at $0.005/result)

Standalone run:
    python -m pipeline.scrapers.indeed_apify_old
writes raw entries to data/raw/indeed_apify_old.json and prints the count fetched.
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

ACTOR_ID = "misceres/indeed-scraper"

DEFAULT_POSITION = "data scientist OR machine learning OR artificial intelligence"
DEFAULT_LOCATION = "San Francisco, CA"
DEFAULT_MAX_ITEMS = 10

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RAW_OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "indeed_apify_old.json"


def fetch_raw() -> list[dict]:
    """Run the Indeed Apify actor and return its raw dataset items.

    Returns an empty list (and logs why) on missing token or actor failure --
    callers should handle empty results gracefully, same as every other
    scraper in this project.
    """
    token = os.environ.get("APIFY_API_TOKEN")
    if not token:
        logger.error("APIFY_API_TOKEN not set; skipping Indeed Apify fetch")
        return []

    position = os.environ.get("APIFY_INDEED_POSITION", DEFAULT_POSITION)
    location = os.environ.get("APIFY_INDEED_LOCATION", DEFAULT_LOCATION)
    max_items = int(os.environ.get("APIFY_INDEED_MAX_ITEMS", DEFAULT_MAX_ITEMS))

    logger.info(
        "Running Apify actor %s (position=%r, location=%r, maxItemsPerSearch=%d)",
        ACTOR_ID, position, location, max_items,
    )

    items: list[dict] = []
    try:
        client = ApifyClient(token)
        run = client.actor(ACTOR_ID).call(
            run_input={
                "position": position,
                "location": location,
                "country": "US",
                "maxItemsPerSearch": max_items,
            }
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

        logger.info("Fetched %d raw items from Indeed (via Apify)", len(items))
    except Exception:
        logger.exception("Failed to fetch Indeed jobs via Apify actor %s", ACTOR_ID)

    return items


def main() -> None:
    items = fetch_raw()
    history_path = write_raw_output("indeed_apify_old", items)
    print(f"Fetched {len(items)} raw entries -> {history_path}")


if __name__ == "__main__":
    main()
