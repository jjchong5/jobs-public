# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: Claude Code
# Prompt: built 2026-07-03 in the same session that later froze
#   wellfound_apify_old.py -- automated reconstruction couldn't isolate a
#   verbatim trigger; full transcript at docs/ai_usage/transcripts/, see
#   docs/ai_usage/prompt_log.md#src-pipeline-scrapers-wellfound_search_apifypy
# Usage: Live Wellfound scraper via a real role+location search-based Apify
#   actor, replacing the old flat-feed wellfound_apify.py.
# -------------------------------------------------------------------------

"""Wellfound (AngelList) role+location search via the Apify actor
`clearpath/wellfound-api-ppe`.

Supersedes `wellfound_apify_old.py` for signal quality, not existence -- that
scraper hits the unauthenticated `wellfound.com/jobs` teaser feed, which is a
fixed, unfiltered ~49-job snapshot regardless of `maxItems` or its own
`keyword`/`location` inputs (verified live 2026-07-03: `maxItems=500` still
returned exactly 49 raw jobs every time, and 4 different keyword/location
combinations all logged "Collected 49 raw jobs" -- those filters are applied
client-side *after* the fixed fetch, not sent to Wellfound as a real query).
Live-tagging that 50-item pool found only 14% scored relevance>=5 against the
project's SF DS/ML/AI profile -- mostly generic startup sales/ops/PM noise.

This module goes through Wellfound's own real role+location search pages
instead (`wellfound.com/role/l/<role-slug>/<location-slug>`), which this
actor's proxy pool can load (unlike direct/`wellfound.py`, hard-blocked by
DataDome, and unlike `wellfound_apify_old.py`'s actor, which 403's on any URL
under `/role/...` -- only its flat `/jobs` fetch gets through). Verified live
before trusting it: `/role/l/data-scientist/san-francisco` returned 75 real,
on-topic SF "Data Scientist" postings across 2 pages (vs. ~14% hit rate on
the flat feed); role slugs were checked individually first since not every
guess resolves -- `applied-scientist` and `machine-learning` both silently
fall back to an unfiltered citywide listing (2,880 jobs, generic junk titles
like "Environmental Test Engineer") rather than erroring, so those two are
deliberately excluded from ROLE_SLUGS below. `data-scientist`,
`machine-learning-engineer`, `ai-engineer`, and `data-engineer` all verified
to return real, on-topic titles.

Cost: pay-per-event, ~$0.003/job at the FREE tier (settles a few seconds
after the run reports back an initial $0.00005-looking `usage_total_usd` --
confirmed live by re-querying the run after a short delay: 27 jobs actually
billed at $0.081, i.e. ~$0.003/job, matching the actor's published FREE-tier
"job-scraped" price). PAGE_LIMIT=0 (fetch every page the site reports) is the
default since role-scoped results are ~90%+ on-topic by construction (unlike
the flat feed, where paying for more volume buys mostly noise) -- a full
4-role SF pull runs several dollars, not several cents; still well inside the
project's $25 Apify session cap and returns real full coverage instead of a
single-page sample.

Required env vars (.env):
    APIFY_API_TOKEN                 -- already set for the other Apify sources
Optional:
    WELLFOUND_SEARCH_ROLES          -- comma-separated role slugs (default: see ROLE_SLUGS)
    WELLFOUND_SEARCH_LOCATION       -- Wellfound location slug (default: san-francisco)
    WELLFOUND_SEARCH_PAGE_LIMIT     -- pages per role query, 0 = unlimited (default: 0)

Standalone run:
    python -m pipeline.scrapers.wellfound_search_apify
writes raw entries to data/raw/wellfound_search_apify.json and prints the count fetched.
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

ACTOR_ID = "clearpath~wellfound-api-ppe"

# "applied-scientist" and "machine-learning" deliberately excluded -- verified
# live to silently fall back to an unfiltered citywide job listing instead of
# a real role-scoped search (see module docstring).
ROLE_SLUGS = ["data-scientist", "machine-learning-engineer", "ai-engineer", "data-engineer"]
DEFAULT_LOCATION_SLUG = "san-francisco"
DEFAULT_PAGE_LIMIT = 0  # 0 = unlimited (fetch every page the actor reports)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RAW_OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "wellfound_search_apify.json"


def fetch_raw() -> list[dict]:
    """Run the Wellfound role+location search actor for each configured role
    slug and return the combined raw dataset items.

    Returns an empty list (and logs why) on missing token or actor failure --
    callers should handle empty results gracefully, same as every other
    scraper in this project. A per-role failure logs and continues rather
    than aborting the whole fetch, since each role query is independent.
    """
    token = os.environ.get("APIFY_API_TOKEN")
    if not token:
        logger.error("APIFY_API_TOKEN not set; skipping Wellfound search fetch")
        return []

    roles_env = os.environ.get("WELLFOUND_SEARCH_ROLES")
    role_slugs = [r.strip() for r in roles_env.split(",")] if roles_env else ROLE_SLUGS
    location_slug = os.environ.get("WELLFOUND_SEARCH_LOCATION", DEFAULT_LOCATION_SLUG)
    page_limit = int(os.environ.get("WELLFOUND_SEARCH_PAGE_LIMIT", DEFAULT_PAGE_LIMIT))

    client = ApifyClient(token)

    def _run_role(role: str) -> list[dict]:
        url = f"https://wellfound.com/role/l/{role}/{location_slug}"
        logger.info("Running Apify actor %s for role=%s location=%s (page_limit=%d)",
                    ACTOR_ID, role, location_slug, page_limit)
        run = client.actor(ACTOR_ID).call(run_input={"urls": [url], "pageLimit": page_limit})
        run = run.model_dump() if hasattr(run, "model_dump") else dict(run)
        dataset_id = run["default_dataset_id"]
        role_items = list(client.dataset(dataset_id).iterate_items())
        logger.info("Fetched %d raw items for role=%s (run status=%s)",
                    len(role_items), role, run.get("status"))
        return role_items

    # Each role query is an independent Apify actor run -- .call() blocks
    # synchronously, so fan these out across threads instead of waiting on
    # each role in turn (same pattern as linkedin_apify.py's query fan-out).
    items: list[dict] = []
    with ThreadPoolExecutor(max_workers=len(role_slugs)) as executor:
        future_to_role = {executor.submit(_run_role, role): role for role in role_slugs}
        for future in as_completed(future_to_role):
            role = future_to_role[future]
            try:
                items.extend(future.result())
            except Exception:
                logger.exception("Failed to fetch Wellfound search results for role=%s", role)

    logger.info("Fetched %d total raw items from Wellfound search across %d role(s)",
                len(items), len(role_slugs))
    return items


def main() -> None:
    items = fetch_raw()
    history_path = write_raw_output("wellfound_search_apify", items)
    print(f"Fetched {len(items)} raw entries -> {history_path}")


if __name__ == "__main__":
    main()
