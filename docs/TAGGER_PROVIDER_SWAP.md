# Tagger LLM provider swap — reference notes

Written 2026-07-03 after hitting the Anthropic Console API spend limit mid
tagging-backlog run. Not needed right now (limit was raised to $150, plenty
for the remaining backlog — see cost math below), but kept here so a future
switch (Codex/OpenAI, Gemini, GLM 5.2, Ollama on mac mini) doesn't require
re-deriving this from scratch.

## What's actually provider-specific

Only one function touches the Anthropic API: `_call_model()` in
`src/pipeline/tagger/tag_item.py` (lines ~39-66). Everything else is
provider-agnostic and needs NO changes on a swap:
- `schema.py` (`TagResult` Pydantic model + validators)
- `prompts.py` (system prompt, few-shot examples, `RAW_TEXT_CHAR_LIMIT`)
- `run_tagging.py`'s orchestration, concurrency, DB writes, locking
- `tag_item.py`'s public signature: `tag_item(raw_text) -> (TagResult|None, model, calls)`

Keep that signature identical on a swap and `run_tagging.py` needs zero changes.

## What changes per-provider

1. **Client init** (`_get_client`, tag_item.py:29-36) — swap SDK
   (`google-genai` / `openai`), swap env var name.
2. **API call shape** (tag_item.py:49-56) — different SDK call signature.
   Anthropic-specific: `output_config={"effort": "medium"}` on the Sonnet
   escalation call (line 48) — no equivalent elsewhere, just drop it.
3. **JSON extraction** (tag_item.py:58-66) — currently strips markdown
   fences + uses `json.JSONDecoder().raw_decode()` to ignore trailing prose,
   because this code path has no native JSON-mode. **Both Gemini and OpenAI
   have real structured-output modes** (OpenAI `response_format=
   {"type":"json_schema",...}`, Gemini `response_schema=`) that can be
   derived directly from the existing `TagResult` Pydantic schema — this
   would be a genuine upgrade over the current string-parsing, not just
   parity.
4. **Token usage reporting** (line 57) — each SDK reports differently:
   - Anthropic: `response.usage.input_tokens` / `.output_tokens`
   - OpenAI: `response.usage.prompt_tokens` / `.completion_tokens`
   - Gemini: `response.usage_metadata.prompt_token_count` / `.candidates_token_count`
   `run_tagging.py` just needs `(model, input_tokens, output_tokens)` tuples back — trivial remap.
5. **Pricing table** (`run_tagging.py:59-62`, `MODEL_PRICING` dict) — add a
   row per new model or cost logging silently reports $0.
6. **Two-tier escalation** (tag_item.py:79-91) — currently Haiku (cheap,
   temp 0.1) → Sonnet (strong, temp 0.2) on confidence < 0.7. Pick an
   equivalent cheap/strong pair *within* the new provider (e.g. Gemini
   Flash → Gemini Pro, GPT-4o-mini → GPT-4o) rather than mixing providers
   mid-escalation, so the confidence-escalation logic stays meaningful.

## Provider options considered (2026-07-03)

- **Codex / Gemini** — fastest to wire in since subscriptions already
  exist; no new billing setup. Neither has Anthropic's exact tool-use
  shape but both have real JSON-schema structured output (see point 3
  above) — arguably better than current approach.
- **2nd Anthropic account** — zero code changes, just a new API key under
  separate billing. Fastest if the goal is just more headroom on the
  existing Haiku/Sonnet setup and prompts.
- **GLM 5.2** — flagged separately as a cost-efficiency swap worth doing
  post-deadline regardless of this incident; see memory
  `tagger_cost_efficiency_priority`. Worth combining if switching anyway
  rather than doing two separate migrations.
- **Ollama on mac mini** — free, but weaker instruction-following on a
  12,000-char raw-text input raises retry/malformed-JSON risk; would need
  the confidence-escalation logic re-tuned against a much less reliable
  base model.

## Cost math for reference (2026-07-03 snapshot)

- Real observed avg cost: **~$0.0054/item** (from `run_log` table, last 800
  tagged items, mix of Haiku + Sonnet-escalation calls).
- Backlog at the time: 7,995 untagged of 18,418 total items.
- Estimated remaining cost: **~$43** — well under the $150 spend limit set
  2026-07-03 to cover testing + tagging through Sunday.

## Why the Console lockout happened (not a rate-limit issue)

The Console (platform.claude.com) API billing is a **separate account/limit
from claude.ai's Pro plan usage bar** — easy to conflate since both show
"usage limits" language. The lockout message ("reached your specified API
usage limits... regain access on 2026-08-01") is the signature of a
**self-configured spend/budget cap** tripping, not RPM/TPM throttling:
- Concurrency was only 15 threads (`run_tagging.py` default) — modest, and
  RPM/TPM throttling shows as per-call 429s, not an account-wide lockout
  with a fixed calendar reset date.
- Spend was 0.03% of the $200K org cap, ruling out a real ceiling — it was
  a configured limit far below that, which raising directly resolved
  (didn't need to wait for the Aug 1 reset).
