# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: Claude Code
# Prompt: Sub-agent build "Build Luma events API scraper" (2026-06-24, no-auth public endpoint research); later touched in a 2026-07-03 multi-file scraper touch-up session (shared-helper refactor) -- see docs/ai_usage/prompt_log.md#src-pipeline-scrapers-luma_eventspy for full text
# Usage: Original fetch_raw() built by sub-agent against a researched no-auth Luma endpoint; later lightly edited alongside hn_whoshiring.py/wellfound.py, likely a shared-helper extraction. Source is frozen per CLAUDE.md's Current State (event sources frozen 2026-07-02).
# -------------------------------------------------------------------------

"""Luma (lu.ma) events scraper.

Fetches raw event listings from Luma's public, no-auth "discover" API, which
backs the city/category browse pages on lu.ma (e.g. https://lu.ma/sf). This
endpoint is unofficial/undocumented -- it is simply the JSON API the lu.ma
website itself calls client-side -- so it could change or be rate-limited
without notice. It does NOT require an API key.

Endpoint used: https://api.lu.ma/discover/get-paginated-events
  ?discover_place_api_id=<place id>&pagination_limit=<n>
The place id for San Francisco (discplace-BDj7GNbGlsF7Cka) was found by
fetching https://lu.ma/sf and reading the embedded __NEXT_DATA__ JSON, which
contains place.api_id under pageProps.initialData.data.place.api_id. Other
cities/categories would need their own place id discovered the same way.

This module only parses the raw listing into a list of dicts -- structured
field extraction (role_type, deadline, etc.) is handled downstream by the LLM
tagger.

NOTE on event descriptions: the discover/listing endpoint above does not
include event descriptions. Full descriptions are only available via a
second per-event call (https://api.lu.ma/event/get?event_api_id=...,
description_mirror field, in ProseMirror doc JSON format). To avoid hammering
the no-auth endpoint with one request per event, fetch_raw() only fetches
descriptions for a small capped number of events (DESCRIPTION_FETCH_LIMIT).
For full-scale, reliable, ToS-sanctioned access (more events, no place-id
reverse engineering, official descriptions/guest data), Luma's official
partner API at https://api.lu.ma/public/v1 requires LUMA_API_KEY (see
.env.example) -- not available in this environment, so this scraper is
built against the no-auth discovery endpoint only.

Standalone run:
    python -m pipeline.scrapers.luma_events
writes raw entries to data/raw/luma_events.json and prints the count fetched.
"""

import json
import logging
from pathlib import Path

import requests

from pipeline.scrapers.raw_writer import write_raw_output

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DISCOVER_URL = "https://api.lu.ma/discover/get-paginated-events"
EVENT_GET_URL = "https://api.lu.ma/event/get"
EVENT_URL_BASE = "https://lu.ma"

# Known discover-place api_ids, found by fetching the corresponding lu.ma
# city/category page and reading place.api_id out of the embedded
# __NEXT_DATA__ JSON. "sf-tech" is the default for this project (SF tech
# events); add more here if other calendars/cities are needed later.
PLACE_IDS = {
    "sf-tech": "discplace-BDj7GNbGlsF7Cka",  # lu.ma/sf
}

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# Cap how many events we fetch full descriptions for, to avoid hammering the
# unofficial endpoint with one request per event in a single run.
DESCRIPTION_FETCH_LIMIT = 15

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RAW_OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "luma_events.json"


def _extract_description_text(description_mirror: dict | None) -> str:
    """Flatten Luma's ProseMirror description doc into plain text."""
    if not description_mirror:
        return ""
    parts: list[str] = []

    def _walk(node: dict) -> None:
        if node.get("type") == "text" and node.get("text"):
            parts.append(node["text"])
        for child in node.get("content") or []:
            _walk(child)

    try:
        _walk(description_mirror)
    except Exception:
        logger.exception("Failed to flatten description_mirror")
    return "\n".join(parts)


def _fetch_description(event_api_id: str) -> str:
    """Best-effort fetch of an event's full description via event/get."""
    try:
        resp = requests.get(
            EVENT_GET_URL,
            params={"event_api_id": event_api_id},
            headers=HEADERS,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return _extract_description_text(data.get("description_mirror"))
    except Exception:
        logger.warning("Failed to fetch description for event %s", event_api_id, exc_info=True)
        return ""


def fetch_raw(calendar_slug_or_query: str = "sf-tech") -> list[dict]:
    """Fetch raw event entries from Luma's public discover API.

    `calendar_slug_or_query` is looked up in PLACE_IDS to get the underlying
    discover_place_api_id. Returns a list of dicts with keys: title, url,
    start_at, location, description, source. Returns an empty list (and logs
    a warning/error) on failure -- this is a scaffold, callers should handle
    empty results gracefully.
    """
    place_id = PLACE_IDS.get(calendar_slug_or_query)
    if place_id is None:
        logger.error(
            "Unknown calendar_slug_or_query=%r -- no known discover_place_api_id. "
            "Known slugs: %s",
            calendar_slug_or_query,
            list(PLACE_IDS),
        )
        return []

    entries: list[dict] = []
    try:
        resp = requests.get(
            DISCOVER_URL,
            params={"discover_place_api_id": place_id, "pagination_limit": 50},
            headers=HEADERS,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        raw_entries = data.get("entries", [])

        if not raw_entries:
            logger.warning("Luma discover API returned 0 entries for %r", calendar_slug_or_query)

        for i, item in enumerate(raw_entries):
            event = item.get("event", {})
            geo = event.get("geo_address_info") or {}
            event_api_id = event.get("api_id", "")
            url_slug = event.get("url", "")

            description = ""
            if event_api_id and i < DESCRIPTION_FETCH_LIMIT:
                description = _fetch_description(event_api_id)

            entries.append(
                {
                    "title": event.get("name", ""),
                    "url": f"{EVENT_URL_BASE}/{url_slug}" if url_slug else "",
                    "start_at": event.get("start_at", ""),
                    "end_at": event.get("end_at", ""),
                    "location": geo.get("full_address") or geo.get("city_state") or "",
                    "description": description,
                    "source": "luma",
                }
            )

        logger.info("Fetched %d raw entries from Luma discover API (%s)", len(entries), calendar_slug_or_query)
    except Exception:
        logger.exception("Failed to fetch/parse Luma discover API for %r", calendar_slug_or_query)

    return entries


def main() -> None:
    entries = fetch_raw()
    history_path = write_raw_output("luma_events", entries)
    print(f"Fetched {len(entries)} raw entries -> {history_path}")


if __name__ == "__main__":
    main()
