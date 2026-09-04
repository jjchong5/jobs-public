# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: Claude Code
# Prompt: iterative schema/storage design across 7 sessions (2026-06-24 to
#   2026-07-04) -- see docs/ai_usage/prompt_log.md#src-pipeline-storage-dbpy
#   for full prompts
# Usage: Original schema/storage layer scaffolded 2026-06-24, then
#   iteratively revised -- adding job-type/industry/rank metric fields,
#   UPSERT and alt-listing dedup tracking, raw-scrape/description-history
#   retention, and duplicate-logging fixes. Edit history spans unrelated
#   concurrent work in other files each session; see the log for the
#   full multi-session breakdown.
# -------------------------------------------------------------------------

"""SQLite storage layer. Single-writer asyncio.Queue coroutine so parallel
async scrapers can enqueue writes without contending on the same connection.
"""
import asyncio
import json
import logging
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from pipeline.classify_location import classify_remote_type

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).resolve().parents[3] / "data" / "pipeline.db"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection()
    try:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        conn.commit()
        _migrate_engagement_type(conn)
        _migrate_tracking_fields(conn)
        _migrate_dedup_tracking(conn)
        _migrate_scoring_rework(conn)
        _migrate_saved_tracking(conn)
        _migrate_role_category_weights(conn)
        _seed_default_profile(conn)
    finally:
        conn.close()


def _migrate_engagement_type(conn: sqlite3.Connection) -> None:
    """CREATE TABLE IF NOT EXISTS is a no-op on an already-existing table, so
    columns added after the table was first created (engagement_type,
    engagement_weights) need an explicit ALTER TABLE for existing DBs."""
    items_cols = {row["name"] for row in conn.execute("PRAGMA table_info(items)")}
    if "engagement_type" not in items_cols:
        conn.execute("ALTER TABLE items ADD COLUMN engagement_type TEXT")
    profile_cols = {row["name"] for row in conn.execute("PRAGMA table_info(preference_profiles)")}
    if "engagement_weights" not in profile_cols:
        conn.execute("ALTER TABLE preference_profiles ADD COLUMN engagement_weights TEXT")
    conn.commit()


def _migrate_role_category_weights(conn: sqlite3.Connection) -> None:
    """Adds preference_profiles.role_category_weights (6th weight dimension,
    2026-07-05 -- see ranker/scores.py). Existing rows get it filled via
    COALESCE in _seed_default_profile, same pattern as the other weight
    columns above."""
    profile_cols = {row["name"] for row in conn.execute("PRAGMA table_info(preference_profiles)")}
    if "role_category_weights" not in profile_cols:
        conn.execute("ALTER TABLE preference_profiles ADD COLUMN role_category_weights TEXT")
    conn.commit()


def _migrate_tracking_fields(conn: sqlite3.Connection) -> None:
    """Adds role_category/industry (LLM-tagged, left null on existing items --
    re-tagging costs real API calls, so backfill only happens on a deliberate
    re-tag pass) and remote_type (derived from `location`, free to backfill
    immediately since it needs no API call)."""
    items_cols = {row["name"] for row in conn.execute("PRAGMA table_info(items)")}
    for col in ("role_category", "industry", "remote_type"):
        if col not in items_cols:
            conn.execute(f"ALTER TABLE items ADD COLUMN {col} TEXT")
    conn.commit()

    rows = conn.execute("SELECT id, location FROM items WHERE remote_type IS NULL").fetchall()
    for row in rows:
        conn.execute(
            "UPDATE items SET remote_type = ? WHERE id = ?",
            (classify_remote_type(row["location"]), row["id"]),
        )
    if rows:
        conn.commit()
        logger.info("Backfilled remote_type for %d existing items", len(rows))


