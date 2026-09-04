-- Opportunity pipeline schema. Designed from real scraped fields
-- (HN Who's Hiring, Luma events) rather than speculative ones.

CREATE TABLE IF NOT EXISTS items (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source          TEXT NOT NULL,         -- hn_whoshiring, luma_events, indeed_rss, linkedin_email, handshake_email, wellfound, builtin_sf
    source_id       TEXT,                  -- comment_id, event id, etc. -- whatever the source provides
    url             TEXT NOT NULL,
    title           TEXT,
    author          TEXT,
    location         TEXT,
    raw_text        TEXT NOT NULL,          -- the untouched scraped text/description
    posted_at       TEXT,                  -- when the item was created/published at the source
    start_at        TEXT,                  -- event start, null for jobs
    end_at          TEXT,                  -- event end, null for jobs
    fetched_at      TEXT NOT NULL,          -- when our scraper pulled it
    raw_json        TEXT,                  -- full original scraped dict, for reprocessing

    -- filled in by the LLM tagger/verifier (section 4), null until tagged
    category        TEXT,                  -- job | event | networking
    role_type       TEXT,                  -- free-text, e.g. "data scientist" -- may be a slash-joined
                                            -- list for multi-role postings; role_category below is
                                            -- the single normalized bucket for grouping/tracking
    role_category   TEXT,                  -- normalized enum bucket, see tagger/schema.py ROLE_CATEGORY_VALUES
    industry        TEXT,                  -- normalized enum bucket, see tagger/schema.py INDUSTRY_VALUES
    seniority       TEXT,
    engagement_type TEXT,                  -- full_time | part_time | contract | freelance | project_based | null if unspecified
    company_stage   TEXT,                  -- pre_seed | seed | series_a_b | growth | public | unknown, see tagger/schema.py
    deadline        TEXT,
    relevance_score REAL,                  -- LEGACY, pre-2026-07-03 tagging runs only. Conflated content
                                            -- quality/spam/preference into one number -- superseded by
                                            -- content_quality (narrower) + spam_risk + ranker/scores.py
                                            -- (preference weighting). Kept for old rows, not written to going
                                            -- forward; do not use for new ranking logic.
    content_quality REAL,                  -- LLM judgment of ONLY how substantive/well-written a posting is,
                                            -- see tagger/schema.py TagResult -- NOT a preference/relevance signal.
                                            -- Internal QA signal, not surfaced as a ranking input or UI-prominent field.
    spam_risk       TEXT,                  -- clean | suspicious | likely_spam, see tagger/schema.py.
                                            -- Reported for visibility only -- deliberately NOT multiplied into
                                            -- any ranking score in ranker/scores.py until validated in use.
    role_expectation_delta REAL,           -- signed -5..5, how much a job's stated requirements deviate from
                                            -- a typical posting with that title (LLM's general knowledge, not
                                            -- a stored corpus -- see docs on the lightweight-vs-full-corpus
                                            -- decision). Negative = less demanding than typical.
    role_expectation_notes TEXT,           -- 1-sentence specific callout, e.g. "4y exp vs usual 2"
    tag_confidence  REAL,
    tagged_at       TEXT,
    tagger_model    TEXT,                  -- haiku | sonnet, whichever produced the final tags

    -- computed at rank-time by ranker/scores.py from tagged fields + the active
    -- preference_profiles weight tables; overwritten each time the ranker runs
    -- (materialized-view style, not an append-only history -- see run_log for
    -- per-run metadata if a trend over time is ever wanted)
    urgency_score     REAL,                -- deadline-dominant sort, preference weights still applied
    preference_score  REAL,                -- full personal preference weight stack (engagement/location/
                                            -- stage/sector/seniority multipliers over content_quality)
    general_score     REAL,                -- preference-UNweighted -- content_quality + deadline only
    ranked_at         TEXT,                -- when these three scores were last computed

    -- derived deterministically from `location` at ingest time (not LLM-tagged,
    -- so it's backfillable for free) -- see classify_location.py
    remote_type     TEXT,                  -- remote | hyperlocal_sf | bay_area | other | unknown

    -- user feedback (UI thumbs up/down) -- buttons hidden in UI for now
    -- (2026-07-04), kept as a column since a future ranking-feedback loop is
    -- planned; not read anywhere yet
    feedback        INTEGER,               -- 1 = up, -1 = down, null = no feedback

    -- user application-workflow tracking (UI Save/Not Interested buttons,
    -- see 2026-07-04). Single-value status, not independent flags -- an item
    -- is in exactly one state at a time (e.g. marking "applied" replaces
    -- "saved" rather than both being true), so progress ("how many applied
    -- this week") and source analysis ("what % of source X gets marked not
    -- interested, and why") can be read directly off one column via GROUP BY.
    application_status TEXT,               -- null (default) | saved | not_interested | applied |
                                            -- callback | interview | offer -- UI-set (not LLM-tagged),
                                            -- see ui/app.py APPLICATION_STATUS_VALUES. callback/
                                            -- interview/offer are schema-ready but not yet reachable
                                            -- from any UI button (planned later).
    not_interested_reason TEXT,            -- only set when application_status = not_interested,
                                            -- e.g. "too_senior" | "too_junior" | "unrelated_field" |
                                            -- "bad_location" | "other: <free text>" -- see
                                            -- ui/app.py NOT_INTERESTED_REASONS. Used to spot
                                            -- per-source patterns (e.g. a source consistently
                                            -- surfacing over-senior roles) for sourcing/tagging fixes.
    status_updated_at TEXT,                -- when application_status was last changed, for
                                            -- day/week progress metrics (planned, not built yet)

    -- repost/cross-source tracking (see docs/SOURCE_OVERLAP.md)
    last_seen_at    TEXT,                  -- most recent time this exact (source,url) was re-scraped
    times_seen      INTEGER NOT NULL DEFAULT 1,  -- how many scrape runs have re-confirmed this exact posting is still live
    dedup_key       TEXT,                  -- normalized "company|title" (see storage/db.py:normalize_dedup_key),
                                            -- only set when both author+title exist; used solely to link
                                            -- CROSS-source postings of the same likely job (see alt_listings).
                                            -- Deliberately NOT used to merge same-source postings sharing a
                                            -- title -- 93% of those are legitimately different postings at
                                            -- different locations, see docs/SOURCE_OVERLAP.md.
    alt_listings    TEXT,                  -- JSON list of {source, url, seen_at}, other sources' postings
                                            -- that matched this row's dedup_key; lives only on the first-seen
                                            -- ("canonical") row for that key -- see storage/db.py:insert_item_sync

    UNIQUE (source, url)
);

CREATE INDEX IF NOT EXISTS idx_items_category ON items(category);
CREATE INDEX IF NOT EXISTS idx_items_relevance ON items(relevance_score);
CREATE INDEX IF NOT EXISTS idx_items_source ON items(source);
-- idx_items_dedup_key is created in db.py's _migrate_dedup_tracking, not here --
-- an existing DB's `items` table won't have the dedup_key column yet at the
-- point this executescript runs (CREATE TABLE IF NOT EXISTS is a no-op on it),
-- so an index on it here would fail on every pre-existing DB.

-- Single-row-per-profile preference store (section 5). Kept as a table,
-- not a config file, so it's queryable/editable from the UI later.
CREATE TABLE IF NOT EXISTS preference_profiles (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL UNIQUE,
    is_active       INTEGER NOT NULL DEFAULT 0,
    role_keywords   TEXT,    -- JSON list, e.g. ["data scientist","ML engineer","AI engineer"]
    location_keywords TEXT,  -- JSON list, e.g. ["San Francisco","Bay Area","Remote"]
    seniority_keywords TEXT, -- JSON list, e.g. ["mid","senior"]
    category_weights TEXT,   -- JSON dict, e.g. {"job": 1.0, "event": 0.6, "networking": 0.5}
    engagement_weights TEXT, -- JSON dict keyed on engagement_type, see ranker/scores.py DEFAULT_ENGAGEMENT_WEIGHTS
    seniority_weights TEXT,  -- JSON dict keyed on seniority, see ranker/scores.py DEFAULT_SENIORITY_WEIGHTS
    location_weights TEXT,   -- JSON dict keyed on remote_type, see ranker/scores.py DEFAULT_LOCATION_WEIGHTS
    sector_weights  TEXT,    -- JSON dict keyed on industry, see ranker/scores.py DEFAULT_SECTOR_WEIGHTS
    stage_weights   TEXT,    -- JSON dict keyed on company_stage, see ranker/scores.py DEFAULT_STAGE_WEIGHTS
    created_at      TEXT NOT NULL
);

-- Ongoing per-run log (# items fetched/tagged/ranked per run, LLM cost/tokens,
-- category breakdown). One row per source per ingest run, or one row per
-- tagging/ranking run. `metrics` is JSON since each stage's fields differ
-- (fetched/inserted/skipped for ingest; tokens/cost/category_counts for tag;
-- items_ranked/top_score for rank) -- same pattern as category_weights above.
-- Category/role/industry counts over time are NOT duplicated here; derive
-- them from `items` (which already has tagged_at + category/role_category/
-- industry per row) via GROUP BY.
CREATE TABLE IF NOT EXISTS run_log (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    stage             TEXT NOT NULL,   -- ingest | tag | rank
    source            TEXT,            -- populated for ingest rows, null for tag/rank
    run_at            TEXT NOT NULL,
    duration_seconds  REAL,
    status            TEXT NOT NULL,   -- ok | error
    error             TEXT,
    metrics           TEXT NOT NULL    -- JSON, shape documented above
);

CREATE INDEX IF NOT EXISTS idx_run_log_stage ON run_log(stage);
CREATE INDEX IF NOT EXISTS idx_run_log_run_at ON run_log(run_at);

-- Append-only archive of prior raw_text versions, written only when a
-- re-scrape of an existing (source,url) finds the text actually changed
-- (see storage/db.py:insert_item_sync case 1). Without this, an edited
-- posting (e.g. company bumps years-of-experience or reworks the stack)
-- silently overwrites the old text with no trace -- fine for current
-- ranking/tagging use, but it's the raw material needed for any future
-- "how do job descriptions drift over time" analysis, so it's captured
-- now rather than retrofitted once the history is already gone.
CREATE TABLE IF NOT EXISTS item_text_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id     INTEGER NOT NULL REFERENCES items(id),
    raw_text    TEXT NOT NULL,   -- the PRIOR raw_text, just before it was replaced
    seen_at     TEXT NOT NULL    -- fetched_at of the scrape that superseded this version
);

CREATE INDEX IF NOT EXISTS idx_item_text_history_item_id ON item_text_history(item_id);
