# Jobs Pipeline — DTSC 691 AI Capstone

AI-powered personal job pipeline: scrapes/ingests job postings from multiple
sources, uses an LLM to verify/tag/rank them, stores results in a DB, and
surfaces them via a UI with notifications and digest reports. Also tracks
professional events and networking leads as a secondary, currently-frozen
capability (see Current State). Built as an Eastern University DTSC 691
(Applied Data Science) AI-track capstone project. Full proposal text lives
in `docs/`.

(Renamed from "Opportunity Pipeline" 2026-07-03 — repo moved to
jjchong5/jobs; see `HISTORY.md` for the rename/scope-framing entry.)

**Explicit non-goal:** this is not a generic SWE project to over-engineer. The
rubric and the author's own intent both want the pipeline + working app to be the
focus, not ML busywork or speculative features. Don't add scope beyond what's below.

## Architecture

```
[Sources] -> [Scrapers/Parsers] -> [Normalizer] -> [LLM Tagger/Verifier]
          -> [SQLite DB] -> [Ranker/Prioritizer]
          -> [Streamlit UI + Digest Reports + Notifications]
```

- **Sources (v1, locked)**: LinkedIn job-alert emails (parse, don't scrape),
  Handshake job emails (parse — Handshake ToS bans 3rd-party scraping), HN "Who's
  Hiring" monthly thread (HTML), Luma (public API), Indeed RSS feed, Wellfound
  (Playwright scrape), Built In SF (HTML scrape).
  Author's stated stance on scraping ToS friction (mentor-raised): "I plan on
  scraping what I can anyway" — Wellfound/Built In are in v1, not deferred. Don't
  re-litigate this; if a specific scraper turns out to be blocked technically
  (aggressive anti-bot, login wall), drop it and note why, but don't skip it
  pre-emptively over ToS concerns alone.
  Ingestion-method spread (capstone framing): email parse / API / HTML scrape / RSS
  / JS-rendered scrape.
- **Future/stretch sources** (not in v1): Greenhouse/Lever ATS boards, Meetup API,
  Eventbrite API, Telegram bot feed (Frontier Tower — deprioritized, hasn't
  surfaced real job listings), Discord/Slack bots.
- **Verifier**: drops bad/irrelevant scrape results before tagging, if needed.
- **Tagger**: LLM extracts structured fields — `role_type`, `seniority`, `location`,
  `deadline`, `category` (job/event/networking), `engagement_type`, `company_stage`,
  `spam_risk`, `role_expectation_delta`/`_notes`, and `content_quality` (0-10,
  internal QA signal only — how substantive/well-written a posting is, NOT a
  preference/relevance signal; not surfaced as a ranking input). The
  "confidence" used to decide Haiku->Sonnet escalation is elicited via prompt
  instruction (LLM self-reports a 0-1 score), not a real calibrated probability —
  mentor flagged this; treat it as a semantic heuristic, not a statistical one.
- **Ranker**: computes three independently-sortable scores per item —
  `preference_score` (main sort, `content_quality` times a product of 6
  explicit weight tables: engagement/seniority/location/sector/company_stage/
  role_category), `urgency_score` (same, with deadline weighted 3x),
  `general_score` (preference-unweighted). See `src/pipeline/ranker/scores.py`
  for the formulas and `preference_profiles` weight-table columns for current
  values. The first 5 weight values were interviewed/locked with the author
  2026-07-03 — see `HISTORY.md#ranking-rework`; don't block on getting them
  "right" on the first pass, they're meant to be tuned over time. The 6th
  (`role_category_weights`) was added 2026-07-05 specifically to derank
  AI-Trainer/data-labeling contractor gigs that were dominating the top
  ranks via unrelated freelance/seniority/sector weights — see
  `HISTORY.md#ai-trainer-derank-fix`; every `role_category` value besides
  `ai_data_labeling` stays neutral (1.0), this isn't a general role-category
  preference weight.
- **Changing ranking weights**: the 6 weight tables (engagement, seniority,
  location, sector, company_stage, role_category) live as JSON columns on the
  active row in `preference_profiles`
  (`SELECT * FROM preference_profiles WHERE is_active=1`), seeded from the
  `DEFAULT_*_WEIGHTS` constants in `src/pipeline/storage/db.py`.
  To change a weight:
  1. Update it directly in the DB (`UPDATE preference_profiles SET
     sector_weights = '{"ai_ml": 1.4, ...}' WHERE is_active = 1`), or edit the
     `DEFAULT_*_WEIGHTS` constant in `db.py` if the new default should apply
     to fresh DBs too (editing the constant alone does NOT update an existing
     row — `_seed_default_profile`'s `COALESCE` only fills nulls, it will not
     overwrite an already-populated weight column; you must also run the
     direct `UPDATE` above, or the change silently won't take effect on the
     live DB — this bit a fresh implementation in this project, see
     `HISTORY.md#ranking-rework`).
  2. Re-run `python -m pipeline.ranker.rank` to recompute
     `urgency_score`/`preference_score`/`general_score` for all tagged items
     — weights are NOT applied retroactively until the ranker runs again.
  3. Adding a brand-new *value* to an existing weighted field (e.g. a new
     `industry` bucket) requires updating the enum in `tagger/schema.py`
     (`INDUSTRY_VALUES` etc.) AND `tagger/prompts.py`'s enum listing, or the
     LLM will never emit it and the new weight will silently never apply. New
     industry/role_category values are NOT retroactively applied to
     already-tagged items — only a re-tag pass changes old rows.
  4. These are real personal-preference decisions the author has already
     reasoned through in detail once (which sectors are favored and why,
     why remote outranks SF-in-person this round, why staff+ is downranked,
     etc.) — see `HISTORY.md#ranking-rework`'s "Decision trail" subsection
     before proposing a different set of values instead of re-deriving them
     from scratch or guessing at intent.
- **Profile preferences**: stored in a SQLite table (not a config file or .env) —
  same storage system as everything else, queryable/editable from the UI later.
- **Storage**: SQLite (WAL mode), single writer coroutine (`asyncio.Queue`) so
  parallel async scrapers can write concurrently without contention. Migration to
  Postgres/Supabase is a deferred option, not needed now.
- **UI**: Streamlit — search, tag-based browse, daily/weekly digest view with
  score-distribution histogram, thumbs-up/thumbs-down feedback buttons per item.
  Keep it functional and clean, not heavily styled — this is a v1 scaffold, not a
  final product; don't sink time into aesthetics.
- **Notifications**: in-UI + email digest for high-priority matches.
- **Scheduling**: APScheduler. HN thread ~monthly; everything else every 6-24h.
  Dedup by source URL/job ID.

## Stack decisions

| Concern | Choice | Why |
|---|---|---|
| DB | SQLite (WAL mode) | zero-setup, AI-trivial migration path to Postgres later if ever needed |
| LLM API | Claude API (Anthropic), Haiku for batch tagging, escalate to Sonnet on low confidence (<0.7) | cost/latency balance; capstone is AI-track, meta-appropriate |
| Scraper | `requests` + Playwright (JS-heavy sites only) | |
| UI | Streamlit | fastest path to a working interactive UI |
| Validation | Pydantic models for LLM output before DB insertion | catches malformed JSON; 2 retries on failure |
| Scheduler | APScheduler | source re-poll on a cadence |

LLM config: Haiku temp 0.1 / max_tokens 300 (deterministic batch tagging). Sonnet
temp 0.2 / max_tokens 600, used only for ambiguous items or deadline extraction.

## Build order (don't skip ahead)

1. Scraper (1-2 sources) -> raw output to JSON/print, no DB yet
2. SQLite schema, designed around real scraped fields (not speculative ones)
3. Ingest pipeline (scraper -> DB), dedup logic
4. LLM tagger/verifier, tested against real ingested data
5. Ranker/prioritizer
6. Streamlit UI — **only after tagged data already exists in the DB**; building UI
   against mocks creates rework
7. Notifications + digest reports

Parallelize with multiple Claude Code agents only for independent scraper builds
(e.g., one agent per source). Everything else (schema, tagger, ranker, UI) stays
single-threaded/single-session — these have sequential dependencies and parallel
work there just creates merge conflicts and context drift.

## Working conventions

- One Claude Code session per component/phase above. Don't one-shot the whole app.
- Project root is `C:\Users\jjcho\code\jobs` (intentionally short path, outside
  OneDrive/sync).
- API keys in `.env`, excluded from version control. `python-dotenv` requires an
  explicit `load_dotenv()` call in-script — being in `requirements.txt` alone does
  nothing.
- When a component lands, add a short newest-first entry to `CHANGELOG.md`
  (one bullet, link to detail) and the full narrative (what was tried, bugs
  found, live-test results) as a new top entry in `HISTORY.md`, then update
  the **Current State** section below to reflect the new current facts.
  Current State should stay a short snapshot — don't let dated narrative
  accumulate there again.
- `AGENTS.md` in this repo just points back here — this file is the single source
  of truth for both Claude Code and Codex.

## Evaluation (capstone rubric requirement)

Ground-truth set: 60 manually labeled items (20 jobs / 20 events / 20 mixed-ambiguous).
Kept at 60, not expanded — author's stated priority is efficacy over rigor; he'll
catch misclassification through actual use. Don't second-guess this and pad the
set unasked.
- Classification accuracy target: >=85%
- Tag-extraction F1 per field (role_type, seniority)
- Spearman correlation: LLM relevance score vs. manual ranking
- Confidence calibration check
- Confusion matrix (scikit-learn) for category classification
- Manual review of top-10 ranked results per scrape cycle; document failure modes
  (hallucinated deadlines, miscategorized roles) candidly — this is expected and
  should be written up, not hidden.

## Error handling philosophy

Author's explicit stance (mentor pushed for more, author declined): try/except +
logging for proper functionality and debuggability, yes. Exhaustive output
validation/error-checking beyond malformed-JSON retries, no — spot-check and fix
as issues surface during actual use, rather than building exhaustive upfront
validation. Don't over-engineer validation layers beyond what's already specified
(Pydantic schema check + 2 retries on the tagger).

## Bias / ethics stance (for context, don't relitigate)

Mentor raised ranking bias, aggregation ethics, and ToS compliance as concerns.
Author's position: this is a single-user personal tool, ranking bias toward
preferred companies/roles is a desired feature not a flaw, and objective
debiasing tests are not a priority for this use case. Don't add bias-detection
tooling or extensive ToS-compliance scaffolding unless asked — one upfront
statement that this is personal-use-only is the author's intended level of
coverage here.

## Current State

For a short, newest-first index of what's landed, see `CHANGELOG.md`; full
narrative history (bugs found, sources evaluated/dropped, live-test
results) is in `HISTORY.md`. For per-source status in table form, see
`docs/SOURCES.md`. For remaining/open work, see `TODO.md`. This section is
a snapshot of what's true *now* — keep it short; put new dated narrative in
`HISTORY.md` (with a short index entry in `CHANGELOG.md`) instead of
growing this section.

**Pipeline status: end-to-end working**, scraper -> DB -> ingest -> tagger ->
ranker -> UI, all code under `src/pipeline/`, tested against real (not
mocked) data throughout. DB at `data/pipeline.db` (gitignored, SQLite WAL
mode) — **44,319 items as of 2026-08-26** (stale-on-read figure below still
useful for the growth narrative, but not the live count).

**Scheduler moved to the Mac mini (2026-08-26)** — always-on host, running
persistently via launchd (`~/Library/LaunchAgents/com.jjcho.jobspipeline.scheduler.plist`),
not Windows Task Scheduler (that registration was blocked on admin
elevation and never actually ran). `pipeline.db` was synced there and
**the Mini is now the source of truth going forward** — Windows's local
copy is a point-in-time secondary, not kept in sync. Every source is on a
daily cadence as a deliberate 2-week calibration trial (`DAILY_TRIAL_END`
in `scheduler.py`, ends 2026-09-09), not a final per-source decision — see
`HISTORY.md#scheduler-moved-to-mac-mini` and `TODO.md` 3b for the
post-trial analysis plan. Scraper fetches (per-source in `ingest.py`, and
internally within `linkedin_apify`/`wellfound_search_apify`/`greenhouse`/
`ashby`/`vc_portfolio`) were also parallelized the same day — see
`HISTORY.md#scraper-fetch-parallelization`.

~27,000+ items across 19 wired sources as of 2026-07-03 (still growing
— another session is actively adding more sourcing; Greenhouse alone grew
from 3,187 to 16,999 items across three same-day passes, 26 -> 67 -> 158 ->
248 boards — the second pass discovered new company board tokens by mining
company names already in the DB from `yc_workatastartup`/`vc_portfolio`
(`HISTORY.md#greenhouse-company-discovery`); the third pulled the full
public YC company directory (6,004 companies, via YC's own public-search
Algolia key) as an independent candidate source, verifying each hit's real
job content against the YC company's stated business before trusting it —
91 of 154 raw hits passed, since short/generic company names (Pulse, Clara,
Agency, Axle, Camp...) collide often with unrelated same-named companies on
Greenhouse's shared slug namespace, see
`HISTORY.md#yc-directory-greenhouse-discovery`. DB total: 44,319 items as of
2026-08-27 (full re-scrape across all 14 live sources after ~7 weeks idle
post-capstone; see `HISTORY.md#batch-413-fix`). Tagging backlog cleared same
day (44,312/44,319 tagged, 43,677 ranked) using the batch-lane cost-cut path
([[tagger-cost-cuts]]) plus a chunking fix for the Batch API's 256MB request
cap ([[batch-413-fix]]) — check `SELECT COUNT(*) FROM items WHERE tagged_at
IS NOT NULL` vs. total item count for the current live number rather than
trusting the prose here, since new scrapes will reopen the gap.

`run_tagging.run()` now takes `--concurrency` (default 15, parallel API calls,
sequential DB writes — checked against the account's real rate-limit headroom
before picking this number, see `HISTORY.md#tagger-concurrency-default`) and
refuses to start a second time while a run is in progress (see
`HISTORY.md#tagger-concurrency`) — don't bypass this by editing around the
lock; if a run needs killing, delete `data/tagging.lock` only after
confirming nothing is actually running. The per-item text sent to the tagger
is no longer capped at 4000 chars (`prompts.py`'s `RAW_TEXT_CHAR_LIMIT`, now
12000) — the old cap was silently truncating ~30% of content on average
across most of the backlog; see `HISTORY.md#raw-text-truncation-cap`.

**Tagger cost cuts (2026-08-26):** prompt caching (system prompt + few-shot
examples combined into one `cache_control`-marked block via
`providers.build_cached_system_blocks`, only per-item `raw_text` stays
dynamic) + a Batch API lane (`batch_tagging.py`, 50% off input/output tokens,
polled every 60s up to a 6h cap) + a fast/slow lane split
(`tag_item.FAST_LANE_COMPANY_WHITELIST`, matched against `items.author` —
**currently empty**, add real company names or every item routes to the
batch lane). Note for future prompt edits: Haiku 4.5's minimum cacheable
prompt is **4,096 tokens**, not the more commonly-cited 1,024/2,048 —
trimming the system prompt/examples block below that reintroduces silent
(no-error) cache misses; check token count against that threshold before
shrinking it. See `HISTORY.md#tagger-cost-cuts` for the full debug story and
why a junk pre-filter was investigated and declined (spam is 0.3%/3.3%
suspicious of tagged volume — not worth building).

**Live sources (19):** HN Who's Hiring, Luma SF events (frozen, see below),
Built In SF, Handshake (email, via Gmail API), We Work Remotely, RemoteOK,
LinkedIn (Apify), Indeed (`indeed_radius` — radius-search actor, replaced
`indeed_apify` 2026-07-03, see below; RSS variant `indeed_rss` is dead —
Indeed retired public RSS), Greenhouse boards, Lever boards, YC Work at a
Startup, Dice, Meetup (frozen), Eventbrite (frozen), Ashby boards, VC
portfolio boards (Getro/Consider), aijobs.net, Wellfound search
(`wellfound_search_apify` — replaced the old flat-feed `wellfound_apify`,
see below).

**Frozen/mothballed (code + data untouched, excluded from default
ingest/schedule, reversible via explicit `sources=[...]`):**
- Event sources (`luma_events`, `meetup`, `eventbrite`) — frozen 2026-07-02,
  author prioritized the job tracker over event tracking pre-capstone
  deadline.
- `wellfound_apify` — mothballed 2026-07-03, only cleared 14% relevance
  hit-rate off a hard ~49-job ceiling (client-side-filtered snapshot, not
  real search). `wellfound_search_apify` is the live replacement (84.2%
  relevance hit-rate via real role+location search URLs).
- `indeed_apify` (renamed `indeed_apify_old`) — mothballed 2026-07-03, not
  for being broken: `indeed_radius` is ~4x cheaper and has a native `radius`
  param closing a real coverage gap (SF vs San Jose searches were ~92%
  non-overlapping without one). Kept live in the codebase as a deliberate
  fallback, since `indeed_radius`'s actor authenticates via harvested
  third-party mobile-app session tokens (no account-ban risk to the author
  either way, but the token pool could get invalidated without warning) —
  see `indeed_radius.py` docstring for the full tradeoff.

**Dropped (genuinely blocked, not ToS retreat):** Wellfound direct scrape
(DataDome), Toptal, Catalant, Upwork, Braintrust, Gun.io, A.Team, Contra,
Turing.com (Incapsula). Full reasoning per source in `docs/SOURCES.md`.

**Blocked / deferred:**
- LinkedIn email parser — no real alert email found in the connected Gmail
  account; deprioritized since `linkedin_apify` already covers LinkedIn
  jobs directly. Repurpose as an eval-time coverage cross-check if a real
  email ever surfaces (see `TODO.md` section 6).
- Evaluation (60-item ground truth set, accuracy/F1/Spearman/confusion
  matrix) — not started; data exists to support it now.

**Known data gaps (not bugs):** `engagement_type`, `role_category`, and
`industry` are `null` on items tagged before those fields existed (older
rows predate the schema addition) — re-tagging costs real API calls and
wasn't asked for. New/re-ingested items get them going forward. A
deliberate re-tag pass is a later call, not scheduled. Same applies to the
2026-07-03 ranking-rework fields (`spam_risk`, `role_expectation_delta`/
`_notes`, `company_stage`) — `null` on anything tagged before that date;
the legacy `relevance_score` column's ~1,900 old values were copied forward
into `content_quality` as an imperfect starting value, not re-derived.

**Notifications (2026-08-26):** Telegram run-summary digest, live —
`src/pipeline/notifications/` (`telegram.py` sendMessage wrapper,
`notifier.py` digest builder), hooked into `scheduler.py`'s nightly
tag+rank job. Reuses the bot token already provisioned for the separate
separate personal Telegram/Claude gateway project
rather than a new bot — this only needs one-way push. Digest is built
from existing `run_log` rows (no new instrumentation): items
scraped/tagged/ranked per source and any errors; no per-provider
API-credit-remaining figures since neither Anthropic nor Apify expose a
reliable balance endpoint. `notify_high_priority_items()` is a
deliberate stub (raises `NotImplementedError`) for a future per-item
alert gated on a company whitelist the author hasn't defined yet — do
not implement that logic without the whitelist. See
`HISTORY.md#telegram-run-summary-notifications`.

**Dedup gap found and fixed (2026-07-03):** `linkedin_apify`'s Apify actor
URL isn't a stable per-posting id (embeds a per-search-render tracking id),
so `UNIQUE(source, url)` couldn't dedup its reposts — 37% of its rows were
undetected duplicates before the fix. `insert_item_sync` now also matches on
`(dedup_key, location)` for that source specifically; see
`HISTORY.md#linkedin-apify-dedup-fix`. The ~505 pre-fix duplicate rows are
left as-is (forward-only fix), and every other source is unaffected —
same-source title collisions elsewhere are genuinely distinct postings, not
scrape artifacts (see `docs/SOURCE_OVERLAP.md`). Re-run
`python -m pipeline.analysis.source_overlap` to refresh that doc's numbers
rather than re-deriving the queries by hand.

**UI application-workflow tracking (2026-07-04):** `items.application_status`
(null | saved | not_interested | applied | callback | interview | offer) plus
`not_interested_reason` and `status_updated_at` — UI-set, not LLM-tagged. Only
`saved` and `not_interested` are reachable from the UI today (📌 Save /
🚫 Not Interested with fixed one-click reasons + free-text "Other"); the
callback/interview/offer states are schema-ready but have no button yet. See
`HISTORY.md#application-status-workflow` and `TODO.md` section 7 for open
work (applied/callback/interview buttons, scroll-based "seen" tracking,
day/week metrics, visual redesign). Thumbs up/down (`feedback` column) are
hidden in the UI — kept for a possible later ranking-feedback loop, not read
by the ranker. One app (`ui/app.py`), not split into eval/workflow UIs.

**Design decision to preserve:** freelance/project-based preference is a
*ranking* signal (`engagement_weights` in the ranker), not a sourcing
filter — scrapers and role-slug lists should keep covering full-time roles
too; don't narrow sourcing in response to the freelance-first ranking
profile.

**Environment:** `.venv` (Python 3.12), deps in `requirements.txt`. Run via
`export PYTHONPATH=src` (or set on Windows) then `python -m pipeline.<module>`.
UI: `streamlit run src/pipeline/ui/app.py`.
