# History

Full narrative detail behind each `CHANGELOG.md` entry — what was tried, bugs
found, live-test results, numbers. `CHANGELOG.md` is the short index; this is
the deep-dive. Newest entries at the top.

---

## 2026-08-27 — Batch API 413 fix, first full-backlog tagging run since the cost cut {#batch-413-fix}

The author asked to run the full pipeline (scrape -> tag -> rank) after ~7 weeks
idle since the July 6 capstone submission. Full ingest landed 15,293 new
items (44,319 total). Ran a 200-item tagging test batch first to get a real
cost number ($0.9535, all realtime/Haiku, 0 Sonnet escalations -- this
predates the same-day cost-cut commit landing) before committing to the
~15k-item backlog; the author asked to hold for the cost-cut work in flight
elsewhere, then gave the go-ahead once `c033130` (see
[[tagger-cost-cuts]]) was committed.

First full-backlog run failed immediately: `run_batch_tagging` built one
Message Batches API request for all 15,222 rows and hit Anthropic's 256MB
per-request cap (`413 Payload Too Large`) before any tagging happened -- the
cost-cut commit's live test only verified a 4-item batch, which never
exercised size limits at backlog scale. No data lost (failed pre-submission),
but the bug blocks any full-backlog run going forward, not just this one.

**Fix:** added `MAX_BATCH_SIZE = 500` and a `_run_batch_chunked` helper in
`batch_tagging.py` that submits/polls/collects sequentially in 500-item
chunks instead of one all-at-once submission, for both the main tagging pass
and the confidence-escalation pass. 500/chunk is a conservative margin given
raw text can run up to 12,000 chars/item (`RAW_TEXT_CHAR_LIMIT`,
[[raw-text-truncation-cap]]).

**Verified live:** full 15,222-item backlog across 31 chunks, 15,215 tagged /
7 failed (JSON parse errors on ambiguous items -- not systemic, consistent
with the project's existing "spot-check, don't over-validate" stance, see
CLAUDE.md's Error handling philosophy). Total cost **$17.54** ($0.003 +
$17.5381 across two run_log rows) -- lines up with the batch-lane 50%
discount plus prompt caching versus the ~$73 extrapolated from the pre-cost-cut
realtime-rate test batch, roughly a 4x reduction. 87 items escalated to the
Sonnet tier via the second batch round.

Ran the ranker afterward (`python -m pipeline.ranker.rank`) to score all
newly tagged items; 43,677 of 44,319 items now have `preference_score` (gap
is untagged/failed items). Top-ranked results looked sane on inspection
(DevRel/AI/ML roles at the top, consistent with the locked preference
weights from [[relevance_ranking_rework]]).

**Process note:** two other sessions (`session-a` wiring Telegram
notifications, `session-b` building an MCP server) were active in this same
shared working directory concurrently. A background tagging run's scratch
log file and process were lost mid-run -- likely collateral from another
session's git/file operations in the shared directory, since all sessions
share one working tree with no per-session isolation. Relaunching with the
log written outside the repo directory (`%TEMP%`) avoided a repeat. Worth
keeping in mind for any future long-running background job here: don't put
scratch state inside the repo path if another concurrent session might touch
it.

---

## 2026-08-26 — Tagger cost cuts: prompt caching, Batch API, fast/slow lanes {#tagger-cost-cuts}

User asked for cost-cutting advice on the tagger ("batching, vectorizing etc").
Read the actual tagger code first rather than giving generic advice — found
per-item calls with no caching, no batching, and the full system prompt +
few-shot examples resent in full on every single call. Recommended, in
priority order: (1) prompt caching on the static system+examples block, (2)
Anthropic's Message Batches API (50% off input+output) for the non-realtime
lane, (3) folding few-shot examples into the cacheable block (they were
previously rebuilt into the *user* message every call, which is never
cacheable), and a possible (4) cheap junk pre-filter -- flagged as probably
not worth it pending a real number. Explicitly left "vectorizing/embeddings"
out as inapplicable: this is a full-text extraction task per posting, not a
similarity-search problem, and dedup already happens pre-tagging.

User confirmed 1+2, asked to fold in 3, asked to add a fast lane for
company-whitelisted items (want faster tagging for postings where applying
quickly plausibly matters), and asked to investigate the junk-filter idea
concretely rather than assume.

**Junk pre-filter decision:** queried the live DB before building anything --
`SELECT spam_risk, COUNT(*) FROM items GROUP BY spam_risk` returned 83
`likely_spam` and 905 `suspicious` out of 27,536 spam-risk-tagged rows (0.3%
and 3.3% respectively). Not worth building a pre-filter or a second
spam-specific doublecheck pass for that little volume, especially given the
false-negative risk (a pre-filter could silently drop a real posting). The
existing Haiku->Sonnet confidence escalation already serves as a general
quality doublecheck; a spam-specific one would be redundant machinery for a
sub-1% problem. Not built -- noted here so it isn't re-proposed without new
evidence the volume has grown.

**What shipped:**

1. **Prompt caching** (`prompts.py`, `providers.py`) -- `build_system_prompt`
   (dated instructions/schema/enums) and `build_examples_block` (few-shot
   examples, now genuinely static -- previously rebuilt into the *user*
   message on every call, which defeats caching since user content always
   differs) are combined into one `cache_control: {"type": "ephemeral"}`
   content block via `providers.build_cached_system_blocks`. Only the per-item
   `raw_text` remains in the dynamic user message.

2. **Real bug found live-testing #1:** the combined block came in at ~2,657
   tokens and silently never cached -- `cache_creation_input_tokens` and
   `cache_read_input_tokens` were both 0 on every call, with no error (this is
   documented Anthropic behavior: below the model's minimum cacheable length,
   caching is skipped silently). Spent real debugging time isolating this,
   including several false leads (temperature, request ordering, block
   splitting) before confirming via a controlled token-count bisection that a
   4,156-token block cached correctly while a 3,416-token block of otherwise
   near-identical content didn't. Confirmed via Anthropic's docs: **Haiku
   4.5's minimum cacheable prompt is 4,096 tokens** -- not the 1,024 (Sonnet/
   Opus-class) or 2,048 (Haiku 3.5, retired) figures that are more commonly
   cited/assumed. `MODEL_PRICING`'s existing per-model precedent (schema.py's
   per-model behavior differences, e.g. Haiku erroring on `output_config.effort`)
   should have been a hint that Haiku-specific quirks are common enough to
   check for, not assume away.

   Closed the ~1,440-token gap with genuinely useful content rather than
   padding: 3 new few-shot examples (a part-time staff+ role at a biotech
   series-A company, a low-content/suspicious ops posting, a networking-event
   edge case) plus a new "ADDITIONAL DISAMBIGUATION NOTES" section in the
   system prompt covering real enum-boundary confusions not previously
   spelled out (founding-engineer title vs role_category, recruiter/agency
   postings vs spam_risk, equity-only comp vs spam_risk, data_scientist vs
   data_analyst, devops_infra_engineer vs software_engineer, ai_ml vs
   ai_research, multi-location/multi-seniority-band postings). Final block:
   4,150 tokens. Verified live via 3 back-to-back calls through the actual
   production `AnthropicTaggerClient.complete()` path: call 1 shows
   `cache_creation_input_tokens=4143`, calls 2-3 show `cache_read_input_tokens=4143`
   and `cache_creation_input_tokens=0` -- cache write then reads, confirmed.

3. **Batch API lane** (`batch_tagging.py`, new file) -- submits items via
   `client.messages.batches.create`, polls `batches.retrieve` every 60s (6h
   safety cap -- well under the API's up-to-24h SLA but generous for a
   once-nightly scheduled job), then parses `batches.results` through the same
   JSON-parsing/Pydantic-validation logic as the realtime path (extracted to
   `tag_item.parse_model_json` so both lanes share one implementation).
   Escalation (confidence < 0.7) runs as a **second** batch round-trip after
   the first batch's results are in, rather than inline per-item like the
   realtime path -- still far cheaper than realtime for the items that don't
   need to be fast. `run_tagging.py`'s `_call_cost` now takes an `is_batch`
   flag applying the 50%-off `BATCH_DISCOUNT` so cost-tracking metrics stay
   accurate per lane.

   Verified live against 4 real untagged DB rows end-to-end: submit -> 4 poll
   cycles -> results retrieval -> parse -> DB write, `{'tagged': 4, 'failed': 0}`,
   lock file released cleanly afterward.

4. **Fast/slow lane split** (`tag_item.py`) -- `FAST_LANE_COMPANY_WHITELIST`
   (currently empty, author-edited plain set, not a DB-editable preference
   like the ranker's weight tables -- this is a short curated list, doesn't
   need UI/query access) matched against `items.author` via the same
   squash-to-alphanumeric normalization as `db.normalize_dedup_key`, so ATS-
   slug names and human display names both match. `run_tagging.py` splits
   untagged rows into `fast_rows` (realtime per-call API, same as the
   pre-existing behavior, still benefits from caching) and `batch_rows`
   (Batch API lane) before tagging, and reports `fast_lane_count`/
   `batch_lane_count` in `record_run` metrics for visibility. **Action item
   for the author:** the whitelist is currently empty, so every item routes
   to the batch lane until real company names are added to
   `FAST_LANE_COMPANY_WHITELIST` in `tag_item.py`.

**Left as an explicit TODO, not built:** reducing escalation *rate* (vs.
escalation *cost*, which caching+batching already address) -- a
`GROUP BY source, tagger_model` query would show which sources drive Sonnet
spend, and a targeted prompt fix for a specific source might cut escalations
more cheaply than further infra changes. Noted as a possible future
cost-saver, not scheduled.

---

## 2026-08-26 — Scraper fetch parallelization {#scraper-fetch-parallelization}

User asked (mid-wait on a live scrape run that was taking a long time):
"advise on ways to shorten each scan (can we run anything in parallel e.g.
separate the apify calls by search term?)". Investigated the actual
bottleneck rather than guessing — found the entire ingest path was
serialized end to end despite every unit of work being independent.

**Where the time was actually going:**
- `ingest.py`'s `run_ingest()` looped over all ~20 sources with a plain
  `for` loop, `await`ing each source's fetch in turn — even though each
  source's `fetch_fn`/`normalize_fn` pair is fully independent and writes
  go through `WriterQueue`, a single-writer coroutine explicitly designed
  for concurrent producers (per `CLAUDE.md`'s stated architecture).
- `linkedin_apify.py` and `wellfound_search_apify.py` each run their own
  internal multi-query fan-out (4 search URLs / 4 role slugs) via a
  sequential `for` loop calling `ApifyClient.actor().call()`, which blocks
  synchronously until that actor run finishes — this was the specific
  pattern the user's question named directly.
- `greenhouse.py`, `ashby.py`, and `vc_portfolio.py` — not initially
  suspected, found by checking every scraper with a per-board/per-query
  loop — had the same shape at much larger scale: Greenhouse alone loops
  over 248 board tokens one HTTP GET at a time; Ashby ~27 boards;
  `vc_portfolio.py` nests 7 boards x 13 keywords x up to 10 paginated
  requests each (91 independent pagination chains, each throttled with its
  own `REQUEST_DELAY_SECONDS = 0.3` sleep between every request) — this was
  likely the single largest contributor to total scan time, confirmed live
  by watching the in-flight scrape's log reach `vc_portfolio` and grind
  through combo after combo before moving on.

**What shipped:**
1. `ingest.py` — `run_ingest()`'s per-source loop replaced with
   `asyncio.gather()` over a per-source `_fetch_and_queue()` coroutine; each
   source's own fetch still runs in a thread via `asyncio.to_thread` (needed
   for sync Playwright sources), but sources no longer wait on each other.
2. `linkedin_apify.py` / `wellfound_search_apify.py` — internal query
   fan-out switched from a sequential `for` loop to
   `ThreadPoolExecutor`/`as_completed`, one worker per query (4 workers —
   small, fixed fan-out size).
3. `greenhouse.py` / `ashby.py` — per-board fetches switched to a
   **bounded** `ThreadPoolExecutor` (`BOARD_FETCH_WORKERS = 20`) rather than
   unbounded, specifically to stay a considerate scraper against a shared
   public API at 248+ boards rather than firing everything at once.
4. `vc_portfolio.py` — parallelized at the (board, keyword) level (91
   independent chains, bounded pool `QUERY_FETCH_WORKERS = 10`) while
   keeping pagination *within* each chain sequential, since each page
   genuinely depends on the prior page's `meta.sequence` cursor and can't be
   parallelized without changing the API contract.
5. `lever.py` — deliberately left alone; only 5 companies, not worth the
   diff.

**Verified live** against real (not mocked) endpoints, since a change here
is easy to get subtly wrong (shared mutable state across threads, dedup
logic reading a set built by multiple threads, etc.) and the project's
stated testing stance is real data, not mocks:
- Ashby: 5 real boards (openai, notion, harvey, cohere, linear) → 1,410
  items in 1.3s, all 5 fetches started at the same timestamp in the log
  (confirming true concurrency, not just non-blocking dispatch).
- Greenhouse: 10 board tokens (4 wrong/404 guesses included on purpose, to
  check per-board failure isolation) → 2,106 items from the 6 valid boards
  in 1.4s; the 4 failing boards logged individually and didn't affect the
  others' results, confirming the per-board try/except still isolates
  failures correctly under threading.
- Did not live-test the Apify-backed changes (LinkedIn/Wellfound search) or
  vc_portfolio against real paid/rate-limited calls during this pass — a
  separate full ingest run was already live-in-progress on Windows at the
  time (see the Mac mini migration entry below) and duplicating those calls
  purely to test would have doubled real spend for no need; syntax-checked
  instead and the logic mirrors the already-verified Ashby/Greenhouse
  pattern closely enough to trust without a second paid run. Correctness of
  the Apify/vc_portfolio paths will get real-world exercise on the Mini's
  first live nightly run under the new code either way.

**Not changed / considered and rejected:** the tagger's own concurrency
(`run_tagging.run(concurrency=15)`) was already deliberately tuned against
real rate-limit headroom in an earlier session — left as-is, no reason to
revisit here. `raw_writer.py` isn't in the timed hot path (only called from
each scraper's standalone `main()`, not from `fetch_raw()` itself).

---

## 2026-08-26 — Scheduler moved to the Mac mini {#scheduler-moved-to-mac-mini}

User asked for advice on a "reasonable schedule to balance cost and
resources with fairly good coverage." Investigation found the nightly
scheduler (`scheduler.py`, built 2026-07-03) was already fully designed —
fixed 3:30am `CronTrigger`, one job per source, tag+rank 15 min later,
history purge 30 min after that — but **never actually running**: the
Windows Task Scheduler registration script
(`scripts/register_scheduler_task.ps1`) needed elevated/admin PowerShell,
which the working session never had, so `Register-ScheduledTask` returned
Access Denied when tried 2026-07-03 and was left unregistered since.

**Decision to move to the Mac mini instead of just fixing the Windows
registration** came from the user directly, once the Windows blocker was
explained — the Mini is always-on, avoiding both the admin-elevation
problem and the separate Windows sleep/wake `SessionStateChangeTrigger`
workaround `CLAUDE.md` already documents as a known gotcha for this kind of
long-running daemon.

**What was actually blocking the move, found by checking rather than
assuming:** the Mini's existing clone (present from an earlier backfill
pass) was **9+ commits stale** (`master` at `0f82385` locally vs. Mini's
`origin/master` also at `0f82385` — the real gap was that 18 local commits
on the working branch, `overnight-pass-2026-07-04`, had never been pushed
to GitHub at all), and had **no `pipeline.db` whatsoever** — the live
28,893-item (at the time) database only ever existed on Windows. Also
missing on the Mini: Gmail OAuth files (`credentials.json`/`token.json`,
needed for the `handshake_email` source) and most optional per-source env
var overrides (only `ANTHROPIC_API_KEY`/`APIFY_API_TOKEN` were set).

**What shipped, in order:**
1. Pushed the local branch to `origin/master` (clean fast-forward, no
   conflicts — confirmed via `--dry-run` first since force-pushing to
   `master` is exactly the kind of action that warrants a confirm-first
   pause).
2. `git pull`led the Mini current, `pip install -r requirements.txt` in its
   venv (already mostly populated from an earlier session; only
   `openai`/`httpx2`/etc. needed installing, for the stubbed GLM tagger
   provider path).
3. Copied `credentials.json`/`token.json` (Gmail OAuth) via `scp` — flagged
   by the harness's auto-mode classifier as a secrets transfer needing
   explicit confirmation first, which the user gave.
