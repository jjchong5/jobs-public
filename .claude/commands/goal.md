---
description: Overnight source-connection pass — attempt remaining sources from docs/SOURCES.md safely, one at a time, real data only.
---

# Overnight source-connection goal (2026-07-02 pass)

Read `CLAUDE.md`, `TODO.md`, and `docs/SOURCES.md` first — they're the source of
truth for architecture, conventions, and current status. Don't restate them,
follow them. In particular: real data only (no mocks), one source built and
live-tested at a time, update `TODO.md`/`docs/SOURCES.md`/`CLAUDE.md`'s Current
State section as each source lands (or gets blocked), same standard every prior
source in this project was held to.

## Hard safety rule — read this before touching any blocked/anti-bot site

Wellfound and other candidate sites are protected by DataDome/Cloudflare-class
anti-bot systems. **Never write or run a custom retry/evasion loop directly
against one of these sites** (rotating headers, retrying on 403, simulating
browser behavior in a loop, etc.) — a stuck agent brute-forcing endpoint
guesses against an anti-bot system reads as attack traffic and risks the
account/IP getting flagged. This is a hard rule, not a suggestion, learned
from a prior incident.

The only sanctioned path for an already-blocked site is a **managed Apify
actor** (same pattern as the working LinkedIn integration in
`src/pipeline/scrapers/linkedin_apify.py`): one scoped test call (actor
minimum, typically ~10 items), then stop. If the actor doesn't exist, fails,
or returns junk (verify by inspecting result URLs — see the Handshake-actor
rejection in `docs/SOURCES.md` for what junk looks like and how it was
caught), log it as blocked with the reason and move to the next source. Do
not retry the same actor repeatedly trying to get a better result.

**Do not use Bright Data this pass.** It's noted as a TODO in
`docs/SOURCES.md` ("Open question for next pass") but is explicitly deferred
to a future supervised session — it's unproven in this codebase and its
billing model isn't confirmed pay-per-use. Apify only, tonight.

## Budget cap

**$25 total Apify spend for the whole run.** Log running cost after each
actor call (Apify's dataset/run response includes cost). If a single test
call would push projected spend over the cap, stop and report instead of
running it. Prefer the cheapest viable test size (actor minimums) over larger
runs — bigger batches are for later, once a source is confirmed good.

## Scope for tonight

**Tier 1 — Apify managed actors (funded, one scoped test each):**
- Wellfound/AngelList — flagged as the next candidate in `docs/SOURCES.md`.
  Search the Apify store for a maintained actor; if multiple exist, prefer
  one with real usage/reviews over an untested one (learn from the Handshake
  actor mislabeling incident — verify the actor is what it claims before
  trusting its output).
- Contra — noted in `docs/SOURCES.md` as worth revisiting via Apify if a
  maintained actor exists. Skip if none does; don't build a custom scraper.
- Indeed — RSS is confirmed dead (retired by Indeed, 404 on every query URL;
  see `docs/SOURCES.md`), but two alternate paths haven't been tried:
  (a) search the Apify store for a maintained Indeed jobs-scraper actor,
  same verification bar as the others (check it returns real Indeed listing
  URLs, not aggregator junk — see the Handshake-actor rejection for what
  that looks like); (b) if no good actor exists, try Indeed's direct
  non-RSS HTML search-results page via plain `requests`+bs4 as a **single**
  test request — if it's clean server-rendered HTML (Built In SF-style),
  build it as a normal Tier 2 direct source. If that single request comes
  back blocked/anti-bot-gated, this falls under the hard safety rule above:
  log it as blocked in `docs/SOURCES.md` with the reason and stop — do not
  retry, rotate headers, or loop against it, same treatment as Wellfound.

**Tier 2 — direct/no-auth, no anti-bot (plain `requests`/HTTP, same pattern as
Built In SF / RemoteOK):**
- Greenhouse boards (`boards.greenhouse.io/<company>`) and Lever boards
  (`jobs.lever.co/<company>`) — these need a target company list, which
  doesn't exist yet. Seed a small placeholder list of SF AI/DS/ML companies
  (same spirit as the existing placeholder preference profile in
  `preference_profiles` — clearly marked as a placeholder to refine later,
  don't spend time curating the "right" list).
- YC Work at Startup
- Dice
- Meetup API
- Eventbrite API

**Handshake live-fetch wiring (infra is ready, code isn't written):**
Gmail OAuth is set up and confirmed working — `src/pipeline/gmail_auth.py`,
`get_gmail_service()`, scope `gmail.readonly`, token already cached in
`token.json` (no browser interaction needed, it refreshes silently). Wire
this into `handshake_email.py`'s `fetch_raw()` to search/pull real new
Handshake alert emails instead of reading the saved fixtures. Test live
against whatever's actually in the inbox.

**LinkedIn email — worth one recheck:** the last check for a LinkedIn alert
email (per `TODO.md`) happened before this pipeline had its own Gmail API
access. Now that `get_gmail_service()` works, do one real search across
the connected university email account for a LinkedIn job-alert email. If one exists
now, that's real signal to start the parser; if not, leave it blocked as
documented — don't chase this further tonight.

**Explicitly excluded — do not attempt:**
- Upwork (explicit ToS ban + stacked anti-bot, harder no than Wellfound)
- Any further direct-scrape attempts on Wellfound itself (already exhausted
  per `docs/SOURCES.md` — UA spoofing, referer warm-up, mouse simulation all
  still 403)
- Telegram/Discord/Slack bots (idea-stage, no concrete target identified)
- Bright Data (see above)

## Per-source workflow

Same sequence as every existing source in this project:
1. Build `fetch_raw()` returning raw items, test standalone (print/JSON,
   no DB yet).
2. Add a normalizer, wire into `ingest.py`'s `NORMALIZERS`.
3. Live-test a small real batch, verify it lands correctly in
   `data/pipeline.db` (check dedup, check field mapping).
4. Update `TODO.md` (check off), `docs/SOURCES.md` (status table), and
   `CLAUDE.md`'s Current State section (what was built, what was tested,
   real numbers/examples — same level of detail as existing entries).

## Done when

Every source listed in scope above has reached a terminal, documented state:
either (a) built, live-tested with real data, wired into `ingest.py`, and
written up, or (b) logged in `docs/SOURCES.md` as blocked with a concrete,
specific reason. Landing some sources in state (b) is an expected, fine
outcome — it's what happened with Wellfound-direct, Indeed RSS, Upwork, etc.
already. The goal is every candidate *attempted and resolved*, not every
candidate *working*.
