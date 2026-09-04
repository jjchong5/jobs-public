# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: Claude Code
# Prompt: "I tested Apify awhile ago and it worked on LinkedIn ... set up the pipeline?" (2026-06-25) -- see docs/ai_usage/prompt_log.md#src-pipeline-scrapers-linkedin_apifypy for full text
# Usage: LinkedIn Apify-actor (curious_coder/linkedin-jobs-scraper) scraper built to pipeline an actor the user had manually verified worked; later touched in a 2026-07-03 follow-up session.
# -------------------------------------------------------------------------

"""LinkedIn job scraper via the Apify actor `curious_coder/linkedin-jobs-scraper`.

LinkedIn itself is hard-blocked for direct scraping (aggressive bot detection;
see docs/SOURCES.md), so this goes through a managed third-party actor instead
of our own HTTP/Playwright code. The actor takes a LinkedIn job-search *URL*
(copied from the browser after applying filters) rather than keyword/location
fields -- there is no separate query API. Pricing is pay-per-result
($1.00 / 1,000 results as of this writing), so `count` is a hard cap on spend
per run, not just a result limit -- keep it deliberately low until cost at
this volume is validated against real usage.

Per CLAUDE.md's standing stance on scraping ToS friction: LinkedIn's ToS bans
automated access, but the author has stated an intent to scrape what's
technically reachable for personal use anyway (same precedent as Wellfound/
Built In). This module doesn't relitigate that; see docs/SOURCES.md for the
full tracking note.

Required env vars (.env):
    APIFY_API_TOKEN          -- Apify account API token
Optional:
    APIFY_LINKEDIN_SEARCH_URL  -- single LinkedIn jobs search URL to scrape.
                                  Overrides the default multi-query fan-out
                                  below with just this one URL.
    APIFY_LINKEDIN_SEARCH_URLS -- multiple search URLs, separated by `|||`.
                                  Overrides the default fan-out with this list.
    APIFY_LINKEDIN_MAX_ITEMS  -- result cap per query (default 200; the actor
                                  plateaus ~170-180/query well under that, so
                                  this rarely binds -- cost is ~$1/1000 results
                                  actually returned, not per the cap)

Query variety, not a higher per-query cap, is what actually multiplies
volume: the actor's real ceiling is per search-URL (~170-180 results),
confirmed via a live overlap probe across 4 varied queries (2026-07-03) --
pairwise Jaccard overlap between queries was only 0.9-15.1%, so different
keyword/location combinations surface largely disjoint job pools rather than
re-returning the same postings. DEFAULT_SEARCH_URLS below runs 4 queries
per call (SF DS/ML/AI, SF AI/ML engineer titles, remote DS/ML/AI, SF
freelance/contract) for ~$0.60/run combined instead of ~$0.18 for one.
Results are deduped across queries by job id before being returned.

Standalone run:
    python -m pipeline.scrapers.linkedin_apify
writes raw entries to data/raw/linkedin_apify.json and prints the count fetched.
"""

import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()


from pipeline.scrapers.raw_writer import write_raw_output
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

ACTOR_ID = "curious_coder/linkedin-jobs-scraper"

DEFAULT_SEARCH_URLS = [
    # sf_ds_ml_ai -- original default query
    "https://www.linkedin.com/jobs/search/"
    "?keywords=data%20scientist%20OR%20machine%20learning%20OR%20artificial%20intelligence"
    "&location=San%20Francisco%20Bay%20Area",
    # sf_ai_engineer -- adjacent title set, low overlap with above (15.1% Jaccard)
    "https://www.linkedin.com/jobs/search/"
    "?keywords=AI%20engineer%20OR%20ML%20engineer%20OR%20applied%20scientist"
    "&location=San%20Francisco%20Bay%20Area",
    # remote_ds_ml_ai -- nationwide remote, nearly disjoint from SF-scoped queries (0.9-1.5%)
    "https://www.linkedin.com/jobs/search/"
    "?keywords=data%20scientist%20OR%20machine%20learning%20OR%20artificial%20intelligence"
    "&location=United%20States&f_WT=2",
    # sf_freelance_contract -- matches the freelance/project-work ranking preference
    "https://www.linkedin.com/jobs/search/"
    "?keywords=machine%20learning%20OR%20AI%20contract%20OR%20freelance"
    "&location=San%20Francisco%20Bay%20Area",
]
DEFAULT_MAX_ITEMS = 200

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RAW_OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "linkedin_apify.json"