def _migrate_scoring_rework(conn: sqlite3.Connection) -> None:
    """Adds the 2026-07-03 scoring rework columns (see relevance_ranking_rework
    memory / schema.sql comments): content_quality/spam_risk/
    role_expectation_delta/role_expectation_notes/company_stage (LLM-tagged,
    left null on existing items -- re-tagging costs real API calls, same
    precedent as role_category/industry backfill above) and
    urgency_score/preference_score/general_score/ranked_at (rank-time
    computed, left null until the next `python -m pipeline.ranker.rank` run
    -- no backfill needed since ranker/scores.py recomputes all tagged items
    each run, not just new ones).

    Old relevance_score values ARE copied forward into content_quality
    as an imperfect-but-usable starting value (low stakes now that this field
    is QA-only, not part of ranking math -- see memory). Not backfilled for
    spam_risk/role_expectation_delta/company_stage since there's no equivalent
    old data to carry forward for those.
    """
    items_cols = {row["name"] for row in conn.execute("PRAGMA table_info(items)")}
    # content_quality_score was the field's name for one day (2026-07-03)
    # before being renamed to content_quality -- rename in place on any DB
    # that already has the old column, rather than adding a fresh (empty)
    # content_quality column and losing that day's backfilled/tagged data.
    if "content_quality_score" in items_cols and "content_quality" not in items_cols:
        conn.execute("ALTER TABLE items RENAME COLUMN content_quality_score TO content_quality")
        conn.commit()
        items_cols = {row["name"] for row in conn.execute("PRAGMA table_info(items)")}

    for col in ("content_quality", "role_expectation_delta",
                "urgency_score", "preference_score", "general_score"):
        if col not in items_cols:
            conn.execute(f"ALTER TABLE items ADD COLUMN {col} REAL")
    for col in ("company_stage", "spam_risk", "role_expectation_notes", "ranked_at"):
        if col not in items_cols:
            conn.execute(f"ALTER TABLE items ADD COLUMN {col} TEXT")
    conn.commit()

    conn.execute(
        "UPDATE items SET content_quality = relevance_score "
        "WHERE content_quality IS NULL AND relevance_score IS NOT NULL"
    )
    conn.commit()

    profile_cols = {row["name"] for row in conn.execute("PRAGMA table_info(preference_profiles)")}
    for col in ("seniority_weights", "location_weights", "sector_weights", "stage_weights"):
        if col not in profile_cols:
            conn.execute(f"ALTER TABLE preference_profiles ADD COLUMN {col} TEXT")
    conn.commit()


def _migrate_saved_tracking(conn: sqlite3.Connection) -> None:
    """Adds `application_status`/`not_interested_reason`/`status_updated_at`
    (UI Save/Not Interested buttons, see 2026-07-04) for existing DBs. All
    null/unset for existing rows -- nothing had a workflow status before this
    feature existed.

    An earlier same-day version of this migration used two separate boolean
    columns (`saved`, `hidden`) instead of one status field -- replaced before
    ever shipping to users once "applied"/"not_interested"/callback-interview-
    offer states were discussed, since a single status column is what makes
    progress tracking and source analysis a plain GROUP BY. If a DB somehow
    has the old columns (dev/test only), migrate their data forward rather
    than silently dropping it.
    """
    items_cols = {row["name"] for row in conn.execute("PRAGMA table_info(items)")}
    if "application_status" not in items_cols:
        conn.execute("ALTER TABLE items ADD COLUMN application_status TEXT")
    if "not_interested_reason" not in items_cols:
        conn.execute("ALTER TABLE items ADD COLUMN not_interested_reason TEXT")
    if "status_updated_at" not in items_cols:
        conn.execute("ALTER TABLE items ADD COLUMN status_updated_at TEXT")
    conn.commit()
    items_cols = {row["name"] for row in conn.execute("PRAGMA table_info(items)")}

    if "saved" in items_cols:
        conn.execute(
            "UPDATE items SET application_status = 'saved' "
            "WHERE saved = 1 AND application_status IS NULL"
        )
    if "hidden" in items_cols:
        conn.execute(
            "UPDATE items SET application_status = 'not_interested' "
            "WHERE hidden = 1 AND application_status IS NULL"
        )
    conn.commit()


def normalize_dedup_key(author: str | None, title: str | None) -> str | None:
    """Normalized "company|title" key used to link cross-source postings of
    what looks like the same job (see alt_listings). Strips ALL non-alphanumeric
    characters, not just punctuation -- lowercasing alone doesn't make ATS-slug
    company names (e.g. ashby's 'elevenlabs') match human display names
    ('Eleven Labs') elsewhere, since that's a missing-space difference, not a
    casing one, and slug-style names cover the highest-volume sources
    (greenhouse/ashby/lever). Still plain string equality, not fuzzy matching
    (e.g. "Sr." vs "Senior" titles still won't match) -- consistent with the
    project's efficacy-over-rigor stance (see CLAUDE.md).
    """
    if not author or not title:
        return None
    def squash(s: str) -> str:
        return re.sub(r"[^a-z0-9]", "", s.lower())
    company, role = squash(author), squash(title)
    if not company or not role:
        return None
    return f"{company}|{role}"