4. **`scheduler.py`**: added `DAILY_TRIAL_END = datetime.date(2026, 9, 9)`
   — every source stays on the existing daily cadence for a **deliberate
   2-week trial**, not a calibrated final decision. This was a direct user
   call, made while reasoning through the cadence question live: real
   per-pull Apify cost (~$0.20/pull LinkedIn, ~$0.03/pull Indeed — both
   already documented in `docs/SOURCES.md`'s 2026-07-04 cost research, well
   under the user's stated $5/pull threshold) meant cost wasn't actually
   the binding constraint the way it first seemed — the real open question
   is miss-rate/freshness, which can only be answered from real repeated-
   poll data. `DAILY_TRIAL_END` doesn't stop the scheduler once it passes;
   it just logs a loud warning on every source-ingest job past that date so
   the still-daily cadence can't silently be forgotten. Analysis plan
   post-trial (documented in `TODO.md` 3b): pull `run_log` (`stage='ingest'`)
   per source, simulate keeping only every-Nth day's run against real
   `items.fetched_at` insert counts, and set real per-source
   `SOURCE_INTERVAL_HOURS` values from actual miss-rate numbers instead of
   the original single-snapshot guess.
5. Waited for an already-in-progress full ingest scrape on Windows (not
   started by this session — found running when the DB-sync step was
   reached, real LinkedIn Apify spend mid-flight) to finish on its own
   before touching `pipeline.db`, rather than risk an inconsistent
   snapshot or wasted spend by interrupting it. Checked back periodically
   (`ScheduleWakeup`) rather than blocking synchronously.
6. Once finished: `PRAGMA wal_checkpoint(TRUNCATE)` to fold the WAL
   cleanly, `PRAGMA integrity_check` (`ok`), `scp`'d `pipeline.db` to the
   Mini, re-ran both checks there — byte-identical file size
   (815,640,576 bytes) and matching item count (44,319) on both sides
   confirmed a clean transfer.
7. launchd agent `~/Library/LaunchAgents/com.jjcho.jobspipeline.scheduler.plist`
   (`RunAtLoad` + `KeepAlive.Crashed` for restart-on-crash without fighting
   a deliberate clean stop, stdout/stderr to `data/scheduler.log`/`.err.log`)
   — `launchctl bootstrap`'d and confirmed running (`state = running,
   last exit code = (never exited)`). First load failed with
   `ModuleNotFoundError: No module named 'pipeline.notifications'` because
   a concurrent session's Telegram-notification commits existed locally but
   hadn't been pushed yet either — pushed again (now including scraper
   parallelization work too), pulled on the Mini, reloaded the agent
   cleanly.

**Left open, not done this session:** `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID`
aren't set in the Mini's `.env` yet (that feature landed on a different
session mid-flight during this same work) — `notifier.py` degrades
gracefully (logs a warning, returns `False`) rather than breaking the
scheduler, so nothing is broken, but the Mini's nightly runs won't push
Telegram digests until those two keys are copied over. `scripts/register_scheduler_task.ps1`/`run_scheduler.bat` are left in the repo
unused rather than deleted, in case Windows-side scheduling is ever wanted
again. Windows's local `pipeline.db` is now a point-in-time secondary copy,
not kept in sync going forward — the Mini is the source of truth.

**Coordination note:** two other sessions were active in the same repo
during this work (`session-a` building the Telegram notifications above,
`session-b` building a read-only MCP server for external DB access) — handled
via cross-session messages rather than silently editing shared files:
confirmed no file overlap before editing `scheduler.py`, flagged when
`scheduler.py` itself would see concurrent edits from both sessions, and
told `session-b` explicitly when `pipeline.db` was and wasn't safe to point
their MCP server's read path at (mid-transfer vs. verified-landed).

---

## 2026-08-26 — Telegram run-summary notifications {#telegram-run-summary-notifications}

User asked directly: "do we have notification built in? if not can we wire
this to my telegram bot (see my other Telegram/Claude gateway project, or e.g. code/kashi for
implementation--feel free to copy keys from there)". Notifications were
listed as "not started, deferred per first-pass scope" in `CLAUDE.md`/
`TODO.md` section 8 — confirmed nothing existed before starting.

**Scope narrowed by the author before building.** Initial framing
(`AskUserQuestion`) offered per-item high-priority alerts vs. a batched
digest. Author's actual answer: build the high-priority-item framework but
leave it **dormant** — for now, just a message whenever a large scrape
happens, with basic run metrics (items scraped, cost, remaining API credit
if available, errors). Threshold for a future per-item alert: "I'll figure
this out later — probably a whitelist of very reputable companies." So the
live path is a run-summary digest, not a ranking-based alert.

**Reused the other project's bot token instead of creating a second bot.**
Checked the author's separate personal Telegram/Claude gateway project (a
self-hosted Docker Telegram/Claude gateway) — its `.env` already had a real
`TELEGRAM_BOT_TOKEN`. `code/kashi` (also named in the request) doesn't
exist on this machine — only that other project did. That project itself
is a full conversational agent (Docker gateway + dashboard, Claude-backed
persona) — overkill for a one-way push, so this project only borrows the
bot token via a plain `requests.post` to Telegram's Bot API `sendMessage`
endpoint (`notifications/telegram.py`), not any of that project's
framework.

**What shipped:**
1. `src/pipeline/notifications/telegram.py` — `send_telegram_message(text)`,
   thin wrapper around `POST /bot<token>/sendMessage`. Returns `False`
   (logged, not raised) if `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID` are unset
   or the request fails — a notification failure must never break the run
   it's reporting on.
2. `src/pipeline/notifications/notifier.py` — `notify_run_summary()` reads
   `run_log` rows from the last 2 hours (wide enough for one nightly
   ingest+tag+rank cycle, narrow enough not to pull in the prior night's
   run) and builds one digest: per-source fetched/inserted counts, tagging
   cost (`cost_usd` from `run_log`'s `tag` stage — already tracked, no new
   instrumentation), items ranked, and any `status='error'` rows. No
   API-credit-remaining figures — neither Anthropic nor Apify expose a
   reliable balance endpoint, and guessing at one would be worse than
   omitting it.
   `notify_high_priority_items()` is a deliberate stub that raises
   `NotImplementedError` rather than silently no-op-ing, so an accidental
   call surfaces immediately instead of looking like it worked. Do not
   implement its whitelist logic without the author providing one.
3. `scheduler.py` — one hook: import + a 4-line try/except calling
   `notify_run_summary()` at the end of `_run_tag_and_rank`, after the
   existing ranking try/except. Minimal diff by design — a second session
   (`session-c`) was mid-edit on the same file (moving the scheduler to the
   Mac mini, adding the `DAILY_TRIAL_END` cadence-trial guard) at the same
   time; coordinated via cross-session messages first to confirm no
   structural collision, and the hook landed cleanly inside their commit
   (`4de1826`) since both sessions shared the same working tree/branch.
4. `.env.example` — documented `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID`,
   noting to copy the token from the other project's `.env` rather than
   provisioning a new bot.

**Getting a real `TELEGRAM_CHAT_ID`.** Telegram's Bot API only exposes a
chat's numeric id via `getUpdates`, which only returns messages sent to the
bot that haven't already been consumed/expired. First `getUpdates` call
came back empty (`pending_update_count: 0`, no webhook set) — likely
because a prior test message was outside Telegram's update retention
window. Asked the author to send the bot a fresh message; the follow-up
`getUpdates` call returned it immediately (`chat.id = 8513297579`), which
was written into `.env`.

**Live-tested, not just unit-tested.** `build_run_summary_text()` run
against the real DB mid-session picked up `session-d`'s concurrent live scrape
run correctly (133 new items across `remoteok`/`weworkremotely`). Then
`python -m pipeline.notifications.notifier` sent one real message to the
author's Telegram, confirmed received.

**Multi-session coordination note (not a code change, but relevant
process):** this session (`session-a`) found two other sessions
(`session-c`, `session-d`) already active in the same `~/code/jobs` working
directory via `ListAgents`, and a third (`session-b`) started mid-task to
build an MCP server over the same DB. All four messaged each other via
`SendMessage` to confirm no file/DB collisions before proceeding, per the
multi-agent team protocol in the global `CLAUDE.md`. No roster file exists
yet for this fleet (`~/code/team/ROSTER.md` is still just the template) —
cross-session messaging carried the coordination instead.

---

## 2026-07-05 — AI-Trainer-gig derank fix {#ai-trainer-derank-fix}

Follow-up on the stretch item logged in `TODO.md` section 5b (never
started). User asked directly: did we start a fix, would fixing it require
re-tagging everything (~$100), and should items just be deranked manually
or left as-is for the capstone demo.

**Diagnosis first.** Queried the live DB before touching anything: 280
items with "AI Trainer"/"AI Training" titles, all already tagged,
`category=job` for all of them — not a tagging gap. The real problem:
**36 of the top 50 items by `preference_score` were AI-Trainer/data-labeling
contractor gigs.** Root cause matched the DevRel proposal's earlier finding
(`HISTORY.md` DevRel entry) — `role_category`/`role_type` isn't in the
weight stack at all today. These gigs were topping the rankings purely by
stacking `engagement_type=freelance` (1.5x) × `seniority=junior/mid`
(1.2-1.3x) × `remote_type=remote` (1.3x) × `industry=ai_ml` (1.4x) — weights
designed to surface real freelance AI engineering work, not Scale-AI-style
RLHF-rater/annotation gigs that happen to share those same tag values.

**Cost question answered directly:** no re-tag needed. None of the existing
5 weight tables or `content_quality` needed to change — this is a new,
orthogonal signal. Went with the "full schema addition" option (vs. a
backfill-only column) since the user wants this classified correctly by the
tagger going forward too, but paired it with a free regex backfill for
already-tagged rows rather than spending API budget re-tagging them.

**What shipped:**
1. `tagger/schema.py` / `tagger/prompts.py`: new `role_category` enum value
   `ai_data_labeling` (AI-Trainer/data-annotation/RLHF-rater contractor
   gigs, distinct from `ml_ai_engineer`), so future tagging calls classify
   these correctly without a script.
2. `storage/db.py`: new `preference_profiles.role_category_weights` column
   (6th weight dimension) via the same `_migrate_*`/`COALESCE` pattern as
   the other 5 weight tables; `DEFAULT_ROLE_CATEGORY_WEIGHTS = {"ai_data_labeling": 0.15}`
   — every other `role_category` value stays neutral (1.0), this is a
   narrow derank, not a general role_category preference weight.
3. `ranker/scores.py` / `ranker/rank.py`: wired the new weight table into
   `preference_multiplier` and `_get_active_profile`.
4. `tagger/backfill_ai_data_labeling.py` (new): one-off regex backfill —
   matches `AI Train(er|ing)`, `Data Annotat(or|ion)`, `Data Label(ing|er)`,
   `RLHF` against `title`/`role_type` on already-tagged items, sets
   `role_category='ai_data_labeling'` via direct SQL `UPDATE`. No LLM call.
   Dry-run first (294 matches, spot-checked the full list — zero false
   positives, caught title variants beyond the original 280 "AI Trainer"
   count, e.g. "Data Annotation Specialist, Arabic Language Najdi/Hijazi
   Dialect", "Financial Advisor - AI Trainer"), then applied for real.

**Verified end-to-end:** ran `init_db()` to apply the migration, ran the
backfill (294 items updated), re-ran `python -m pipeline.ranker.rank`
(recomputes scores for all tagged items, no LLM cost). Top 20 by
`preference_score` is now real engineering/product roles (ML Engineer,
Founding Research Engineer RL/Reasoning, Robot Learning Residency, AI
Backend/Frontend Engineer, Founding AI Engineer, etc.) — confirmed via a
direct query that **0 of the new top 50** are `ai_data_labeling` items,
down from 36/50 before the fix.

**Answered the "leave as-is" question:** recommended deranking rather than
presenting unchanged, since 36/50 top-ranked items being contractor
data-labeling gigs reads as an unfixed bug rather than a deliberate
preference choice, and undercuts the demo's "ranker reflects real
preference" pitch. Framed as a good demo beat — eval surfaced a real
ranking issue, targeted fix applied and verified, not hidden.

**Known residual gap:** the regex is title/role_type-based; a posting whose
title doesn't mention any trigger phrase but is genuinely a data-labeling
gig in body text only would still slip through. Not chased further this
pass — 294/294 known-pattern cases matched, zero false positives, and the
top-50 result is already clean.

---

## 2026-07-05 — AI usage citation pass {#ai-usage-citation-pass}

Full per-file AI usage citation reconstruction for the capstone submission
requirement (syllabus: "How to Cite AI Usage" — per-file code comment plus a
consolidated statement). Method and two worked examples had already been
designed in a prior session (`docs/ai_usage/CITATION_METHOD.md`); this pass
executed the full run across all 41 `.py` files under `src/pipeline/` (45
counting `__init__.py` markers).

**Classification pass.** Grepped all 67 (later 69, as sessions kept
running) `.jsonl` transcripts at
`C:\Users\jjcho\.claude\projects\C--Users-jjcho-code-jobs\` for
Write/Edit/MultiEdit `tool_use` records targeting each file, bucketing into
single-event (15 files) vs. multi-event (26 files). 4 files
(`builtin_sf.py`, `indeed_rss.py`, `hn_whoshiring.py`, `luma_events.py`,
`wellfound.py` — 5 once found) showed zero or partial direct Write/Edit
history despite clearly existing in the repo with real git history.

**Sub-agent discovery.** Investigating the gap found these files were
created not by a direct Write in the main session transcript, but by a
**sub-agent spawned via the `Agent` tool** from the original 2026-06-24
scaffold session (5 parallel scraper-build agents dispatched around
08:39-09:19 that morning: HN Who's Hiring, Indeed RSS, Luma events,
Wellfound, Built In SF). A top-level-only transcript scan is blind to this
— the sub-agent's own Write calls live in a separate nested transcript
context not captured by grepping the parent session's `tool_use` records
for `Write`/`Edit`. Had to add a second scan specifically for `Agent`
tool_use events whose `prompt`/`description` field named one of the target
files, which surfaced all 5 (confirmed no other sessions used the `Agent`
tool to build a source file). The sub-agent prompts themselves were fully
recoverable verbatim from the `Agent` tool_use's own `input.prompt` field —
same citation standard as a direct Write, just a different discovery path.

**Extraction script bugs found and fixed along the way:** a `parentUuid`
chain-walker crashed on a Windows console Unicode-encoding error (an arrow
character in a real prompt); an early version walked back and collected
*every* real user message in the chain rather than stopping once a
substantive one was found, which pulled in entire injected skill-doc texts
(e.g. a `/loop` skill's full parsing-rules body) and produced multi-hundred-KB
output files. Fixed by capping candidates collected (max 3) and truncating
each to 3000 chars.

**Parallelized drafting.** Given the size (41 files, dozens of sessions),
work was estimated at 20-45+ minutes done serially; user chose to have 4
subagents draft citations in parallel from pre-extracted transcript text
(never given raw transcript access themselves — only the already-walked
candidate quotes — to keep the "never fabricate a quote" guarantee
enforceable by construction, not just by instruction). Each subagent
covered a distinct file batch and was explicitly instructed to state
"no clean prompt attribution could be reconstructed" rather than invent one
when the extracted candidates were empty or pure skill boilerplate. Spot-check
against raw transcripts (a handful of quotes across all 4 batches) found zero
fabrication — every batch honestly flagged its own weak spots (e.g. batch 2's
report: "3 sessions had zero recoverable prompt, 2 surfaced only skill
boilerplate").

**Result:** all 45 files got a short `AI USAGE CITATION` header (tool, prompt
gist, pointer). Full quotes assembled into `docs/ai_usage/prompt_log.md`.
Roughly 8 files (`rank.py`, `scores.py`, `ashby.py`, `handshake_email.py`,
`lever.py`, `vc_portfolio.py`, `wellfound_search_apify.py`,
`yc_workatastartup.py`) had at least one session where no real triggering
prompt could be isolated — most commonly because the chain walk landed on
`/loop`/`claude-api` skill-injected boilerplate or a bare one-word
acknowledgment ("yes", "go ahead") rather than a substantive free-text ask,
not because nothing was ever asked.

**Follow-up requested by the author:** a bare "not recoverable" reads like a
shrug rather than documentation, and the actual transcripts are a stronger
source of truth than any reconstruction. Copied the full un-redacted-except-one-class
transcript set (all 69 `.jsonl` files) into `docs/ai_usage/transcripts/` as
primary-source backing evidence, with a `README.md` explaining what they are
and how to grep them. **Before copying, scanned for secrets** — found a live
Apify API token pattern (46-char `apify_api_...` format, matching the live
key in `.env`) appearing 11 times across 4 transcript files (likely pasted
terminal/dashboard output during scraper-build sessions). Redacted all 11
occurrences to `[REDACTED]` in the copies only; the original unredacted
transcripts remain untouched on the local machine. Verified zero remaining
credential-shaped strings (Anthropic/OpenAI/AWS/Apify/Gmail key patterns,
PEM private-key blocks) in the copied set after redaction. Updated the 8
"not recoverable" headers plus `prompt_log.md`'s framing note to point at
`docs/ai_usage/transcripts/` as the real backing source, rather than
presenting the gap as unrecoverable.

All 45 modified files verified to still `py_compile` cleanly after header
insertion.

---

## 2026-07-05 — Apply toggle, urgency-tab deadline field {#apply-toggle-urgency-deadline}

Live UI testing surfaced two accidental "Apply" clicks (db ids 25950, 25956)
with no real applications behind them — reset both to `application_status =
NULL` directly in the DB (`status_updated_at`/`not_interested_reason` cleared
too), confirmed via `SELECT application_status, COUNT(*) ... GROUP BY` before
and after (2 -> 0 `applied` rows).

**Apply is now a toggle**, matching the existing Save/Unsave pattern:
`render_item()`'s action_cols[1] branch now shows "Unapply" (resets status to
null) when `application_status == "applied"`, instead of only showing a
static "Applied (...)" caption. `callback`/`interview`/`offer` still show as
a plain caption — those states have no button path yet (see TODO.md
Section 7's existing open item on that).

**Urgency fields**: `deadline` was tagged/stored (`items.deadline`) but never
surfaced in the UI at all. Added it to `UI_COLUMNS` so it loads with the rest
of the dataframe, shown inline on item cards when `sort_by == "urgency_score"`
(next to the existing score tag), and added as a column in the Metrics tab's
top-20 table when urgency is the selected sort field. No new DB column or
tagger change needed — the field already existed, just wasn't wired to any
view.

**Open decision, not resolved this pass**: author isn't sure whether
`category`'s `event`/`networking` values should stay filterable from the main
Browse sidebar, given events are a frozen/secondary capability
(CLAUDE.md "Current State"). Logged as an open TODO (Section 7) rather than
guessing at a direction — options are keep as-is, move to a separate tab, or
drop the filter option (underlying data is untouched either way).

---

## 2026-07-04 — DevRel Engineer ranking follow-up: proposal, not applied {#devrel-ranking-proposal}

Overnight unattended pass, item 4. Following up on the Spearman
manual-ranking pass finding that db id 25978 ("DevRel Engineer" at Whissle
AI) ranked 2nd of 18 manually, surprising the author since he hadn't
previously thought of DevRel as a distinct favored category.

**Checked both halves of TODO.md's original either/or framing** ("if
role_category has a slot, this is a weight change; if not, a schema
change") and found the real answer doesn't fit either cleanly: `role_category`
has no DevRel bucket (id 25978 tags `other`), but more importantly **the
ranker doesn't weight `role_category`/`role_type` at all** —
`ranker/scores.py`'s `preference_multiplier()` only has 5 weight tables
(category/engagement/seniority/location/sector/stage — sector being
`industry`), none keyed on role. So there's no existing lever to adjust
either way.

**Why id 25978 ranks highly anyway:** its actual tagged fields
(`engagement_type=freelance` 1.5x, `seniority=junior` 1.3x,
`industry=ai_ml` 1.4x) already stack favorably under the active profile's
existing weights — its high manual rank is fully explained by those three
fields, unrelated to it being a DevRel role specifically. This matters for
what the author should decide: is his interest really DevRel-as-a-category,
or was this one example's appeal actually "freelance + junior + AI," with
DevRel incidental? Only he can answer that.

**Wrote up two options, applied neither:**
- **A — do nothing.** Current weights may already be sufficient if DevRel
  postings happen to co-occur with already-favored engagement/seniority/
  industry values. Risk: a full-time/mid-level/non-ai_ml-tagged DevRel
  posting gets no special treatment today.
- **B — add `role_category` as a real 6th weight dimension.** Would need a
  new `ROLE_CATEGORY_VALUES` enum value (`tagger/schema.py` +
  `tagger/prompts.py`), a new weight table in `ranker/scores.py`'s
  `preference_multiplier()`, and a new `preference_profiles` JSON column —
  same mechanical pattern as the existing 5 tables (see `CLAUDE.md`'s
  "Changing ranking weights" section).

**Retag blast-radius sized for Option B:** live query found 53
already-tagged items with `role_type` text matching devrel/developer-
relations/developer-advocate/developer-evangelist/community-engineer
patterns, currently scattered across 6 different `role_category` values
(36 `sales_marketing`, 11 `other`, 2 null, 2 `software_engineer`, 1
`product_manager`, 1 `ops_admin`) — confirming the LLM already bucket this
role type inconsistently, which a dedicated enum value would fix. 53 items
is small and cheap to retarget-retag (filtered by the same `role_type LIKE`
patterns), not a full 28,893-item backlog re-tag.

Full writeup: `docs/reports/devrel_ranking_proposal_2026-07-04.md`. Nothing
applied to `tagger/schema.py`, `tagger/prompts.py`, `ranker/scores.py`, or
the DB — this is a preference decision for the author to make, per this
pass's instructions.

---

## 2026-07-04 — Scoped coverage-gap estimate {#coverage-gap-estimate}

Overnight unattended pass, item 3. `TODO.md` Priority #1 asked for a rough
"we're likely missing about X%" estimate, explicitly not a fix — no new
sources/companies were added to the live scraper config this pass.

**Method:** picked ~25 candidate AI-relevant SF/remote company slugs across
Greenhouse and Ashby, checked each against the existing `BOARD_TOKENS`/
`BOARD_NAMES` lists before probing, then live-queried the public job-board
APIs (same endpoints the existing scrapers already use, no login/anti-bot
risk). ~16% hit rate (4/25) — consistent with prior Greenhouse/Ashby passes'
finding that slug-guessing has a low success rate. Confirmed-new, live,
not-already-tracked boards: `together-ai` (Greenhouse, 58 jobs), `decagon`
(Ashby, 114), `vanta` (Ashby, 107), `crusoe` (Ashby, 354) — 633 combined
jobs, comparable in scale to several companies already in the DB (OpenAI 719,
Anthropic 397, ElevenLabs 145, Baseten 67, Modal 31, Pinecone 3).

**Rough estimate:** given the low per-guess hit rate and that a quick,
sub-hour probing pass still turned up 4 solidly-sized new boards, a rough
extrapolation against TODO.md's own "top 500-2,000 SF companies" framing
puts the likely uncovered fraction at **60-90% by company count** — wide
and explicitly approximate, not a rigorous audit. Full numbers/method/
caveats in `docs/reports/coverage_gap_estimate_2026-07-04.md`.

**Confirms rather than changes the existing plan:** this doesn't suggest
slug-guessing at scale is the fix — the binding constraint is finding real
company *names* to try (funding databases, event listings, news), same
conclusion TODO.md already had before this pass; this just gives it a number.

**Incidental bug found (not fixed):** `sierra` and `writer` are both already
listed in `ashby.py`'s `BOARD_NAMES` (with comments recording 145/49 jobs at
add-time, matching this pass's live counts of 147/49 — so the boards
themselves are fine and haven't drifted), but both have **zero rows in the
DB** for either token. The scraper module itself isn't the problem; likely
never actually run against `ingest.py` since being added, or a downstream
wiring gap. Not investigated further this pass (tangential to tonight's
scope) — flagged in `TODO.md` section 1 for a quick look before the next
Ashby re-fetch.

---

## 2026-07-04 — Deadline field: found a real internal-target-vs-applicant-deadline example {#deadline-field-internal-target-example}

Overnight unattended pass, item 2. `TODO.md` section 4 flagged that the
`deadline` field had never been checked against a real "we aim to fill this
role by X" internal-recruiter-target posting (as opposed to an applicant-
facing "apply by X" deadline) — every prior check only had applicant-facing
examples or genuine rolling-basis nulls to test against.

**Searched the DB (read-only) for internal-target phrasing** — `raw_text LIKE
'%anticipated start%'`, `'%looking to fill%'`, `'%hire by%'`,
`'%start date of%'`, `'%ideal start date%'`, `'%onboard by%'`, etc. Found real
hits (postdoc/research listings using "anticipated start date" for an
academic-hire-cycle target, one startup co-founder posting talking about
"closing the CTO hire by end of June 2026").

**Case 1 (id 13501, `indeed_apify_old`, "Assistant/Associate/Full Project
Scientist"): tagger handled this one correctly.** The posting has *both* an
internal target ("Anticipated start: Winter/Spring 2026" — a vague season,
not a concrete date, correctly not extracted) and a real applicant-facing
deadline ("Final date: Friday, Jul 31, 2026 ... Applications will continue
to be accepted until this date"). Tagged `deadline=2026-07-31`, which matches
the real applicant-facing final date, not the vague internal target. This is
the good-case outcome the field is supposed to produce.

**Case 2 (id 15877, `wellfound_search`, "CTO / Technical Co-Founder"): found
a real problem.** This is a pre-funding co-founder pitch, not a normal job
posting with an application window. Its only date-shaped text is "We're
closing the CTO hire by end of June 2026. Pre-seed funding target:
July-August 2026" — both of these are internal targets (a hiring-close goal
and a fundraising-close goal), neither is an applicant-facing deadline, and
"end of June 2026" was already in the past relative to today (2026-07-04;
this item was presumably scraped/tagged before that date but the field isn't
timestamped against tagging time). The tagger produced `deadline=2026-08-31`
— a date that doesn't match either quoted phrase (not June 30, not clearly
derived from "July-August"; closest explanation is it took the *end* of the
funding-target range and applied it as if it were an application deadline).
This is a genuine extraction problem: the field conflated an internal
funding-close estimate with an applicant deadline, on a posting that has no
real applicant deadline to extract at all.

**Conclusion:** the field's core design (single ISO-date-or-null,
"rolling basis" → null) still holds up as the right shape — case 1 shows it
correctly distinguishing an internal target from a real deadline when both
are present in reasonably normal application-process language. The failure
mode in case 2 is narrower than "the field's shape is wrong": it's that
non-standard postings (pre-funding co-founder pitches, informal
recruiting language) can hand the tagger date-shaped text that isn't a
deadline in either sense, and the model reaches for the closest-sounding
number rather than returning null. Reintroducing a "rolling basis" flag
(considered and rejected 2026-07-03) would not have caught this — case 2 has
no rolling-basis language at all, it's a hallucinated date pulled from an
unrelated internal target. Recommend, next time the tagger prompt is
touched: add an explicit instruction that internal targets (start dates,
hiring-close targets, funding-close targets) are NOT `deadline` values and
should produce null unless the text also states an applicant-facing
apply-by/review-by date. Not applied automatically this pass — a prompt
change should be tested against a small batch before trusting it, and this
pass's hard constraint was no bulk tagging calls.

---

## 2026-07-04 — Tagger provider abstraction (GLM 5.2 groundwork) {#glm-provider-abstraction}

Overnight unattended pass, item 1. Goal: after a GLM API key is added
post-submission, switching the tagger's provider should be a one-line env var
change, not a code change. Anthropic stays the default/active provider
tonight — no bulk API calls, no provider switch.

**What was hardcoded before:** `tag_item.py`'s `_get_client()` instantiated an
`Anthropic` client directly; `HAIKU_MODEL`/`SONNET_MODEL` constants and
`_call_model()`'s request/response shape (Anthropic's `messages.create`,
`response.content[0].text`, `response.usage.input_tokens`) were Anthropic-specific
throughout `tag_item()`'s escalation logic.

**What was built:** `src/pipeline/tagger/providers.py` defines a `TaggerClient`
ABC with one method, `complete(system_prompt, user_message, tier) ->
CompletionResult`, plus a `ModelTier` dataclass (model/temperature/max_tokens)
and each client exposes `default_tier`/`escalation_tier` attributes. Two
implementations:
- `AnthropicTaggerClient` — today's behavior moved here unchanged, including
  the Sonnet-only `output_config={"effort": "medium"}` escalation quirk.
- `GLMTaggerClient` — stubbed against GLM's OpenAI-compatible chat-completions
  API (uses the `openai` SDK pointed at Zhipu's `base_url`, per
  docs.z.ai/api-reference — this compatibility is the one thing actually
  verified via docs, not assumed). Everything else about it is a placeholder:
  model ids (`glm-4.6-flash`/`glm-4.6-plus`), the escalation-tier
  reasoning-effort param (left unset rather than guessing a name that might
  error the same way Haiku errors on Anthropic's `effort` param), and pricing
  (no number found confidently via web search this pass, left as an explicit
  TODO rather than invented).

`tag_item.py` now calls `providers.get_tagger_client()` once and drives its
`default_tier`/`escalation_tier` through the same confidence-escalation logic
as before — `tag_item()`'s public signature/behavior is unchanged.
`TAGGER_PROVIDER` env var (default `anthropic`) selects the provider, read
once via a small factory (`_PROVIDERS` dict + cached singleton), not scattered
`if provider ==` checks.

**Verified live:** ran the existing `python -m pipeline.tagger.tag_item`
smoke test after the refactor (one real Anthropic API call, the one exception
to tonight's no-bulk-spend constraint) — output unchanged from pre-refactor
behavior (same JSON shape, `model=claude-haiku-4-5-20251001`, sensible
tag values for the fixed sample posting). Confirms the refactor didn't break
the live path.

**Not done / explicitly left as stubs:** GLM path is entirely unverified
against a real account (no key available). `run_tagging.py`'s `MODEL_PRICING`
table has no GLM entry — cost logging will show $0 for GLM calls until real
per-token rates are added. `openai` package added to `requirements.txt`
(was already present transitively via some other dependency, now declared
explicitly since `providers.py` imports it directly for the GLM path).

**To flip on:** add a real key to `.env`'s `GLM_API_KEY`, set
`TAGGER_PROVIDER=glm`, re-run the `tag_item.py` smoke test to confirm the
stub's assumptions (model ids, response shape) hold before trusting it for
anything real. See `TODO.md` section 4 for the full list of what's still
unconfirmed.

---

## 2026-07-04 — Application-workflow tracking + UI performance pass {#application-status-workflow}

Prompted by two rounds of live feedback on the Streamlit UI: first that page
reloads (including the thumbs up/down buttons) were slow, then a request to
replace thumbs up/down with an actual save/apply workflow.

**Perf pass 1 (query trimming).** `load_items()` was doing `SELECT * FROM
items` — pulling `raw_json` (~276MB across ~28,893 rows) and the full
`raw_text` (~154MB) into memory on every 30s cache refresh, even though the
UI only ever shows `raw_text` truncated to 1000 chars and never touches
`raw_json` at all. Trimmed the query to only UI-used columns and added
`SUBSTR(raw_text, 1, 1000)` in SQL. Tradeoff surfaced and confirmed with the
author: the Browse search box now only matches the first 1000 chars of a
posting, same as what's displayed — acceptable since search already matched
what you could see, not the full body.

**Feedback-button investigation.** The thumbs up/down buttons wrote to a
`feedback` column that nothing reads — no ranking logic, no filter, no
digest ever consumed it. Every click also called `st.cache_data.clear()` +
`st.rerun()`, forcing a full ~29k-row re-fetch for what should've been a
single-cell UPDATE. First pass (superseded below) patched the cached
DataFrame in place instead of clearing the cache.

**First workflow-tracking design (superseded same day).** Initially added
two independent boolean columns, `saved` and `hidden`, with a Saved tab and
a Hide button — modeled on the existing thumbs-up/down pattern. This
shipped once, including a live-tested `_migrate_saved_tracking`. Before the
next conversation turn, the author clarified the real want: track
`saved`/`applied`/`not_interested` now (with reason capture for
not_interested, to support later per-source pattern analysis — e.g. "does
source X keep surfacing over-senior roles"), plus `callback`/`interview`/
`offer` later, and reconsidered whether hide/save should be independent
booleans at all.

**Final design: single `application_status` column.** Replaced the two
booleans with one status field (null | saved | not_interested | applied |
callback | interview | offer) plus `not_interested_reason` and
`status_updated_at` — confirmed with the author that an item should be in
exactly one state at a time (marking "applied" replaces "saved" rather than
both being true), since that's what makes progress tracking and per-source
analysis a plain `GROUP BY` on one column instead of reasoning about flag
combinations. `_migrate_saved_tracking` was rewritten to add the new
columns and forward-migrate any pre-existing `saved`/`hidden` data (dev/test
safety net; no real user data existed under the old columns yet since they'd
only just shipped).

**Not Interested UX.** Built as a popover with five fixed one-click reasons
(Too Senior, Too Junior, Unrelated Field, Bad Location, Low Pay/Engagement
Type) plus a free-text "Other" — fixed short labels chosen over always-free-
text specifically so `not_interested_reason` stays GROUP-BY-able later, per
the author's stated goal of eventually analyzing sourcing quality from this
data. A "Show items marked Not Interested" checkbox (default off) plus an
"Undo" button on revealed items covers the author's explicit concern about
misclicks needing a way back.

**Scope-split reconsidered and reverted.** Partway through, framed `ui/app.py`
as an "eval/testing UI" with a separate future "Workflow UI" planned — the
author caught this before it could cause confusion for the capstone
submission (an "eval UI" label reads as if it *is* the rubric's evaluation
harness, which is a separate, not-yet-built deliverable — see `TODO.md`
section 6). Reverted; the author isn't sure yet whether the eventual UI
should be one app or several, so this stays one `ui/app.py` for now, with a
"testing" tab as a plausible later addition to the same app rather than a
separate one.

**Perf pass 2 (fragments + pagination).** Confirmed Streamlit 1.58 (installed
version) supports `@st.fragment` (available since 1.37) and `st.rerun(scope=
"fragment")`. Wrapped each tab's body (Browse/Saved/Metrics) in its own
fragment so a click inside one tab — Save, Not Interested, a filter change,
pagination — only reruns that tab's fragment, not the whole script including
the other two tabs' full item lists. This was the actual fix for the
author's stated "near-instant" bar: previously every interaction re-rendered
up to 100 full item-cards (each with a container, expander, and multiple
buttons) three times over (once per tab), regardless of which tab was
visible or what changed. Browse also switched from rendering up to 100 items
per load to paginating 20 at a time with Prev/Next, cutting per-interaction
widget count further. Considered fragmenting individual item cards for even
finer granularity but decided against it for now — tab-level fragments
already remove the main cost (cross-tab re-render), and per-card fragments
would add real code complexity (key-scoping, more state to track) for a
much smaller marginal gain at current item-per-page counts.

**Small requested changes bundled in:** "Digest" tab renamed to "Metrics";
sidebar "Show events & networking" now defaults on (was off) so
event/networking category values are reachable in Browse's Category filter
by default — the author wants to be able to peruse that data even though
category-based filtering is expected to matter less long-term once the
workflow features mature.

**Left for later, explicitly discussed and deferred, not built this pass:**
applied/callback/interview/offer buttons (schema supports them, no UI yet),
scroll-position-based "seen" tracking (Streamlit has no native
intersection-observer hook — will likely need a custom `st.components.v1`
component), a Metrics-tab day/week applied/viewed rollup (blocked on the
above two), not-interested-reason source-quality analysis (blocked on
enough data accumulating), and a full visual/UX redesign (author wants the
whole app to "look nicer and better use space" — explicitly scoped as a
deliberate later pass once the workflow feature set is finalized, so it's
designed once rather than redone). See `TODO.md` section 7 for the full
open-items list.

---

## 2026-07-03 — YC public-directory Greenhouse discovery pass {#yc-directory-greenhouse-discovery}

Follow-up to the same-day company-name-mining pass (158 boards, see
`#greenhouse-company-discovery` below): that pass could only discover
companies already surfacing elsewhere in the DB (`yc_workatastartup`,
`vc_portfolio`). This pass sourced a genuinely new, larger candidate list —
the full public YC company directory — independent of what the pipeline had
already ingested.

**Source discovery.** `ycombinator.com/companies` renders client-side via
Algolia; the page's HTML ships `window.AlgoliaOpts` with a public,
search-only API key (`app: 45BWZJ1SGC`), scoped by the key's own embedded
restrictions to the `YCCompany_production`/`YCCompany_By_Launch_Date_production`
indices and a `ycdc_public` tag filter — i.e., it's a key YC ships to every
anonymous visitor specifically to power this public directory page, not a
privileged credential. Queried directly via `POST
https://45BWZJ1SGC-dsn.algolia.net/1/indexes/YCCompany_production/query`.

**Pagination cap.** The key enforces `paginationLimitedTo=1000` — `page`+
`hitsPerPage` past 1000 total results silently returns empty pages regardless
of the real total (6,004 companies). Worked around by faceting on `batch`
(50 values, YC's cohort field, e.g. "Winter 2022": 398 companies) and
querying each batch separately via `facetFilters`, each well under the 1000
cap — 6,004 unique companies recovered in ~50 sequential requests.

**Candidate generation.** Filtered to `status` in `{Active, Public}` (6,004 ->
4,164), excluded company names already normalized-matching a company already
in the DB (`company` field parsed from `raw_json` across
`yc_workatastartup`/`vc_portfolio`/`greenhouse`/`lever`/`ashby`/`aijobs_net`,
597 distinct names) and excluded slugs already in `BOARD_TOKENS` -> 4,428
candidate slugs. Probed all 4,428 live against the public Greenhouse
Jobs API concurrently (30-way `asyncio`/`aiohttp` semaphore, ~12s wall time)
-> 154 resolved with jobs.

**False-positive problem (the actual hard part).** Many YC company names are
short/generic English words (Pulse, Agency, Clear, Camp, Radar, Flip, Axle,
Symphony, Mesh, Guild, Array, Bird, Stage, Super...) that collide with
unrelated companies using the same board token on Greenhouse's shared
namespace — e.g. `clara` resolved to a Brazil/Mexico/Colombia accounts-payable
fintech's careers board, not YC's SF-based "AI primary care doctor" Clara;
`pulse` resolved to a UK NHS healthcare-staffing board, not YC's Bengaluru
EMR company; `agency` resolved to a "Freelance AI Trainer" gig-worker
crowdsourcing board (Scale-AI-style data labeling), not YC's
security/compliance-headcount-replacement company. This is the same failure
mode flagged in the `#greenhouse-company-discovery` entry below for "shield"
— just far more common at this candidate volume, since short generic names
are disproportionately likely among common English/business words.

Delegated a systematic verification pass (subagent, `general-purpose`):
for each of the 154 hits, compare live job titles/locations/content against
the YC company's `one_liner`/`all_locations` (also pulled from the Algolia
index) and judge INCLUDE/EXCLUDE, leaning EXCLUDE on thin evidence per
instruction (a wrong company's postings polluting a personal job tracker is
worse than a missed board, and this list can be revisited later). Result:
94 include / 60 exclude. Manually spot-checked ~10 of the includes myself
against a broader job-title sample (not just the first 3) before trusting
the pass; found 3 the subagent should have excluded on its own stated
criteria (`agency` — AI-trainer gig board, semantically opposite of
"replaces compliance headcount"; `axle` — bioinformatics/flow-cytometry
biotech jobs, not an "AI-native insurance clearinghouse"; `flip` — healthcare/
retail BD-rep and enterprise-CSM roles, nothing resembling a sneaker resale
marketplace) and manually overrode those three to exclude. Final: **91
verified new boards**.

**Result:** `BOARD_TOKENS` 157 -> 248. Standalone `fetch_raw()` against just
the 91 new tokens returned 1,843 raw items live; a full `run_ingest(sources=
["greenhouse"])` re-fetch across all 248 boards inserted 1,811 new items
(17,614 raw fetched, 15,803 already-existing duplicates correctly skipped via
the existing `UNIQUE(source, url)` dedup). DB total: 28,893 items (up from
~27,000).

**Not done / explicitly deferred:** the requested deeper "top 500-2,000
AI-relevant SF companies" search (via broader internet/event search — local
news, Luma events, etc. — rather than an existing structured directory) is
tracked as a high-priority TODO item, not attempted here. This pass only
covers the "get most of it easily for free" half of that ask.

