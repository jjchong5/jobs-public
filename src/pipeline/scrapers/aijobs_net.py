# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: Claude Code
# Prompt: Reviewed/expanded aijobs.net scraper page-cap headroom (2026-07-03) -- see docs/ai_usage/prompt_log.md#src-pipeline-scrapers-aijobs_netpy for full text
# Usage: aijobs.net scraper reviewed and page-limit (PAGES) headroom analyzed/expanded against the site's much larger total job count; original build-session prompt not cleanly recoverable.
# -------------------------------------------------------------------------

"""aijobs.net scraper (plain HTML scrape, server-rendered, no anti-bot).

aijobs.net ("The go-to, no-nonsense, fast and lean job site in AI, ML, Data
Science and Big Data") is a topical AI/ML/DS job board -- unlike Greenhouse/
Lever/Ashby/VC-portfolio boards, every listing here is already in-domain, so
there's no need for a keyword filter to scope relevance (same rationale the
original source request called out: "directly topical rather than filtered
down from a generalist board").

The homepage (`aijobs.net/?page=N`) is plain server-rendered HTML with a
Bootstrap-based job list (`ul#job_list`), no anti-bot markers encountered on
a first plain `requests` GET -- same class of source as Built In SF. Its
search/filter form (topics/skills/roles/regions/cities/etc.) is a
JS-populated `<select>` with empty options in the raw HTML, so it can't be
driven without a browser -- not attempted; pagination via `?page=N` is
sufficient for a scoped placeholder pull, same "don't over-curate" stance as
every other source list in this project.

**Company name is not present on the list page** (checked directly --
`/company/` appears only in nav chrome, not per-card); it's only shown on
each job's own detail page (`@ <company>` link). That means one extra HTTP
GET per job on top of the list-page fetches.

**Site-wide total checked live (2026-07-03): 46,090 jobs.** This is a global
board (every country, every remote listing), not SF-scoped -- the original
`PAGES=2` (100 jobs) cap only ever saw the newest 100 of that 46k. Tried to
find a real server-side filter before just raising the page count: the
select fields (`topics`/`countries`/`regions`/etc.) are backed by real
per-field autocomplete endpoints (`/ac/topic/`, `/ac/country/`, ... --
`django-tomselect`), and querying those directly resolves real pks (e.g.
`topics=9` for "Data Science", `countries=238` for "United States"). But
passing those same pks as `?topics=9&countries=238` on the list page itself
does **not** filter -- the total stayed 46,090 regardless, confirmed by
direct comparison against the unfiltered request. The actual filter
submission is evidently not a plain GET the way Django-rendered forms
usually are (likely POST+CSRF or an htmx partial-swap this project didn't
reverse-engineer) -- replicating it, or driving the real `<select>` UI with
Playwright, would work but is a meaningfully bigger lift than every other
change in this pass, so it wasn't pursued here. **Advice if this needs
revisiting**: render the page once with Playwright, apply the topic/country
filter through the real UI, and capture the resulting network request (same
discovery technique already used for `vc_portfolio.py`'s Getro API) rather
than guessing at the submission shape.

Given no clean filter exists, `PAGES` is raised to a bounded, still-polite
slice of the newest listings (assumed newest-first by the site's own
default sort, unverified beyond observing distinct job sets page-to-page)
rather than attempting the full 46k (which would mean ~922 pages and
~1,800+ requests per run). Relevance filtering for this larger, still
mostly-global slice continues to happen downstream in the LLM tagger, same
as the original 100-job pull.

Known data quirk (verified against the raw HTTP response, not our bug, same
category as the Luma mojibake precedent): a small number of location strings
contain a mojibake byte in place of a country name suffix (e.g. "United
<mojibake>" instead of "United States").

Standalone run:
    python -m pipeline.scrapers.aijobs_net
writes raw entries to data/raw/aijobs_net.json and prints the count fetched.
"""

import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
from bs4 import BeautifulSoup


from pipeline.scrapers.raw_writer import write_raw_output
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BASE_URL = "https://aijobs.net"
LIST_URL = BASE_URL + "/?page={page}"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# Raised 2026-07-03 from 2 -> 20 -> 60 (3,000 jobs) now that server-side
# filtering is confirmed unavailable (see module docstring) -- still a
# fraction of the real 46,090 total, but author wants to test real per-source
# ceilings before re-imposing cost/volume caps.
PAGES = 60
REQUEST_DELAY_SECONDS = 0.3
# The per-job detail GET (company name + description, one extra request per
# listing -- see module docstring) was the real bottleneck, not the site's
# tolerance: previously done sequentially with a 0.3s sleep between every one
# of the 50 detail fetches per page (~1min/page). No rate-limiting/anti-bot
# response has been seen from this site at any concurrency tested. A small
# bounded thread pool parallelizes just the detail fetches within one page
# (list-page fetches and inter-page pacing stay sequential) -- confirmed live
# 2026-07-03 that this cuts per-page time substantially with no errors.
DETAIL_FETCH_WORKERS = 8