def _migrate_dedup_tracking(conn: sqlite3.Connection) -> None:
    """Adds repost/cross-source tracking columns (see schema.sql) for existing
    DBs. dedup_key is backfilled immediately (deterministic, no API call --
    same reasoning as remote_type in _migrate_tracking_fields above);
    last_seen_at/times_seen are backfilled to their first-insert defaults.

    Deliberately NOT done here: retroactively linking existing cross-source
    duplicate rows into alt_listings. That would mean picking a canonical row
    and deleting the others -- a destructive change to already-tagged/ranked
    data that shouldn't happen as a side effect of a schema migration. Existing
    duplicates (see docs/SOURCE_OVERLAP.md) stay as separate rows; only
    newly-ingested items get folded going forward. A retroactive merge pass is
    a deliberate later decision if it's ever wanted, same precedent as the
    role_category/industry backfill decision above.
    """
    items_cols = {row["name"] for row in conn.execute("PRAGMA table_info(items)")}
    if "last_seen_at" not in items_cols:
        conn.execute("ALTER TABLE items ADD COLUMN last_seen_at TEXT")
    if "times_seen" not in items_cols:
        conn.execute("ALTER TABLE items ADD COLUMN times_seen INTEGER NOT NULL DEFAULT 1")
    if "dedup_key" not in items_cols:
        conn.execute("ALTER TABLE items ADD COLUMN dedup_key TEXT")
    if "alt_listings" not in items_cols:
        conn.execute("ALTER TABLE items ADD COLUMN alt_listings TEXT")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_items_dedup_key ON items(dedup_key)")
    conn.commit()

    conn.execute("UPDATE items SET last_seen_at = fetched_at WHERE last_seen_at IS NULL")
    rows = conn.execute(
        "SELECT id, author, title FROM items WHERE dedup_key IS NULL AND author IS NOT NULL AND title IS NOT NULL"
    ).fetchall()
    for row in rows:
        key = normalize_dedup_key(row["author"], row["title"])
        if key:
            conn.execute("UPDATE items SET dedup_key = ? WHERE id = ?", (key, row["id"]))
    if rows:
        logger.info("Backfilled dedup_key for %d existing items", len(rows))
    conn.commit()


# Weight tables locked with the user 2026-07-03 (see relevance_ranking_rework
# memory). All are multipliers applied in ranker/scores.py, baseline 1.0.
DEFAULT_ENGAGEMENT_WEIGHTS = {
    "freelance": 1.5, "project_based": 1.5, "contract": 1.1, "part_time": 1.0, "full_time": 1.0,
}
DEFAULT_SENIORITY_WEIGHTS = {
    "intern": 1.3, "junior": 1.3, "mid": 1.2, "senior": 1.0, "staff+": 0.7, "n/a": 1.0,
}
DEFAULT_LOCATION_WEIGHTS = {
    "remote": 1.3, "hyperlocal_sf": 1.2, "bay_area": 1.1, "other": 0.6, "unknown": 1.0,
}
DEFAULT_STAGE_WEIGHTS = {
    "pre_seed": 1.1, "seed": 1.3, "series_a_b": 1.3, "growth": 1.0, "public": 0.8, "unknown": 1.0,
}
_FAVORED_SECTORS = (
    "ai_ml", "ai_research", "robotics", "science", "biotech", "adult_caregiving",
    "real_estate", "transportation", "politics_civic", "prediction_markets",
    "fintech", "ai_education",
)
DEFAULT_SECTOR_WEIGHTS = {sector: 1.4 for sector in _FAVORED_SECTORS}
# Added 2026-07-05: AI-Trainer/data-labeling contractor gigs were ranking in
# the top 50 by preference_score (36/50 in one snapshot) purely from stacking
# freelance(1.5x) x junior/mid-seniority(1.2-1.3x) x remote(1.3x) x
# ai_ml-sector(1.4x) weights meant for real freelance AI eng work. This is
# the only role_category_weights entry that isn't 1.0 -- everything else is
# an unweighted engineering/product/etc. bucket, deliberately left neutral.
DEFAULT_ROLE_CATEGORY_WEIGHTS = {"ai_data_labeling": 0.15}


