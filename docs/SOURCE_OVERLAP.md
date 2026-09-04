# Source overlap analysis (jobs only)

Re-run `python -m pipeline.analysis.source_overlap`
(`src/pipeline/analysis/source_overlap.py`) to regenerate the numbers below
against the live DB — don't re-derive these queries by hand next time this
doc needs refreshing.

**Refreshed 2026-07-03** against `data/pipeline.db` (11,858 total items across
19 sources, all rows queried — no sampling). Original version of this report
(2026-07-02, 7,412 items) is superseded; see git history for that snapshot.
Data has grown substantially since, especially the Apify-mediated sources:
`indeed_apify` 19→2,310, `linkedin_apify` 10→1,350, and the new
`wellfound_search` (784, replacing the mothballed `wellfound_apify_old`, now
50 and frozen). Apify-mediated sources (`indeed_apify`, `linkedin_apify`,
`wellfound_search`, `wellfound_apify_old`) now make up 4,494/11,858 (38%) of
the entire DB.

Each source already dedups against itself (`UNIQUE(source, url)` in the
schema), but the same real job posting can show up on multiple *different*
sources under different URLs — e.g. a role posted directly on a company's
Greenhouse board might also get aggregated onto LinkedIn or Indeed. This
checks for that using the existing `normalize_dedup_key(author, title)`
helper in `src/pipeline/storage/db.py` (already backfilled into the
`dedup_key` column for all rows with both fields) — a normalized
`company|title` key. That's the only signal that actually means "the same job
posting" — matching on title alone would falsely flag e.g. two unrelated
companies both hiring a "Data Scientist" as overlap, so title-only matching is
not used anywhere in this report.

**Excluded from the overlap metric (no usable company field):**
`hn_whoshiring` (`author` is the HN poster's username, not a company — still
true at current volume, checked directly), `weworkremotely` (`author` always
NULL). Event sources (`luma_events`, `meetup`, `eventbrite`, frozen per
CLAUDE.md) are listed for volume context only.

Most items (10,293/11,858, 87%) are untagged (`category IS NULL`) — tagging
volume lags ingestion volume, which just grew a lot. This doesn't affect the
analysis below: `dedup_key` is computed at ingest time from raw
`author`/`title`, independent of LLM tagging.

## Ranked by item count, with job-overlap %

| Rank | Source | Items | Kind | Confident job overlap (company+title match on another source) |
|---|---|---|---|---|
| 1 | `greenhouse` | 3187 | job | 75/2517 (3.0%) |
| 2 | `indeed_apify` | 2310 | job | 129/2154 (6.0%) |
| 3 | `ashby` | 1787 | job | 47/1567 (3.0%) |
| 4 | `linkedin_apify` | 1350 | job | 89/1057 (8.4%) |
| 5 | `wellfound_search` | 784 | job | 53/780 (6.8%) |
| 6 | `hn_whoshiring` | 700 | job | n/a (no company field) |
| 7 | `vc_portfolio` | 591 | job | 121/529 (22.9%) |
| 8 | `lever` | 329 | job | 1/192 (0.5%) |
| 9 | `remoteok` | 252 | job | 1/251 (0.4%) |
| 10 | `aijobs_net` | 100 | job | 0/58 (0.0%) |
| 11 | `luma_events` | 78 | event | n/a (event, out of scope) |
| 12 | `weworkremotely` | 75 | job | n/a (no company field) |
| 13 | `meetup` | 64 | event | n/a (event, out of scope) |
| 14 | `yc_workatastartup` | 55 | job | 1/55 (1.8%) |
| 15 | `handshake_email` | 51 | job | 0/50 (0.0%) |
| 16 | `wellfound_apify_old` | 50 | job (frozen) | 5/49 (10.2%) |
| 17 | `eventbrite` | 46 | event | n/a (event, out of scope) |
| 18 | `builtin_sf` | 29 | job | 10/29 (34.5%) |
| 19 | `dice` | 20 | job | 5/18 (27.8%) |

Percentages are distinct-key overlap (how many of a source's *unique*
company+title postings are also seen elsewhere), not row overlap. Denominator
is unique keys, not raw item count, since sources with heavy within-source
multiplicity (see below) would otherwise understate their true overlap rate.

## Pairwise shared-key matrix

Cell = number of distinct `(company, title)` keys the row source shares with
the column source. Only pairs with ≥1 shared key are shown.

