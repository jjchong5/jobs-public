# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: Claude Code
# Prompt: AI-assisted (2026-07-02 multi-scraper session), no clean prompt
#   attribution reconstructed -- see docs/ai_usage/prompt_log.md#src-pipeline-scrapers-dicepy
# Usage: Dice job-board scraper.
# -------------------------------------------------------------------------

"""Dice job search scraper (dice.com).

Dice's job search results are loaded client-side (React/Next.js) after the
initial page load -- unlike Built In SF, a plain `requests` GET returns 200
but the job cards aren't present in the raw HTML (confirmed 2026-07-02: no
`__NEXT_DATA__` or other embedded JSON payload in the initial response).
Uses Playwright to render the page and read the job cards out of the DOM
after JS runs, same general technique as wellfound.py -- but unlike
Wellfound, Dice returned a normal 200 with real content on the very first
request, no anti-bot wall encountered (no CAPTCHA, no 403s), so a single
render-and-read pass is all this needs.

Card structure (verified against real rendered DOM, 2026-07-02):
    div[data-testid="job-card"]
      a[data-testid="job-search-job-detail-link"]  -- title text + href (/job-detail/<guid>)
      a[href*="/company-profile/"]                  -- company name
      p.text-sm.font-normal.text-zinc-600 (x2)       -- location, then posted-date ("Xd ago"/"Today")

Standalone run:
    python -m pipeline.scrapers.dice
writes raw entries to data/raw/dice.json and prints the count fetched.
"""

import json
import logging
from pathlib import Path

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


from pipeline.scrapers.raw_writer import write_raw_output
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BASE_URL = "https://www.dice.com"
SEARCH_URL = "https://www.dice.com/jobs?q={query}&location={location}"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RAW_OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "dice.json"


def _extract_card(card) -> dict | None:
    title_a = card.find(attrs={"data-testid": "job-search-job-detail-link"})
    if not title_a:
        return None

    company = None
    for a in card.find_all("a", href=True):
        if "/company-profile/" in a["href"]:
            text = a.get_text(strip=True)
            if text:
                company = text
                break

    location_ps = card.find_all("p", class_="text-sm font-normal text-zinc-600")
    location = location_ps[0].get_text(strip=True) if location_ps else None
    posted = location_ps[2].get_text(strip=True) if len(location_ps) > 2 else None

    href = title_a.get("href", "")
    url = f"{BASE_URL}{href}" if href.startswith("/") else href

    return {
        "title": title_a.get_text(strip=True),
        "company": company,
        "url": url,
        "location": location,
        "posted": posted,
        "source": "dice",
    }


def fetch_raw(query: str = "data scientist", location: str = "San Francisco, CA") -> list[dict]:
    """Render a Dice job search results page with Playwright and extract raw
    job cards. Returns an empty list (and logs why) on any failure -- this is
    a scaffold, callers should handle empty results gracefully."""
    url = SEARCH_URL.format(query=query.replace(" ", "%20"), location=location.replace(" ", "%20").replace(",", "%2C"))
    logger.info("Rendering Dice job search: %s", url)

    items: list[dict] = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent=USER_AGENT)
            page.goto(url, timeout=30000)
            page.wait_for_selector('[data-testid="job-card"]', timeout=15000)
            html = page.content()
            browser.close()

        soup = BeautifulSoup(html, "html.parser")
        cards = soup.find_all(attrs={"data-testid": "job-card"})
        if not cards:
            logger.warning("Dice returned 0 job cards for query=%r (page may have changed)", query)

        for card in cards:
            try:
                item = _extract_card(card)
                if item:
                    items.append(item)
            except Exception:
                logger.exception("Failed to parse a Dice job card; skipping it")

        logger.info("Fetched %d raw items from Dice", len(items))
    except Exception:
        logger.exception("Failed to fetch/render Dice job search page")

    return items


def main() -> None:
    items = fetch_raw()
    history_path = write_raw_output("dice", items)
    print(f"Fetched {len(items)} raw entries -> {history_path}")


if __name__ == "__main__":
    main()
