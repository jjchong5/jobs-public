# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: Claude Code (sub-agent via Agent tool)
# Prompt: "Build Built In SF HTML scraper" sub-agent task (2026-06-24) --
#   see docs/ai_usage/prompt_log.md#src-pipeline-scrapers-builtin_sfpy
# Usage: Built In SF job-listings HTML scraper, built and live-tested
#   entirely by a spawned sub-agent; never edited again afterward.
# -------------------------------------------------------------------------

"""Built In SF job listings scraper (https://www.builtinsf.com/jobs).

Built In SF's job search page is server-rendered (job cards are present in the
initial HTML response, no JS execution required), so this uses plain
`requests` + BeautifulSoup rather than Playwright.

Locked v1 source per project docs -- scrape what we can, only drop if
technically blocked (aggressive anti-bot/login wall), not over ToS concerns.
This module only collects raw fields (title, company, url, location,
description snippet) -- structured extraction (role_type, seniority, etc.) is
handled downstream by the LLM tagger.

Standalone run:
    python -m pipeline.scrapers.builtin_sf
writes raw entries to data/raw/builtin_sf.json and prints the count fetched.
"""

import json
import logging
from pathlib import Path

import requests
from bs4 import BeautifulSoup


from pipeline.scrapers.raw_writer import write_raw_output
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BUILTIN_SF_JOBS_URL = "https://www.builtinsf.com/jobs"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

# Project root is src/pipeline/scrapers/../../.. -> C:\Users\jjcho\code\jobs
PROJECT_ROOT = Path(__file__).resolve().parents[3]
RAW_OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "builtin_sf.json"


def _extract_card(card) -> dict | None:
    """Pull raw fields out of a single job-card element."""
    title_a = card.select_one('[data-id="job-card-title"]')
    if not title_a:
        return None

    company_a = card.select_one('[data-id="company-title"]')
    href = title_a.get("href", "")
    url = f"https://www.builtinsf.com{href}" if href.startswith("/") else href

    location = None
    work_type = None
    salary = None
    seniority = None
    for row in card.select(".d-flex.align-items-start.gap-sm"):
        icon = row.select_one("i")
        span = row.select_one("span")
        if not icon or not span:
            continue
        icon_classes = icon.get("class") or []
        text = span.get_text(strip=True)
        if "fa-location-dot" in icon_classes:
            location = text
        elif "fa-house-building" in icon_classes:
            work_type = text
        elif "fa-sack-dollar" in icon_classes:
            salary = text
        elif "fa-trophy" in icon_classes:
            seniority = text

    # Description snippet lives in the collapsible "drop-data-<id>" panel,
    # which is a sibling of the card rather than nested inside it.
    snippet = None
    job_card_id = card.get("id", "")  # e.g. "job-card-8657768"
    if job_card_id:
        numeric_id = job_card_id.rsplit("-", 1)[-1]
        drop = card.find_parent().select_one(f"#drop-data-{numeric_id}") if card.find_parent() else None
        if drop:
            desc_div = drop.select_one(".fs-sm.fw-regular")
            if desc_div:
                snippet = desc_div.get_text(strip=True)

    return {
        "title": title_a.get_text(strip=True),
        "company": company_a.get_text(strip=True) if company_a else "",
        "url": url,
        "location": location,
        "work_type": work_type,
        "salary": salary,
        "seniority": seniority,
        "snippet": snippet,
        "source": "builtin_sf",
    }


def fetch_raw(query: str = "data scientist") -> list[dict]:
    """Fetch raw job listing items from Built In SF's job search for `query`.

    Returns a list of dicts with keys: title, company, url, location,
    work_type, salary, seniority, snippet, source. Returns an empty list (and
    logs a warning/error) on any failure -- this is a scaffold, callers should
    handle empty results gracefully.
    """
    params = {"search": query}
    logger.info("Fetching Built In SF jobs: %s params=%s", BUILTIN_SF_JOBS_URL, params)

    items: list[dict] = []
    try:
        resp = requests.get(
            BUILTIN_SF_JOBS_URL,
            params=params,
            headers={"User-Agent": USER_AGENT},
            timeout=30,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        cards = soup.select('[data-id="job-card"]')

        if not cards:
            logger.warning("Built In SF returned 0 job cards for query=%r (page may have changed or blocked us)", query)

        for card in cards:
            try:
                item = _extract_card(card)
                if item:
                    items.append(item)
            except Exception:
                logger.exception("Failed to parse a job card; skipping it")

        logger.info("Fetched %d raw items from Built In SF", len(items))
    except Exception:
        logger.exception("Failed to fetch/parse Built In SF jobs page")

    return items


def main() -> None:
    items = fetch_raw()
    history_path = write_raw_output("builtin_sf", items)
    print(f"Fetched {len(items)} raw entries -> {history_path}")


if __name__ == "__main__":
    main()
