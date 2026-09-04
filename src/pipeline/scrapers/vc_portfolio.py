# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: Claude Code
# Prompt: Reviewed/expanded VC-portfolio (Getro/Consider) board scraper headroom (2026-07-03) -- see docs/ai_usage/prompt_log.md#src-pipeline-scrapers-vc_portfoliopy for full text
# Usage: VC-portfolio board scraper built and later reviewed for pagination headroom (10-page/keyword cap) as part of a per-source volume-ceiling pass; earlier pagination-undercounting bugfix's triggering prompt is in the raw transcripts at docs/ai_usage/transcripts/ but wasn't isolated by automated reconstruction.
# -------------------------------------------------------------------------

"""VC portfolio job board scraper (Getro/Consider-powered public API).

Several major VC firms host a cross-portfolio job board on the Getro/Consider
platform (`jobs.<firm>.com`), which aggregates open roles from every company
in that firm's portfolio into one searchable board. The board's search UI
calls a public, unauthenticated JSON API at
`https://<board_host>/api-boards/search-jobs` (POST, JSON body) -- discovered
by rendering `jobs.a16z.com/jobs` once with Playwright and inspecting the
real XHR request the search box fires (not guessed/brute-forced), then
confirmed to work with a plain `requests.post` (no browser needed at
runtime). No auth, no anti-bot encountered on the boards that responded.

Each portfolio board aggregates thousands of jobs across every industry the
firm invests in (a16z alone reports ~15,478 total), so unlike Greenhouse/
Lever this can't just pull "the whole board" -- `query.titlePrefix` (a
substring match against job title, confirmed by observing the real
search-box request) is used to scope each board to `KEYWORDS` matching this
project's seeded SF DS/ML/AI profile, same spirit as the Meetup/Eventbrite
keyword-search approach.

`BOARDS` is a placeholder list of VC firms confirmed live against the real
API (2026-07-02) -- same "reasonable starting set, don't over-curate" spirit
as the Greenhouse/Lever/Ashby company lists. Two candidates
(`jobs.generalcatalyst.com`, `jobs.khoslaventures.com`) returned HTTP 403 on
a single plain request -- treated as blocked per the project's hard
anti-bot-safety rule (no retry/header-rotation loop against a site that
403s), not chased further. Two more (`jobs.indexventures.com`,
`jobs.nea.com`) failed DNS resolution outright (wrong subdomain guess, not a
block) and were dropped rather than guessed at further.

Standalone run:
    python -m pipeline.scrapers.vc_portfolio
writes raw entries to data/raw/vc_portfolio.json and prints the count fetched.
"""

import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests


from pipeline.scrapers.raw_writer import write_raw_output
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

SEARCH_API_URL = "https://{host}/api-boards/search-jobs"

# Confirmed live (2026-07-02) -- each (host, board_id) pair returned real
# jobs from the public API for at least one KEYWORDS query.
BOARDS = [
    ("jobs.a16z.com", "andreessen-horowitz"),
    ("jobs.sequoiacap.com", "sequoia-capital"),
    ("jobs.greylock.com", "greylock-partners"),
    ("jobs.bvp.com", "bessemer-ventures"),
    ("jobs.lsvp.com", "lightspeed"),
    ("jobs.gv.com", "gv"),
    ("jobs.kleinerperkins.com", "kleiner-perkins"),
]

# Widened (2026-07-03) from the original 3-term list after confirming live
# that the API paginates (see below) -- a single keyword against one board
# can undercount by more than half (a16z + "data scientist" alone: 117 total,
# the old 50-cap-per-query/no-pagination code only surfaced 50 of them).
# These terms are still a titlePrefix *substring* match (confirmed against
# the real search-box request, not guessed), so broader/adjacent phrasing
# matters more than exact job-title casing.
KEYWORDS = [
    "data scientist",
    "machine learning",
    "AI engineer",
    "artificial intelligence",
    "data science",
    "research scientist",
    "applied scientist",
    "ML engineer",
    "data engineer",
    "deep learning",
    "NLP",
    "computer vision",
    "LLM",
]

RESULTS_PER_QUERY = 50
# Safety cap, not an expected steady-state count -- confirmed live that the
# API paginates via a `meta.sequence` cursor with a real `total` field (a16z
# + "data scientist" = 117 total across 3 pages, no overlap between pages).
# Caps a single keyword/board combo at 10 pages (500 results) so a
# unexpectedly broad term (e.g. a generic top-level board with a huge
# portfolio) can't turn one run into an unbounded crawl. Confirmed live
# 2026-07-03 (temporarily raised to 50 to test this): every board+keyword
# combo across all 7 live boards topped out at page 2 (100 results) --
# the real ceiling here is the board/keyword universe, not pagination depth.
MAX_PAGES_PER_QUERY = 10
REQUEST_DELAY_SECONDS = 0.3


