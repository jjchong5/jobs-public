# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: Claude Code
# Prompt: "That harvesting method shouldn't expose me to any account
#   risk..." (2026-07-03) -- see docs/ai_usage/prompt_log.md#src-pipeline-scrapers-indeed_radiuspy
# Usage: Indeed radius-search Apify-actor scraper, replacing indeed_apify.py
#   as the live Indeed source; docstring documents the session-token
#   authentication tradeoff discussed in the prompt.
# -------------------------------------------------------------------------

"""Indeed job scraper via the Apify actor `memo23/apify-indeed-cheerio-ppr`.

Live-replaces indeed_apify_old.py (misceres/indeed-scraper) as the default
Indeed source, added 2026-07-03 after a capped-cost live comparison: this
actor has a native `radius` param (miles) that closes a real coverage gap --
indeed_apify_old.py has no radius/distance input, so "San Francisco, CA" and
"San Jose, CA" searches came back ~92% non-overlapping even though both are
Bay Area. A single radius=25 search around San Francisco returned 1,594 items
for $2.00 (~$0.00125/item, capped by the actor's own internal 1,600-item
pay-per-result ceiling, not exhausted -- more available), vs ~$0.005/item and
no radius coverage on the old actor.

Tradeoff, not free lunch: this actor's logs show it authenticating to
Indeed's private mobile API using harvested third-party mobile-app session
cookies (real Cloudflare `cf_clearance`/`__cf_bm` bypass tokens plus another
user's actual search history baked into the request), rotated via what looks
like a Telegram-bot-managed device-token pool -- not the actor's own
dedicated login, and not the project author's credentials either way, so
there's no personal account-ban risk. The real risk is reliability: that
harvested-token pool could get detected and invalidated at any time, breaking
this actor without warning. indeed_apify_old.py is deliberately kept live in
the codebase (not deleted, just excluded from the default source rotation via
FROZEN_SOURCES) as a known-working fallback for exactly that scenario --
re-enable it by passing sources=["indeed_apify_old"] to run_ingest().

This actor also enforces its own `ACTOR_MAX_PAID_DATASET_ITEMS` ceiling
(1,600 as of this writing) independent of whatever `max_jobs`/cost cap is
requested -- a single run cannot return more than that regardless of budget,
so broader pulls need either multiple runs (different keyword/location
splits) or a higher ceiling if the actor's pricing tier changes.

Required env vars (.env):
    APIFY_API_TOKEN               -- Apify account API token (already set for other sources)
Optional:
    APIFY_INDEED_RADIUS_POSITION  -- search keywords (default: broadened SF DS/ML/AI set)
    APIFY_INDEED_RADIUS_LOCATION  -- search location (default: San Francisco, CA)
    APIFY_INDEED_RADIUS_MILES     -- search radius in miles (default: 25)
    APIFY_INDEED_RADIUS_MAX_JOBS  -- result cap per run (default 500; actor's own
                                      1,600-item pay-per-result ceiling is the hard cap
                                      regardless of this value)

Standalone run:
    python -m pipeline.scrapers.indeed_radius
writes raw entries to data/raw/indeed_radius.json and prints the count fetched.
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

ACTOR_ID = "memo23/apify-indeed-cheerio-ppr"

DEFAULT_POSITION = (
    "data scientist OR machine learning engineer OR artificial intelligence "
    "OR ai engineer OR data engineer OR research scientist OR generative AI "
    "OR applied scientist OR computer vision OR robotics"
)
DEFAULT_LOCATION = "San Francisco, CA"
DEFAULT_RADIUS_MILES = 25
DEFAULT_MAX_JOBS = 500
COUNTRY = "United States"  # actor requires the full country name, not a code


def fetch_raw() -> list[dict]:
    """Run the Indeed radius-search Apify actor and return its raw dataset items.

    Returns an empty list (and logs why) on missing token or actor failure --
    callers should handle empty results gracefully, same as every other
    scraper in this project.
    """
    token = os.environ.get("APIFY_API_TOKEN")
    if not token:
        logger.error("APIFY_API_TOKEN not set; skipping Indeed radius fetch")
        return []

    position = os.environ.get("APIFY_INDEED_RADIUS_POSITION", DEFAULT_POSITION)
    location = os.environ.get("APIFY_INDEED_RADIUS_LOCATION", DEFAULT_LOCATION)
    radius = int(os.environ.get("APIFY_INDEED_RADIUS_MILES", DEFAULT_RADIUS_MILES))
    max_jobs = int(os.environ.get("APIFY_INDEED_RADIUS_MAX_JOBS", DEFAULT_MAX_JOBS))

    logger.info(
        "Running Apify actor %s (position=%r, location=%r, radius=%d, maxJobs=%d)",
        ACTOR_ID, position, location, radius, max_jobs,
    )

    items: list[dict] = []
    try:
        client = ApifyClient(token)
        run = client.actor(ACTOR_ID).call(
            run_input={
                "position": position,
                "location": location,
                "radius": radius,
                "country": COUNTRY,
                "maxJobs": max_jobs,
                "sort": "relevance",
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

        logger.info("Fetched %d raw items from Indeed (via radius Apify actor)", len(items))
    except Exception:
        logger.exception("Failed to fetch Indeed jobs via Apify actor %s", ACTOR_ID)

    return items


def main() -> None:
    items = fetch_raw()
    history_path = write_raw_output("indeed_radius", items)
    print(f"Fetched {len(items)} raw entries -> {history_path}")


if __name__ == "__main__":
    main()