def _seed_default_profile(conn: sqlite3.Connection) -> None:
    """Generic SF DS/ML/AI default — placeholder until real preferences are
    characterized. See CLAUDE.md section 'Ranker'."""
    existing = conn.execute(
        "SELECT 1 FROM preference_profiles WHERE name = ?", ("default_sf_ds_ml_ai",)
    ).fetchone()
    if existing:
        # Backfill weight columns on profiles that pre-date them.
        conn.execute(
            """UPDATE preference_profiles SET
                 engagement_weights = COALESCE(engagement_weights, ?),
                 seniority_weights = COALESCE(seniority_weights, ?),
                 location_weights = COALESCE(location_weights, ?),
                 sector_weights = COALESCE(sector_weights, ?),
                 stage_weights = COALESCE(stage_weights, ?),
                 role_category_weights = COALESCE(role_category_weights, ?)
               WHERE name = ?""",
            (
                json.dumps(DEFAULT_ENGAGEMENT_WEIGHTS),
                json.dumps(DEFAULT_SENIORITY_WEIGHTS),
                json.dumps(DEFAULT_LOCATION_WEIGHTS),
                json.dumps(DEFAULT_SECTOR_WEIGHTS),
                json.dumps(DEFAULT_STAGE_WEIGHTS),
                json.dumps(DEFAULT_ROLE_CATEGORY_WEIGHTS),
                "default_sf_ds_ml_ai",
            ),
        )
        conn.commit()
        return
    conn.execute(
        """INSERT INTO preference_profiles
           (name, is_active, role_keywords, location_keywords, seniority_keywords,
            category_weights, engagement_weights, seniority_weights, location_weights,
            sector_weights, stage_weights, role_category_weights, created_at)
           VALUES (?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            "default_sf_ds_ml_ai",
            json.dumps(["data scientist", "machine learning", "ML engineer",
                        "AI engineer", "data engineer", "applied scientist"]),
            json.dumps(["San Francisco", "Bay Area", "SF", "Remote"]),
            json.dumps(["mid", "senior"]),
            json.dumps({"job": 1.0, "event": 0.6, "networking": 0.5}),
            json.dumps(DEFAULT_ENGAGEMENT_WEIGHTS),
            json.dumps(DEFAULT_SENIORITY_WEIGHTS),
            json.dumps(DEFAULT_LOCATION_WEIGHTS),
            json.dumps(DEFAULT_SECTOR_WEIGHTS),
            json.dumps(DEFAULT_STAGE_WEIGHTS),
            json.dumps(DEFAULT_ROLE_CATEGORY_WEIGHTS),
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    conn.commit()



# Sources whose per-item URL is not a stable identifier for the underlying
# posting -- e.g. linkedin_apify's Apify actor URL embeds a per-search-render
# trackingId/refId/position that differs on every scrape even for the exact
# same job, so UNIQUE(source, url) structurally can't dedup reposts there
# (confirmed 2026-07-03, see docs/SOURCE_OVERLAP.md: 0% exact-URL overlap
# across runs vs. real company+title+location overlap). For these sources,
# same-source (dedup_key, location) is treated as a repost signal instead --
# unlike greenhouse/ashby/lever, where a same-source title+location collision
# is dominated by genuinely distinct postings (1-10% single-location), this
# source's collisions are 89% single-location, i.e. dominated by re-scrapes
# of the same posting.
UNSTABLE_URL_SOURCES = {"linkedin_apify"}


def insert_item_sync(conn: sqlite3.Connection, item: dict) -> bool:
    """Insert one normalized item, or fold it into existing tracking if it's a
    repeat. Three-way branch, safe without extra locking because WriterQueue
    guarantees single-writer access (see class docstring below) -- no race
    between a lookup and its write:

      1. Repost of an existing row -- either the exact same (source, url), or,
         for UNSTABLE_URL_SOURCES, the same (source, dedup_key, location) under
         a different url. Bumps times_seen/last_seen_at on the existing row
         instead of silently no-op'ing, so "still live as of X" is recoverable
         later. If the re-scraped raw_text actually differs from what's
         stored, archives the OLD text to item_text_history before
         overwriting, so description-drift-over-time analysis has real data
         to work with instead of only ever seeing the latest version.
      2. Essential duplicate (same normalized dedup_key already present under
         a DIFFERENT source): append {source, url, seen_at} to the canonical
         (first-seen) row's alt_listings instead of inserting a new row.
         Matches within the SAME source are excluded here on purpose (handled
         by case 1's unstable-URL fallback instead, where warranted) -- for
         every other source, same-source title collisions are the
         same-title-different-location case documented in
         docs/SOURCE_OVERLAP.md (93% of same-source title collisions are
         genuinely different postings), so they keep getting their own rows.
      3. Neither: insert as a new row.

    Returns True only for case 3 (a genuinely new row was created) -- callers
    that count "inserted vs skipped" (e.g. WriterQueue, run_log metrics) keep
    working unchanged, since both fold cases correctly read as "no new row."
    """
    now = item.get("fetched_at", datetime.now(timezone.utc).isoformat())
    try:
        dedup_key = normalize_dedup_key(item.get("author"), item.get("title"))

        existing = conn.execute(
            "SELECT id, raw_text FROM items WHERE source = ? AND url = ?",
            (item["source"], item["url"]),
        ).fetchone()

        if not existing and dedup_key and item["source"] in UNSTABLE_URL_SOURCES:
            existing = conn.execute(
                """SELECT id, raw_text FROM items
                   WHERE source = ? AND dedup_key = ? AND location IS ?
                   ORDER BY fetched_at ASC LIMIT 1""",
                (item["source"], dedup_key, item.get("location")),
            ).fetchone()

        if existing:
            new_raw_text = item.get("raw_text")
            if new_raw_text and new_raw_text != existing["raw_text"]:
                conn.execute(
                    "INSERT INTO item_text_history (item_id, raw_text, seen_at) VALUES (?, ?, ?)",
                    (existing["id"], existing["raw_text"], now),
                )
                conn.execute(
                    "UPDATE items SET raw_text = ?, last_seen_at = ?, times_seen = times_seen + 1 WHERE id = ?",
                    (new_raw_text, now, existing["id"]),
                )
            else:
                conn.execute(
                    "UPDATE items SET last_seen_at = ?, times_seen = times_seen + 1 WHERE id = ?",
                    (now, existing["id"]),
                )
            conn.commit()
            return False

        if dedup_key:
            canonical = conn.execute(
                """SELECT id, alt_listings FROM items
                   WHERE dedup_key = ? AND source != ?
                   ORDER BY fetched_at ASC LIMIT 1""",
                (dedup_key, item["source"]),
            ).fetchone()
            if canonical:
                alt_listings = json.loads(canonical["alt_listings"] or "[]")
                already_linked = any(
                    a["source"] == item["source"] and a["url"] == item["url"] for a in alt_listings
                )
                if not already_linked:
                    alt_listings.append({"source": item["source"], "url": item["url"], "seen_at": now})
                    conn.execute(
                        "UPDATE items SET alt_listings = ? WHERE id = ?",
                        (json.dumps(alt_listings), canonical["id"]),
                    )
                    conn.commit()
                return False

        cur = conn.execute(
            """INSERT INTO items
               (source, source_id, url, title, author, location, raw_text,
                posted_at, start_at, end_at, fetched_at, last_seen_at, times_seen,
                raw_json, remote_type, dedup_key)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                item["source"], item.get("source_id"), item["url"], item.get("title"),
                item.get("author"), item.get("location"), item["raw_text"],
                item.get("posted_at"), item.get("start_at"), item.get("end_at"),
                now, now, 1,
                json.dumps(item.get("raw_json", item)),
                classify_remote_type(item.get("location")),
                dedup_key,
            ),
        )
        conn.commit()
        return cur.rowcount > 0
    except sqlite3.Error:
        logger.exception("Failed to insert item %s", item.get("url"))
        return False


