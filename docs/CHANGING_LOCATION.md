# Changing the location focus

**Short version:** this pipeline ships tuned for San Francisco / the Bay
Area, because that's where the original author was job-hunting. Nothing
about the code is San-Francisco-specific at a deep level — it's a handful
of default search terms and one ranking-preference table. This doc walks
through exactly what to change, file by file, to point it somewhere else
(or nowhere in particular).

If you've never edited a `.env` file or a Python constant before, don't
worry — every step below says exactly what to type and where.

## The three places location shows up

1. **Scrapers** — some job sources take a location as a search parameter
   (e.g. "search Indeed for jobs near Austin, TX"). These are the easiest
   to change: no code editing, just a `.env` setting.
2. **The ranker's location weights** — after jobs are tagged, a scoring
   step multiplies each job's score up or down based on where it is. This
   doesn't hide any jobs, it just changes what shows up near the top.
3. **Company-list sources** — a few sources (Greenhouse, Ashby, Lever)
   don't search by location at all — they pull from a hand-picked list of
   companies, and those companies happen to be mostly SF-based today.
   Changing "location" here means editing the company list, not a setting.

## 1. Scrapers you can retarget with `.env` — no code editing

Open your `.env` file (see the main [README](../README.md#setup) if you
haven't created one yet — it's a plain text file in the project's root
folder, `jobs/.env`). Add or edit these lines. If a line isn't already in
your `.env`, just add it — a blank/missing var falls back to the SF
default shown.

```bash
# Indeed (radius search around a city)
APIFY_INDEED_RADIUS_POSITION=data scientist OR machine learning
APIFY_INDEED_RADIUS_LOCATION=Austin, TX
APIFY_INDEED_RADIUS_MILES=25

# Dice
DICE_QUERY=data scientist
DICE_LOCATION=Austin, TX

# Wellfound (search-based scraper)
WELLFOUND_SEARCH_ROLES=data-scientist,machine-learning-engineer
WELLFOUND_SEARCH_LOCATION=austin  # Wellfound's own URL slug for the city, all lowercase

# LinkedIn (whole search-URL override, not just a location string --
# see step-by-step instructions below)
APIFY_LINKEDIN_SEARCH_URL=
```

**How to get a LinkedIn search URL:** LinkedIn doesn't offer a simple
`?location=` parameter here — the scraper needs a full LinkedIn job-search
URL. To get one: go to linkedin.com/jobs, search for your target
role + location the normal way, copy the URL from your browser's address
bar once the results load, and paste the whole thing as
`APIFY_LINKEDIN_SEARCH_URL` in `.env`.

Once you've changed these, re-run the scraper (or the full pipeline — see
the [README](../README.md#running-the-pipeline)) and it'll search your new
location instead of San Francisco. No restart of anything else needed —
`.env` is read fresh each time a script starts.

**Costs money to run:** these sources ([Apify](https://apify.com)-hosted
actors — Indeed, Wellfound, LinkedIn) cost a small amount per run (well
under $1 for a typical search) once you've set up your own Apify account
and API token. See `.env.example` for the `APIFY_API_TOKEN` variable.

## 2. Sources that are location-agnostic already

These sources have no location concept at all — they pull everything, and
rely entirely on the LLM tagger + ranker to sort out what's relevant to
you. Nothing to change here regardless of where you live:
HN "Who's Hiring", RemoteOK, We Work Remotely, aijobs.net,
YC Work at a Startup.

## 3. Sources you can't relocate by changing a setting

- **Built In SF** (`builtin_sf.py`) is a specific regional edition of a
  site that also runs Built In NYC, Built In Austin, Built In Chicago,
  etc. under different domains. To cover a different city here you'd need
  to point the scraper at that city's Built In domain and re-check its
  page structure still matches (a real code change, not a setting) — or
  just leave this source off (see "Turning sources on/off" below).
- **Greenhouse, Ashby, Lever** pull from a hand-picked list of company job
  boards (`BOARD_TOKENS`/`BOARD_NAMES`/`COMPANY_SLUGS` near the top of
  each file in `src/pipeline/scrapers/`), not a location search. The list
  happens to skew SF/Bay-Area because that's where the original author was
  building it from. To retarget: open the file, and add/remove company
  names in that list. Each of those platforms is free and public to query
  — you don't need an account, just the company's board slug (visible in
  the URL when you view their careers page, e.g.
  `boards.greenhouse.io/anthropic` → slug is `anthropic`).
- **Luma events, Meetup** (currently off by default — see
  `FROZEN_SOURCES` in `src/pipeline/ingest.py`) are hardcoded to SF place
  IDs/coordinates. Not worth touching unless you're re-enabling event
  tracking for your own city — if you want to, look at the `PLACE_IDS`
  dict in `luma_events.py` or the `SF_LAT`/`SF_LON` constants in
  `meetup.py` for what to add.

## 4. The ranker's location weight table (affects sort order, not what's collected)

This is a separate thing from scraping — it runs *after* jobs are tagged,
and only changes which jobs float to the top of your results, not which
jobs get collected in the first place.

It lives in `src/pipeline/storage/db.py`, look for
`DEFAULT_LOCATION_WEIGHTS`:

```python
DEFAULT_LOCATION_WEIGHTS = {
    "remote": 1.3, "hyperlocal_sf": 1.2, "bay_area": 1.1, "other": 0.6, "unknown": 1.0,
}
```

Each number is a multiplier — above 1.0 ranks a job higher, below 1.0
ranks it lower, relative to a job tagged `"unknown"`. Today, anything the
tagger classifies as neither SF/Bay-Area nor remote gets a 0.6x
multiplier (ranked lower, not hidden).

**If you're not in the Bay Area, the simplest change** is to set
`"other"` to `1.0` (neutral, no penalty) or higher if you want local jobs
prioritized:

```python
DEFAULT_LOCATION_WEIGHTS = {
    "remote": 1.3, "hyperlocal_sf": 1.0, "bay_area": 1.0, "other": 1.2, "unknown": 1.0,
}
```

**Important:** editing this constant only affects *new* databases. If
you've already run the pipeline once, your database already has a saved
copy of these weights. To apply a change to an existing database, either:
- Delete `data/pipeline.db` and start fresh (loses any jobs you've already
  collected/tagged), or
- Update the row directly — open a Python shell with the project's
  virtual environment active and run:
  ```python
  import sqlite3, json
  conn = sqlite3.connect("data/pipeline.db")
  conn.execute(
      "UPDATE preference_profiles SET location_weights = ? WHERE is_active = 1",
      (json.dumps({"remote": 1.3, "hyperlocal_sf": 1.0, "bay_area": 1.0, "other": 1.2, "unknown": 1.0}),)
  )
  conn.commit()
  ```
  Then re-run the ranker (`python -m pipeline.ranker.rank`) to apply the
  new weights to jobs already in your database — weights aren't applied
  retroactively until the ranker runs again.

## 5. Turning sources on/off entirely

If a source doesn't make sense for you (e.g. you'll never live in SF and
don't want Built In SF results at all), you can run the pipeline against
only a specific list of sources instead of everything:

```python
import asyncio
from pipeline.ingest import run_ingest

asyncio.run(run_ingest(sources=["hn_whoshiring", "remoteok", "weworkremotely", "indeed_radius"]))
```

The full list of valid source names is the `NORMALIZERS` dictionary near
the bottom of `src/pipeline/ingest.py` — every key in that dictionary is a
usable source name.

## Related

- [CUSTOMIZING_PROMPTS.md](CUSTOMIZING_PROMPTS.md) — changing what the AI
  tagger looks for (role types, seniority, industries) independent of
  location.
