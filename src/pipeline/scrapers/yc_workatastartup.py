# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: Claude Code
# Prompt: built 2026-07-02, extended 2026-07-03 during the overnight
#   source-connection passes -- automated reconstruction couldn't isolate a
#   verbatim trigger; full transcripts at docs/ai_usage/transcripts/, see
#   docs/ai_usage/prompt_log.md#src-pipeline-scrapers-yc_workatastartuppy
# Usage: YC Work at a Startup board scraper.
# -------------------------------------------------------------------------

"""Y Combinator "Work at a Startup" job scraper (workatastartup.com).

The jobs listing pages (`/jobs` and `/jobs/l/<category>`) are server-rendered
via Inertia.js -- the full job list for the page is embedded as JSON in a
`data-page="..."` attribute on the root `<div>`, present in the initial HTML
with no login required and no JS execution needed. Confirmed live (2026-07-02):
plain `requests` with browser-like `Accept`/`Accept-Language` headers works;
a bare default `requests` header set gets HTTP 406 (Cloudflare-class header
sniffing, not a CAPTCHA/anti-bot block -- realistic headers alone clear it,
no retry loop needed).

No per-job public URL is exposed by this source -- `applyUrl` is a YC
account-signup/login redirect, not a viewable posting page. Same situation as
Handshake (see handshake_email.py): this module constructs a synthetic-but-
resolvable URL pointing at the company's public profile page
(`workatastartup.com/companies/<slug>?jobId=<id>`, itself confirmed public/
unauthenticated) with the real numeric job id as a query param, so dedup is
unique per job even though the URL doesn't deep-link to the exact posting.
The real signup/apply link is preserved in `raw_json.applyUrl` for manual
click-through if the user wants to actually apply.

**Checked live (2026-07-03) whether this source was under-fetching, same
pass that expanded vc_portfolio.py/aijobs_net.py/greenhouse.py/lever.py/
ashby.py: it wasn't.** `LISTING_PATHS` already covers the only DS/ML/AI-
relevant category YC exposes (`roleLinks` lists exactly 10 top-level
categories -- Engineering, Design, Recruiting, Science, Product, Operations,
Sales, Marketing, Legal, Finance -- "Science" is the only DS/ML/AI-adjacent
one and was already included). Confirmed each category page returns its
*entire* result set in one response, not a truncated page (`/jobs/l/
science?page=2` returned the same 26 jobs as page 1, not a next page or an
empty one; a `?query=` param was also tried and silently ignored -- no
keyword search exists here, matching Greenhouse/Lever/Ashby's "no
cross-company/cross-category search" shape). No pagination or volume cap
to raise; this source was already fetching everything reachable.

Standalone run:
    python -m pipeline.scrapers.yc_workatastartup
writes raw entries to data/raw/yc_workatastartup.json and prints the count fetched.
"""

import json
import logging
from pathlib import Path

import requests
from bs4 import BeautifulSoup


from pipeline.scrapers.raw_writer import write_raw_output
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BASE_URL = "https://www.workatastartup.com"
# /jobs = default "Engineering / Software Engineer" category; /jobs/l/science
# covers Data Science/ML roles -- the two categories most relevant to the
# seeded SF DS/ML/AI preference profile. Same "seed a reasonable default,
# don't over-curate" stance as the Greenhouse/Lever company lists.
LISTING_PATHS = ["/jobs", "/jobs/l/science"]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RAW_OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "yc_workatastartup.json"


def fetch_raw(listing_paths: list[str] = LISTING_PATHS) -> list[dict]:
    """Fetch raw job postings from YC Work at a Startup listing pages.

    Returns a list of dicts with keys: id, title, jobType, location,
    roleType, salary, companyName, companySlug, companyOneLiner, applyUrl,
    source. Dedups across listing pages by job id (the Science and
    Engineering categories can overlap). Returns whatever succeeded if a
    page fails -- logs a warning rather than aborting the whole run.
    """
    seen_ids: set[int] = set()
    items: list[dict] = []
    for path in listing_paths:
        url = f"{BASE_URL}{path}"
        logger.info("Fetching YC Work at a Startup listing: %s", url)
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            page_div = soup.find("div", attrs={"data-page": True})
            if not page_div:
                logger.warning("No data-page payload found on %s (page may have changed)", url)
                continue
            data = json.loads(page_div["data-page"])
            jobs = data.get("props", {}).get("jobs", [])
            if not jobs:
                logger.warning("YC listing %s returned 0 jobs", url)
            for job in jobs:
                job_id = job.get("id")
                if job_id in seen_ids:
                    continue
                seen_ids.add(job_id)
                job = dict(job)
                job["source"] = "yc_workatastartup"
                items.append(job)
        except Exception:
            logger.exception("Failed to fetch/parse YC Work at a Startup listing %s", url)

    logger.info("Fetched %d raw items from YC Work at a Startup", len(items))
    return items


def main() -> None:
    items = fetch_raw()
    history_path = write_raw_output("yc_workatastartup", items)
    print(f"Fetched {len(items)} raw entries -> {history_path}")


if __name__ == "__main__":
    main()
