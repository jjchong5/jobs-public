# Customizing what the AI tagger looks for

**Short version:** this pipeline was tuned for one person's job search
(data science / ML / AI roles, freelance-friendly, SF/remote). The AI
tagging step and the ranking step are where that personal taste lives —
this doc explains how to change it to fit yours, without needing to
understand the rest of the codebase.

If you've never edited a Python file before: the changes below are all
"change this word/number to a different word/number" edits inside
existing files, using a plain text editor (VS Code, Notepad, etc.) —
you're not writing new code, just adjusting values.

## How tagging works, in short

Every scraped job posting gets sent to an LLM (Claude) with instructions
telling it what fields to extract and what values are allowed for each
field. That's it — there's no separate "training" step. To change what
gets tagged, you edit the instructions (the prompt) and/or the allowed
values (the schema).

Three files matter here, all under `src/pipeline/tagger/`:

- **`schema.py`** — the list of allowed values for each field (e.g. what
  counts as a "role category" or "industry"). Also the safety net: if the
  AI returns something not on this list, it gets set to blank rather than
  crashing.
- **`prompts.py`** — the actual instructions sent to the AI, plus a
  handful of worked examples ("few-shot examples") showing correct
  input/output pairs.
- **`tag_item.py`** — runs one item through the tagger. Useful for testing
  a prompt change on a single item before running it on your whole
  database.

## Example: adding a new role category

Say you want the tagger to recognize "technical writer" as its own
bucket, instead of falling into the generic `"other"`.

1. Open `src/pipeline/tagger/schema.py`. Find `ROLE_CATEGORY_VALUES` near
   the top — it's a tuple (a fixed list) of allowed string values. Add
   your new one:
   ```python
   ROLE_CATEGORY_VALUES = (
       "software_engineer",
       "devops_infra_engineer",
       # ...existing values...
       "technical_writer",   # <-- new
       "other",
   )
   ```
2. Open `src/pipeline/tagger/prompts.py`. Search for `ROLE_CATEGORY_ENUM`
   — it's built from the same list, so it updates automatically. No
   change needed there unless you want to also add a clarifying comment
   for the AI (worth doing if the category could be ambiguous — see the
   comments already there for other categories as examples of the style).
3. **(Optional but recommended)** If you want this category to affect
   ranking (e.g. down-rank or up-rank technical writer postings), add it
   to `ROLE_CATEGORY_WEIGHTS` in `src/pipeline/storage/db.py` — see
   "Changing ranking weights" below. If you skip this, the new category
   still gets tagged correctly, it just won't influence sort order (same
   as most existing categories — only one is currently weighted).
4. Test it on one item before running it on everything:
   ```bash
   python -m pipeline.tagger.tag_item
   ```
   This makes one real API call — cheap, but not free. Check the output
   looks right before tagging your whole backlog.

**Important:** existing already-tagged items in your database do NOT get
retagged automatically when you add a new category — only items tagged
*after* your change will use it. If you want to reclassify old items into
the new category, you'd need to re-run the tagger against them
specifically (see `run_tagging.py --limit N`, or ask an AI coding
assistant to help write a small backfill script — this project itself was
built with one, so that's a completely normal way to extend it).

## Example: changing what "relevant" means

The system prompt (`SYSTEM_PROMPT_TEMPLATE` in `prompts.py`) is one long
string with the full instructions. It's written in plain English — read
through it once before changing anything, since later instructions
sometimes reference earlier ones.

Things you can change:
- **The `category` field's "irrelevant" bucket** — currently defined
  loosely as spam/junk. If you want stricter or looser filtering (e.g.
  auto-marking anything that isn't full-time as irrelevant, if you don't
  want freelance work at all), edit the instructions around the
  `"category"` field description.
- **The few-shot examples** (`FEW_SHOT_EXAMPLES`, further down in the same
  file) — these are worked examples the AI learns the desired output
  format from. A couple of them use San Francisco as the example
  location (that's just because that's where the real input postings came
  from when these examples were written — it doesn't bias the AI toward
  preferring SF, but if you want to be thorough, feel free to swap in an
  example from your own target region/field).
- **`content_quality`, `spam_risk`, `role_expectation_delta`** — these are
  scored fields with their own instructions in the prompt. If your use
  case doesn't care about one of these (e.g. you don't need
  spam-detection because your sources are all reputable), you can leave
  it as-is — an unused field doesn't hurt anything, it's just extra
  signal you're not required to use downstream.

**Keep changes incremental.** Change one thing, test it with
`tag_item.py` against a couple of real postings, and read the output
before changing more. LLM prompts are sensitive to phrasing in ways that
aren't always obvious — a change that seems unrelated can shift how the
AI treats other fields.

## Changing ranking weights (separate from tagging)

Tagging decides *what a posting is* (its category, seniority, location,
etc.) — ranking decides *how high it sorts*, based on weight tables that
multiply a posting's base score up or down per field value. This is
where personal taste (freelance vs. full-time, junior vs. senior, etc.)
actually lives.

The six weight tables — `engagement_weights`, `seniority_weights`,
`location_weights`, `sector_weights`, `stage_weights`,
`role_category_weights` — are defined as `DEFAULT_*_WEIGHTS` constants in
`src/pipeline/storage/db.py`. Each is a dictionary of `{value: multiplier}`
pairs, multiplier `1.0` = neutral, higher = ranked up, lower = ranked
down. For example:

```python
DEFAULT_SENIORITY_WEIGHTS = {
    "intern": 1.3, "junior": 1.3, "mid": 1.2, "senior": 1.0, "staff+": 0.7, "n/a": 1.0,
}
```

This default setup favors junior/mid roles and downranks staff+ senior
roles — that was one person's preference, not a general default. If you
want the opposite (you're senior and don't want to see internships), flip
the numbers:

```python
DEFAULT_SENIORITY_WEIGHTS = {
    "intern": 0.5, "junior": 0.6, "mid": 0.9, "senior": 1.3, "staff+": 1.4, "n/a": 1.0,
}
```

**Same caveat as the location doc:** editing these constants only affects
a brand-new database. If you already have `data/pipeline.db`, either
delete it and start over, or update the live row directly and re-run the
ranker — full instructions in
[CHANGING_LOCATION.md](CHANGING_LOCATION.md#4-the-rankers-location-weight-table-affects-sort-order-not-what-s-collected)
(the same update mechanism applies to all six weight tables, not just
location).

## Related

- [CHANGING_LOCATION.md](CHANGING_LOCATION.md) — changing which region
  gets scraped and how location affects ranking.
- `src/pipeline/tagger/tag_item.py` — the fastest way to test a prompt
  change against one real item before committing to a full tagging run.