def _parse_card(li) -> dict:
    a = li.find("a", class_="stretched-link")
    for sp in a.find_all("span"):
        sp.decompose()
    title = a.get_text(strip=True)
    url = BASE_URL + a["href"] if a["href"].startswith("/") else a["href"]

    left, right = li.find_all("div", recursive=False)
    left_subdivs = left.find_all("div", recursive=False)
    salary_span = left_subdivs[0].find("span", class_="text-bg-success") if left_subdivs else None
    salary = salary_span.get_text(strip=True) if salary_span else None
    tags = [s.get_text(strip=True) for s in left_subdivs[1].find_all("span")] if len(left_subdivs) > 1 else []

    right_subdivs = right.find_all("div", recursive=False)
    seniority = job_type = None
    if right_subdivs:
        badges = right_subdivs[0].find_all("span")
        if len(badges) > 0:
            seniority = badges[0].get_text(strip=True)
        if len(badges) > 1:
            job_type = badges[1].get_text(strip=True)
    location = None
    remote = False
    if len(right_subdivs) > 1:
        remote = right_subdivs[1].find("span", class_="text-bg-success") is not None
        loc_div = right_subdivs[1]
        for sp in loc_div.find_all("span"):
            sp.decompose()
        location = loc_div.get_text(strip=True) or None
    posted_ago = right_subdivs[2].get_text(strip=True) if len(right_subdivs) > 2 else None

    return {
        "title": title,
        "url": url,
        "salary": salary,
        "tags": tags,
        "seniority": seniority,
        "job_type": job_type,
        "location": location,
        "remote": remote,
        "posted_ago": posted_ago,
    }


def _fetch_company_and_description(url: str) -> tuple[str | None, str]:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        company_link = soup.find("a", href=lambda h: h and h.startswith("/company/"))
        company = None
        if company_link:
            company = company_link.get_text(strip=True).lstrip("@").strip()
        main = soup.find("main")
        description = main.get_text("\n", strip=True) if main else ""
        return company, description
    except Exception:
        logger.exception("Failed to fetch job detail page %s", url)
        return None, ""


def fetch_raw(pages: int = PAGES) -> list[dict]:
    """Fetch raw job postings from aijobs.net's paginated listing.

    Returns a list of dicts with keys: title, company, url, location,
    salary, tags, seniority, job_type, remote, posted_ago, description,
    source. Returns whatever succeeded if some pages/detail fetches fail --
    logs a warning rather than aborting the whole run.
    """
    items: list[dict] = []
    for page in range(1, pages + 1):
        url = LIST_URL.format(page=page)
        logger.info("Fetching aijobs.net listing page %d", page)
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            job_list = soup.find("ul", id="job_list")
            cards = job_list.find_all("li", recursive=False) if job_list else []
            if not cards:
                logger.warning("aijobs.net page %d returned 0 job cards, stopping early", page)
                break
            parsed_cards = []
            for li in cards:
                try:
                    parsed_cards.append(_parse_card(li))
                except Exception:
                    logger.exception("Failed to parse aijobs.net card on page %d", page)
            with ThreadPoolExecutor(max_workers=DETAIL_FETCH_WORKERS) as pool:
                details = pool.map(lambda c: _fetch_company_and_description(c["url"]), parsed_cards)
                for card, (company, description) in zip(parsed_cards, details):
                    card["company"] = company
                    card["description"] = description
                    card["source"] = "aijobs_net"
                    items.append(card)
        except Exception:
            logger.exception("Failed to fetch aijobs.net page %d", page)
        time.sleep(REQUEST_DELAY_SECONDS)

    logger.info("Fetched %d raw items from aijobs.net (%d pages)", len(items), pages)
    return items


PROJECT_ROOT = Path(__file__).resolve().parents[3]
RAW_OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "aijobs_net.json"


def main() -> None:
    items = fetch_raw()
    history_path = write_raw_output("aijobs_net", items)
    print(f"Fetched {len(items)} raw entries -> {history_path}")


if __name__ == "__main__":
    main()
