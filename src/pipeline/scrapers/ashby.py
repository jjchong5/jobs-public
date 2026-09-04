# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: Claude Code
# Prompt: built during the 2026-07-02 overnight source-connection pass, one
#   follow-up session whose prompt automated reconstruction couldn't isolate
#   (full transcript in docs/ai_usage/transcripts/), and a 2026-07-05 bugfix +
#   company-list addition -- see docs/ai_usage/prompt_log.md#src-pipeline-scrapers-ashbypy
# Usage: Ashby ATS board scraper; later sessions fixed a bug and expanded
#   the tracked company list.
# -------------------------------------------------------------------------

"""Ashby job board scraper (public per-company JSON API).

Ashby exposes a public, unauthenticated JSON API per company at
`https://api.ashbyhq.com/posting-api/job-board/<board_name>?includeCompensation=true`
-- no auth, no anti-bot, one HTTP GET per company. Same shape/tradeoff as
greenhouse.py and lever.py: no cross-company search, so this needs a target
company list.

`BOARD_NAMES` is a placeholder list of SF AI-native companies confirmed live
against the real API (2026-07-02) -- same spirit as the Greenhouse/Lever
lists and the seeded default preference profile: a reasonable starting set,
not an exhaustively curated "right" list. Don't block on expanding it.

Standalone run:
    python -m pipeline.scrapers.ashby
writes raw entries to data/raw/ashby.json and prints the count fetched.
"""

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests


from pipeline.scrapers.raw_writer import write_raw_output
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BOARD_API_URL = "https://api.ashbyhq.com/posting-api/job-board/{board_name}?includeCompensation=true"

# Confirmed live (2026-07-02) -- each of these board names returned >0 real
# jobs from the public API. Placeholder list, refine later. Several
# candidates tried (perplexity-ai, huggingface, sourcegraph, mistral,
# anthropic, scale-ai, etc.) 404'd -- either they don't use Ashby or use a
# different board-name slug than the obvious guess; not chased further,
# same "don't block on curating the right list" stance as Greenhouse/Lever.
BOARD_NAMES = [
    "openai",
    "notion",
    "harvey",
    "elevenlabs",
    "cohere",
    "langchain",
    "linear",
    "baseten",
    "modal",
    "ashby",
    "anyscale",
    "airbyte",
    "pinecone",
    "weaviate",
    # Added 2026-07-03: AI/ML/DS-native companies, probed live against ~90
    # candidate slugs (job counts confirmed >0 at probe time). Same "no
    # cross-company search on this platform" situation as Greenhouse/Lever --
    # a fuller fetch means a longer company list, not more results per call.
    "abridge",     # 54 jobs  -- Abridge, clinical documentation AI
    "cerebras",    # 96 jobs  -- Cerebras, AI chips
    "cursor",      # 112 jobs -- Cursor (Anysphere), AI coding assistant
    "deepgram",    # 58 jobs  -- Deepgram, speech AI
    "fiddler-ai",  # 10 jobs  -- Fiddler AI, ML observability/monitoring
    "llamaindex",  # 10 jobs  -- LlamaIndex, RAG/data framework
    "poolside",    # 14 jobs  -- Poolside, foundation models for code
    "replit",      # 98 jobs  -- Replit, AI-assisted coding platform
    "roboflow",    # 27 jobs  -- Roboflow, computer vision tooling
    "runway",      # 4 jobs   -- Runway, generative video AI
    "sierra",      # 145 jobs -- Sierra, AI customer-service agents
    "snowflake",   # 420 jobs -- Snowflake, data cloud platform
    "suno",        # 59 jobs  -- Suno, AI music generation
    "synthesia",   # 73 jobs  -- Synthesia, AI video generation
    "viggle",      # 6 jobs   -- Viggle, AI video/motion generation
    "writer",      # 49 jobs  -- Writer, enterprise generative AI
    # Added 2026-07-05 (coverage-gap sizing pass, docs/reports/coverage_gap_estimate_2026-07-04.md):
    "decagon",     # 114 jobs -- Decagon, AI customer support agents
    "vanta",       # 107 jobs -- Vanta, security/compliance automation
    "crusoe",      # 354 jobs -- Crusoe Energy, clean compute infrastructure
]


BOARD_FETCH_WORKERS = 20  # bounded pool -- each board is one independent GET,
                          # but firing all boards at once regardless of list
                          # size would be inconsiderate to Ashby's shared API


def _fetch_board(board_name: str) -> list[dict]:
    url = BOARD_API_URL.format(board_name=board_name)
    logger.info("Fetching Ashby board: %s", board_name)
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    jobs = data.get("jobs", [])
    if not jobs:
        logger.warning("Ashby board %s returned 0 jobs", board_name)
    return [
        {
            "title": job.get("title", ""),
            "company": board_name,
            "url": job.get("jobUrl", ""),
            "location": job.get("location"),
            "department": job.get("department"),
            "employment_type": job.get("employmentType"),
            "updated_at": job.get("publishedAt"),
            "content": job.get("descriptionHtml", ""),
            "source": "ashby",
        }
        for job in jobs
    ]


def fetch_raw(board_names: list[str] = BOARD_NAMES) -> list[dict]:
    """Fetch raw job postings from each Ashby board name.

    Returns a list of dicts with keys: title, company, url, location,
    department, employment_type, updated_at, content, source. Returns
    whatever succeeded if some boards fail -- logs a warning per failed
    board rather than aborting the whole run.

    Boards are fetched concurrently (bounded pool, see BOARD_FETCH_WORKERS)
    -- each is an independent HTTP GET with no shared state, so running them
    one at a time was pure serialized latency for no benefit.
    """
    items: list[dict] = []
    with ThreadPoolExecutor(max_workers=BOARD_FETCH_WORKERS) as executor:
        future_to_board = {executor.submit(_fetch_board, b): b for b in board_names}
        for future in as_completed(future_to_board):
            board_name = future_to_board[future]
            try:
                items.extend(future.result())
            except Exception:
                logger.exception("Failed to fetch/parse Ashby board %s", board_name)

    logger.info("Fetched %d raw items from Ashby (%d boards)", len(items), len(board_names))
    return items


PROJECT_ROOT = Path(__file__).resolve().parents[3]
RAW_OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "ashby.json"


def main() -> None:
    items = fetch_raw()
    history_path = write_raw_output("ashby", items)
    print(f"Fetched {len(items)} raw entries -> {history_path}")


if __name__ == "__main__":
    main()
