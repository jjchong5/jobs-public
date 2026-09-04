# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: Claude Code
# Prompt: AI-assisted; automated transcript reconstruction couldn't isolate a triggering message for this file's 3 sessions -- the real prompts exist verbatim in the raw session transcripts at docs/ai_usage/transcripts/, see docs/ai_usage/prompt_log.md#src-pipeline-scrapers-handshake_emailpy
# Usage: Handshake email parser (Gmail API-based) built/edited across 3 sessions (2026-06-24, 2026-07-02, 2026-07-03).
# -------------------------------------------------------------------------

"""Handshake job-alert email parser.

Handshake bans third-party scraping of its site (CLAUDE.md), but parsing the
job-alert emails the student already receives is fair game. `fetch_raw()`
now pulls live via the pipeline's own Gmail API access (`gmail_auth.py`,
scope `gmail.readonly`, credentials/token confirmed working unattended as of
2026-07-02) -- it searches the connected university email account for real messages
from `handshake@g.joinhandshake.com` and parses their HTML bodies directly.
Confirmed live: alerts are still landing at this address (most recent found:
2026-06-29), resolving the earlier documented concern that they might have
moved to a different inbox this session can't read. Falls back to the
`data/samples/handshake/` fixture files (the original scaffold path) if the
Gmail API call fails or returns nothing, so this stays runnable offline/in
tests without real API access.

Card structure (verified against 2 saved fixture emails AND a live-fetched
real email, 2026-07-02 -- unchanged):
    <a class="job-list-content-link" href="...tracking redirect...">
      <span class="job-list-employer">Company Name</span>
      <span class="job-list-title">Job Title</span>
      <span class="job-list-meta">$20/hr • Internship • Remote</span>
    </a>

The href is a one-time Handshake email-tracking redirect link, not a stable
per-job URL -- it is NOT safe to dedup on directly (the same job re-sent in a
later email gets a different encoded link). `fetch_raw()` returns the raw
redirect URL as `tracking_url`; the caller is responsible for resolving it to
a stable URL (e.g. via a HEAD request following redirects) before using it as
a dedup key. `ingest.py`'s `normalize_handshake()` instead dedups on a content
hash of company+title+work_type, which also has the useful side effect of
correctly deduping the same job across separate weekly emails.

Standalone run:
    python -m pipeline.scrapers.handshake_email
writes raw entries to data/raw/handshake_email.json and prints the count fetched.
"""

import base64
import json
import logging
import re
from pathlib import Path

from bs4 import BeautifulSoup


from pipeline.scrapers.raw_writer import write_raw_output
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SAMPLES_DIR = PROJECT_ROOT / "data" / "samples" / "handshake"
RAW_OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "handshake_email.json"

GMAIL_SEARCH_QUERY = "from:handshake@g.joinhandshake.com"
GMAIL_MAX_RESULTS = 10

META_PATTERN = re.compile(r"\s*•\s*")  # bullet "•" separates pay / type / location


def parse_email_html(html: str, email_sent_at: str | None = None) -> list[dict]:
    """Parse one Handshake alert email's HTML into a list of raw job dicts.

    Job cards themselves carry no per-job date -- `email_sent_at` (the
    containing email's send time, ISO 8601) is used as a `posted_at` proxy
    when supplied. It means "alert sent," not "job posted," but is strictly
    more useful than the None this previously left every Handshake item with.
    """
    soup = BeautifulSoup(html, "html.parser")
    jobs = []
    for card in soup.find_all("a", class_="job-list-content-link"):
        employer = card.find("span", class_="job-list-employer")
        title = card.find("span", class_="job-list-title")
        meta = card.find("span", class_="job-list-meta")
        meta_parts = META_PATTERN.split(meta.get_text(strip=True)) if meta else []
        # meta is "pay • type • location", but pay is sometimes omitted
        pay = meta_parts[0] if len(meta_parts) == 3 else None
        work_type = meta_parts[-2] if len(meta_parts) >= 2 else None
        location = meta_parts[-1] if meta_parts else None
        jobs.append(
            {
                "title": title.get_text(strip=True) if title else "",
                "company": employer.get_text(strip=True) if employer else None,
                "pay": pay,
                "work_type": work_type,
                "location": location,
                "tracking_url": card.get("href", ""),
                "email_sent_at": email_sent_at,
                "source": "handshake_email",
            }
        )
    return jobs