| source pair | shared keys |
|---|---|
| `linkedin_apify` <-> `vc_portfolio` | 45 |
| `greenhouse` <-> `vc_portfolio` | 41 |
| `indeed_apify` <-> `linkedin_apify` | 39 |
| `indeed_apify` <-> `vc_portfolio` | 34 |
| `ashby` <-> `indeed_apify` | 32 |
| `greenhouse` <-> `indeed_apify` | 23 |
| `indeed_apify` <-> `wellfound_search` | 18 |
| `greenhouse` <-> `wellfound_search` | 14 |
| `ashby` <-> `vc_portfolio` | 13 |
| `vc_portfolio` <-> `wellfound_search` | 11 |
| `greenhouse` <-> `linkedin_apify` | 10 |
| `ashby` <-> `linkedin_apify` | 9 |
| `linkedin_apify` <-> `wellfound_search` | 8 |
| `builtin_sf` <-> `vc_portfolio` | 7 |
| `greenhouse` <-> `builtin_sf` | 3 |
| `wellfound_apify_old` <-> `wellfound_search` | 3 |
| `dice` <-> `linkedin_apify` | 3 |
| `builtin_sf` <-> `linkedin_apify` | 2 |
| `dice` <-> `indeed_apify` | 2 |
| all remaining pairs | 1 each |

## Takeaways (cross-source)

Still no source clears a 40% confident cross-source overlap threshold, and
the broad conclusion from the original report holds: each source is
contributing mostly unique postings, not just re-scraping what others already
found. `greenhouse`/`lever`/`ashby` pull direct company boards (fixed
placeholder company list); the aggregators only sample a differently-filtered
slice of the market each run.

What changed with volume: the three general-market aggregators added since
the last pass (`indeed_apify`, `linkedin_apify`, `wellfound_search`) now
show up as each other's biggest cross-source overlap partners (`indeed_apify`
<-> `linkedin_apify`: 39 shared keys; `indeed_apify` <-> `wellfound_search`:
18) — expected, since all three now sample the same real SF/Bay Area DS/ML/AI
job market at meaningfully higher volume than the earlier single-digit test
runs. `vc_portfolio`'s overlap % nearly doubled (12%→23%) as `greenhouse`/
`ashby` coverage widened (see `03db341`) — more of the VC-backed companies now
have both a tracked portfolio listing and their own board indexed directly.
`builtin_sf` (34.5%) and `dice` (27.8%) remain the highest cross-source
overlap sources in relative terms, but both are tiny (29 and 20 items), so a
handful of shared keys swings the percentage a lot — not a meaningful signal
at this size.

## Within-source (company+title) multiplicity

Grouped by `(source, dedup_key)` across all 10,954 rows with both `author`
and `title` populated (excludes `hn_whoshiring`/`weworkremotely`).

**Rate:** 990 groups have >1 posting, covering 2,575 rows (23.5% of
keyed rows) — concentrated in the ATS-API sources (`greenhouse` 384 groups,
`ashby` 137, `lever` 77, `vc_portfolio` 51) same as before, plus now
`indeed_apify` (118) and `linkedin_apify` (212) at meaningfully higher
volume than last pass. **Group size** is still skewed small (699/990, 71%
are exactly 2 postings), with the same `aijobs_net` "Senior Tableau
Developer" mass-post outlier (39 postings, one per Latin American city) still
present.

**Single-location rate is where sources diverge sharply** — of a source's
duplicate groups, what fraction have every posting at the *same* location
(a strong signal of true re-surfacing rather than a legitimately distinct
posting per city):

| Source | Dup groups | Rows | % of source | Single-location groups |
|---|---|---|---|---|
| `lever` | 77 | 214 | 65.0% | 0/77 (0%) |
| `greenhouse` | 384 | 1052 | 33.0% | 19/384 (5%) |
| `ashby` | 137 | 357 | 20.0% | 2/137 (1%) |
| `vc_portfolio` | 51 | 113 | 19.1% | 5/51 (10%) |
| `indeed_apify` | 118 | 274 | 11.9% | 31/118 (26%) |
| `wellfound_search` | 4 | 8 | 1.0% | 4/4 (100%) |
| **`linkedin_apify`** | **212** | **505** | **37.4%** | **188/212 (89%)** |

`greenhouse`/`ashby`/`lever`/`vc_portfolio` reconfirm the original finding:
duplication is overwhelmingly real multi-location multiplicity (companies
opening the same req in several cities/regions), not a scrape or dedup
artifact — single-location rates stay in the single digits. `indeed_apify`
sits in between (26% single-location): sampled cases (e.g. AMD "MTS Software
Development Engineer" appearing twice each in San Jose and Santa Clara with
distinct `jk=` ids, or `DataAnnotation`'s generic remote-training titles
recurring across many Bay Area cities) look like genuinely separate postings
or recruiter mass-posts rather than re-scrape duplicates — Indeed's `jk=`
job-key is a stable per-posting identifier, so a repeat `(company, title,
location)` combination there is more likely a real second req than a scrape
artifact.

