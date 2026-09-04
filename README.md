# Jobs Pipeline

AI-powered personal pipeline that scrapes/ingests job postings, tags and
ranks them with Claude, and surfaces them in a Streamlit UI. Also tracks
professional events/networking leads as a secondary, currently-frozen
capability. Built as an Eastern University DTSC 691 AI capstone project.
See [CLAUDE.md](CLAUDE.md) for full architecture/design notes and
[TODO.md](TODO.md) for detailed build status.

## Status

End-to-end pipeline works against real (non-mocked) data: scrapers -> SQLite
-> LLM tagger -> ranker -> Streamlit UI. 566 real items ingested and tagged
as of the last run. See "Current State" in [CLAUDE.md](CLAUDE.md) for the
full rundown of what's tested and what's still blocked (LinkedIn/Handshake
email parsers, evaluation harness, notifications).

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
playwright install               # needed for the Wellfound scraper
```

Create a `.env` file in the project root with:

```
ANTHROPIC_API_KEY=your-key-here
```

`ANTHROPIC_API_KEY` is only needed for the LLM tagging/ranking stage —
scraping, ingest, and browsing raw results in the UI all work with it
unset (see [docs/RUNNING_WITHOUT_ANTHROPIC.md](docs/RUNNING_WITHOUT_ANTHROPIC.md)).

`.env` is gitignored. `python-dotenv` is loaded explicitly in-code — being
in `requirements.txt` alone does nothing.

Set `PYTHONPATH` to `src` before running any module:

```bash
# Windows (PowerShell)
$env:PYTHONPATH = "src"

# bash
export PYTHONPATH=src
```

## Running the pipeline

Run each stage in order — later stages depend on data from earlier ones.

**1. Scrape + ingest into the DB** (HN Who's Hiring, Luma SF events, Built In
SF; Indeed RSS is dead, Wellfound is blocked by anti-bot — see CLAUDE.md):

```bash
python -m pipeline.ingest
```

Writes to `data/pipeline.db` (SQLite, gitignored). Safe to re-run — dedups
by `(source, url)`.

**2. Tag ingested items with the LLM** (optional — skip this and step 3 if
`ANTHROPIC_API_KEY` isn't set; the UI still works on raw ingested items.
Haiku by default, escalates to Sonnet on low self-reported confidence):

```bash
python -m pipeline.tagger.run_tagging
python -m pipeline.tagger.run_tagging --limit 50   # tag only N items
```

**3. Rank tagged items** by relevance score, category weight, and deadline
urgency:

```bash
python -m pipeline.ranker.rank
python -m pipeline.ranker.rank --limit 20
```

**4. Launch the UI** (search, tag browse, digest view, score histogram,
👍/👎 feedback):

```bash
streamlit run src/pipeline/ui/app.py
```

## Project layout

```
src/pipeline/
  scrapers/    # one module per source (hn_whoshiring, luma_events, builtin_sf, indeed_rss, wellfound)
  storage/     # SQLite schema + single-writer queue (db.py)
  ingest.py    # runs all scrapers, normalizes, writes through the storage queue
  tagger/      # LLM tagging (prompts.py, schema.py, tag_item.py, run_tagging.py)
  ranker/      # rank.py — scores tagged items
  ui/          # Streamlit app (app.py)
tests/
data/          # pipeline.db (gitignored)
docs/          # original capstone proposal docs
```

## Tests

```bash
pytest tests/
```
