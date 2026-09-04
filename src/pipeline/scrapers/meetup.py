# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: Claude Code
# Prompt: AI-assisted (2026-07-02 multi-scraper session), no clean prompt
#   attribution reconstructed -- see docs/ai_usage/prompt_log.md#src-pipeline-scrapers-meetuppy
# Usage: Meetup API event scraper. Now frozen/mothballed (event tracking
#   de-prioritized 2026-07-02 per CLAUDE.md).
# -------------------------------------------------------------------------

"""Meetup event scraper via the public `gql-ext` GraphQL endpoint (api.meetup.com/gql-ext).

Meetup deprecated its old open REST v3 API (confirmed 2026-07-02: the
legacy `/find/upcoming_events` endpoint now 404s). Meetup's own website
frontend queries a GraphQL endpoint at `api.meetup.com/gql-ext` anonymously
(no API key/OAuth token in the request) to power its own public search UI --
confirmed live by introspecting the schema and running a real `eventSearch`
query with no auth headers at all. This is the same "use what the site's own
frontend already calls publicly" precedent as Luma's unofficial discover API
elsewhere in this project, not a private/internal API requiring credentials
(no key was found, guessed, or needed).

Standalone run:
    python -m pipeline.scrapers.meetup
writes raw entries to data/raw/meetup.json and prints the count fetched.
"""

import json
import logging
from pathlib import Path

import requests


from pipeline.scrapers.raw_writer import write_raw_output
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

GRAPHQL_URL = "https://api.meetup.com/gql-ext"

# San Francisco coordinates -- matches the seeded SF-focused default
# preference profile used elsewhere in this pipeline.
SF_LAT = 37.7749
SF_LON = -122.4194
SEARCH_RADIUS_MILES = 25

# Keyword searches relevant to the seeded SF DS/ML/AI preference profile.
QUERIES = ["data science", "machine learning", "artificial intelligence"]

EVENT_SEARCH_QUERY = """
query($filter: EventSearchFilter!, $first: Int) {
  eventSearch(filter: $filter, first: $first) {
    edges {
      node {
        id
        title
        description
        dateTime
        endTime
        eventUrl
        venue { name city state }
        group { name urlname }
      }
    }
  }
}
"""


def fetch_raw(queries: list[str] = QUERIES, results_per_query: int = 20) -> list[dict]:
    """Fetch raw SF-area events from Meetup's public GraphQL search for each
    query in `queries`. Dedups across queries by event id. Returns whatever
    succeeded if a query fails -- logs a warning rather than aborting the
    whole run."""
    seen_ids: set[str] = set()
    items: list[dict] = []
    for query in queries:
        logger.info("Searching Meetup events: query=%r", query)
        try:
            resp = requests.post(
                GRAPHQL_URL,
                json={
                    "query": EVENT_SEARCH_QUERY,
                    "variables": {
                        "filter": {
                            "query": query,
                            "lat": SF_LAT,
                            "lon": SF_LON,
                            "radius": SEARCH_RADIUS_MILES,
                        },
                        "first": results_per_query,
                    },
                },
                headers={"Content-Type": "application/json"},
                timeout=20,
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("errors"):
                logger.warning("Meetup GraphQL returned errors for query=%r: %s", query, data["errors"])
            edges = (data.get("data") or {}).get("eventSearch", {}).get("edges", [])
            if not edges:
                logger.warning("Meetup query=%r returned 0 events", query)
            for edge in edges:
                node = edge.get("node") or {}
                event_id = node.get("id")
                if not event_id or event_id in seen_ids:
                    continue
                seen_ids.add(event_id)
                node = dict(node)
                node["matched_query"] = query
                node["source"] = "meetup"
                items.append(node)
        except Exception:
            logger.exception("Failed to fetch/parse Meetup events for query=%r", query)

    logger.info("Fetched %d raw items from Meetup", len(items))
    return items


PROJECT_ROOT = Path(__file__).resolve().parents[3]
RAW_OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "meetup.json"


def main() -> None:
    items = fetch_raw()
    history_path = write_raw_output("meetup", items)
    print(f"Fetched {len(items)} raw entries -> {history_path}")


if __name__ == "__main__":
    main()