---

## 2026-07-03 — Project rename + scope-framing correction {#project-rename-scope-framing}

Two administrative/documentation-only changes, requested together, neither
touching code, schema, or module names:

**Rename.** "Opportunity Pipeline" -> "Jobs Pipeline". The GitHub repo was
already renamed to `jjchong5/jobs` in a separate session earlier the same
day, with the local git remote already pointed there — this pass just
brought in-repo text in line. Updated: `CLAUDE.md` title/description,
`README.md` title/description, and the two page-title/header strings in
`src/pipeline/ui/app.py` (`st.set_page_config` and `st.title`). Left
`docs/initiating chat.txt` untouched — it's the original capstone scoping
transcript, archival by nature, not a live-facing doc. Considered "Jobs"
(matches repo name exactly) vs. "Jobs Pipeline" (keeps the pipeline framing
used throughout the architecture docs); author picked "Jobs Pipeline".

**Scope-framing.** Author: "I'm not sure how much I'll build out the
events/networking tracking anyways." This did not change any code — event
sources (`luma_events`, `meetup`, `eventbrite`) were already frozen
2026-07-02 (see the freeze entry earlier in this file), so the code-level
decision predates this change and was already reversible via the existing
`FROZEN_SOURCES` pattern in `src/pipeline/ingest.py`. What changed here is
the pitch: `CLAUDE.md`'s opening description and `README.md`'s description
no longer describe jobs/events/networking as three co-equal pillars — they
lead with job-tracking as primary and mention events/networking as a
secondary, currently-frozen capability. The tagger's `category` field
(job/event/networking) and the UI's category filter are untouched — they
still work, cost nothing to keep, and aren't part of this framing change.