`linkedin_apify` is the clear outlier: 89% of its duplicate groups are
single-location, and it alone accounts for 188 of the 254 (74%) single-location
duplicate groups in the *entire* DB despite being a much smaller source than
`greenhouse`. See the dedicated section below for why.

## Why `linkedin_apify` self-duplicates and the others mostly don't

The user asked specifically to characterize this, since `indeed_apify` and
`linkedin_apify` were both scaled up via multiple manual runs with different
search parameters (San Francisco vs. San Jose location, broadened query,
retry passes — see `data/raw/indeed_apify_sanjose*.json` and
`data/raw/linkedin_apify_{broadened,retry,split}.json`). Comparing those raw
run files directly (independent of the DB) shows the two behave completely
differently:

**`indeed_apify` across its 3 known runs (SF, San Jose, San Jose-broadened):**
exact-URL overlap between runs is low (16-116 shared URLs per pair, out of
200-1200 items) and roughly matches the company+title overlap (53-113 shared
keys per pair) — the two measures agree, because Indeed's `viewjob?jk=<id>`
URL is a stable, content-addressed identifier. A re-scrape of the same
listing produces the *same* URL, so `UNIQUE(source, url)` correctly
dedups it at insert time. The residual overlap that does land in the DB (11.9%
of the source, mostly multi-location as shown above) is real market
multiplicity, not a dedup failure.

**`linkedin_apify` across its 4 known runs (test, broadened, retry, split):**
exact-URL/id overlap is **0 shared URLs across every single pair**, even
between runs covering overlapping search areas — yet company+title overlap
is substantial (55-88 shared keys per pair, ~16-25% of each run's unique
keys). The reason: the Apify actor's `link` field is a LinkedIn tracking
URL that embeds a `trackingId`/`refId`/`position` unique to that specific
search-results render, not a stable per-posting id — confirmed directly in
the DB, e.g. Adobe's "Machine Learning Engineer" in San Jose shows up as 5
separate rows, each with a different `-<numeric-id>` in the URL path and a
completely different `trackingId` query param, despite being (as far as the
title/company/location fields show) the same real posting scraped on
different runs. **This means `UNIQUE(source, url)` structurally cannot dedup
`linkedin_apify` reposts** — unlike every other source in this DB, where the
URL is a stable identifier for the underlying posting. It isn't a bug in the
ingest code; it's that the chosen identifier (`url`) isn't a valid dedup key
for this specific actor's output shape.

**Net effect:** `linkedin_apify` is carrying real duplicate rows today — 505
of its 1,350 rows (37%) are a same-company-same-title-same-location repeat of
another row already in the DB, the highest true-duplicate rate of any source
by a wide margin. `wellfound_search`, despite also running multiple
role×location search combinations by design (see `ROLE_SLUGS` loop in
`wellfound_search_apify.py`), doesn't have this problem — its actor returns
real `wellfound.com/company/<slug>/jobs/<slug>` URLs, which are stable and
correctly dedup. So the issue is specific to the LinkedIn actor's URL scheme,
not a general consequence of running multiple location searches or of using
Apify as a provider.

**Fixed 2026-07-03** (`src/pipeline/storage/db.py:insert_item_sync`): added
an `UNSTABLE_URL_SOURCES = {"linkedin_apify"}` set. For sources in that set,
if the (source, url) lookup misses, `insert_item_sync` now also checks for an
existing row with the same (source, dedup_key, location) before treating the
item as new. A match is folded exactly like a same-URL repost — `times_seen`/
`last_seen_at` bumped, and the old `raw_text` archived to `item_text_history`
if the re-scraped text actually changed — so date-of-repeat-sighting and
description-drift tracking both keep working for this source, they just key
off `(dedup_key, location)` instead of `url`. Verified live against a copy of
the real DB: a simulated re-scrape of an existing `linkedin_apify` posting
(new tracking URL, changed description) folded into the existing row
(`times_seen` 1→2, old text archived) instead of creating a duplicate; a
same-company-same-title posting at a genuinely different location still
inserted as a new row, confirming the fix doesn't over-fold legitimate
distinct postings.

**Forward-only, not retroactive** — same precedent as the original
`dedup_key`/`alt_listings` rollout (`_migrate_dedup_tracking` in `db.py`): the
505 existing `linkedin_apify` duplicate rows identified above are left as
separate rows, not merged or deleted. Retroactively picking a canonical row
and folding history into it is a bigger, more destructive decision than a
migration should make as a side effect; a deliberate retroactive merge pass
is a later call if it's ever wanted.

## Dedup decision (carried forward from 2026-07-02, still current)

No change to the live ingest/DB dedup key. `UNIQUE(source, url)` stays as
the only enforced gate; `dedup_key` remains a read-only analysis column, not
wired into `insert_item_sync` as a filter — except for the `linkedin_apify`
gap identified above, which is a real change candidate, not yet acted on.
