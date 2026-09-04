# Running without an Anthropic API key

The LLM tagging/ranking stage is optional. Scraping, ingest, dedup, and
browsing raw results in the Streamlit UI all work with `ANTHROPIC_API_KEY`
left blank in `.env`.

## What works with no key

- `python -m pipeline.ingest` — scrapes every configured source and writes
  raw items to `data/pipeline.db`, same as with a key set.
- `streamlit run src/pipeline/ui/app.py` — opens with an info banner
  ("N items ingested, but none are tagged yet") and shows the raw ingested
  items: title, source, company, location, posted date, link. Search and
  the source/date filters work normally. Category filters, digest view,
  and score-sorted views have nothing to show, since those all key off
  tagger output.
- `python -m pipeline.scheduler` — runs scrapers on their normal cadence.
  The tag/rank step logs one line ("Tagging skipped: no tagger provider
  configured") each cycle and moves on, instead of throwing.

## What needs a key

- `python -m pipeline.tagger.run_tagging` — tagging itself. Without a key
  this returns immediately with `{"tagged": 0, "failed": 0,
  "skipped_reason": "no_provider_configured"}` rather than raising.
- `python -m pipeline.ranker.rank` — technically provider-agnostic (it's
  pure math over already-tagged DB columns, see `ranker/scores.py`), but
  its query only selects rows with a non-null `category`, so with nothing
  tagged it correctly ranks 0 items. This isn't a bug in the ranker; it's
  just that ranking has nothing to sort yet.
- Category browsing, digest view, and preference-weighted sort in the UI.

## Provider choice

`TAGGER_PROVIDER` in `.env` selects `anthropic` (default) or `glm` (see
`docs/TAGGER_PROVIDER_SWAP.md` — GLM support is stubbed but unverified
against a real account). Either provider requires its own API key; the
pipeline treats "no key for the selected provider" as "tagging disabled,"
not as an error condition.