No changes to DB schema, table names, `pipeline.*` module/package names, or
`docs/SOURCES.md` (its intro is a status-tracking table, not project-pitch
prose, so there was no framing language to correct there).

---

## 2026-07-03 — LinkedIn multi-query fan-out, backlog raw-pull audit {#linkedin-query-fanout}

**Uncommitted.**

Prompted by "have we basically hit the ceiling on relevant jobs per source"
— audited `linkedin_apify` specifically, since the memory note from the
2026-07-03 Apify actor-vetting investigation flagged it as untested
headroom: `APIFY_LINKEDIN_MAX_ITEMS=200` looked like a spend cap, but the
actor itself plateaus around 170-180 results per search URL regardless of
that cap, and query variety (not a higher cap) had never actually been
tested against the author's own search terms.

**Live overlap probe (4 queries, $0.426 total):** ran the actor against 4
varied search URLs — the existing default (SF, "data scientist OR machine
learning OR artificial intelligence"), an adjacent SF title set ("AI
engineer OR ML engineer OR applied scientist"), a nationwide remote search,
and a freelance/contract-angled SF search (matching the ranker's
freelance-preference weighting). Results: 180 / 170 / 170 / 89 items,
531 unique job ids in the union. Pairwise Jaccard overlap between any two
queries was only 0.9-15.1% — even the two SF-scoped queries with adjacent
title sets shared just 15.1%. Confirms the actor's ~170-180 ceiling is
per-query, not a platform-wide LinkedIn ceiling; different keyword/location
combinations surface largely disjoint job pools.

**Wired into `linkedin_apify.py`.** `fetch_raw()` now loops over a
`DEFAULT_SEARCH_URLS` list (the same 4 queries from the probe) each call,
dedups results across queries by job id before returning, and still
respects `APIFY_LINKEDIN_SEARCH_URL` (single override) or the new
`APIFY_LINKEDIN_SEARCH_URLS` (pipe-`|||`-separated list override) if a
narrower run is ever wanted. `ingest.py` required no changes — `fetch_raw()`
kept the same no-arg/flat-list signature.

Live end-to-end run: 383 unique raw items fetched across the 4 queries,
199 new items inserted into the DB (184 skipped as dupes of items already
present from earlier single-query runs).

**Backlog raw-pull audit.** Separately asked to confirm all recent test
pulls had actually made it into the DB. Cross-referenced every file in
`data/raw/` (including the manually-named one-off snapshots
`linkedin_apify_{broadened,retry,split}.json` and
`indeed_apify_sanjose{,_broadened}.json`/`indeed_memo23_test.json` from the
2026-07-03 dedup/actor-vetting investigations) against `run_log` and live DB
contents:

- `indeed_memo23_test.json`, `indeed_apify_sanjose*.json`,
  `linkedin_apify_split.json` — already fully accounted for, matching
  documented `run_log`/`HISTORY.md` entries exactly.
- `linkedin_apify_broadened.json` (762 items) and
  `linkedin_apify_retry.json` (340 items) — raw `id`/URL comparison against
  the DB showed 120 and 35 "missing" items respectively. Re-ran both through
  `ingest_raw_file()` to be sure: **0 inserted for both**, all skipped as
  duplicates. This is correct, not a bug — `linkedin_apify` is in
  `UNSTABLE_URL_SOURCES` (see `#linkedin-apify-dedup-fix`), so its real dedup
  key is `(dedup_key, location)` (normalized company+title+location), not
  the actor's per-render URL/id. The "missing by id" items were the exact
  same postings already present under a different id from another run —
  the fix from the earlier dedup investigation was doing its job correctly.

Net effect: no real gap existed in the backlog beyond the 199 items the
fan-out itself surfaced as genuinely new. DB now at 27,082 total items
across 20 sources (`linkedin_apify`=1,549).

---

## 2026-07-03 — Greenhouse company-name discovery pass {#greenhouse-company-discovery}

**Commit:** none yet — uncommitted in the working tree as of this writing.

Follow-up to the same-day full-volume pass (see
`HISTORY.md#greenhouse-full-volume-pass`), prompted by the user asking
whether "all potential matching jobs off Greenhouse" had been captured. The
honest answer: exhaustive *within* the 67 tracked boards (confirmed no
per-call cap), but incomplete in *company coverage* — Greenhouse has no
cross-company directory/search API, so any company whose board token was
never guessed contributes zero jobs, invisibly. The 67-board list so far was
built entirely from hand-guessed candidate slugs (obvious company-name
variants), which has an unbounded blind spot.

Realized the pipeline already had a free, non-guessed source of real company
names: 436 distinct company names sitting in the `items` table from
`yc_workatastartup` and `vc_portfolio` (`author` column), sources with no
overlap in origin from the hand-guessed Greenhouse list. Generated Greenhouse
slug candidates per company name (lowercase, dash-joined, no-space, plus
variants with common suffixes stripped — "Inc", "Labs", "AI", "Technologies",
"Health", "Corp", "Therapeutics", "Systems", etc.) — 436 companies produced
621 candidate slugs after dedup against the existing 67-token list. Probed
all 621 live in parallel (`ThreadPoolExecutor`, 30 workers) against the real
`boards-api.greenhouse.io/v1/boards/<slug>/jobs` endpoint: 91 resolved with
non-empty `jobs`.

Notable finds that a hand-guessed AI/SF-tech list would never have produced:
`spacex` (1,829 jobs) and `andurilindustries` (2,170 jobs) — both real,
neither an "AI-native" company by branding, but genuinely relevant (defense
tech, heavy ML/autonomy hiring) and only discoverable because they'd already
shown up as employers on YC/VC-portfolio boards.

**Verified before trusting generic-word slugs** (a real risk with this
method — short common words are more likely to collide with an unrelated
company's real board): spot-checked `flex`, `mill`, `hive`, `found`,
`future`, `fal`, `alloy`, `verse`, `paradigm`, `current` by pulling each
board's actual job titles and confirming they were consistent with the
expected company (e.g. `mill` returned "AI Engineer, Computer Vision" /
"Hardware Systems Engineering Intern" — matches Mill Industries' actual
hardware/AI product; `hive` returned German/Dutch-language listings —
consistent with Hive AI's stated EU presence). One rejected: `shield`
(guessed for Shield AI) resolved to `corvo792.github.io/ghdemoboard2/` — an
unrelated GitHub Pages Greenhouse demo board, not a real company — excluded
from the list entirely.

Added all 90 verified tokens (91 found, 1 rejected) to `BOARD_TOKENS` in
`src/pipeline/scrapers/greenhouse.py` (158 boards total, up from 67).
Live-tested end-to-end: fetch returned 15,772 raw items across 157 boards
(one board 0-jobs at fetch time vs. probe time — normal churn, not a bug),
up from 7,617. Full ingest: 7,784 inserted / 7,988 deduped. Greenhouse total
in DB: 15,188 items (up from 7,404); pipeline-wide total: 27,082 items.

No code changes beyond `BOARD_TOKENS` — the discovery method (mine existing
DB company names, generate slug variants, probe live, spot-check
generic-word matches) is documented here and in `docs/SOURCES.md` as a
reusable pattern, not implemented as a standalone script, since it's a
one-off list-building exercise rather than something that needs to run
again on a schedule. Same pattern could be applied to Lever/Ashby's smaller
company lists if their coverage becomes a priority later.

---

## 2026-07-03 — `run_ingest` spend trap found live; added `ingest_raw_file()` {#ingest-raw-file-spend-trap}

**Uncommitted.**

While testing `indeed_radius` headroom (max-out-volume pass following the
Apify actor-vetting sanity check), ran a capped live probe against San
Jose, CA (`radius=25`, `maxJobs=1600`, `max_total_charge_usd=$2.00`) —
succeeded cleanly, actor log confirmed genuine exhaustion ("Finished! Total
1673 requests: 1673 succeeded, 0 failed"), 1,600 items for $2.007, saved to
`data/raw/history/indeed_radius_20260703T100521Z.json`.

**Then triggered an unintended second paid run.** Called
`run_ingest(sources=["indeed_radius"])` intending to ingest that saved file
— but `run_ingest` always calls the source's live `fetch_fn` directly
(`ingest.py`'s per-source loop has no "ingest from an already-fetched file"
path), and the new shell invocation didn't carry forward the
`APIFY_INDEED_RADIUS_LOCATION`/`_MAX_JOBS` env vars from the first run. That
silently kicked off a second live Apify run against the module's *defaults*
(San Francisco, `maxJobs=500`) — cost $0.632, fetched 500 SF items,
ingested 289 new / 211 skipped. Not wasted data (real SF items, correctly
deduped), but not the San Jose data intended, and an unplanned spend
($2.64 total vs. the $2.00 approved).

**Fix.** The actual San Jose file was then ingested correctly via a one-off
script that read the saved JSON and pushed it through
`normalize_indeed_radius` + `WriterQueue` directly (1,118 inserted / 482
skipped, 70% net-new — confirms the SF/San Jose non-overlap coverage-gap
thesis from `docs/SOURCES.md`'s `indeed_radius` entry). Ported that pattern
into `ingest.ingest_raw_file(source, path)`, a permanent function alongside
`run_ingest()`: takes a source name and a raw JSON path, runs it through
that source's registered normalizer and the same `WriterQueue`/`record_run`
machinery, but never touches `fetch_fn` — no way for it to trigger a live
paid call. Intended for exactly this "fetch once (possibly at real cost),
inspect/decide, ingest separately" workflow, which the codebase didn't
previously support at all — `run_ingest` was the only ingest path, and it
always re-fetches.

**Takeaway for future Apify volume-testing passes:** after a capped live
probe, use `ingest_raw_file()` against the timestamped
`data/raw/history/<source>_<timestamp>.json` it wrote, not
`run_ingest(sources=[...])` — the latter is only safe when you want a fresh
live fetch with that source's current default params.

---

## 2026-07-03 — Greenhouse full-volume pass {#greenhouse-full-volume-pass}

**Commit:** none yet — uncommitted in the working tree as of this writing.

Context: reviewing per-source headroom against real platform ceilings (not
self-imposed caps) found Greenhouse/Lever/Ashby have no per-call cap or
pagination at all — a single API call already returns a company's entire
board (confirmed earlier, e.g. Stripe: 491 jobs in one response). So for
these three, "more volume" only ever means "more companies," never more
pages/keywords per company. Greenhouse was sitting at just 26 board tokens
(from two earlier passes), a much smaller universe than SF/AI-native tech
actually offers.

Built a ~196-candidate list spanning foundation-model labs, AI
infra/tooling, applied-AI verticals (legal, healthcare, security), data/
analytics platforms, and general SF tech (since several already-live tokens,
e.g. Stripe/Discord/Asana, aren't AI-native either — relevance filtering is
the tagger's job, not the scraper's). Probed all candidates live in parallel
(`ThreadPoolExecutor`, 20 workers) against the real
`boards-api.greenhouse.io/v1/boards/<token>/jobs` endpoint — 64 of 196
resolved with `jobs: [...]` non-empty; the rest 404'd (wrong slug guess or
not on Greenhouse at all). 41 of the 64 weren't already in `BOARD_TOKENS`.

Added all 41 without further AI-fit curation, matching the existing "seed
reasonably, don't over-curate" precedent from the two prior passes. Notable
additions by job count: `mongodb` (398), `coreweave` (278, GPU cloud infra),
`graphcore` (251, AI accelerator chips), `cloudflare` (233), `roblox` (231),
`airbnb` (223), `elastic` (202), `reddit` (191), `pinterest` (187),
`tenstorrent` (123, AI accelerator chips), `cresta` (104, applied
conversational AI) — down to single-digit boards like `comet` (4, ML
experiment tracking) and `stabilityai`-adjacent labs already covered.

Live-tested end-to-end: standalone fetch returned 7,617 raw items across 67
boards (up from 3,187 across 26). Full ingest via
`run_ingest(sources=["greenhouse"])`: 4,217 inserted / 3,399 skipped as
duplicates — the dedup number checks out, since re-fetching the original 26
boards should (and did) produce ~3,187 exact repeats, with the net-new
volume coming entirely from the 41 added boards. DB total for `source=
"greenhouse"` after this pass: 7,404 items.

No code changes beyond `BOARD_TOKENS` in `src/pipeline/scrapers/
greenhouse.py` — fetch/normalize/ingest logic was already correct from the
original build.

---

## 2026-07-03 — company_stage: OpenAI/Anthropic wrongly tagged "public" {#company-stage-public-benefit-bug}

**Commit:** none yet — uncommitted in the working tree as of this writing.

Caught by the user eyeballing the QA sanity-check report (a spot-check
catching a real bug the automated pass missed). Query confirmed the scale:
123 `openai` + 114 `anthropic` postings tagged `company_stage: "public"` out
of ~938 sampled — neither company is publicly traded. Root cause, confirmed
by reading the actual raw_text: every Anthropic posting's boilerplate footer
says "Anthropic is a **public benefit corporation** headquartered in San
Francisco" — a *legal structure* term, unrelated to stock-market listing.
The model was keying off the literal word "public" in that phrase. The old
prompt wording ("well-known public company name") didn't help — ambiguous
between "well-known" and "public."

**Fix (`tagger/prompts.py`, `COMPANY_STAGE_ENUM` guidance):** clarified
"public" means actually stock-market-traded; named OpenAI/Anthropic/Stripe/
SpaceX/Databricks explicitly as "growth" examples; called out the "public
benefit corporation" phrase by name as a trap to not key off of. Verified
live against the exact posting that triggered the original false positive
(item id 3879, the Anthropic Enterprise Sales Manager role) — now returns
`company_stage: "growth"` instead of `"public"`. Also verified against a
real untagged OpenAI posting — same correct result.

**Not yet backfilled:** the 237 already-tagged OpenAI/Anthropic rows from
this session's sample still carry the wrong `"public"` value until a
targeted re-tag pass touches them; the fix only affects rows tagged from
this point forward.

## 2026-07-03 — Saved source-overlap analysis as a reusable script {#source-overlap-script}

The queries behind `docs/SOURCE_OVERLAP.md` and the `linkedin_apify` dedup
fix (`#linkedin-apify-dedup-fix` below) were one-off scratchpad code, gone at
the end of the session. Ported them into
`src/pipeline/analysis/source_overlap.py` (`python -m
pipeline.analysis.source_overlap`) instead: per-source item counts +
dedup_key coverage, cross-source overlap %, the pairwise shared-key matrix,
and within-source multiplicity + single-location rate, all queried live off
`get_connection()` rather than a hardcoded snapshot. Verified it reproduces
the exact numbers already in `docs/SOURCE_OVERLAP.md` (down to the individual
pairwise counts) before treating it as the source of truth going forward.
Deliberately left out of scope: re-diffing the raw multi-run Apify JSON files
(the one-off `indeed_apify_sanjose*.json` / `linkedin_apify_{broadened,retry,
split}.json` comparison) — those were manually-named snapshots specific to
that investigation, not a standing file-naming convention, so there's nothing
generic to re-run there.

## 2026-07-03 — Indeed radius search (`indeed_radius`) replaces `indeed_apify` {#indeed-radius}

**Uncommitted.**

Following up on the earlier-established finding that `misceres/indeed-scraper`
(the actor behind the old `indeed_apify` source) has no radius/distance
parameter — a live comparison had shown "San Francisco, CA" and "San Jose,
CA" searches came back ~92% non-overlapping despite both being Bay Area —
ran two capped-cost live probes against alternate Apify actors to see if
either the Indeed coverage gap or LinkedIn's ~170/term anonymous-scrape
ceiling could be improved.

**Indeed probe — clear win.** Tested `memo23/apify-indeed-cheerio-ppr`
(244 users, 7,536 runs; $0.00175→$0.00125/result at PAY_PER_EVENT tier vs
misceres' $0.005/result) with the existing 3-term combined query, `location:
"San Francisco, CA"`, `radius: 25` (miles — a param `misceres` doesn't have
at all), capped at `max_total_charge_usd=$2.00`. Result: **1,594 items for
$2.00**, capped by the actor's own internal `ACTOR_MAX_PAID_DATASET_ITEMS`
ceiling (1,600 as of this writing), not our $2 budget — truncated, not
exhausted, more available. That's ~45% more volume than the existing
1,095-item SF-only misceres pull, in one search, at roughly 4x lower
per-item cost.

**Worth flagging plainly:** this actor's run logs show it authenticating to
Indeed's private mobile API using what looks like a harvested real
mobile-app session — live `cf_clearance`/`__cf_bm` Cloudflare bypass cookies
plus another actual user's search history (`q=project+manager`,
`q=data+entry+work+from+home`, etc.) baked into the request, with a
`sendMessage failed: ETELEGRAM` log line suggesting the actor operator
manages a pool of these harvested device tokens via a Telegram bot. That's a
materially different mechanism than `misceres`' residential-proxy HTML
scraping. Confirmed with the author before adopting: no personal
account-ban risk either way (neither actor uses the author's own
credentials) — the actual risk is that the harvested-token pool could get
detected/invalidated at any time, breaking the actor without warning, not
exposing the author's account.

**LinkedIn probe — inconclusive, actor-specific failure, not a ceiling
finding.** Tested `thirdwatch/linkedin-jobs-scraper` (121 users, 1,379 runs,
$0.001/result, `queries`-array input) with a single "data scientist" /
"San Francisco Bay Area" query, capped at `max_total_charge_usd=$1.00`, to
see whether the ~170/term ceiling already observed on `curious_coder` (the
actor behind `linkedin_apify`) was actor-specific or platform-wide. The run
stalled after 60 job cards crawled locally (visible in its own logs) but
**zero items were ever pushed to the Apify dataset** and cost stayed at the
flat $0.00005 actor-start fee for 35+ minutes with no progress — aborted via
the API rather than left running. Doesn't answer the ceiling question either
way; just establishes this particular alternate actor is unreliable at this
scale. The LinkedIn ceiling question remains open.

**Implementation.** Renamed `indeed_apify.py` → `indeed_apify_old.py`
(git history preserved via `git mv`), same reversible mothball pattern as
`wellfound_apify_old.py` — added to `ingest.py`'s `FROZEN_SOURCES`, existing
2,310 DB rows migrated `source='indeed_apify'` → `'indeed_apify_old'` for
naming consistency. Unlike the wellfound mothball, `indeed_apify_old` isn't
frozen for being broken or low-quality — it's kept live in the codebase
specifically as a fallback in case `indeed_radius`'s harvested-token
mechanism gets blocked. New `indeed_radius.py` module added (broadened
10-term keyword set carried over from the earlier keyword-mining pass,
`radius=25` default, `country="United States"` — the actor rejects the
`"US"` country-code shorthand `misceres` accepts). Already-fetched probe
data (1,594 raw items, already paid for) was ingested through the new
normalizer directly rather than re-fetching: 936 inserted, 658 skipped as
real duplicates against the existing `indeed_apify_old` data — DB now at
12,794 total items, `indeed_apify_old`=2,310, `indeed_radius`=936.

---

## 2026-07-03 — Refreshed source-overlap analysis, fixed linkedin_apify dedup {#linkedin-apify-dedup-fix}

**Commit:** `6274f05`

Re-ran the cross-source/within-source overlap analysis from `docs/SOURCE_OVERLAP.md`
against the now-11,858-item DB (was 7,412 at the original 2026-07-02 pass) —
requested specifically to characterize whether `indeed_apify` and
`linkedin_apify`'s multiple manual runs (different location searches, broadened
queries, retries) were producing duplicate rows.

**Found a real asymmetry between the two.** Diffing the raw Apify run files
directly (`data/raw/indeed_apify_sanjose*.json`,
`data/raw/linkedin_apify_{broadened,retry,split}.json`):

- `indeed_apify`'s `viewjob?jk=<id>` URL is stable and content-addressed —
  exact-URL overlap between runs tracked company+title overlap almost 1:1,
  confirming `UNIQUE(source, url)` correctly dedups it. Only 11.9% of the
  source is same-company-same-title duplicated, and most of that (74%) is
  real multi-location multiplicity (e.g. `DataAnnotation`'s generic
  remote-training titles recurring across many Bay Area cities), not a scrape
  artifact.
- `linkedin_apify`'s actor `link` field embeds a `trackingId`/`refId`/
  `position` unique to that specific search-results render — **0% exact-URL
  overlap across every pair of its 4 known runs**, even though 16-25% of each
  run's unique company+title keys reappeared in another run. Confirmed
  directly in the DB: Adobe's "Machine Learning Engineer" in San Jose showed
  up as 5 separate rows, each a different URL/trackingId, same real posting.
  Net effect measured in the live DB: 505 of `linkedin_apify`'s 1,350 rows
  (37%) were an undetected duplicate of another row already present — the
  highest true-duplicate rate of any source, and this one source accounted
  for 74% of all single-location duplicate groups in the entire DB.
  `wellfound_search` runs the same kind of multi-location-search loop by
  design and doesn't have this problem (its URLs are stable
  `wellfound.com/company/<slug>/jobs/<slug>` paths) — so the issue is
  specific to this one Apify actor's URL scheme, not multi-search dedup in
  general.

**Fix, `storage/db.py`:** added `UNSTABLE_URL_SOURCES = {"linkedin_apify"}`.
`insert_item_sync`'s repost-detection step now falls back to a same-source
`(dedup_key, location)` lookup for sources in that set when the `(source,
url)` lookup misses, and folds a match exactly like a same-URL repost —
`times_seen`/`last_seen_at` bumped, prior `raw_text` archived to
`item_text_history` if the re-scraped text actually changed (same repost
pipeline added in `34a947b`, just keyed differently for this one source).
Every other source keeps using `url`, matching the existing
`docs/SOURCE_OVERLAP.md` finding that same-source title collisions elsewhere
are dominated by genuinely distinct postings (1-10% single-location), not
re-scrapes.

**Verified live** against a copy of the real DB (not just reasoning from the
data): simulated a re-scrape of an existing `linkedin_apify` row (new
tracking URL, changed description text) — folded into the existing row
(`times_seen` 1→2, `last_seen_at` updated, old text archived to
`item_text_history`) instead of creating a duplicate; a same-company-same-title
item at a genuinely different location still inserted as a new row, confirming
the fix doesn't over-fold legitimately distinct postings.

**Forward-only, not retroactive** — same precedent as the original
`dedup_key`/`alt_listings` rollout (`abebcd4`, see `#dedup-tracking` below):
the 505 existing duplicate rows are left as separate rows, not merged or
deleted. A retroactive merge pass is a deliberate later call, not done as a
side effect here.

## 2026-07-03 — Raw-text truncation cap raised 4000 → 12000 chars {#raw-text-truncation-cap}

**Commit:** none yet — uncommitted in the working tree as of this writing.

User asked why `build_user_message()` truncates `raw_text` to 4000 chars at
all — window-fit or scraper limit? Neither: it's an arbitrary constant with
no comment explaining the number, left over from before the schema grew to
13 fields. Checked against the real untagged backlog before touching it:

- **71.6%** of the 11,227-item untagged backlog exceeds 4000 chars.
- The 4 biggest sources (`greenhouse`, `indeed_apify_old`, `ashby`,
  `indeed_radius`, `linkedin_apify`) were losing **~30% of content on
  average**, worst case 78-88% (some Greenhouse/Ashby postings run
  15,000-26,000+ chars).
- Fields the tagger extracts — `deadline`, `company_stage`,
  `role_expectation_delta`, comp details — often sit in the back half of a
  posting (after the intro/company blurb), so this wasn't a benign cut.

Raised the cap to 12,000 chars (`prompts.py`, now a named constant
`RAW_TEXT_CHAR_LIMIT` instead of a bare literal) — covers 99.2% of the
backlog in full (vs. 28.4% before). Computed the real cost delta before
committing to it: summed `min(len,12000) - min(len,4000)` across all 11,227
untagged rows → ~4.6M extra input tokens → **~$4.60 total** across the whole
remaining backlog. Verified live: re-tagged 3 real `ashby` postings (long
ones, ~5,900 chars avg) at the new limit — sensible output, `input_tokens`
per call rose from ~2,400 (fixed overhead only) to ~3,500 (fixed overhead +
now-uncapped content), matching the math.

Left it a cap, not unlimited — a few genuinely pathological scrapes exist
(one `remoteok` item is 33,736 chars) and there's no reason to pay for
whatever noise is in the outlier tail.

## 2026-07-03 — Tagging concurrency default raised 5 → 15 {#tagger-concurrency-default}

**Commit:** none yet — uncommitted in the working tree as of this writing.

User asked why the concurrency default was 5, and whether to check local
system settings before raising it. Local CPU/network isn't the relevant
ceiling here — this is I/O-bound (waiting on Anthropic's servers), not local
compute. Checked the actual constraint instead: made one real Haiku call via
`.with_raw_response` and read the rate-limit headers back —
`anthropic-ratelimit-requests-limit: 10000`/min,
`anthropic-ratelimit-tokens-limit: 12000000`/min. At ~2,400-3,500 input
tokens/call and ~2s latency, 5 concurrent workers uses a small fraction of
either ceiling — the account has room for far more before rate limits become
the bottleneck. Raised the default to 15 (not higher, since this is a
one-time backlog-clearing job, not sustained production traffic, and very
high concurrency mostly adds noise if something *is* wrong at scale without
buying much more speed once past this point).

## 2026-07-03 — Tagging-run re-entrancy lock + bounded concurrency {#tagger-concurrency}

**Commit:** none yet — uncommitted in the working tree as of this writing.

Investigating why `run_log` showed `wellfound_search` tagged twice (784 items
at $2.17, then 717 of the same rows re-tagged ~4s later for another $1.98)
found the cause: `run_tagging.run()` had no guard against two invocations
running at once. Two processes both querying `tagged_at IS NULL` can read the
same untagged snapshot before either commits, so both claim overlapping rows.
Real money wasted (~$2), not just a theoretical race.

**Fix, `tagger/run_tagging.py`:**
- A plain re-entrancy lock — `os.open(..., O_CREAT | O_EXCL)` on
  `data/tagging.lock`, released in a `finally` block. If a second run starts
  while one is in progress, it logs and returns
  `{"tagged": 0, "failed": 0, "skipped_reason": "already_running"}`
  immediately, no API calls made. Deliberately simple (no PID liveness check,
  no distributed lock) — this is a single-machine, human-triggered-plus-one-
  future-scheduler-job situation, not a multi-worker fleet.
- Bounded concurrency via `--concurrency` (default 5): the independent
  `tag_item()` network calls run in a `ThreadPoolExecutor`, but every DB write
  still happens sequentially on the main thread as each future completes —
  same single-writer discipline as the rest of the pipeline, just the network
  round-trips are parallelized. This is a wall-clock fix only; it does not
  change cost (same number of API calls, same tokens per call).

**Verified live**, not just unit-tested: ran `--source dice --limit 2
--concurrency 2` for real ($0.0002ish), confirmed both rows wrote correctly
and the lock file was removed on exit; separately pre-created the lock file
and confirmed a `run()` call bails immediately with `already_running` and
makes zero API calls before manually clearing the lock.

**Real bug this test also surfaced (not fixed, noted for later):** both test
items came back tagged `irrelevant` despite clearly-real titles ("Data
Scientist", "Data scientist - only local resume"). Root cause: `dice.py`'s
scraper only captures title/company/location/posted-date from the Dice search
results page — there's no job description in `raw_json` at all, so
`normalize_dice`'s `raw_text` is just the posted-date string ("12d ago",
"Today"). Not a normalizer bug (nothing is being dropped) — the scraper never
had a description to carry. Fixing this would mean an extra detail-page fetch
per job, tripling scrape complexity for a 20-item source. Left as-is given
capstone deadline pressure; dice items will generally undertag until this is
revisited.

## 2026-07-03 — Relevance/ranking rework {#ranking-rework}

**Commit:** none yet — uncommitted in the working tree as of this writing.

Triggered by a review of per-scraper quality counts, which surfaced that the
old `relevance_score` was a single opaque LLM number (one vague prompt line:
"how relevant to a SF-based data scientist/ML/AI job seeker") multiplied by
`category_weight * engagement_weight` in the ranker — stacking preference
multipliers on top of an ungrounded score compounds noise rather than
correcting it, and the score didn't reference the user's actual stored
preferences at all.

**New tagger fields** (`tagger/schema.py`, `tagger/prompts.py`):
- `content_quality` (renamed from `content_quality_score` same day, after the
  user asked to simplify the name and reorder it lower in the prompt schema
  — confirmed field order has no effect on LLM output, purely for human
  readability) — narrowed to ONLY judge how substantive/well-written a
  posting is, explicitly NOT a preference signal. Internal QA use only, not
  surfaced in ranking math or prominently in the UI.
- `spam_risk` (clean/suspicious/likely_spam) — categorical, not numeric (no
  need for fine granularity on a filter signal). Deliberately kept OUT of
  all ranking score math; reported in the UI for visibility so the user can
  validate false-positive rate before ever using it as a filter.
- `role_expectation_delta` (signed -5..5) + `role_expectation_notes` (free
  text) — how much a posting's stated requirements deviate from a *typical*
  posting for that job title (e.g. "4y exp required vs usual 2"). Shipped as
  the lightweight version: LLM judges against its own general/training
  knowledge of the role, no stored reference corpus. A fuller corpus-derived
  version (cluster real scraped postings per `role_category`, derive an
  actual reference profile, compare against that) was explicitly deferred —
  current tagged volume per role_category is too thin to make clustering
  meaningful yet.
- `company_stage` (pre_seed/seed/series_a_b/growth/public/unknown) — new
  LLM-extracted enum, free on the same tagging call.
- `engagement_type` gained a `part_time` value (previously only
  full_time/contract/freelance/project_based — an ongoing-but-reduced-hours
  role didn't fit any existing value).
- `INDUSTRY_VALUES` expanded from 10 to 19 buckets. Old `biotech_health`
  split into `biotech` (pharma/life-sciences, favored), `health_general`
  (general healthcare, NOT favored per explicit user instruction), and
  `adult_caregiving` (elder/disability care, favored, split out as its own
  bucket since the user wants it specifically surfaced). Added `ai_research`,
  `science`, `real_estate`, `transportation`, `politics_civic`,
  `prediction_markets`, `fintech` (re-added, wasn't previously favored),
  `ai_education`, `education`.

**New scoring architecture** (`ranker/scores.py`, new file; `ranker/rank.py`,
rewritten): the old single `computed_score` became three named,
independently-sortable scores, all computed at rank-time from tagged fields
and persisted to the DB (materialized-view style, overwritten each run — not
an append-only history):
- `general_score` — preference-UNweighted, `content_quality + deadline_boost`
  only. Closest to "how good does this look to a generic viewer."
- `preference_score` — the main sort. `content_quality * (full weight-table
  product) + deadline_boost`, where the weight-table product multiplies
  5 independently-tunable tables: engagement, seniority, location (keyed on
  the existing `remote_type` field), sector (keyed on `industry`), and
  company stage.
- `urgency_score` — same as `preference_score` but with the deadline boost
  weighted 3x, so a high-preference item with a looming deadline surfaces
  above a slightly-higher-preference item with no deadline.

User explicitly wanted separate, independently-tunable weight tables (not one
folded-together number) specifically so each dimension could be adjusted
without touching the others. All 5 tables live as JSON columns on
`preference_profiles`, locked via a multi-round interview:
- **Seniority**: junior/intern 1.3x, mid 1.2x, senior 1.0x, staff+ 0.7x, n/a
  1.0x — upranks higher-callback-probability (less senior/competitive)
  postings.
- **Location** (keyed on `remote_type`): remote 1.3x, hyperlocal_sf 1.2x,
  bay_area 1.1x, other 0.6x, unknown 1.0x — remote prioritized over SF
  in-person per explicit user preference this round.
- **Sector** (keyed on `industry`): flat 1.4x for 12 favored buckets (ai_ml,
  ai_research, robotics, science, biotech, adult_caregiving, real_estate,
  transportation, politics_civic, prediction_markets, fintech,
  ai_education), 1.0x baseline for the rest. User confirmed flat rather than
  tiered weighting within favored sectors, to keep it simple for a first
  pass.
- **Company stage**: pre_seed 1.1x, seed 1.3x, series_a_b 1.3x, growth 1.0x,
  public 0.8x, unknown 1.0x — favors early-stage (faster hiring, less rigid
  process for freelance/project work).
- **Engagement**: freelance/project_based 1.5x, contract 1.1x, part_time/
  full_time 1.0x. User flagged this may eventually move to a UI-level
  filter/category split instead of a score multiplier — noted as not fully
  settled, multiplier and filter aren't mutually exclusive so this isn't a
  dead end either way.

**DB migration** (`storage/db.py` `_migrate_scoring_rework`): old
`relevance_score` column kept as-is (legacy/reference, not written to going
forward) and its ~1,900 already-tagged values copied forward into the new
`content_quality` column as an imperfect-but-usable starting value — low
stakes now that the field is QA-only rather than a ranking input. New
columns added via `ALTER TABLE`; the one-day-only `content_quality_score`
name (renamed to `content_quality` same day) required an explicit `ALTER
TABLE ... RENAME COLUMN` in the migration to avoid losing that day's
backfilled/tagged data.

**Also landed in the same session** (small, isolated, built proactively per
user's "if it's easy or small build it now" instruction): `item_text_history`
table + diff-on-rescrape logic in `storage/db.py`'s `insert_item_sync` —
archives the prior `raw_text` before overwriting when a re-scraped
`(source, url)` comes back with different text. Previously an edited posting
(e.g. company bumps years-of-experience) silently overwrote the old text with
no trace. Not used for any analysis yet — raw material for a future
job-description-drift-over-time feature the user wants to explore later
(inspired by work Marina Wynn has reportedly done), captured now since
delaying capture means permanently losing the history. Verified live:
unchanged repost → no history row; changed repost → old text archived,
`times_seen` still incremented correctly either way.

**Live-verified end-to-end** against the real (not mocked) `data/pipeline.db`
throughout: migration ran clean on the existing 163MB/~11,858-item DB;
several live tagging calls against real untagged items round-tripped all new
fields correctly (`content_quality`, `spam_risk`, `company_stage`,
`part_time` engagement type, expanded `industry` enum all populated as
expected); `python -m pipeline.ranker.rank` computed and persisted all three
scores for all 1,344+ tagged items under all three `--sort-by` modes.

**Not done in this pass:** the actual retag of the ~9,800 items ingested but
never tagged (Greenhouse/Indeed/Ashby/LinkedIn/VC-portfolio/Lever/aijobs.net/
Meetup/YC/Handshake/Eventbrite/Dice) — folded into whatever the next full
retag pass is, not special-cased. No UI work beyond wiring the new sort
selector and spam-hide toggle into the existing Browse/Digest tabs.

### Decision trail — how we got to the numbers above

This section exists because the user explicitly asked to preserve *how* these
decisions were reached, not just the final values — they're load-bearing for
his actual job search, not defaults he's likely to accept as-is if wrong.

**1. Started from a symptom, not a spec.** The user asked for per-scraper
quality counts (high/med/low % based on `relevance_score`). That surfaced two
problems he flagged unprompted: (a) most items were simply untagged, not
low-quality — the tagger had never run against 11 of 18 sources; (b) of what
*was* tagged, the score itself was suspect. He asked to review the scoring
methodology before trusting the counts at all.

**2. Diagnosed the actual mechanism before proposing fixes.** Read
`tagger/prompts.py` and `ranker/rank.py` together and found: `relevance_score`
came from one unrubric'd prompt line, and the ranker did
`relevance_score * category_weight * engagement_weight`. The user's own
one-line assessment once this was laid out: multiplying an ungrounded number
by preference weights "compounds noise instead of correcting it" — his words
approximately, and the framing that shaped everything after. This diagnosis
(not a proposed fix) is what he was actually validating before any redesign
started.

**3. First proposal was almost right but under-scoped.** Initial pitch: split
into an LLM "content quality" judgment plus deterministic weight tables,
folding most of the requested factors (freelance-vs-FT, remote-vs-SF,
FT/PT, startup stage, sector, entry-level uprank) into weight tables rather
than prompt prose. The user accepted the 2-tier architecture immediately
("I like your proposal") but then **expanded scope past what was proposed**:
he wanted spam-likelihood and a description-vs-typical-posting deviation
metric broken out as their OWN fields, not absorbed into "content quality."
He was explicit that spam risk should be usable later as an application-time
filter, and that the deviation metric was inspired by wanting an at-a-glance
"this Data Scientist listing wants 4y exp, not the usual 2" signal — i.e. he
was designing from his own resume-screening workflow, not asking for a
generic quality score.

**4. Interviewed rather than guessed on scope-expanding decisions.** For each
open design fork, the two live options were surfaced with a recommended
default and the user picked or overrode:
- Deviation metric: lightweight (LLM's own knowledge) vs. full corpus-derived
  reference profiles built by clustering real scraped postings. User accepted
  the lightweight version, but only after the tradeoff was made explicit —
  the full version was correctly identified as more accurate long-term but
  premature given how few tagged items exist per `role_category` bucket right
  now. This is a "revisit later, not never" decision, not a rejection.
- `company_stage` as a new tagged field now vs. deferred: user chose "now"
  since it's free on the same LLM call already reading the text.

**5. Naming had to be worked through in the open, not assumed.** First
attempt named the LLM field `content_quality_score` and the ranker's final
number `ranking_score`. The user pushed back with a genuinely useful
question — "now that we're separating spam and role_description_delta out,
what is content_quality_score still actually doing?" — which forced a real
answer (it's down to catching low-effort/inexperienced-poster listings that
aren't spam, just bad) rather than a rename for its own sake. That question
also surfaced that a SINGLE final "ranking_score" was the wrong shape: the
user said he wants (eventually) multiple sorters — application-urgency,
preference-weighted, and a preference-blind "general desirability" one (the
last with a stated future interest in going beyond SF/US data, noted as a
post-capstone TODO, not scoped now). That reshaped the ranker from
"compute one number" to "compute three named scores," which is a bigger
architectural change than the rename that triggered it.

**6. Storage/architecture questions were reasoned through with the user, not
just decided.** When the three-score idea came up, the assistant initially
suggested computing them live (unstored) for simplicity. User asked directly
"why not store them" — a fair challenge, since SQLite already had a
`ranked_at`-style precedent (`tagged_at`) and DB storage cost was already
established as a non-issue (163MB for ~11.9K items, ~14KB/item). Resolved to
store all three, recomputed each ranker run (materialized-view style, not an
audit trail — `run_log` already covers per-run metadata if a trend view is
ever wanted). The user also asked whether scoring logic should live in a
separate `scores.py` given the ranker was about to do more than "rank" —
agreed, split into pure-function `scores.py` (formulas) vs. `rank.py`
(orchestration + persistence + sort), specifically because weight tables are
expected to be tuned repeatedly and the formulas needed to stay easy to
read/test in isolation from DB/CLI concerns.

**7. Weight VALUES were extracted via structured multi-round interview, not
guessed.** Rather than propose a full weight table and ask for approval/
rejection in one shot, each dimension was asked about separately with 2-4
concrete options (plus "custom numbers" always available) so the user could
react to real tradeoffs instead of blank-slating: engagement spread, seniority
curve (which required clarifying what "staff+" means before he'd commit —
he confirmed his assumption was right once told it means Staff/Principal/
Distinguished), sector picks, location priority. Two follow-up rounds were
needed because his sector picks (AI education, research, real estate,
transportation, politics, prediction markets) didn't fit the existing
10-value `INDUSTRY_VALUES` enum — rather than silently collapsing them into
"other" (which would have defeated the purpose of weighting them), the
mismatch was surfaced explicitly and the user chose to expand the enum. That
expansion snowballed once raised: he asked to also split `biotech_health`
(wanting `adult_caregiving` broken out as its own trackable bucket, and
`health_general` explicitly EXCLUDED from favored status — "should not
include general health" was a deliberate exclusion, not an oversight), add
`fintech` back in, rename "research" to distinguish AI-specific research from
general `science`, and consider whether more general buckets (`education`)
were missing entirely. None of this was pre-planned; it emerged from
iterating the enum against his actual resume/interest profile in real time.

**8. Two things were explicitly flagged as unsettled rather than forced to a
premature decision.** (a) Whether engagement type should be a ranking
multiplier at all, vs. a UI-level filter/category split — user said "I
might actually want these categorically separated by the UI anyways," and
rather than resolve that ambiguity by fiat, it was shipped as a multiplier
FOR NOW with the caveat recorded that a UI filter could later coexist with
it. (b) Sector/stage weights were shipped flat (no tiering within "favored")
specifically because the user said keep it simple for a first pass, not
because tiering was rejected as a concept — recorded as "revisit once you've
seen it play out," not closed.

**9. A tangential idea got captured and partially built without derailing the
main task.** Mid-interview, the user asked whether raw scrape data was being
retained (yes) and floated wanting to eventually analyze how job description
requirements drift over time, referencing that Marina Wynn reportedly does
similar analysis. This was recognized as clearly out of scope for the ranking
rework itself, but small enough (one new table, ~10-line diff to one insert
function) and valuable enough (any delay = permanently lost history, since
the existing repost-handling silently overwrote `raw_text` with no trace) that
it was built immediately in the same session rather than deferred — the user
explicitly authorized this with "if it's easy or small build it now, otherwise
write an export prompt." The actual trend-analysis code was NOT built; only
the raw-capture layer (`item_text_history` + diff-on-rescrape) exists so data
starts accumulating now instead of later.

## 2026-07-03 — Fuller-fetch pass on the still-capped free sources {#fuller-fetch-pass}

**Commit:** none yet — uncommitted in the working tree as of this writing.

Follow-up to a question about which sources (besides LinkedIn/Indeed, whose
Apify caps were already known) were only pulling a partial slice of
available matching jobs. Audited every scraper for hard caps (fixed page
counts, `maxItems`, keyword-count limits) and found five: `wellfound_apify`
(handled separately by the author in a parallel session — see the Wellfound
entries below), `vc_portfolio.py`, `aijobs_net.py`, and the company-list
breadth on `greenhouse.py`/`lever.py`/`ashby.py`. Author asked to raise each
of the free ones to "as full as polite" from already-relevant areas, and to
brainstorm targeted-fetch options where jobs aren't category/keyword
searchable at all (the ATS boards).

- **`vc_portfolio.py`** was capped at 50 results per keyword with no
  pagination — confirmed live this undercounted badly: a16z + "data
  scientist" alone had 117 total matches via the API's own `total` field,
  so the old code silently dropped 57% of even a single keyword/board
  combo. The API turned out to support real cursor-based pagination via a
  `meta.sequence` token (confirmed live: consecutive pages returned
  disjoint job sets, not overlapping ones) — added a pagination loop that
  walks each keyword/board combo until `total` is reached, an empty/short
  page comes back, or a `MAX_PAGES_PER_QUERY=10` safety cap is hit (so an
  unexpectedly broad term can't turn into an unbounded crawl). Also widened
  `KEYWORDS` from 3 terms to 13 (added "artificial intelligence", "data
  science", "research scientist", "applied scientist", "ML engineer", "data
  engineer", "deep learning", "NLP", "computer vision", "LLM"), and added a
  0.3s delay between requests now that call volume is much higher.
  Live-verified: a16z alone with just 2 of the 13 keywords went from a
  100-item hard cap to 265 real deduplicated items.
- **`aijobs_net.py`** was `PAGES=2` (100 of a site-wide total). Checked the
  real total before deciding how far to raise it: 46,090 jobs site-wide —
  this is a global board (every country, every remote listing), not
  SF-scoped, so raising the page count alone doesn't get "fuller," it gets
  "more of mostly-irrelevant." Looked for a real filter before falling back
  to a bigger unfiltered slice: the site's `topics`/`countries`/`regions`/
  etc. `<select>` fields are backed by real per-field autocomplete
  endpoints (`/ac/topic/`, `/ac/country/`, ... — `django-tomselect`), and
  querying those directly resolves real pks (`topics=9` for "Data
  Science", `countries=238` for "United States"). But passing those same
  pks as query params on the list page itself does **not** filter — total
  stayed 46,090 regardless, confirmed by direct comparison against the
  unfiltered request. The actual filter submission isn't a plain GET the
  way Django-rendered forms usually are (likely POST+CSRF or an htmx
  partial-swap this pass didn't reverse-engineer) — noted as a real,
  bigger-lift option for later (render once with Playwright, apply the
  filter through the real UI, capture the resulting network request, same
  discovery technique already used for `vc_portfolio.py`'s Getro API), not
  pursued now. Raised `PAGES` to 20 (1,000 of the newest jobs, assumed
  newest-first per the site's default sort — not verified beyond observing
  distinct job sets page-to-page), added a 0.3s delay per request and
  per-job detail fetch, and an early-stop if a page returns 0 cards.
  Relevance filtering for this larger, still mostly-global slice continues
  to happen downstream in the LLM tagger, same division of labor as
  before. Live-verified a reduced 3-page run: 150 real items with full
  descriptions, no errors.
- **`greenhouse.py`/`lever.py`/`ashby.py`** — checked whether these were
  actually under-fetching per company first: confirmed live that a single
  API call already returns a company's *entire* board (Stripe: 491 jobs in
  one response, no pagination). So there was nothing to raise per company —
  the only lever here is company-list breadth, since none of these
  platforms expose cross-company search. Probed ~90 candidate SF/Bay Area
  AI-native company slugs live against all three APIs (some names hit on
  more than one platform — kept each company on exactly one platform to
  avoid double-ingesting the same jobs under two different `source`
  values). Added, all confirmed with real non-zero job counts and verified
  through the actual scraper parsing code (not just the raw endpoint): 12
  to Greenhouse (`xai` 214 jobs, `togetherai` 57, `abnormalsecurity` 63,
  `snorkelai` 47, `vannevarlabs` 31, `fireworksai` 33, `arizeai` 39,
  `labelbox` 14, `inflectionai` 5, `assemblyai` 4, `imbue` 3, `stabilityai`
  1), 1 to Lever (`zilliz` 11), and 16 to Ashby (`snowflake` 420, `sierra`
  145, `cursor` 112, `replit` 98, `cerebras` 96, `synthesia` 73, `vanta`-
  adjacent candidates like `drata`/`ramp`/`vanta`/`deel` deliberately
  excluded as not AI/DS/ML-native despite real job counts, `deepgram` 58,
  `writer` 49, `abridge` 54, `roboflow` 27, `poolside` 14, `fiddler-ai` 10,
  `llamaindex` 10, `viggle` 6, `runway` 4).
- **`yc_workatastartup.py`** — checked and it was already fetching
  everything reachable: `roleLinks` lists exactly 10 top-level categories,
  "Science" (the only DS/ML/AI-adjacent one) was already included, and each
  category page returns its full result set in one response (`/jobs/l/
  science?page=2` returned the same 26 jobs as page 1, not a next page or
  an empty one). A `?query=` param was tried and silently ignored — no
  keyword search exists here either. No code change; documented the
  finding in the module docstring instead of leaving it unexplained.
- Wellfound itself (`wellfound_apify`) is excluded from this pass —
  handled by the author directly in a separate session; see the Wellfound
  role+location search entry below for that thread's outcome.

## 2026-07-03 — `wellfound_apify` renamed to `wellfound_apify_old` {#wellfound-rename}

**Commit:** none yet — uncommitted in the working tree as of this writing.

Author asked for the mothballed source (see below) to be explicitly renamed,
not just frozen under its original name, so it reads unambiguously as
archived wherever it shows up (module name, source column, scheduler
config). Renamed via `git mv` (history preserved):
`src/pipeline/scrapers/wellfound_apify.py` →
`src/pipeline/scrapers/wellfound_apify_old.py`. Updated in lockstep:
`ingest.py` (`NORMALIZERS` key, `FROZEN_SOURCES` entry, the
`normalize_wellfound_apify_old` function and its `source` field value),
`scheduler.py` (`SOURCE_INTERVAL_HOURS` key, `DEAD_SOURCES` comment), and
cross-reference mentions in `wellfound_search_apify.py`/`indeed_apify.py`
docstrings. Migrated the local DB in place (`UPDATE items/run_log SET
source='wellfound_apify_old' WHERE source='wellfound_apify'`) so the
existing 50 tagged rows stay under the same source key the code now uses —
50 `items` rows + 2 `run_log` rows renamed, verified via `NORMALIZERS`/
`FROZEN_SOURCES` membership checks post-rename. Added a module-top note in
`wellfound_apify_old.py` flagging it archived, why, and the reversible
re-enable path, mirroring the mothball precedent already used for the
frozen event sources. `docs/SOURCES.md`'s row for this source, and other
`HISTORY.md` entries referencing the old bare name, are left as accurate
history rather than rewritten.

## 2026-07-03 — Data-breadth stance vs. engagement-type preference (clarified) {#data-breadth-stance}

**Commit:** documentation-only clarification, no code change; folded into
`3c7bd70`'s CLAUDE.md/TODO.md update.

Freelance/project-based/contract work is the author's likely *application*
preference once he starts actually applying, but that's a ranking
preference, not a sourcing filter. The pipeline should keep ingesting and
tagging full-time roles alongside freelance ones — don't narrow scrapers,
role-slug lists, or ingest filters to freelance-only in response to this,
and don't treat a source's full-time skew (like `wellfound_search` above)
as something to fix by filtering it down. `engagement_weights` in the
ranker (full_time weighted down to 0.4 vs. 1.0 for freelance/project_based)
is already the correct mechanism for this — it demotes full-time in
ranking without removing it from the data. Keep it that way.

## 2026-07-03 — Wellfound role+location search, replacing the flat-feed approach {#wellfound-search}

**Commit:** `fa4de91`

Author asked whether the existing Wellfound source (`wellfound_apify`, 50
items/run from the unauthenticated `/jobs` feed) could be made
keyword-searchable or otherwise higher-signal, with an explicit "if not,
punt it" fallback. Investigated rather than assumed:

- Live-tagged the existing 50-item `wellfound_apify` pool first (it had
  never actually been tagged before this pass) to get a real baseline:
  only 14% scored `relevance>=5` against the SF DS/ML/AI profile — mostly
  generic startup sales/ops/PM noise. Then tested raising
  `APIFY_WELLFOUND_MAX_ITEMS` to 500 live — got back exactly 49 items, same
  as the 50-cap default. Root cause found by reading the actor's own run
  logs: its `maxItems`/`keyword`/`location` inputs are all client-side
  filters over one fixed unauthenticated page snapshot (~49 jobs), not real
  server-side search — confirmed with 4 different keyword/location
  combinations, all logging "Collected 49 raw jobs." So the flat feed has
  a hard ~49-job ceiling regardless of settings.
- Checked whether Wellfound has real server-side search at all before
  concluding "no": direct `/role/r/<slug>` pages are DataDome-blocked (403)
  even through the existing actor's proxy. Searched the Apify store for an
  alternative and found `clearpath/wellfound-api-ppe` (700 users), which
  does get past that block and accepts real
  `wellfound.com/role/l/<role-slug>/<location-slug>` search URLs — verified
  live before trusting it: `/role/l/data-scientist/san-francisco` returned
  75 real, on-topic postings. Individually verified each candidate role
  slug rather than assuming they'd all resolve — `applied-scientist` and
  `machine-learning` silently fall back to an unfiltered citywide listing
  instead of erroring, so those two are excluded; `data-scientist`,
  `machine-learning-engineer`, `ai-engineer`, `data-engineer` all confirmed
  real and on-topic.
- Built `src/pipeline/scrapers/wellfound_search_apify.py`, wired into
  `ingest.py` under a new `wellfound_search` key (kept separate from
  `wellfound_apify`, not a replacement — same precedent as
  `indeed_rss`/`indeed_apify`). Live ingest across all 4 roles x all pages:
  784 items, 0 failures, ~$4.6 total Apify spend (well under the $25
  session cap). Live-tagged all 784: 84.2% scored `relevance>=5`, a ~6x
  signal-density improvement over the flat feed's 14%, and ~100x more
  usable matches in absolute terms (660 vs. ~7) for a few dollars.
- **Known gap, not a bug:** still skews full-time (767/784
  `engagement_type`) despite the freelance-first profile — this source is
  now strong for full-time SF DS/ML/AI matches specifically, not for the
  freelance-sourcing sub-feature. That's fine, not a defect to fix — see
  the data-breadth entry above. Full detail and the exact investigation
  trail in `docs/SOURCES.md`.
- Also added a `--source` filter to `run_tagging.py` (`python -m
  pipeline.tagger.run_tagging --source <name>`) so a source can be
  re-tagged in isolation without spending on the ~6,700 other untagged
  items DB-wide — needed for this pass, reusable for future scoped re-tag
  passes (e.g. the `engagement_type`/`role_category`/`industry` backfill
  gaps noted below).
- **`wellfound_apify` mothballed same day** (author decision): given it
  only ever cleared a 14% relevance hit rate off a hard ~49-job ceiling,
  added to `FROZEN_SOURCES` in `ingest.py` alongside the frozen event
  sources — same reversible pattern (code/data untouched, just excluded
  from the default `run_ingest()`/scheduler source list; pass
  `sources=["wellfound_apify"]` explicitly to re-enable). `wellfound_search`
  is the live replacement going forward.

## 2026-07-02 — Scheduler {#scheduler}

**Commit:** none yet — `src/pipeline/scheduler.py` is untracked/uncommitted
in the working tree as of this writing (despite the dated claim of landing
2026-07-02 in the original CLAUDE.md text this entry was migrated from).

`src/pipeline/scheduler.py`, APScheduler `BackgroundScheduler` with one
interval job per source plus a tag+rank job every 30 minutes. Per-source
cadence lives in `SOURCE_INTERVAL_HOURS` (a plain dict, source name ->
hours) so any source can be tuned independently without touching scheduling
logic; `build_scheduler(interval_overrides={...})` also accepts ad-hoc
overrides at call time. All 16 live sources default to once/day —
deliberately capped there rather than polling faster, since a one-off
analysis of each source's `posted_at` distribution (done in-chat, not saved
as a file) showed we don't yet have real repeated-poll data to justify going
faster for any source, and several paid Apify sources (`indeed_apify`,
`linkedin_apify`, `wellfound_search`) turn faster polling directly into
spend. `indeed_rss`/`wellfound` (confirmed dead/superseded), the frozen
event sources, and `wellfound_apify` (mothballed 2026-07-03) are excluded
from the schedule entirely. Calibrating real per-source cadence off actual
`run_log` history is tracked in `TODO.md` section 3b — not done yet, since
the scheduler hadn't run long enough at the time to have that data.

## 2026-07-02 — Repost/cross-source dedup tracking {#dedup-tracking}

**Commit:** `abebcd4`

Analysis this session (in `docs/SOURCE_OVERLAP.md`) found same-source
same-title duplication is overwhelmingly real multiplicity (93% of groups
are the same title open at different locations, not the same posting twice)
but flagged two gaps in the old `INSERT OR IGNORE` dedup: no "still live as
of X" signal on re-scrapes, and no link between the same job posted on two
different sources under different URLs. Built both, live-tested against the
real (then-9,732-row) DB:

- **Schema**: `items` gained `last_seen_at`, `times_seen` (bumped on exact
  `(source,url)` re-scrapes instead of the old silent no-op), `dedup_key`
  (normalized `company|title`, see `normalize_dedup_key` in `storage/db.py`
  — strips all non-alphanumeric chars, not just punctuation, so ATS-slug
  company names like ashby's `elevenlabs` match human display names like
  "Eleven Labs" elsewhere; still plain string equality, not fuzzy matching
  — "Sr." vs "Senior" titles still won't match, consistent with
  efficacy-over-rigor), and `alt_listings` (JSON list of `{source, url,
  seen_at}`, lives only on the first-seen "canonical" row for a
  `dedup_key`). Migration-safe `ALTER TABLE` + backfill, same pattern as
  `engagement_type`/`role_category`. `dedup_key` backfilled for 8,828 of
  9,732 existing rows for free (deterministic, no API call);
  `last_seen_at`/`times_seen` initialized to first-insert defaults for
  existing rows.
- **`insert_item_sync` is now a 3-way branch**: exact repost (same
  `source,url`) bumps `times_seen`/`last_seen_at` on the existing row; a
  `dedup_key` match under a different source appends to that row's
  `alt_listings` instead of inserting a new row; same-source matches under
  the same `dedup_key` are explicitly excluded from linking and still get
  their own row — that's the location-variant case from the analysis
  above, and folding those would have reintroduced the exact problem the
  analysis ruled out. Safe without extra locking: `WriterQueue` already
  guarantees single-writer access, so there's no race between the lookup
  and the write.
- **Verified live** with 4 synthetic cases (cleaned up after, no
  production rows touched): new item inserts normally; exact repost
  returns `inserted=False` and bumps `times_seen` 1->2; same `dedup_key`
  from a different source folds into the canonical row's `alt_listings`
  with zero new rows created; same `dedup_key` from the same source
  (simulating a second office) still inserts as its own row. All four
  matched the intended design.
- **Explicit decision, not done**: existing cross-source duplicate rows
  (the ~54 real `(company, title)` collisions found in the
  `docs/SOURCE_OVERLAP.md` analysis) are not retroactively collapsed into
  `alt_listings` — that would mean picking a canonical row and deleting the
  others, a destructive change to already-tagged/ranked data that
  shouldn't happen as a migration side effect. Only newly-ingested items
  get folded going forward; a retroactive merge pass is a deliberate later
  call if it's ever wanted.
- **Known limitation, accepted rather than solved**: `dedup_key` has no
  location component. Checked real cross-source location strings before
  deciding this (e.g. ashby gives `"San Francisco"`, `vc_portfolio`'s
  Getro aggregator gives `"San Francisco, California, United States, San
  Francisco"` for the literal same posting) — location strings are too
  inconsistently formatted across sources to require an exact match
  without losing real matches to formatting noise, so `alt_listings`
  linking can occasionally attach to the "wrong" of two location-variant
  canonical rows when a source has more than one office open under the
  same title. Low stakes: no row is ever dropped either way, and
  `alt_listings` is a coverage signal ("did another source already catch
  this job"), not something driving a UI merge today.
- **Not built (deferred, not needed yet)**: no scheduler exists to make
  `times_seen`/`last_seen_at` meaningful over real calendar time yet (no
  `APScheduler` wiring found anywhere in `src/` at the time) — author
  planning that separately, likely with per-source cadence (data-change
  rate, paid-API cost, anti-bot risk all argue for different intervals per
  scraper, not one shared loop). No UI surface for `alt_listings`/
  `times_seen` either — an opt-in Browse-tab grouping ("x2 postings,
  expand") was discussed and intentionally left for later, only if
  near-duplicates turn out to be an obvious annoyance during actual use.

## 2026-07-02 — Run-log + cost tracking, industry/role taxonomy {#run-log-taxonomy}

**Commit:** `abebcd4`

Author wants a persistent log of items fetched/tagged/ranked per run (with
category breakdown) plus LLM cost/token spend, and asked to eventually track
job type/title and industry/sector (robotics, bio, etc.) and
remote/local/hyperlocal(SF) as well. Live-tested against the real,
then-7,412-row DB, same standard as the rest of the pipeline:

- **Schema**: new `run_log` table (`stage`, `source`, `run_at`,
  `duration_seconds`, `status`, `error`, `metrics` JSON) via a
  migration-safe `ALTER`/`CREATE`, same "everything in SQLite" convention
  as `preference_profiles`. One row per source per ingest run (cheap
  fetched/inserted/skipped counts, known before any LLM call runs — logged
  at ingest time, not deferred to tagging); one row per tagging run
  (tokens, cost, category/engagement_type breakdown); one row per rank run
  (items ranked, top score, active profile). Deliberately did not duplicate
  category/role/industry counts into `run_log`'s JSON — `items` already
  carries one row per tagged item with its own `tagged_at`, so historical
  breakdowns by any dimension are a `GROUP BY` away and don't need to be
  pre-baked into a log row.
- **New `items` columns**: `role_category` and `industry` (LLM-tagged,
  fixed enums, `tagger/schema.py`) plus `remote_type` (deterministic,
  derived from the already-scraped `location` field via
  `classify_location.py` — no LLM call needed). `role_category`'s starting
  taxonomy (`software_engineer`, `devops_infra_engineer`,
  `data_scientist`, `data_engineer`, `ml_ai_engineer`, `data_analyst`,
  `product_manager`, `designer`, `sales_marketing`, `ops_admin`, `other`)
  was built from the real distribution of already-tagged `role_type` free
  text (253 distinct values across then-566 tagged items — "software
  engineer" alone was 61) rather than guessed, per author's suggestion.
  `industry`'s starting list (`ai_ml`, `robotics`, `biotech_health`,
  `fintech`, `climate_energy`, `enterprise_saas`, `consumer_gaming`,
  `hardware_semiconductor`, `government_defense`, `other`) has no existing
  data to derive from, so it's a placeholder in the same spirit as the
  seeded default preference profile — expand as real items surface sectors
  that don't fit. `role_type` stays free text for detail/display;
  `role_category` is the normalized bucket for grouping/tracking. Same
  coercing-validator pattern as `seniority`/`engagement_type`: unknown
  values null out rather than failing the item. `remote_type`
  (`remote`/`hyperlocal_sf`/`bay_area`/`other`/`unknown`) was backfilled
  for free across all 7,412 existing items on the first `init_db()` run
  post-migration (no re-tagging needed, unlike `role_category`/`industry`)
  — verified distribution: 3,581 other / 2,065 hyperlocal_sf / 1,089 remote
  / 453 unknown / 224 bay_area.
- **Explicit author decision**: existing tagged items are left `null` for
  `role_category`/`industry` rather than re-tagged now (matches the
  `engagement_type` precedent) — re-tagging costs real API calls and
  wasn't asked for; new/re-ingested items get them going forward.
- **Cost tracking**: `tag_item()` now returns per-call `(model,
  input_tokens, output_tokens)` for every API call made (1, or 2 if
  escalated to Sonnet); `run_tagging.py` sums these and prices them against
  a small `MODEL_PRICING` table ($1/$5 per 1M tokens Haiku, $3/$15 Sonnet,
  checked 2026-07-02) into `cost_usd` on the `run_log` row.
- **Verified live, not just unit-level**: ingested a real batch from
  `remoteok` (100 fetched, 27 inserted, 73 deduped — correct `run_log`
  ingest row); ran the tagger on 5 real untagged items (correct `run_log`
  tag row: `haiku_calls`, `sonnet_calls`, tokens, `cost_usd`, category
  counts); confirmed the null-for-non-jobs path directly, then confirmed
  the populated path against a real ML-engineer job string
  (`role_category: "ml_ai_engineer"`, `industry: "ai_ml"`); ran the ranker
  and confirmed its `run_log` row (`items_ranked`, `top_score`, active
  profile name).
- **Known gap, not a bug**: pre-existing items show `role_category`/
  `industry` = null for the same reason `engagement_type` had this gap
  after it was added — they predate the field. Worth a deliberate re-tag
  pass later if one happens for another reason.
- **Not yet built**: no UI surface for `run_log` (e.g. a "Runs" tab) —
  wasn't asked for this pass, only the underlying logging.

## 2026-07-02 — Added-scrapers pass (same day, follow-up request) {#added-scrapers-pass}

**Commit:** `b0a17ea`

Author asked for 4 specific new sources to close a "SF AI/DS/ML, full-time +
freelance" gap: Ashby-hosted boards, VC portfolio boards, an AI-topical job
board, and Turing.com. Same build -> standalone test -> wire into
`ingest.py` -> live DB test -> verify dedup standard as every prior source.
Full detail in `TODO.md` and `docs/SOURCES.md`.

- **Ashby boards**: same public per-company JSON API shape as
  Greenhouse/Lever (`api.ashbyhq.com/posting-api/job-board/<name>`, no
  auth). Probed ~34 candidate SF AI-native company slugs; 14 confirmed live
  (`openai`, `notion`, `harvey`, `elevenlabs`, `cohere`, `langchain`,
  `linear`, `baseten`, `modal`, `ashby`, `anyscale`, `airbyte`, `pinecone`,
  `weaviate`). Verified `openai`'s 719 jobs are real, not a name collision,
  by inspecting sample URLs against OpenAI's actual careers page.
  `src/pipeline/scrapers/ashby.py`, wired into `ingest.py`. Live ingest:
  1,787/1,787 inserted, 0 dupes; re-run confirmed full dedup.
- **VC portfolio boards** (a16z, Sequoia, Greylock, Bessemer, Lightspeed,
  GV, Kleiner Perkins): several VC firms host a cross-portfolio job board
  on the Getro/Consider platform. No documented API — found the real
  endpoint (`POST <board_host>/api-boards/search-jobs`) by rendering
  `jobs.a16z.com/jobs` once with Playwright and capturing the real XHR the
  search box fires (observed, not guessed — same discovery discipline as
  the Dice DOM approach), then confirmed a plain `requests.post` works at
  runtime, no browser needed after discovery. Each board aggregates its
  entire portfolio (a16z alone: 15,478 jobs across every industry), so used
  the same `titlePrefix` keyword param the real UI uses with 3 DS/ML/AI
  keywords, mirroring the Meetup/Eventbrite keyword-search pattern rather
  than pulling everything. Two candidate boards (`generalcatalyst`,
  `khoslaventures`) 403'd on the first plain request — logged blocked per
  the hard anti-bot-safety rule, not retried; two more failed DNS outright
  and were dropped. `src/pipeline/scrapers/vc_portfolio.py`, wired into
  `ingest.py`. Live ingest: 591 inserted / 224 skipped on the first run —
  confirmed the 224 are genuine duplicates (several companies are backed
  by more than one firm in the list, so the same real job URL legitimately
  appears on multiple boards), not a scraper bug; re-run confirmed full
  dedup (0 new / 815 skipped).
- **aijobs.net**: topical AI/ML/DS-only board, so unlike the generalist ATS
  boards no keyword filter was needed — every listing is already
  in-domain, matching the original rationale for requesting this source.
  Plain server-rendered HTML (`?page=N`), no anti-bot on the first request,
  same class of source as Built In SF. The site's own filter form uses
  JS-populated `<select>`s (empty in raw HTML) — not driven via browser
  automation since plain pagination was sufficient for a scoped pull.
  Company name is absent from the list page (verified directly) and only
  appears on each job's detail page, so `fetch_raw()` makes one extra GET
  per job; kept to `PAGES=2` (100 jobs, ~150 total requests) as a
  placeholder volume, easy to raise later (see the fuller-fetch pass
  above). Confirmed (not a bug): a handful of location strings carry a
  mojibake byte where a country-name suffix should be, verified against
  the raw HTTP response, same category as the Luma mojibake precedent.
  `src/pipeline/scrapers/aijobs_net.py`, wired into `ingest.py`. Live
  ingest: 100/100 inserted, 0 dupes; re-run confirmed full dedup.
- **Turing.com**: checked and blocked. A single plain request to
  `turing.com/jobs` returned an Incapsula (Imperva) anti-bot challenge page
  (not real content) — stopped immediately per the hard anti-bot-safety
  rule, no retry or header rotation attempted. Checked Apify per the
  sanctioned fallback: no targeted Turing.com actor exists in the store
  (closest match was a generic mislabeled multi-source aggregator, same red
  flag as the rejected Handshake actor), so no paid test call was made.
  Turing's actual product model — developers apply to join a talent pool
  that's matched to clients, not an open browsable board — may not even
  expose scrapable listings the way this pipeline's other sources do.
  Staying dropped, no code written.
- **DB total after this pass**: 7,412 items across 18 sources (up from
  4,579 across 15 sources at the end of the prior overnight pass — part of
  the increase is also organic re-poll growth on already-wired sources,
  e.g. `hn_whoshiring` and `remoteok` picked up new postings between
  passes).

## 2026-07-02 — Overnight source-connection pass, continued {#overnight-pass-continued}

**Commit:** `b0a17ea`

Same session as the Indeed-via-Apify work below. Attempted every remaining
candidate source from `docs/SOURCES.md`; each reached a terminal, documented
state (built + live-tested, or blocked with a concrete reason) — full detail
and reasoning in `TODO.md` and `docs/SOURCES.md`, high points here:

- **Wellfound via Apify**: direct scrape stays hard-blocked (see below);
  evaluated 14 Apify store actors, deliberately passed over the
  highest-usage one (`orgupdate/...`) since that publisher's Handshake actor
  was already rejected as a mislabeled aggregator, picked
  `crawlerbros/wellfound-scraper` instead (narrowest scope, cheapest, no
  login). Verified real data via a 10-item test call before trusting it
  (cost ~$0.00005), then live-ingested 50 real items, 0 dupes, $0.02.
  `src/pipeline/scrapers/wellfound_apify.py`.
- **Contra**: checked Apify for a maintained actor per plan — all 3
  candidates found are freelancer-profile/lead-gen scrapers (for finding
  people to hire), not job/project listings to apply to. Contra's actual
  product shape doesn't fit this pipeline's purpose regardless of scrape
  quality; stays dropped, no code written.
- **Greenhouse** (`src/pipeline/scrapers/greenhouse.py`) and **Lever**
  (`src/pipeline/scrapers/lever.py`): both were Future/stretch, blocked
  only on needing a target company list. Tested candidate SF AI/DS/ML
  companies live against each platform's public per-company JSON API (no
  auth): 14 confirmed on Greenhouse, 4 on Lever (most non-Greenhouse
  companies tried turned out to use Ashby or a custom career page instead
  of Lever). Placeholder lists, same spirit as the seeded default
  preference profile. Live ingest: 3,187 + 329 real items, 0 dupes. High
  Greenhouse volume is expected — each board returns its entire open-roles
  list, no per-role filter in the public API; relevance filtering is left
  to the LLM tagger.
- **YC Work at a Startup** (`src/pipeline/scrapers/yc_workatastartup.py`): a
  bare `requests` call 406'd; realistic `Accept`/`Accept-Language` headers
  cleared it immediately (not an anti-bot block). The job list is embedded
  as JSON in the page's Inertia.js `data-page` attribute, no login/JS
  needed. No stable per-job public URL exists (same gap as Handshake) —
  built a synthetic dedup URL from the source's real job id against the
  (confirmed public) company profile page, same precedent as Handshake's
  content-hash approach. Live ingest: 55 real items (Engineering + Science
  categories), 0 dupes.
- **Dice** (`src/pipeline/scrapers/dice.py`): plain `requests` returns 200
  but no job data (client-rendered React app). Did not grep the site's
  minified JS bundles for its internal search API/key — the session's own
  safety controls flagged that as credential-hunting and blocked it;
  respected the block rather than working around it, and used Playwright to
  render the page and read job cards from the post-JS DOM instead (same
  technique already used for `wellfound.py`, no anti-bot wall encountered
  here so a single render pass sufficed). Live ingest: 20 real items, 0
  dupes.
- **Meetup** (`src/pipeline/scrapers/meetup.py`): old public REST API is
  dead (404, genuine deprecation). Checked whether Meetup's own frontend
  still calls something public — `api.meetup.com/gql-ext` answers real
  GraphQL queries with zero auth headers, same "unofficial but genuinely
  public, no credential needed" shape as Luma's discover API already used
  in this project (a meaningfully different situation from the Dice case
  above, where no such public endpoint existed and the internal-API route
  was correctly dropped instead). Live ingest: 64 real SF AI/ML events
  across 3 keyword searches, 0 dupes.
- **Eventbrite** (`src/pipeline/scrapers/eventbrite.py`): same move as
  Meetup — old public search API is dead (404), but the public search
  website embeds real first-page results as JSON (`window.__SERVER_DATA__`)
  in plain server-rendered HTML, no auth/JS needed. Live ingest: 46 real
  SF-area DS/ML/AI events, 0 dupes, genuine stable per-event URLs (no
  synthetic dedup key needed, unlike Handshake/YC).
- **Handshake, made live**: both prior blockers (see below) are now
  cleared. Added `fetch_emails_from_gmail()` to `handshake_email.py`,
  searching `from:handshake@g.joinhandshake.com` against
  the connected university email address and parsing HTML bodies directly with the
  same `parse_email_html()` logic (verified unchanged against a real
  live-fetched email). `fetch_raw()` tries Gmail first, falls back to the
  fixture files only if that fails. Live-tested: 10 real emails -> 48
  parsed job cards -> 37 new / 11 correctly deduped on ingest (DB now has
  47 real Handshake items).
- **LinkedIn email, rechecked**: still blocked, see "Blocked / deferred"
  entry below.
- **Budget**: $25 Apify cap for the whole pass. Actual spend: ~$0.02
  (Wellfound) + $0.12 (Indeed, see below) = ~$0.14 total, well under.
- **DB total after this pass**: 4,579 items across 15 sources (up from 718
  at the end of the freelance-sourcing sub-feature pass).

**Blocked / deferred at this point, needs follow-up:**
- LinkedIn email parser: still blocked, not started. No LinkedIn alert
  email exists in the connected Gmail account, and unlike Handshake there's
  no LinkedIn setting found yet to redirect alerts to a different address —
  needs a manually forwarded/saved real alert email before this can be
  built. Rechecked same day now that the pipeline has its own Gmail API
  access (201 "linkedin" keyword matches inspected, none from an actual
  `linkedin.com` sending domain) — still nothing, staying blocked.
  Deprioritized same day: pushed to much later and no longer intended as a
  standalone source build — `linkedin_apify.py` already covers LinkedIn
  jobs directly. If/when a real alert email does surface, repurpose it for
  the evaluation pass instead (`TODO.md` section 6): extract the jobs it
  lists and check whether the scrapers (`linkedin_apify` or others) already
  captured the same postings, as a coverage sanity check rather than a
  parser to build and maintain.
- Evaluation (60-item ground truth set, accuracy/F1/Spearman/confusion
  matrix): not started, intentionally deferred since it depends on tagged
  data existing (it now does — natural next step at the time).
- Notifications (section 8): not started, explicitly deferred per
  first-pass scope.
- A real `ANTHROPIC_API_KEY` landed in `.env` (gitignored, not committed)
  and the tagger has been run against it successfully — this blocker from
  the previous pass is resolved.

## 2026-07-02 — Indeed via Apify (overnight source-connection pass) {#indeed-apify}

**Commit:** `b0a17ea`

Indeed's public RSS feed is confirmed dead (retired by Indeed, 404 on every
query — `indeed_rss.py` kept as-is, correct/reusable if Indeed ever restores
it). Went straight to a managed Apify actor rather than attempting a direct
HTML scrape. Searched the Apify store for "indeed": picked
`misceres/indeed-scraper` over roughly a dozen similarly-named competitors on
usage alone — 26,122 users / 1,695,895 runs, an order of magnitude ahead of
the next-closest. Same extra-scrutiny standard as the Handshake-actor
rejection and the Wellfound-actor pick (see `docs/SOURCES.md`), easily
cleared here by volume. Verified before trusting it: ran a 10-item test call
(position="data scientist OR machine learning OR artificial intelligence",
location="San Francisco, CA", cost $0.045) and inspected results directly —
real `indeed.com/viewjob?jk=<id>` URLs, real companies matching real titles
(DocuSign "Senior Data Scientist - Growth Marketing", Harvey "Data
Scientist, Product", Socure "Senior Data Scientist..."), real salary ranges
and ISO-parsed posting dates — not aggregator junk like the rejected
Handshake actor. Built `src/pipeline/scrapers/indeed_apify.py` (same shape
as `linkedin_apify.py`/`wellfound_apify.py`), wired into `ingest.py` under a
new `indeed_apify` key (kept separate from the dead `indeed_rss` key).
Live-tested through the full ingest pipeline: 10/10 inserted with 0 dupes,
then a re-run confirmed dedup (7 new / 3 skipped — Indeed's live search
results shifted slightly between the two ~2-minute-apart runs, expected for
a live time-sensitive search, not a dedup bug). Cost: $0.12 total across the
test call + two ingest runs. Full detail in `docs/SOURCES.md`.

## 2026-07-02 — First overnight scaffold pass {#first-scaffold-pass}

**Commits:** `35df650`, `8b11bf1`, `611ad28`, `81f4c07`

Landed an end-to-end working pipeline (scraper -> DB -> ingest -> tagger ->
ranker -> UI), all code under `src/pipeline/`. Details and per-item status
are in `TODO.md` (checked off section by section).

**Event tracking frozen** (commit `8e7125d`, separate from the scaffold
commits above): with 4 days left before the capstone
presentation/submission, author's priority is the job tracker working well,
not event tracking. Events (Luma/Meetup/Eventbrite) were muddying the
default job view and author is unconvinced they belong in this DB at all vs.
a calendar tool — decided to freeze rather than build a parallel
tagger/ranker for them (would've been new scope this week for a
non-priority feature). `run_ingest()` in `src/pipeline/ingest.py` now
defaults to skipping `luma_events`, `meetup`, and `eventbrite` via a
`FROZEN_SOURCES` set — scraper code and DB rows are untouched, not deleted,
so this is reversible (`run_ingest(sources=[...])` still works to re-enable
one explicitly). `src/pipeline/ui/app.py` adds a sidebar checkbox "Show
events & networking" (default off) that filters both the Browse and Digest
tabs down to jobs-only by default. Already-ingested event rows stay in
`data/pipeline.db` for now; whether to move them out to a calendar tool
instead is a deliberate later decision, not done here.

**Working end-to-end, tested against real (not mocked) data:**
- Scrapers: HN Who's Hiring (491 live items via HN Algolia API), Luma SF
  events (50 live items via the unofficial no-auth
  `api.lu.ma/discover/get-paginated-events`), Built In SF (25 live items via
  plain `requests`+bs4 against `builtinsf.com/jobs`, server-rendered, no
  anti-bot encountered). Indeed RSS is built but **dead** — Indeed retired
  public RSS feeds, confirmed 404 (superseded same day by `indeed_apify.py`,
  see above). Wellfound direct-scrape is built but **hard-blocked by
  DataDome CAPTCHA** (403 on every job-bearing URL; tried UA spoofing,
  referer warm-up, non-headless, webdriver masking, simulated mouse/scroll —
  all still blocked). Genuine technical block, not a ToS retreat — matches
  CLAUDE.md's own carve-out for dropping a source. `fetch_raw()` correctly
  returns `[]` and logs why rather than fabricating data. Superseded same
  day by `wellfound_apify.py` (see above) for real data.
- Storage: SQLite schema at `src/pipeline/storage/schema.sql` (`items` +
  `preference_profiles` tables), WAL mode, single-writer `asyncio.Queue` in
  `src/pipeline/storage/db.py`. DB file at `data/pipeline.db` (gitignored).
- Ingest: `src/pipeline/ingest.py` normalizes HN/Luma/Indeed/BuiltIn/Wellfound
  raw output into the `items` schema and writes through the queue. Note:
  scraper fetches now run via `asyncio.to_thread` — sync Playwright (used by
  the Wellfound scraper) cannot run directly inside ingest's asyncio event
  loop, and this crashed with a Playwright sync/async-loop error before the
  fix. Live-tested: 566 items now in DB (491 HN + 50 Luma + 25 Built In),
  dedup verified by re-running (second pass correctly skipped all
  previously-seen items as duplicates on `UNIQUE(source, url)`).
- Ranker: `src/pipeline/ranker/rank.py`, reads the active
  `preference_profiles` row (seeded default: generic SF DS/ML/AI keywords,
  category weights job=1.0/event=0.6/networking=0.5) and ranks by
  relevance_score * weight + deadline-urgency boost. Tested against all 566
  real tagged items; top results are plausible (e.g. "Staff Data Scientist -
  Product Analytics" at 9.0).
- LLM tagger: fully tested live against all 566 real items, 100% tagged, 0
  failures. 334 job / 193 irrelevant / 21 event / 18 networking; 554 stayed
  on Haiku, 12 escalated to Sonnet. Found and fixed 4 real bugs in this pass
  (full detail in `TODO.md` section 4): tagger was never shown `title`
  (caused a real event to be misclassified as irrelevant), deadlines
  without a year were hallucinated to the wrong year (no "today" context in
  the prompt), ~11% of items failed validation on a free-text `seniority`
  value outside the fixed enum (added a coercing validator + tightened the
  prompt), and the rest failed on trailing prose after the JSON object
  (switched to `raw_decode` to parse just the first JSON object). Also
  confirmed (not our bug) that Luma's own API serves mojibake text for some
  descriptions — verified directly against the raw HTTP response before our
  code touches it.
- UI: `src/pipeline/ui/app.py` (Streamlit, run via `streamlit run
  src/pipeline/ui/app.py`). Actually browser-tested with Playwright
  (navigate, screenshot, click tabs, exercise the search box) against the
  real fully-tagged DB, not just an HTTP-200 ping. Found and fixed 2 real
  bugs this way: missing titles rendered as the literal text "nan" (pandas
  loads SQL NULL as float NaN, which is truthy in Python, so `row["title"]
  or fallback` never fell back — fixed with `pd.notna()`), and the search
  box crashed on regex special characters like "C++" because it was passed
  straight into `pandas.str.contains` as a regex pattern — fixed with
  `regex=False`.

## 2026-06-24 — Freelance/project-based sourcing sub-feature {#freelance-sourcing}

**Commit:** `b0a17ea`

Author's actual job-hunt priority shifted to freelance/contract/project AI
engineering work (self-paced/a la carte) over full-time roles; the pipeline
had never modeled engagement type before this. Built as an additive
sub-feature on the existing scraper -> ingest -> tagger -> ranker -> UI
plumbing, not a parallel system. Tested end-to-end against real data, same
standard as the rest of the pipeline:

- Researched freelance/AI marketplaces for scrapability before building
  anything (HTTP status checks, anti-bot marker scans, live Playwright render
  checks where a page was JS-rendered). Picked **We Work Remotely** (public
  category RSS feeds, no auth/anti-bot) and **RemoteOK** (public JSON API,
  no auth/anti-bot, ToS just asks for attribution). Dropped Toptal/Catalant
  (HTTP 403, hard-blocked), Upwork (explicit ToS ban on automation + stacked
  Cloudflare/DataDome anti-bot), Braintrust (not blocked, but its public page
  is teaser cards with no stable per-item URL — real listings sit behind a
  separate gated app), Gun.io (signup-gated, no real listings visible without
  an account), A.Team (404, invite-only curated network), and Contra (no
  official API). Same "drop only if genuinely blocked" bar as the existing
  Wellfound precedent.
- Schema: added `engagement_type` to `items` and `engagement_weights` to
  `preference_profiles` via a migration-safe `ALTER TABLE` (since `CREATE
  TABLE IF NOT EXISTS` doesn't touch existing tables) — ran live against the
  real, then-566-row `data/pipeline.db`; verified no data loss and the
  existing profile backfilled with `{"freelance": 1.0, "project_based": 1.0,
  "contract": 0.8, "full_time": 0.4}`.
- Scrapers: `src/pipeline/scrapers/weworkremotely.py` (54 real entries) and
  `remoteok.py` (100 real entries), wired into `ingest.py`. Live ingest run
  added 152 new real items, DB now at 718 total.
- Tagger: `engagement_type` extraction added to `TagResult` with a coercing
  validator mirroring the seniority pattern (the lesson from that earlier
  ~11% failure rate — constrain the prompt enum tightly, coerce free-text
  values to `null` instead of failing the item). Tagged live against all 152
  new items: 0 failures. 97 `full_time` / 15 `freelance` / 7 `contract` / 4
  `project_based` / rest `null`. Real hit: "Lemon.io: Senior AI Engineer /
  Architect" tagged `freelance`, relevance 8.5.
- Ranker: `engagement_weights` applied multiplicatively alongside
  `category_weights`; unstated `engagement_type` defaults to weight 1.0
  (most items) rather than being penalized. Verified live: two items with
  identical `relevance_score=8.5`, the one tagged `full_time` scored 3.40,
  the one tagged `freelance` kept the full 8.50 — freelance/project work
  now reliably outranks equivalent full-time listings.
- UI: added an "Engagement type" filter to the Browse tab, shown inline per
  item and as a Digest table column. Browser-tested live with Playwright
  against the real 718-item DB: filtering to `freelance` produced exactly 15
  results (matching a direct DB query); no regressions to existing filters,
  search, or the score histogram.
- **Known gap, not a bug:** the pre-existing 566 items still show
  `engagement_type = null` because they were tagged before this field
  existed — they were never re-tagged, so this isn't the LLM judging them
  unstated. Backfilling would mean re-running real (costed) API tagging
  calls against already-tagged items; left out of scope since the task only
  called for testing against the newly-ingested items. Worth a deliberate
  re-tag pass later if/when one happens for another reason.

## 2026-06-24 — Handshake email parser {#handshake-parser}

**Commit:** `b0a17ea`

Got 2 real Handshake alert emails by reading the user's connected Gmail account
directly (the originals were already there, no forward needed), saved as HTML
fixtures in `data/samples/handshake/`, and built
`src/pipeline/scrapers/handshake_email.py` against the real markup (`<a
class="job-list-content-link">` cards with employer/title/meta spans). Tested
live: 10/10 real job cards parsed with 0 failures, wired into `ingest.py`'s
`NORMALIZERS`, inserted into the real DB with correct dedup verified on
re-run. Used a content hash (company+title+work_type) as the dedup key
instead of Handshake's own link, since that link is a one-time
email-tracking redirect that changes per send, not a stable per-job URL.