def record_run(
    stage: str,
    metrics: dict,
    source: str | None = None,
    duration_seconds: float | None = None,
    status: str = "ok",
    error: str | None = None,
) -> None:
    """Append one row to `run_log`. See schema.sql for the metrics shape per stage."""
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO run_log (stage, source, run_at, duration_seconds, status, error, metrics)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                stage, source, datetime.now(timezone.utc).isoformat(),
                duration_seconds, status, error, json.dumps(metrics),
            ),
        )
        conn.commit()
    finally:
        conn.close()


class WriterQueue:
    """Single-writer coroutine: scrapers/ingest call `await queue.put(item)`,
    one background task drains the queue into SQLite so concurrent async
    scrapers never contend on the same connection."""

    def __init__(self):
        self._queue: asyncio.Queue = asyncio.Queue()
        self._conn = get_connection()
        self._task: asyncio.Task | None = None
        self.inserted = 0
        self.skipped = 0
        self.inserted_by_source: dict[str, int] = {}
        self.skipped_by_source: dict[str, int] = {}

    async def put(self, item: dict) -> None:
        await self._queue.put(item)

    async def start(self) -> None:
        self._task = asyncio.create_task(self._run())

    async def _run(self) -> None:
        while True:
            item = await self._queue.get()
            if item is None:  # sentinel to stop
                self._queue.task_done()
                break
            inserted = insert_item_sync(self._conn, item)
            source = item["source"]
            if inserted:
                self.inserted += 1
                self.inserted_by_source[source] = self.inserted_by_source.get(source, 0) + 1
            else:
                self.skipped += 1
                self.skipped_by_source[source] = self.skipped_by_source.get(source, 0) + 1
            self._queue.task_done()

    async def stop(self) -> None:
        await self._queue.put(None)
        if self._task:
            await self._task
        self._conn.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_db()
    print(f"DB initialized at {DB_PATH}")
