# Changelog

- **2026-08-27** — Fixed Batch API 413 on large backlogs: the tagger cost-cut
  commit submitted the entire untagged backlog as one Message Batches API
  call, which hit Anthropic's 256MB request-size cap at ~15k queued items.
  Added 500-item chunking (`MAX_BATCH_SIZE` in `batch_tagging.py`), sequential
  per-chunk submit/poll/collect. Verified live: full 15,222-item backlog
  tagged across 31 chunks, 15,215 succeeded / 7 failed (parse errors, not
  systemic) for $17.54 total — in line with the batch-lane discount vs. the
  ~$73 realtime-rate estimate from the pre-cost-cut code.
- **2026-08-26** — Tagger cost cuts: prompt caching, Batch API lane, and a
  fast/slow-lane split by company whitelist. Found and fixed a real bug along
  the way — Haiku 4.5's minimum cacheable prompt is 4,096 tokens (not the
  commonly-cited 1,024/2,048), so the original system prompt + few-shot block
  (~2,657 tokens) was silently never caching; closed the gap with genuinely
  useful disambiguation content, not padding. Verified live: cache writes then
  reads correctly, and a real 4-item batch tagging run completed end-to-end
  with zero failures. → [detail](HISTORY.md#tagger-cost-cuts)
- **2026-08-26** — Scraper fetch parallelization: `run_ingest()` now fetches
  all sources concurrently (`asyncio.gather`) instead of one at a time;
  `linkedin_apify`/`wellfound_search`'s internal multi-query fan-outs and
  `greenhouse`/`ashby`/`vc_portfolio`'s per-board(/keyword) HTTP fetches now
  run through thread pools instead of sequential loops (Greenhouse alone was
  248 sequential board GETs). Verified live: 10 Greenhouse boards completed
  in 1.4s concurrent vs. one-at-a-time before. → [detail](HISTORY.md#scraper-fetch-parallelization)
- **2026-08-26** — Scheduler moved to the Mac mini (always-on host) and
  `pipeline.db` synced there; the Mini is now the live/current copy going
  forward, Windows is a secondary/fallback copy. Started a deliberate 2-week
  daily-cadence calibration trial (`DAILY_TRIAL_END` in `scheduler.py`,
  ends 2026-09-09) instead of guessing per-source poll intervals. Windows
  Task Scheduler registration superseded, not needed. →
  [detail](HISTORY.md#scheduler-moved-to-mac-mini)
- **2026-08-26** — Read-only MCP server for external humans/agents: new
  `src/pipeline/mcpserver/` module exposing `search_items`/`rank_items`/
  `export_top_n` (hard-capped at 50 items, custom caller-supplied ranking
  weights only — the author's own tuned preference weights never exposed), API-key
  auth + rate limiting, deployed via ngrok tunnel and live-tested against
  the real DB (local smoke tests + external test client). →
  [detail](HISTORY.md#read-only-mcp-server)
- **2026-08-26** — Telegram run-summary notifications: new
  `src/pipeline/notifications/` module (`telegram.py` sendMessage wrapper,
  `notifier.py` digest builder off existing `run_log` rows), hooked into
  `scheduler.py`'s nightly tag+rank job. Reuses the bot token already
  provisioned for a separate personal Telegram/Claude gateway project rather than a new bot.
  Reports items scraped/tagged/ranked per source and any errors; no
  per-item alerting yet — `notify_high_priority_items()` is a deliberate
  stub pending a company whitelist the author hasn't defined. Live-tested
  against the real DB and a real Telegram delivery. →
  [detail](HISTORY.md#telegram-run-summary-notifications)
- **2026-07-05** — AI-Trainer-gig derank fix: added `role_category` value
  `ai_data_labeling` (schema + prompt) and a 6th ranker weight table
  (`role_category_weights`, 0.15 for this bucket, neutral elsewhere).
  Regex-backfilled 294 already-tagged AI-Trainer/data-annotation/RLHF-rater
  items with no re-tag needed (zero API cost). Verified: top-50 by
  `preference_score` went from 36/50 data-labeling gigs to 0/50 after
  re-running the ranker. → [detail](HISTORY.md#ai-trainer-derank-fix)
- **2026-07-05** — AI usage citation pass: reconstructed per-file prompt
  attribution for all 45 `src/pipeline/` source files from Claude Code
  session transcripts (including 5 files built by a sub-agent, discovered
  via a separate scan since they were invisible to a top-level-only
  transcript walk). Each file got a short `AI USAGE CITATION` header;
  full quotes live in `docs/ai_usage/prompt_log.md`. Where a file's real
  triggering prompt couldn't be cleanly isolated, that's stated plainly
  rather than fabricated — and the full raw transcripts (69 sessions, one
  live Apify API token pattern redacted) were archived to
  `docs/ai_usage/transcripts/` as backing evidence, so "not recoverable"
  points to real primary-source material instead of reading as a dead
  end. → [detail](HISTORY.md#ai-usage-citation-pass)
- **2026-07-05** — Apply button made a toggle (Apply/Unapply, matching the
  existing Save/Unsave pattern); reset 2 items accidentally marked "applied"
  during UI testing back to untriaged. Added `deadline` to the urgency-sort
  item display and Metrics table. Logged an open TODO on whether
  event/networking category filtering belongs in the main Browse tab or a
  separate one. → [detail](HISTORY.md#apply-toggle-urgency-deadline)
- **2026-07-04** — DevRel Engineer ranking proposal (not applied — awaiting
  author decision): found the ranker doesn't weight `role_category` at all
  today; id 25978's high manual rank comes entirely from existing
  freelance/junior/ai_ml weights, not anything DevRel-specific. Two options
  written up with a 53-item retag blast-radius estimate. →
  [proposal](docs/reports/devrel_ranking_proposal_2026-07-04.md)
- **2026-07-04** — Scoped coverage-gap estimate: live-probed 4 new
  Greenhouse/Ashby boards (633 combined jobs), rough extrapolation suggests
  60-90% of the "top 500-2,000 SF AI companies" universe still uncovered.
  Incidental bug found: `sierra`/`writer` Ashby boards configured but never
  ingested (0 items in DB despite real live job counts). →
  [report](docs/reports/coverage_gap_estimate_2026-07-04.md)
- **2026-07-04** — Deadline field validation: found a real "internal-target
  date vs. applicant-facing deadline" bug (a pre-funding co-founder pitch with
  no real applicant deadline got a hallucinated `deadline` from unrelated
  funding-target language). Documented, not fixed yet (no bulk tagging this
  pass). → [detail](HISTORY.md#deadline-field-internal-target-example)
- **2026-07-04** — Tagger provider abstraction: `TaggerClient` interface with
  an Anthropic implementation (today's behavior, unchanged, smoke-tested live)
  and a stubbed GLM 5.2 implementation, switchable via `TAGGER_PROVIDER` env
  var. GLM model ids/pricing are placeholders pending a real API key. →
  [detail](HISTORY.md#glm-provider-abstraction)
- **2026-07-04** — Streamlit UI: replaced thumbs up/down with a single
  `application_status` workflow field (saved/not_interested/applied/
  callback/interview/offer), a "Save"/"Not Interested" (with reason) button
  pair, a new Saved tab, "Digest" renamed to "Metrics", and a `@st.fragment`
  + pagination performance pass so tab/filter/button interactions no longer
  rerun the whole page. → [detail](HISTORY.md#application-status-workflow)
- **2026-07-03** — Added weekly meta-analysis report (counts by source,
  category, remote-type, normalized top locations, spam/quality signal;
  rolling window + all-time comparison, derived fresh from DB timestamps
  each run). Tagging backlog finished this run: 28,893/28,893 (100%). →
  [latest report](docs/reports/weekly_2026-07-03.md),
  [detail](HISTORY.md#weekly-meta-analysis-report)
- **2026-07-03** — YC public-directory Greenhouse discovery pass: pulled all
  6,004 YC portfolio companies from ycombinator.com's public Algolia search
  index, derived slug candidates not already in the DB, probed live — 91 new
  verified boards (248 total, up from 157). 1,811 new items ingested
  (28,893 total in DB, up from ~27,000). →
  [detail](HISTORY.md#yc-directory-greenhouse-discovery)
- **2026-07-03** — Renamed project "Opportunity Pipeline" -> "Jobs Pipeline"
  (repo already moved to `jjchong5/jobs` in a prior session); reframed
  CLAUDE.md/README.md pitch to lead with job-tracking, events/networking as
  secondary/frozen. No code, schema, or module-name changes. →
  [detail](HISTORY.md#project-rename-scope-framing)
- **Uncommitted.** `linkedin_apify` now fans out across 4 varied search
  queries per run instead of one (live overlap probe showed only 0.9-15.1%
  pairwise duplication between queries) — 531 unique jobs for ~$0.43 vs.
  ~180 for ~$0.18 previously. Also audited all recent raw test-pull files
  for DB gaps; none found beyond what the fan-out itself added. →
  [detail](HISTORY.md#linkedin-query-fanout)
- **2026-07-03** — Greenhouse company-name discovery pass: mined 436 company
  names already in the DB from `yc_workatastartup`/`vc_portfolio`, generated
  slug candidates, probed live — 91 new boards (158 total, up from 67).
  15,188 items in DB (up from 7,404). →
  [detail](HISTORY.md#greenhouse-company-discovery)
- **Uncommitted.** Added `ingest.ingest_raw_file()` to ingest an already-fetched
  raw JSON file without re-invoking a source's live (paid) `fetch_fn` — see
  `HISTORY.md#ingest-raw-file-spend-trap`.

Short, newest-first index of what landed in each work pass. Full narrative
detail (what was tried, bugs found, live-test numbers) lives in
`HISTORY.md`, linked per entry below. For the current, non-historical
snapshot of what's built/live/blocked, see CLAUDE.md's Current State
section. For per-source status in table form, see `docs/SOURCES.md`. For
remaining work, see `TODO.md`.

Note on commit references: several entries below share a commit hash
because that work was committed as one batch after the fact rather than
commit-per-sub-feature (mainly `b0a17ea`, which bundles Handshake email,
freelance sourcing, Indeed/Wellfound-via-Apify, and both the overnight
source-connection and added-scrapers passes). Two recent entries are
flagged uncommitted — they match pending changes in the working tree as of
this writing.

- **2026-07-03** — Greenhouse full-volume pass: probed ~196 more candidate
  company boards live, added 41 confirmed-live tokens (67 total). 7,617 raw
  items fetched (up from 3,187), 4,217 new inserted / 3,399 deduped. →
  [detail](HISTORY.md#greenhouse-full-volume-pass)
- **2026-07-03** — Fixed `company_stage` false-positive: 237 OpenAI/Anthropic
  postings tagged "public" (both private) because the model keyed off
  "public benefit corporation" boilerplate — caught by user spot-check on
  the QA report. *(uncommitted)* →
  [detail](HISTORY.md#company-stage-public-benefit-bug)
- **2026-07-03** — Saved the source-overlap analysis as a reusable script
  (`src/pipeline/analysis/source_overlap.py`, `python -m
  pipeline.analysis.source_overlap`) instead of leaving it as one-off
  scratchpad code — re-run it directly next time `docs/SOURCE_OVERLAP.md`
  needs refreshing. → [detail](HISTORY.md#source-overlap-script)
- **2026-07-03** — Indeed radius search (`indeed_radius`) replaces
  `indeed_apify` (renamed `indeed_apify_old`, frozen) as the default Indeed
  source: native `radius` param closes the SF/San Jose non-overlap gap,
  ~4x cheaper (~$0.00125/item vs $0.005/item). Old actor kept live in the
  codebase, not deleted, as a fallback. *(uncommitted)* →
  [detail](HISTORY.md#indeed-radius)
- **2026-07-03** — Refreshed source-overlap analysis at 11,858 items (up
  from 7,412) and fixed `linkedin_apify` dedup: its Apify actor URL isn't a
  stable per-posting id (unlike every other source), so `UNIQUE(source,
  url)` missed 37% of its rows as duplicates. `insert_item_sync` now folds
  same-source `(dedup_key, location)` matches like a same-URL repost.
  `6274f05` → [detail](HISTORY.md#linkedin-apify-dedup-fix)
- **2026-07-03** — Raw-text truncation cap raised 4000→12000 chars: was
  cutting 71.6% of the untagged backlog (avg ~30% of content lost, worst case
  78-88%); new cap covers 99.2% for ~$4.60 extra total. *(uncommitted)* →
  [detail](HISTORY.md#raw-text-truncation-cap)
- **2026-07-03** — Tagging concurrency default raised 5→15 after checking the
  account's actual rate-limit headroom (10k req/min, 12M tokens/min) — local
  system specs aren't the relevant ceiling for an I/O-bound job.
  *(uncommitted)* → [detail](HISTORY.md#tagger-concurrency-default)
- **2026-07-03** — Tagging-run re-entrancy lock + bounded concurrency: fixes a
  real ~$2 double-tagging race on `wellfound_search`; `--concurrency` flag
  parallelizes API calls (DB writes stay sequential). *(uncommitted)* →
  [detail](HISTORY.md#tagger-concurrency)
- **2026-07-03** — Relevance/ranking rework: split the old single
  `relevance_score` into `content_quality` (internal QA signal),
  `spam_risk`, `role_expectation_delta`/`_notes`, and `company_stage`;
  replaced the old multiplicative ranker with three named rank-time scores
  (`urgency_score`/`preference_score`/`general_score`) driven by 5 explicit,
  user-tunable weight tables. *(uncommitted)* → [detail](HISTORY.md#ranking-rework)
- **2026-07-03** — Fuller-fetch pass on the still-capped free sources: raised
  hard caps on `vc_portfolio.py` (pagination added, 100→265+ items),
  `aijobs_net.py` (2→20 pages), and added ~29 more AI-native companies
  across Greenhouse/Lever/Ashby. *(uncommitted)* → [detail](HISTORY.md#fuller-fetch-pass)
- **2026-07-03** — `wellfound_apify` renamed to `wellfound_apify_old` to read
  unambiguously as archived. *(uncommitted)* → [detail](HISTORY.md#wellfound-rename)
- **2026-07-03** — Clarified: freelance-preference is a ranking signal, not a
  sourcing filter — keep ingesting full-time roles too. → [detail](HISTORY.md#data-breadth-stance)
- **2026-07-03** — Wellfound role+location search (`wellfound_search_apify`)
  replaces the flat-feed `wellfound_apify` (84.2% vs 14% relevance hit-rate);
  old source mothballed. `fa4de91` → [detail](HISTORY.md#wellfound-search)
- **2026-07-02** — Scheduler: APScheduler with per-source cadence, all live
  sources default to once/day. *(uncommitted)* → [detail](HISTORY.md#scheduler)
- **2026-07-02** — Repost/cross-source dedup tracking: `times_seen`,
  `last_seen_at`, `dedup_key`/`alt_listings` linking across sources.
  `abebcd4` → [detail](HISTORY.md#dedup-tracking)
- **2026-07-02** — Run-log + cost tracking, `role_category`/`industry`/
  `remote_type` taxonomy added to `items`. `abebcd4` → [detail](HISTORY.md#run-log-taxonomy)
- **2026-07-02** — Added-scrapers pass: Ashby boards, VC portfolio boards
  (Getro), aijobs.net; Turing.com blocked (Incapsula). `b0a17ea` → [detail](HISTORY.md#added-scrapers-pass)
- **2026-07-02** — Overnight source-connection pass: Wellfound-via-Apify,
  Greenhouse, Lever, YC Work at a Startup, Dice, Meetup, Eventbrite,
  Handshake made live via Gmail. `b0a17ea` → [detail](HISTORY.md#overnight-pass-continued)
- **2026-07-02** — Indeed via Apify (`indeed_apify`), replacing the dead
  public RSS feed. `b0a17ea` → [detail](HISTORY.md#indeed-apify)
- **2026-07-02** — First overnight scaffold pass: end-to-end pipeline
  (scraper→DB→ingest→tagger→ranker→UI) live-tested against 566 real items;
  event tracking frozen. `35df650`, `8b11bf1`, `611ad28`, `81f4c07`, `8e7125d`
  → [detail](HISTORY.md#first-scaffold-pass)
- **2026-06-24** — Freelance/project-based sourcing sub-feature: We Work
  Remotely + RemoteOK scrapers, `engagement_type` schema + ranking weights.
  `b0a17ea` → [detail](HISTORY.md#freelance-sourcing)
- **2026-06-24** — Handshake email parser, built against real alert emails.
  `b0a17ea` → [detail](HISTORY.md#handshake-parser)