def _find_html_part(payload: dict) -> str | None:
    """Recursively search a Gmail message payload for the text/html body part."""
    if payload.get("mimeType") == "text/html" and payload.get("body", {}).get("data"):
        return payload["body"]["data"]
    for part in payload.get("parts") or []:
        found = _find_html_part(part)
        if found:
            return found
    return None


def fetch_emails_from_gmail(max_results: int = GMAIL_MAX_RESULTS) -> list[tuple[str, str | None]]:
    """Fetch recent Handshake alert email HTML bodies via the pipeline's own
    Gmail API access (gmail_auth.get_gmail_service(), scope gmail.readonly).

    Returns a list of (html, sent_at_iso) tuples, most recent first. sent_at_iso
    is derived from Gmail's internalDate (server receipt time, ms since epoch) --
    used downstream as a posted_at proxy. Returns an empty list (and lets the
    caller decide whether to fall back) if the API call fails for any reason --
    e.g. missing credentials.json/token.json, no matching messages.
    """
    from datetime import datetime, timezone

    from pipeline.gmail_auth import get_gmail_service

    service = get_gmail_service()
    results = (
        service.users()
        .messages()
        .list(userId="me", q=GMAIL_SEARCH_QUERY, maxResults=max_results)
        .execute()
    )
    message_refs = results.get("messages", [])
    if not message_refs:
        logger.warning("Gmail search for %r returned 0 messages", GMAIL_SEARCH_QUERY)
        return []

    htmls: list[tuple[str, str | None]] = []
    for ref in message_refs:
        msg = service.users().messages().get(userId="me", id=ref["id"], format="full").execute()
        html_data = _find_html_part(msg["payload"])
        if not html_data:
            logger.warning("Handshake email %s has no text/html part; skipping", ref["id"])
            continue
        sent_at = None
        internal_date = msg.get("internalDate")
        if internal_date:
            sent_at = datetime.fromtimestamp(int(internal_date) / 1000, tz=timezone.utc).isoformat()
        html = base64.urlsafe_b64decode(html_data).decode("utf-8", errors="replace")
        htmls.append((html, sent_at))

    logger.info("Fetched %d Handshake alert email bodies from Gmail", len(htmls))
    return htmls


def fetch_raw(samples_dir: Path = SAMPLES_DIR) -> list[dict]:
    """Fetch Handshake job-alert emails and parse all job cards.

    Tries the live Gmail API first (searches the pipeline's connected
    account for real Handshake alert emails). Falls back to reading saved
    .html fixtures from `samples_dir` if the Gmail call fails or returns
    nothing -- keeps this runnable offline/in tests without real API access.
    """
    jobs: list[dict] = []

    try:
        htmls = fetch_emails_from_gmail()
    except Exception:
        logger.exception("Gmail live-fetch failed; falling back to fixture files")
        htmls = []

    if htmls:
        for html, sent_at in htmls:
            try:
                parsed = parse_email_html(html, email_sent_at=sent_at)
                jobs.extend(parsed)
            except Exception:
                logger.exception("Failed to parse a live-fetched Handshake email; skipping it")
        logger.info("Fetched %d total entries from live Handshake Gmail fetch", len(jobs))
        return jobs

    logger.warning("No live Handshake emails fetched from Gmail; falling back to fixtures")
    if not samples_dir.exists():
        logger.warning("Handshake samples directory not found: %s", samples_dir)
        return jobs

    html_files = sorted(samples_dir.glob("*.html"))
    if not html_files:
        logger.warning("No Handshake .html fixtures found in %s", samples_dir)
        return jobs

    for html_file in html_files:
        try:
            html = html_file.read_text(encoding="utf-8")
            parsed = parse_email_html(html)
            logger.info("Parsed %d job cards from %s", len(parsed), html_file.name)
            jobs.extend(parsed)
        except Exception:
            logger.exception("Failed to parse Handshake fixture %s", html_file)

    logger.info("Fetched %d total entries from Handshake email fixtures", len(jobs))
    return jobs


def main() -> None:
    entries = fetch_raw()
    history_path = write_raw_output("handshake_email", entries)
    print(f"Fetched {len(entries)} raw entries -> {history_path}")


if __name__ == "__main__":
    main()