QUERY_FETCH_WORKERS = 10  # bounded pool -- each (board, keyword) pagination
                          # chain is independent, but boards/keyword.py should
                          # still be considerate of the shared Getro/Consider
                          # API rather than firing all 90+ chains at once


def _fetch_board_keyword(host: str, board_id: str, keyword: str) -> list[dict]:
    """Paginate one (board, keyword) combo via the API's `meta.sequence`
    cursor until it runs out of results, an empty/short page comes back, or
    MAX_PAGES_PER_QUERY is hit as a safety cap. Pagination within a combo is
    inherently sequential (each page needs the prior page's cursor); combos
    themselves are independent and safe to run concurrently."""
    url = SEARCH_API_URL.format(host=host)
    items: list[dict] = []
    sequence = None
    for page_num in range(1, MAX_PAGES_PER_QUERY + 1):
        meta = {"size": RESULTS_PER_QUERY}
        if sequence:
            meta["sequence"] = sequence
        body = {
            "meta": meta,
            "board": {"id": board_id, "isParent": True},
            "query": {"titlePrefix": keyword, "promoteFeatured": True},
        }
        logger.info("Fetching VC board: %s (query=%r, page=%d)", host, keyword, page_num)
        resp = requests.post(url, json=body, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        jobs = data.get("jobs", [])
        if page_num == 1 and not jobs:
            logger.warning("VC board %s returned 0 jobs for %r", host, keyword)
        for job in jobs:
            job_id = str(job.get("jobId"))
            items.append(
                {
                    "title": job.get("title", ""),
                    "company": job.get("companyName"),
                    "url": job.get("url") or job.get("applyUrl"),
                    "location": ", ".join(job.get("locations") or []) or None,
                    "vc_firm": board_id,
                    "salary": job.get("salary"),
                    "remote": job.get("remote"),
                    "job_functions": [f.get("label") for f in (job.get("jobFunctions") or [])],
                    "posted_at": job.get("timeStamp"),
                    "job_id": job_id,
                    "source": "vc_portfolio",
                }
            )
        total = data.get("total", 0)
        fetched_so_far = page_num * RESULTS_PER_QUERY
        if not jobs or len(jobs) < RESULTS_PER_QUERY or fetched_so_far >= total:
            break
        sequence = (data.get("meta") or {}).get("sequence")
        if not sequence:
            break
        time.sleep(REQUEST_DELAY_SECONDS)
    return items


def fetch_raw(boards: list[tuple[str, str]] = BOARDS, keywords: list[str] = KEYWORDS) -> list[dict]:
    """Fetch raw job postings from each VC portfolio board for each keyword.

    Confirmed live that consecutive pages return disjoint job sets, not
    overlapping ones. Returns a list of dicts with keys: title, company, url,
    location, vc_firm, salary, remote, job_functions, posted_at, source.
    Dedupes within a board across overlapping keyword matches (a job can
    match more than one keyword) by (board_id, jobId). Returns whatever
    succeeded if some boards/queries fail -- logs a warning rather than
    aborting the run.

    Each (board, keyword) pagination chain runs concurrently (bounded pool,
    see QUERY_FETCH_WORKERS) -- with 7 boards x 13 keywords, running all ~91
    chains one at a time (each with its own REQUEST_DELAY_SECONDS throttle
    between pages) was the slowest part of the whole ingest run.
    """
    items: list[dict] = []
    seen_job_ids_by_board: dict[str, set[str]] = {board_id: set() for _, board_id in boards}
    with ThreadPoolExecutor(max_workers=QUERY_FETCH_WORKERS) as executor:
        future_to_query = {
            executor.submit(_fetch_board_keyword, host, board_id, keyword): (host, board_id, keyword)
            for host, board_id in boards
            for keyword in keywords
        }
        for future in as_completed(future_to_query):
            host, board_id, keyword = future_to_query[future]
            try:
                query_items = future.result()
            except Exception:
                logger.exception("Failed to fetch/parse VC board %s for %r", host, keyword)
                continue
            seen_job_ids = seen_job_ids_by_board[board_id]
            for item in query_items:
                job_id = item["job_id"]
                if job_id in seen_job_ids:
                    continue
                seen_job_ids.add(job_id)
                items.append(item)

    logger.info("Fetched %d raw items from VC portfolio boards (%d boards)", len(items), len(boards))
    return items


PROJECT_ROOT = Path(__file__).resolve().parents[3]
RAW_OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "vc_portfolio.json"


def main() -> None:
    items = fetch_raw()
    history_path = write_raw_output("vc_portfolio", items)
    print(f"Fetched {len(items)} raw entries -> {history_path}")


if __name__ == "__main__":
    main()