def _resolve_search_urls() -> list[str]:
    urls_env = os.environ.get("APIFY_LINKEDIN_SEARCH_URLS")
    if urls_env:
        return [u.strip() for u in urls_env.split("|||") if u.strip()]

    single_url = os.environ.get("APIFY_LINKEDIN_SEARCH_URL")
    if single_url:
        return [single_url]

    return DEFAULT_SEARCH_URLS


def _run_query(client: ApifyClient, search_url: str, max_items: int) -> list[dict]:
    logger.info("Running Apify actor %s (max_items=%d, url=%s)", ACTOR_ID, max_items, search_url)
    run = client.actor(ACTOR_ID).call(run_input={"urls": [search_url], "count": max_items})
    run = run.model_dump() if hasattr(run, "model_dump") else dict(run)
    logger.info(
        "Apify run %s finished, status=%s, cost_usd=%s",
        run.get("id"),
        run.get("status"),
        run.get("usage_total_usd"),
    )
    dataset_id = run["default_dataset_id"]
    return list(client.dataset(dataset_id).iterate_items())


def fetch_raw() -> list[dict]:
    """Run the LinkedIn Apify actor across each configured search URL and
    return the combined, deduped raw dataset items.

    Returns an empty list (and logs why) on missing token; a failed query
    within the fan-out is logged and skipped rather than aborting the whole
    run, same as every other scraper in this project's error-handling style.
    """
    token = os.environ.get("APIFY_API_TOKEN")
    if not token:
        logger.error("APIFY_API_TOKEN not set; skipping LinkedIn Apify fetch")
        return []

    search_urls = _resolve_search_urls()
    max_items = int(os.environ.get("APIFY_LINKEDIN_MAX_ITEMS", DEFAULT_MAX_ITEMS))
    client = ApifyClient(token)

    # Each search URL is an independent Apify actor run (own dataset, own
    # cost) -- .call() blocks synchronously waiting on the actor, so running
    # the fan-out in threads turns N sequential waits into one wait for the
    # slowest query instead of the sum of all of them.
    seen_ids: set = set()
    items: list[dict] = []
    with ThreadPoolExecutor(max_workers=len(search_urls)) as executor:
        future_to_url = {
            executor.submit(_run_query, client, search_url, max_items): search_url
            for search_url in search_urls
        }
        for future in as_completed(future_to_url):
            search_url = future_to_url[future]
            try:
                query_items = future.result()
            except Exception:
                logger.exception("Failed to fetch LinkedIn jobs via Apify actor %s for url=%s", ACTOR_ID, search_url)
                continue

            new_count = 0
            for rec in query_items:
                job_id = rec.get("id") or rec.get("link")
                if job_id in seen_ids:
                    continue
                seen_ids.add(job_id)
                items.append(rec)
                new_count += 1
            logger.info("Query returned %d items, %d new after dedup", len(query_items), new_count)

    logger.info(
        "Fetched %d unique raw items from LinkedIn across %d quer%s (via Apify)",
        len(items), len(search_urls), "y" if len(search_urls) == 1 else "ies",
    )

    return items


def main() -> None:
    items = fetch_raw()
    history_path = write_raw_output("linkedin_apify", items)
    print(f"Fetched {len(items)} raw entries -> {history_path}")


if __name__ == "__main__":
    main()
