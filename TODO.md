# TODO

See `CLAUDE.md` for architecture/stack rationale, `CHANGELOG.md`/`HISTORY.md`
for what's already shipped and why, and `docs/SOURCES.md` for the full
per-source tracker (built/blocked/dropped with reasoning). This file is
open work only — once an item ships, it moves to CHANGELOG/HISTORY instead
of staying here as a checked box.

## Priority (highest first)

1. **Coverage audit + comprehensive AI-relevant company sourcing (top
   500-2,000 SF companies), prioritized above other open work (2026-07-04
   direction from author).** Two Greenhouse expansion passes so far
   (company-name mining from existing DB data, then the full public YC
   directory — see `HISTORY.md#yc-directory-greenhouse-discovery`) both
   worked from *existing structured lists* (DB contents, then YC's own
   directory). A genuinely comprehensive "top AI-relevant SF companies" list
   needs a different kind of sourcing: broader internet/event search — local
   news, Luma events (even though the source itself is frozen, the event
   listings themselves are a company-discovery signal), funding
   announcements, fringe/niche job boards not yet evaluated, etc. — not just
   probing another existing directory. No free/easy single API covers this;
   expect this to be a real research task, not a quick script.
   - [x] **Estimate current coverage gap — scoped slice done 2026-07-04.**
         Live-probed 4 confirmed-new Greenhouse/Ashby boards (`together-ai`,
         `decagon`, `vanta`, `crusoe` — 633 combined live jobs, comparable in
         scale to several already-tracked companies) against ~25 total
         guesses (~16% hit rate, consistent with prior passes). Rough,
         explicitly-approximate extrapolation: likely **60-90% of the
         "top 500-2,000 SF AI companies" universe still uncovered** by
         company count. Full method/numbers/caveats:
         `docs/reports/coverage_gap_estimate_2026-07-04.md`. Confirms this
         pass's existing framing — the binding constraint is finding company
         *names*, not probing capacity; slug-guessing alone won't close this,
         needs the broader research pass already described above.
         **Incidental bug found, not fixed:** `sierra` and `writer`, both
         already in `ashby.py`'s `BOARD_NAMES`, have **zero items in the DB**
         despite live-confirmed to currently return real jobs (147 and 49
         respectively) — a real "configured but never ingested" gap, separate
         from the new-company-sourcing question. Worth a quick investigation
         (check `ingest.py`'s `NORMALIZERS`/`FROZEN_SOURCES` wiring for these
         two board names specifically) before the next Ashby re-fetch.
   - [ ] Add more companies (target list expansion, same discovery methods
         as above) and evaluate fringe/less-obvious job sites not yet tried
         (beyond the current 19 live sources — see `docs/SOURCES.md` for
         what's already covered vs. dropped/blocked).
2. **Tagging backlog** — see Section 4 for current numbers (Current State's
   snapshot may be stale; check `SELECT COUNT(*) FROM items WHERE
   tagged_at IS NOT NULL` vs. total for the live figure).
3. **Evaluation** — not started at all; data now exists to support it.
   See Section 6.
4. **Scheduler cadence calibration** — intervals are still a single-snapshot
   guess. See Section 3b.
5. **Apify plan review** — decide Free vs. Starter once steady-state spend
   is known. See Section 3b.
6. **Notifications** — Telegram run-summary digest shipped 2026-08-26;
   per-item high-priority alerts still open (blocked on a company
   whitelist). See Section 8.
7. **Capstone admin** — proposal, Drive setup, peer posts, presentation,
   AI usage statement. See last section.

## 0a. Apify actor exploration (deferred until after 2026-07-06 capstone submission)
- [ ] `worldunboxer/rapid-linkedin-scraper` location-sensitivity check: rerun
      against a different, less SF-saturated location (e.g. "United States"
      or a second city) to see whether the ~2,047-item genuine-exhaustion
      ceiling found for "data scientist"/San Francisco Bay Area
      (`HISTORY.md` — Apify actor vetting investigation, 2026-07-03) holds
      generally or was specific to how deep LinkedIn's SF Bay Area DS
      listings run. Explicitly deferred so this exploratory spend/data
      doesn't muddy the dataset right before Sunday's submission — do not
      run this before then.

## 0. Setup
- [ ] LinkedIn job-alert email parser — still blocked (no sample email
      ever found), deprioritized indefinitely. `linkedin_apify` already
      covers LinkedIn directly. If a real alert email ever surfaces, use
      it only as an eval-time coverage cross-check (Section 6), not as a
      new source to build. See `docs/SOURCES.md` "Not started" table.
- [ ] Handshake email-parse: `.env` real `ANTHROPIC_API_KEY` — confirm
      still set; everything else in this section shipped (see
      `docs/SOURCES.md`).

## 1. Scrapers/parsers
Done — 20 sources live across email/API/RSS/HTML-scrape/JS-scrape/Apify
methods, ~12,794 items in the DB as of 2026-07-03. Full build narrative,
per-source test numbers, and drop reasoning (Toptal, Upwork, Braintrust,
Gun.io, A.Team, Contra, Turing.com, Wellfound direct) live in
`docs/SOURCES.md` and `HISTORY.md` — nothing left open here.

## 2. Storage
Done — schema, WAL mode, single-writer queue, engagement_type +
ranking-rework columns (`content_quality`, `spam_risk`,
`role_expectation_delta`/`_notes`, `company_stage`) all migrated live
against the populated DB. See `HISTORY.md#ranking-rework`.

## 3. Ingest pipeline
Done — scraper → normalizer → DB, dedup by `(source, url)` plus a
`(dedup_key, location)` fallback for `linkedin_apify`'s unstable URLs
(`HISTORY.md#linkedin-apify-dedup-fix`).

## 3b. Scheduler
- [x] APScheduler wiring, one job per source + tag+rank job —
      `src/pipeline/scheduler.py`.
- [x] Switched from interval-since-process-start to a fixed nightly
      `CronTrigger` (3:30am ingest, 3:45am tag+rank, 4:00am history purge)
      — author is often up until 2-3am and wants polls landing while
      asleep. See `scripts/run_scheduler.bat` for the Task Scheduler launch
      wrapper (follows the Windows Task Scheduler gotchas in global
      CLAUDE.md: `.bat` wrapper, `StopExisting`, unlimited execution time).
- [x] ~~Register the Windows Task Scheduler entry.~~ Superseded 2026-08-26 —
      moved the scheduler to the Mac mini instead (always-on, avoids the
      Windows admin-elevation blocker and the sleep/wake `SessionUnlock`
      workaround entirely). `register_scheduler_task.ps1`/`run_scheduler.bat`
      are left in place, unused, in case Windows-side scheduling is ever
      wanted again.
- [x] **Mac mini scheduler setup, done 2026-08-26.** Code pushed/pulled
      current, `pipeline.db` synced (WAL-checkpointed, `scp`'d, integrity +
      item-count verified on both sides), Gmail OAuth files copied,
      `~/Library/LaunchAgents/com.jjcho.jobspipeline.scheduler.plist`
      registered (`RunAtLoad` + `KeepAlive.Crashed`) and confirmed running.
      Mini is now the source of truth for `pipeline.db` going forward. See
      `HISTORY.md#scheduler-moved-to-mac-mini` for the full narrative.
      Follow-up: `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID` aren't set in the
      Mini's `.env` yet (degrades gracefully, just means no Telegram
      digests from the Mini's runs until copied over).
- [ ] **Mac Mini git/gh auth fix.** Per global CLAUDE.md's "Connecting to
      the mac mini" notes: `git push` over SSH to the Mini fails because its
      `credential.helper=osxkeychain` can't unlock non-interactively, and
      `gh` isn't installed there — `git pull`/`fetch` on the Mini worked fine
      when tested 2026-08-26 (read-only over SSH is unaffected), so the
      scheduler pulling latest code on its own isn't blocked; only pushing
      *from* the Mini is. Not urgent now that the Mini is push-only-from-
      Windows/pull-only-on-Mini in practice, but fix properly (SSH-key based
      remote instead of HTTPS+osxkeychain, or `gh auth login` on the Mini) if
      the Mini ever needs to commit/push its own work.
- [ ] **Calibrate real per-source cadence (2-week daily trial, ends
      2026-09-09).** Moved to the Mac mini running daily for every source
      (see `scheduler.py`'s `DAILY_TRIAL_END`) specifically to collect real
      repeated-poll data -- author's call 2026-08-26 was daily-for-2-weeks
      then decide weekly/biweekly per source from actual miss counts, not
      guesswork (paid-Apify per-pull cost is cheap enough -- LinkedIn
      ~$0.20/pull, Indeed ~$0.03/pull -- that daily cost isn't the
      constraint; freshness/miss-rate is the open question). After
      2026-09-09: pull `run_log` (`stage='ingest'`) grouped by source, and
      for each source simulate keeping only every-Nth day's run (weekly =
      every 7th, biweekly = every 14th) -- compare real inserted-item counts
      (via `items.fetched_at` matched back to `run_log.run_at`) against what
      a sparser cadence would have caught, to get an actual miss-rate number
      per source rather than the old single-snapshot guess. Consistently
      high-miss-rate sources stay daily or go sub-24h; consistently
      0-miss-at-weekly sources are safe to slow down. Also worth fixing
      while calibrating: 5 sources have no `posted_at` at all
      (`luma_events`, `builtin_sf`, `handshake_email`, `yc_workatastartup`,
      `meetup`), so there's no timing signal for them beyond `run_log`'s
      own fetched-at history.
- [ ] **Review Apify plan choice once real spend data exists.** Currently
      on Starter ($29/mo, Bronze Store discount) — see the "Apify
      subscription plan research" section in `docs/SOURCES.md` for the
      full Free/Starter/Scale/Business comparison. Once daily re-polling shows
      real steady-state spend (Wellfound search's uncapped per-run cost is
      the main unknown), decide: downgrade to Free ($5/mo credit) if usage
      comfortably fits, or switch Starter to annual billing (~10% off) if
      usage consistently exceeds Free's credit.

## 4. LLM tagger/verifier
- [x] Schema, Pydantic validation + 2 retries, Haiku/Sonnet escalation,
      re-entrancy lock, `--concurrency` flag, raw-text cap raised to 12000
      chars — see `HISTORY.md#tagger-concurrency`,
      `HISTORY.md#raw-text-truncation-cap`.
- [x] **Provider abstraction for a future GLM 5.2 swap (2026-07-04, overnight
      pass)** — `src/pipeline/tagger/providers.py` now has a `TaggerClient`
      interface with `AnthropicTaggerClient` (today's live behavior,
      unchanged) and a stubbed `GLMTaggerClient`. Provider selection is
      `TAGGER_PROVIDER=anthropic|glm` (default `anthropic`), read once in
      `providers.get_tagger_client()`. Smoke-tested: the Anthropic path still
      works end-to-end unchanged (`python -m pipeline.tagger.tag_item`, one
      real API call, confirmed 2026-07-04). See `HISTORY.md#glm-provider-abstraction`
      for the full narrative.
      **To flip on GLM once you have a key:** add a real key to `.env`'s
      `GLM_API_KEY`, set `TAGGER_PROVIDER=glm`, then re-run the same
      `tag_item.py` smoke test before trusting it for anything real. **Still
      stubbed/unverified — confirm before use:**
      - Real GLM 5.2 model ids (`GLM_DEFAULT_MODEL`/`GLM_ESCALATION_MODEL` in
        `providers.py` are placeholder names following Zhipu's naming
        convention, not verified against a live account).
      - GLM's actual reasoning-effort/thinking-mode param name and values for
        the escalation tier (Anthropic's `output_config.effort="medium"`
        equivalent) — left unset in the stub rather than guessing a param
        that might error.
      - Real GLM pricing — not confidently found via web search this pass;
        `run_tagging.py`'s `MODEL_PRICING` has no GLM entry, so cost logging
        will silently show $0 for GLM calls until a real per-token rate is
        added.
      - `openai` package added to `requirements.txt` for the GLM SDK path
        (already installed as a transitive dep; now declared explicitly).
- [ ] Verifier step to drop bad scrape results — still deferred; no junk
      has surfaced that warrants it.
- [x] **Validate `deadline` field extraction against a real internal-target
      example — done 2026-07-04, found a real bug.** Searched the DB for
      "anticipated start"/"looking to fill"/"hire by"/etc. phrasing. Two real
      cases: (1) id 13501 — posting has both a vague internal target
      ("Anticipated start: Winter/Spring 2026") and a real applicant deadline
      ("Final date: Jul 31, 2026"); tagger correctly extracted the latter,
      ignored the former — the good-case outcome. (2) id 15877 — a pre-
      funding co-founder pitch with *only* internal-target language
      ("closing the CTO hire by end of June 2026. Pre-seed funding target:
      July-August 2026", no real applicant deadline anywhere) — tagger
      hallucinated `deadline=2026-08-31`, matching neither quoted phrase
      (closest guess: took the end of the funding-target range). Full
      writeup: `HISTORY.md#deadline-field-internal-target-example`.
      **Not fixed yet** (no bulk tagging allowed this pass) — recommended fix
      next time the tagger prompt is touched: explicit instruction that
      internal targets (start dates, hiring-close targets, funding-close
      targets) are NOT `deadline` values, produce null unless the text also
      states a real applicant-facing apply-by/review-by date. The field's
      overall single-ISO-date-or-null shape still holds up; this is a
      narrower prompt-clarity gap, not a schema problem. A "rolling basis"
      flag (rejected 2026-07-03) would not have caught this case either —
      worth remembering if this comes up again.
- [ ] **Tagging backlog: only ~1,565–1,650 of ~12,794 items tagged (~13%).**
      Sources landed after the last big tagging pass and have never been
      through the tagger — led by `greenhouse` (~3,200), `indeed_apify_old`,
      `indeed_radius`, `ashby`, `linkedin_apify`. Run
      `python -m pipeline.tagger.run_tagging` against the untagged backlog.
- [ ] Known data gaps from schema additions, not bugs — re-tagging costs
      real API calls, not scheduled yet: `engagement_type`/`role_category`/
      `industry` are `null` on anything tagged before those fields existed;
      `spam_risk`/`role_expectation_delta`/`_notes`/`company_stage` are
      `null` on anything tagged before 2026-07-03's ranking rework (that
      pass also copied the old `relevance_score` forward into
      `content_quality` as an imperfect starting value for ~1,900 rows,
      not re-derived). A full re-tag pass would clear all of this at once
      — bundle it with the backlog item above if/when it happens.
- [ ] **Pre-LLM filter for tagging cost (deferred, data-gated — do not
      design yet).** Tagging cost scales with item volume and is already
      running $100-200 to clear the ~12,794-item backlog; discussed
      2026-07-03 whether a cheap pre-filter (keyword rules and/or
      embedding-similarity triage) should gate which items reach the
      LLM tagger at all. Explicitly decided *not* to design this now,
      for two reasons: (1) no filter-design input exists yet — real
      signal has to come from actual thumbs-up/down feedback and
      observed skip patterns in the UI, not guessed keyword rules
      written from intuition (a rigid title-based seniority filter
      would, e.g., silently drop a "CTO" posting from an early-stage
      startup that's actually looking for a cofounder-level AI eng —
      a real false negative the author explicitly wants to avoid,
      and a false negative from a silent filter is invisible in a way
      a manual pass-over isn't); (2) current backlog volume is a
      one-time historical dump across months of retroactive scraping,
      not steady-state weekly volume — the filter's ROI depends on
      the *recurring* rate, which isn't known until the scheduler has
      run a few weeks at normal cadence post-backlog (ties to the
      cadence-calibration item above). Finish tagging the backlog
      as-is first; revisit only once both real weekly volume and real
      feedback data exist. If/when revisited: bias any filter toward
      flagging-for-review over silent-drop for ambiguous cases
      (especially title-based seniority signals), and prefer deriving
      rules from observed thumbs-down patterns over hand-written
      heuristics.

## 5. Ranker/prioritizer
Done — reworked 2026-07-03 into `content_quality` × 5 weight tables
(engagement/seniority/location/sector/company_stage) producing three
independently-sortable scores (`preference_score`, `urgency_score`,
`general_score`). See `CLAUDE.md`'s ranker section and
`HISTORY.md#ranking-rework` (includes the full decision trail — don't
re-derive weight values from scratch, they're already reasoned through).
Weights are meant to be tuned over time, not a one-shot problem to solve.

## 5b. Ranking follow-ups (from Spearman manual-ranking pass, 2026-07-04)
- [x] **AI-Trainer-gig derank fix — done 2026-07-05.** 36/50 top items by
      `preference_score` were AI-Trainer/data-labeling contractor gigs
      stacking freelance/junior/remote/ai_ml weights meant for real freelance
      AI eng work. Added `role_category=ai_data_labeling` (schema + prompt),
      a new `role_category_weights` 6th weight table (0.15 for this bucket),
      regex-backfilled 294 already-tagged items (no re-tag, no API cost),
      re-ran the ranker. Verified: 0/50 in the new top 50. See
      `HISTORY.md#ai-trainer-derank-fix`. **Note for the DevRel item below:**
      this fix already builds the `role_category_weights` 6th dimension that
      DevRel Option B proposed — if Option B is chosen, it's now just adding
      a `devrel_engineer` `role_category` value + one weight entry, not new
      ranker plumbing.
- [ ] **DevRel Engineer ranking — proposal written, awaiting author decision
      (2026-07-04 overnight pass).** Checked both halves of the original
      question: (1) `role_category` has no DevRel bucket (id 25978 tags
      `role_category=other`); (2) more importantly, **the ranker doesn't
      weight `role_category`/`role_type` at all** — there's no existing
      weight table for it, so this isn't really a "schema vs. weight-table"
      fork like originally framed. id 25978 already ranks highly today purely
      from its `freelance`(1.5x)/`junior`(1.3x)/`ai_ml`(1.4x) field values
      stacking under existing weights, unrelated to it being DevRel
      specifically. Full proposal with two options (A: do nothing, current
      weights already surface this case; B: add `role_category` as a real
      6th weight dimension) and a retag blast-radius estimate (53
      already-tagged items have DevRel-like `role_type` text, scattered
      across 6 different `role_category` values today — a small, cheap
      targeted re-tag if Option B is chosen, not a full backlog re-tag):
      `docs/reports/devrel_ranking_proposal_2026-07-04.md`. **Needs the
      author to pick A or B** — this is a real preference question (is
      DevRel-as-a-category actually the thing you want upweighted, or was
      this one item's high rank really about freelance+junior+ai_ml?), not
      resolved automatically this pass. **Update 2026-07-05:** Option B's
      "add role_category_weights as a 6th dimension" plumbing now already
      exists (built for the AI-Trainer fix above) — Option B is now cheaper
      than originally scoped, just a new enum value + weight entry.

## 6. Evaluation — not started
- [ ] Manually label 60-item ground-truth set (20 jobs / 20 events / 20
      ambiguous). Data to support this now exists (12,794 items, ~1,650
      tagged).
- [ ] Classification accuracy (target ≥85%), tag F1, Spearman correlation,
      confusion matrix (scikit-learn).
- [ ] Document failure cases (hallucinated deadlines, miscategorized
      roles) candidly.
- [ ] If a real LinkedIn alert email ever surfaces: use it only as a
      scraper-coverage cross-check (does `linkedin_apify` already capture
      the same postings?), not as a new source to build.
- [ ] **Scraper coverage check (new eval angle, 2026-07-04): are the
      scrapers capturing all they potentially could per source, not just
      tagging/ranking correctly once captured?** No existing eval measures
      this — everything above tests correctness of items already in the DB,
      not completeness of collection. Scope deliberately narrow and
      safe: public API/HTML sources only (Greenhouse, Lever, Ashby, YC Work
      at a Startup, aijobs.net, RemoteOK, HN Who's Hiring) — **do not**
      extend this to the Apify-routed sources (LinkedIn/Indeed/Wellfound),
      which are already routed through paid managed actors specifically
      because direct access was blocked/risky; pointing a browsing agent at
      those adds real anti-bot/ban risk for a comparatively low-value
      signal. Pick a handful of specific searches/filters per safe source,
      compare a live browse count (manual, or one supervised
      claude-in-chrome pass — not an autonomous/overnight loop, per the
      "Autonomous loops vs. anti-bot-sensitive live APIs" lesson in global
      CLAUDE.md) against the DB count for that same query. A real,
      demonstrable coverage number (e.g. "X/Y postings visible on
      Greenhouse's live board are in the DB") would be a genuinely useful
      addition to the Evaluation section/video if there's time — not
      required, but higher-signal than the LLM classification scale-check
      stretch item above.

## 7. UI (Streamlit)
Search/filters, tag browse, metrics + histogram, engagement-type filter,
all browser-tested live with Playwright against the real DB.

**One app, not split (decided 2026-07-04).** Considered splitting into a
separate eval/testing UI vs. a workflow UI, but the author isn't sure yet
what the eventual UI(s) should look like — reverted that framing. For now
everything stays in this one `ui/app.py`; a "testing" tab on the main app is
plausible for later, not a separate app. Don't reintroduce an eval/workflow
split without the author asking for it again.

**2026-07-04: single `application_status` field replaces thumbs + separate
save/hide flags.** Thumbs up/down (`feedback` column) are hidden in the UI —
nothing reads that column for ranking yet, and a deliberate feedback→ranking
design is a separate later project. Workflow state is now one column,
`application_status` (`storage/schema.sql`, migrated via
`_migrate_saved_tracking` in `db.py`): null (default) → `saved` → `applied` →
`callback` → `interview` → `offer`, or `not_interested` at any point — an
item is in exactly one state at a time (marking "applied" replaces "saved"),
so progress tracking and per-source analysis are a plain `GROUP BY` on this
column. `applied`/`callback`/`interview`/`offer` are schema-ready but have no
UI button yet (see open items below) — only `saved` and `not_interested` are
reachable from the UI today.
- "📌 Save" button + "Saved" tab (sorted by `preference_score`).
- "🚫 Not Interested" opens a popover with fixed one-click reasons (Too
  Senior / Too Junior / Unrelated Field / Bad Location / Low Pay-Engagement)
  plus a free-text "Other", stored in `not_interested_reason` — meant to
  support later per-source analysis (e.g. "does source X consistently
  surface over-senior roles?"), not just a record of the click.
- Not-interested items are hidden from Browse by default but there's a
  "Show items marked Not Interested" checkbox to reveal + undo an accidental
  click (`Undo` button resets `application_status` to null).
- "Digest" tab renamed to "Metrics".
- Category filter's "event"/"networking" values reachable by default again
  (sidebar "Show events & networking" now defaults on) so the author can
  peruse that data now, even though category-based filtering is expected to
  matter less long-term.

**2026-07-04: performance pass.** Each tab body is now `@st.fragment`
(Streamlit ≥1.37) so a click inside one tab (Save/Not-Interested, a filter,
pagination) only reruns that tab, not the whole script/page — previously
every interaction re-rendered all three tabs' full item lists. Browse also
paginates (20 items/page with Prev/Next) instead of rendering up to 100
item-cards on every load. `load_items()`'s query is trimmed to only UI-used
columns and truncates `raw_text` to 1000 chars in SQL (author confirmed this
tradeoff — search only matches the first 1000 chars of a posting, same as
what's displayed). Author is explicitly picky about load speed going
forward — if reloads still aren't near-instant, the next lever is
fragmenting individual item cards (rejected for now in favor of simplicity)
or dropping `st.container(border=True)`/expander widget overhead per card.

**Open work (not started, discussed 2026-07-04):**
- [ ] **Reachable "applied"/"callback"/"interview"/"offer" buttons.** Schema
      supports them (`application_status`) but no UI surfaces them yet —
      needs UX design (probably progressive buttons on a saved item, e.g.
      "Mark Applied" appearing once saved, then "Got Callback" etc.).
- [ ] **"Seen" tracking based on actual scroll position, not just page load.**
      Author wants items marked "seen" only once actually scrolled into view,
      not merely fetched into the DOM. Streamlit has no native
      scroll-visibility hook — this likely needs a custom component or JS
      bridge (`st.components.v1`) to detect viewport-intersection client-side
      and report back. Worth checking Streamlit's component ecosystem for an
      existing intersection-observer component before building one from
      scratch. Seen items should stay visible (not auto-hidden) but be
      visually de-emphasized so revisits don't re-read the same postings.
- [ ] **Metrics tab: applied/viewed per day or week.** Once "seen" tracking
      and the applied/callback/interview/offer buttons exist, add day/week
      rollups off `status_updated_at` — how many jobs looked at vs. applied
      to over time.
- [ ] **Not-interested reason analysis.** Once enough `not_interested_reason`
      data accumulates, look for per-source patterns (e.g. a source
      consistently surfacing over-senior roles) to suggest sourcing/tagging
      fixes — this was the explicit motivation for capturing reasons instead
      of a plain hide.
- [x] **Visual/UX redesign, pass 1 (2026-07-04, `ui-redesign` branch).** Two
      iterations: first pass (dark theme, rounded pill badges, card
      containers) was rejected by the author as reading like "every other
      AI-gen frontend" — an honest limitation of the generic dashboard
      formula (dark glassmorphism + saturated pill badges), not really a
      Streamlit ceiling. Second pass switched to an editorial/terminal
      direction instead: light paper background, serif type, monospace
      uppercase tags/scores, ruled-list item rows (no card borders), one
      restrained accent color (muted brick) reserved for the primary action
      and score figures, flat square buttons. Browser-verified live via
      Playwright. Confirmed real Streamlit limitation for anything beyond
      this: CSS-only styling can get to "doesn't look AI-generated" but not
      to a fully bespoke/custom product feel — that needs a real frontend
      framework where DOM structure is controlled directly, not painted
      over Streamlit's own component markup. See CHANGELOG/HISTORY for the
      commit-level detail and the token-cost estimate given for a React/
      Tailwind-style rebuild.
- [ ] **Apply/Research/Share buttons — currently UI stubs, not real
      backends (2026-07-04).** Added to Browse and Saved tabs as part of
      pass 1: "Apply" sets `application_status='applied'` and shows a toast
      noting no agentic flow exists yet; "Research" shows a static
      placeholder explaining the intended feature; "Share" is the one
      that's fully real (mailto: link, Telegram share link, copyable raw
      URL — needs no backend). Real design work still open:
  - [ ] **Apply → agentic/semi-agentic application flow.** Author's stated
        target: clicking Apply opens the actual application page and an
        agent takes over the form-fill (or hands off to the user
        partway if it can't complete something). No design started —
        open questions include how much of this can/should be automated
        given most job postings' apply flows are on arbitrary third-party
        ATS pages (Greenhouse/Lever/Ashby-hosted forms, LinkedIn's native
        apply, etc.), and what a safe human-in-the-loop handoff looks like.
  - [ ] **Research → founder/company assessment.** Author's stated target:
        gather founder background/character, company industry/niche,
        upside assessment, and culture signals per item, likely via a
        research-agent pass (web search + synthesis) rather than a static
        lookup. No design started — needs a decision on data sources
        (LinkedIn founder profiles, Crunchbase/PitchBook-style funding
        data, company blog/culture pages), how results get cached/stored
        (new DB columns vs. on-demand only), and cost per research run
        given this would be additional LLM+search spend per item, not a
        one-time batch cost like tagging.
- [ ] **Sector/type icons.** Author idea (2026-07-04): small icons per item
      for sector (robots for robotics, rocket for space, DNA/flask for
      bio, etc.) and/or freelance-vs-traditional engagement type, as a
      faster visual scan aid than the current text tags. Not scoped yet —
      would need an icon set decision (emoji vs. a real icon font/SVG set)
      and a sector taxonomy to map icons onto (current `category`/
      `role_category`/`engagement_type` fields may or may not be granular
      enough as-is).
- [ ] **Event/networking category filter placement/fix (2026-07-05).** Author
      unsure yet whether to keep `event`/`networking` as reachable
      `category` filter values in the main Browse flow at all — probably
      better split into a separate tab rather than mixed into the primary
      job-browsing filter set, since events are a frozen/secondary capability
      (see CLAUDE.md "Current State"). Needs a decision before further work:
      keep as-is, move to their own tab, or drop the filter option entirely
      (data stays in DB either way).

## 8. Notifications + reports
- [x] **Telegram run-summary digest — done 2026-08-26.** Fires
      automatically after each nightly `_run_tag_and_rank` (scheduler.py):
      items scraped/tagged/ranked per source + errors, built from existing
      `run_log` rows. `src/pipeline/notifications/telegram.py` +
      `notifier.py`. See `HISTORY.md#telegram-run-summary-notifications`.
- [ ] **Per-item high-priority alerts — deliberately deferred, framework
      stubbed.** `notify_high_priority_items()` exists but raises
      `NotImplementedError` — blocked on the author defining a company
      whitelist ("I'll figure this out later — probably a whitelist of
      very reputable companies", 2026-08-26). Don't implement without it.
- [ ] In-UI high-priority match alerts.
- [ ] Email digest.

## 9. Commercial marketability (research, not code — not started)
- [ ] **What would need to change before this could be sold, or sold as a
      usage/access product?** Author idea (2026-07-04), purely a research
      question for now, no scoping done. Things worth digging into when
      this gets picked up: the ranking/preference system is currently
      single-user and hardcoded to one person's weights/values (see
      CLAUDE.md's ranker section — explicitly a personal-preference design,
      not a general one) — would need per-user profiles, not a single
      active row in `preference_profiles`; the ToS posture (CLAUDE.md's
      bias/ethics stance: "single-user personal tool" is the stated
      justification for skipping ToS-compliance scaffolding and scraping
      several sites directly — that posture likely does not survive
      contact with a multi-user commercial product, especially the sources
      scraped against ToS friction, e.g. Wellfound/Built In, or the
      Apify-routed sources using harvested session tokens); data licensing
      for redistributing scraped job postings to other users/customers;
      LLM API cost scaling per user (currently ~$100-200 one-time for a
      personal backlog — very different economics multiplied across paying
      users); and whether the value proposition is the aggregation+ranking
      itself or the underlying scraping infrastructure. Explicitly a
      later/parallel research task, not something to act on now.

## Capstone admin (parallel track, not code)
- [ ] Finalize and submit project proposal (draft exists — see `docs/`).
- [ ] Google Drive folder structure + sharing permissions (see
      `docs/Google Drive Setup.txt`).
- [ ] Weekly peer discussion posts as required by course schedule.
- [ ] **Presentation video.** ≤30 min is the only hard constraint; no
      required section order or slide count (confirmed against the actual
      Project Guidelines PDF + rubric + 5 example-video transcripts — see
      `docs/overview/video_requirements_and_examples.md`). Loose outline
      landed on: name/background → scope/ambition → architecture (one
      diagram slide, then switch to live VS Code/terminal for the parts
      that need to be seen running) → demo functions → demo/eval testing
      (give this real air time — it's where "effectiveness" +
      "candid limitations" actually get satisfied, per both comparable
      example videos) → lessons learned/future features → thanks/close.
      Minimal slides, ad-libbed over the outline rather than a word-for-word
      script — matches what passing examples in the same AI/ML rubric
      category actually did.
  - [ ] Optional/stretch, only if time permits, not blocking: re-run the
        Spearman ranking eval after applying the AI-Trainer-gig derank fix
        (see Section 5b context — ranking is the actual AI-justification
        centerpiece, so this is the highest-value eval addition if there's
        time), ideally on a larger manually-ranked sample than the existing
        18-item passes for a stronger correlation read.
  - [ ] Optional/stretch, explicitly not needed, do only if it becomes
        interesting later: an LLM-judge scale-check of classification
        accuracy against a larger (100-200+) unlabeled sample. Cheap
        (~$1-2 on Haiku) but weak as an independent accuracy claim (the
        tagger judging itself isn't independent evidence) — only worth
        doing if framed honestly on camera as a coverage/generalization
        check ("does 96.7% hold up directionally at scale"), not as a
        second accuracy metric. Skip unless it earns its place.
- [x] **AI Usage Statement / per-file citations — done 2026-07-05.** All 45
      `src/pipeline/` source files now carry an `AI USAGE CITATION` header;
      full verbatim prompt log at `docs/ai_usage/prompt_log.md`; complete
      raw session transcripts (69 files, one live Apify token pattern
      redacted) archived at `docs/ai_usage/transcripts/` as primary-source
      backing evidence for every citation, including files where automated
      reconstruction couldn't isolate a clean triggering prompt. See
      `HISTORY.md#ai-usage-citation-pass`.
