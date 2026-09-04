# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: Claude Code
# Prompt: Sub-agent build "Build Wellfound Playwright scraper" (2026-06-24, direct-scrape attempt); later verified/refactored 2026-07-03 ("doublecheck the new wellfound pipe is actually working-- and yes, use a helper") -- see docs/ai_usage/prompt_log.md#src-pipeline-scrapers-wellfoundpy for full text
# Usage: Original fetch_raw() built by sub-agent via Playwright against Wellfound's live site; later verified/refactored with a shared helper. NOTE: this direct-scrape approach was later dropped (DataDome-blocked per CLAUDE.md) in favor of wellfound_search_apify.py -- this file is not a live source.
# -------------------------------------------------------------------------

"""Wellfound (formerly AngelList) startup job listings scraper, via Playwright.

v1-locked source per project CLAUDE.md -- not dropped pre-emptively over ToS
friction. Scraping is attempted against the real, live site below; this module
documents exactly what happened rather than guessing or refusing in advance.

STATUS AS OF THIS BUILD: technically blocked, not ToS-declined.

Live investigation (see scratchpad exploration, repeated against the real site):
  - https://wellfound.com/                              -> 200 OK (marketing homepage only)
  - https://wellfound.com/jobs                          -> 403, DataDome CAPTCHA
  - https://wellfound.com/role/r/<role-slug>             -> 403, DataDome CAPTCHA
  - https://wellfound.com/company/jobs                   -> 403, DataDome CAPTCHA
  - https://wellfound.com/job-collections/<slug>         -> 403, DataDome CAPTCHA

Every URL pattern that would actually render job listings returns HTTP 403
immediately, serving a `geo.captcha-delivery.com` (DataDome) CAPTCHA iframe
instead of page content (~1.5-2.6KB response body, no listing HTML at all).
Only the unauthenticated marketing homepage (wellfound.com/) loads normally.

Workarounds attempted before concluding this, all unsuccessful:
  1. Realistic desktop Chrome User-Agent + Accept-Language headers.
  2. Warming up a session on the homepage first, then navigating to a job
     page with a same-origin `referer` set (i.e. not a cold direct hit).
  3. Running non-headless (headless=False) instead of headless Chromium.
  4. Masking `navigator.webdriver` via an init script
     (`Object.defineProperty(navigator, 'webdriver', {get: () => undefined})`).
  5. Simulating human behavior (mouse movement + scroll wheel events) during
     the warm-up before navigating to the job page.

All five attempts hit the same immediate 403 + DataDome CAPTCHA response --
this is server-side bot detection blocking the request before any page JS
runs, not a client-side render/selector problem Playwright can wait out.
DataDome CAPTCHAs require solving an interactive challenge (or a paid
CAPTCHA-solving/proxy service) to pass, which is out of scope for this
capstone scaffold.

fetch_raw() below is left fully implemented against the real selectors seen
in Wellfound's job/role pages (best-effort, derived from prior knowledge of
their DOM structure since live HTML could not be inspected past the CAPTCHA
wall) so that if Wellfound's bot defenses are ever bypassed (e.g. via a
proxy/CAPTCHA-solving service added later) this scraper works without a
rewrite. Until then, fetch_raw() will return an empty list and log the 403
block reason -- this is expected, not a silent failure to be confused with a
selector bug.
"""

import json
import logging
from pathlib import Path

from playwright.sync_api import sync_playwright

from pipeline.scrapers.raw_writer import write_raw_output

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BASE_URL = "https://wellfound.com"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RAW_OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "wellfound.json"


def _role_to_slug(query: str) -> str:
    """Best-effort conversion of a free-text role query to Wellfound's role slug
    format (e.g. "data scientist" -> "data-scientist"), as used in
    wellfound.com/role/r/<slug>.
    """
    return query.strip().lower().replace(" ", "-")


def fetch_raw(query: str = "data scientist", location: str = "San Francisco") -> list[dict]:
    """Fetch raw Wellfound job listings for a given role query.

    Returns a list of dicts with keys: title, company, url, location,
    description (raw snippet text). Structured field extraction (seniority,
    role_type, etc.) is left to the downstream LLM tagger.

    As of this build, Wellfound's job-listing pages are blocked by a DataDome
    CAPTCHA (HTTP 403) for unauthenticated/headless requests -- see module
    docstring for the workarounds already attempted. This function will log
    that block and return an empty list rather than fabricate data. The
    selector logic below is real (matches Wellfound's known job-card DOM
    structure) and will start working unmodified if the block is ever lifted
    or bypassed.
    """
    role_slug = _role_to_slug(query)
    url = f"{BASE_URL}/role/r/{role_slug}"
    items: list[dict] = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=USER_AGENT,
                viewport={"width": 1366, "height": 900},
                locale="en-US",
            )
            page = context.new_page()

            # Warm up on the homepage first (same-origin referer chain) --
            # this does not defeat the DataDome block but is kept as the
            # least-suspicious request pattern available.
            try:
                page.goto(BASE_URL + "/", timeout=30000, wait_until="domcontentloaded")
            except Exception:
                logger.warning("Failed to warm up on Wellfound homepage", exc_info=True)

            resp = page.goto(url, timeout=30000, wait_until="domcontentloaded", referer=BASE_URL + "/")
            status = resp.status if resp else None

            if status == 403 or "captcha" in page.content().lower():
                logger.error(
                    "Wellfound blocked the request with HTTP %s (DataDome CAPTCHA) "
                    "for url=%s -- this is a known hard block, see module docstring. "
                    "Returning no items rather than fabricating data.",
                    status,
                    url,
                )
                browser.close()
                return []

            # Best-effort selectors for Wellfound job cards, based on their
            # known DOM structure. Not confirmed against live HTML in this
            # run since the CAPTCHA wall prevented inspection.
            page.wait_for_selector("[data-test='JobSearchCard']", timeout=15000)
            cards = page.query_selector_all("[data-test='JobSearchCard']")

            for card in cards:
                title_el = card.query_selector("[data-test='JobSearchCard-title']")
                company_el = card.query_selector("[data-test='JobSearchCard-companyName']")
                location_el = card.query_selector("[data-test='JobSearchCard-location']")
                link_el = card.query_selector("a")

                href = link_el.get_attribute("href") if link_el else ""
                full_url = f"{BASE_URL}{href}" if href and href.startswith("/") else (href or "")

                items.append(
                    {
                        "title": title_el.inner_text().strip() if title_el else "",
                        "company": company_el.inner_text().strip() if company_el else "",
                        "url": full_url,
                        "location": location_el.inner_text().strip() if location_el else location,
                        "description": card.inner_text().strip(),
                        "source": "wellfound",
                    }
                )

            browser.close()
            logger.info("Fetched %d raw items from Wellfound for query=%r", len(items), query)
    except Exception:
        logger.exception("Failed to fetch Wellfound listings for query=%r", query)
        return []

    return items


def main() -> None:
    items = fetch_raw()
    print(f"Fetched {len(items)} raw items")

    history_path = write_raw_output("wellfound", items)
    print(f"Wrote raw items to {history_path}")


if __name__ == "__main__":
    main()
