# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: Claude Code
# Prompt: 2026-07-05 overnight-pass task, "GLM 5.2 / provider-swap
#   groundwork" section -- see docs/ai_usage/prompt_log.md#src-pipeline-tagger-providerspy
# Usage: Provider-agnostic TaggerClient abstraction (Anthropic + stubbed
#   GLM implementations), selected via TAGGER_PROVIDER env var, Anthropic
#   remaining the default/active provider.
# -------------------------------------------------------------------------

"""Provider abstraction for the tagger's LLM calls. Anthropic is the live default;
GLM (Zhipu AI) is stubbed against its published API shape so that switching providers
later is a `TAGGER_PROVIDER` env var change, not a code change.

Verified vs. assumed for the GLM implementation (2026-07-04, no GLM API key available
to test against -- this path is unexercised):
- VERIFIED (via GLM API docs, https://docs.z.ai/api-reference): GLM's chat-completions
  API is OpenAI-compatible -- same request/response shape as `openai.chat.completions.create`,
  reachable by pointing the `openai` SDK's `base_url` at Zhipu's endpoint
  (`https://open.bigmodel.cn/api/paas/v4/` domestic, `https://api.z.ai/api/paas/v4/`
  international) with a GLM API key as the bearer token.
- ASSUMED (not verified against a real account): exact GLM 5.2 model id strings,
  effort/thinking-mode parameter name and values, and current pricing -- see the
  TODO constants below. Confirm all three against a real GLM API key before flipping
  TAGGER_PROVIDER=glm to anything but a manual smoke test.
"""
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass

from anthropic import Anthropic


@dataclass
class ModelTier:
    """One escalation tier (cheap-default or escalated) for a provider."""
    model: str
    temperature: float
    max_tokens: int


@dataclass
class CompletionResult:
    text: str
    input_tokens: int
    output_tokens: int


class TaggerClient(ABC):
    """One provider's ability to run a single tagging completion call.

    Escalation policy (confidence < threshold -> retry with the escalated tier)
    lives in tag_item.py, not here -- this interface only knows how to make one
    call against one tier for one provider.
    """

    #: Cheap default tier used for every item.
    default_tier: ModelTier
    #: Escalated tier used when default_tier's self-reported confidence is low.
    escalation_tier: ModelTier

    @abstractmethod
    def complete(self, system_prompt: str, user_message: str, tier: ModelTier) -> CompletionResult:
        ...


def build_cached_system_blocks(system_prompt: str) -> list[dict]:
    """System prompt + few-shot examples as one cache_control-marked content
    block. Both are fully static across every call (independent of item text;
    the only date-dependent bit is "today", already baked into system_prompt
    by build_system_prompt before this runs) -- caching them means repeated
    calls within the ~5min TTL pay ~10% input-token rate on this block instead
    of 100%, which is the bulk of every call's input tokens given how much
    fixed schema/enum/few-shot text there is vs. one item's raw_text. Deferred
    import of build_examples_block avoids a circular import at module load.
    """
    from pipeline.tagger.prompts import build_examples_block

    combined = f"{system_prompt}\n\n{build_examples_block()}"
    return [{"type": "text", "text": combined, "cache_control": {"type": "ephemeral"}}]


class AnthropicTaggerClient(TaggerClient):
    """Today's behavior, preserved byte-for-byte from the pre-refactor tag_item.py."""

    def __init__(self):
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set in environment/.env")
        self._client = Anthropic(api_key=api_key)
        self.default_tier = ModelTier("claude-haiku-4-5-20251001", temperature=0.1, max_tokens=300)
        self.escalation_tier = ModelTier("claude-sonnet-4-6", temperature=0.2, max_tokens=600)

    def complete(self, system_prompt: str, user_message: str, tier: ModelTier) -> CompletionResult:
        kwargs = {}
        if tier.model == self.escalation_tier.model:
            # Haiku 4.5 errors on output_config.effort (unsupported), so this is
            # Sonnet-only. Sonnet 4.6 defaults to "high" effort when unset -- too
            # much for a fixed-schema classification/extraction call. "medium"
            # (not "low") since this is specifically the escalation path for
            # items Haiku was already unsure about.
            kwargs["output_config"] = {"effort": "medium"}
        response = self._client.messages.create(
            model=tier.model,
            max_tokens=tier.max_tokens,
            temperature=tier.temperature,
            system=build_cached_system_blocks(system_prompt),
            messages=[{"role": "user", "content": user_message}],
            **kwargs,
        )
        text = response.content[0].text.strip()
        return CompletionResult(text, response.usage.input_tokens, response.usage.output_tokens)

    def build_message_params(self, system_prompt: str, user_message: str, tier: ModelTier) -> dict:
        """Same request shape as complete(), but returned as a plain dict instead
        of being sent -- used by run_tagging.py to assemble Message Batches
        requests for the non-realtime lane (see MODULE docstring)."""
        kwargs = {}
        if tier.model == self.escalation_tier.model:
            kwargs["output_config"] = {"effort": "medium"}
        return dict(
            model=tier.model,
            max_tokens=tier.max_tokens,
            temperature=tier.temperature,
            system=build_cached_system_blocks(system_prompt),
            messages=[{"role": "user", "content": user_message}],
            **kwargs,
        )

    @property
    def raw_client(self) -> Anthropic:
        """Escape hatch for run_tagging.py's Batches API calls, which need the
        underlying SDK client directly (batches.create/results are not part of
        the single-call TaggerClient interface)."""
        return self._client


# TODO(glm): confirm real GLM 5.2 model ids against a live account before use.
# These are placeholders following Zhipu's public naming convention (glm-4.x-flash
# = cheap tier, glm-4.x-plus = escalated tier), NOT verified model strings.
GLM_DEFAULT_MODEL = "glm-4.6-flash"  # TODO(glm): confirm actual GLM 5.2 cheap-tier model id
GLM_ESCALATION_MODEL = "glm-4.6-plus"  # TODO(glm): confirm actual GLM 5.2 escalation-tier model id
GLM_BASE_URL = "https://api.z.ai/api/paas/v4/"  # international endpoint per docs.z.ai; domestic is open.bigmodel.cn


class GLMTaggerClient(TaggerClient):
    """Stubbed against GLM's OpenAI-compatible API shape. Untested against a real
    key -- see module docstring for what's verified vs. assumed."""

    def __init__(self):
        # Imported lazily so the `openai` package is only required when this
        # provider is actually selected.
        from openai import OpenAI

        api_key = os.environ.get("GLM_API_KEY")
        if not api_key:
            raise RuntimeError("GLM_API_KEY not set in environment/.env")
        self._client = OpenAI(api_key=api_key, base_url=GLM_BASE_URL)
        self.default_tier = ModelTier(GLM_DEFAULT_MODEL, temperature=0.1, max_tokens=300)
        self.escalation_tier = ModelTier(GLM_ESCALATION_MODEL, temperature=0.2, max_tokens=600)

    def complete(self, system_prompt: str, user_message: str, tier: ModelTier) -> CompletionResult:
        kwargs = {}
        if tier.model == self.escalation_tier.model:
            # TODO(glm): confirm GLM's actual reasoning-effort parameter name/values
            # (Zhipu calls this "thinking" on some GLM models, e.g.
            # {"thinking": {"type": "enabled"}}) -- not verified against a live
            # response, so left unset rather than guessing a param that could
            # error the same way Haiku errors on Anthropic's output_config.effort.
            pass
        response = self._client.chat.completions.create(
            model=tier.model,
            max_tokens=tier.max_tokens,
            temperature=tier.temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            **kwargs,
        )
        text = response.choices[0].message.content.strip()
        usage = response.usage
        return CompletionResult(text, usage.prompt_tokens, usage.completion_tokens)


_PROVIDERS = {
    "anthropic": AnthropicTaggerClient,
    "glm": GLMTaggerClient,
}

_client: TaggerClient | None = None
_client_unavailable: bool = False


class TaggerUnavailableError(RuntimeError):
    """Raised when no tagger provider is configured (e.g. no ANTHROPIC_API_KEY).
    Scraping/ingest/ranking never import this module, so this only surfaces to
    code that explicitly tries to tag -- callers should catch it and skip
    tagging rather than crash (see run_tagging.run())."""


def tagger_available() -> bool:
    """Cheap check for callers (run_tagging.py, scheduler.py) that want to skip
    tagging entirely -- and log only once -- instead of hitting
    TaggerUnavailableError on every item/run."""
    provider = os.environ.get("TAGGER_PROVIDER", "anthropic").strip().lower()
    if provider == "anthropic":
        return bool(os.environ.get("ANTHROPIC_API_KEY"))
    if provider == "glm":
        return bool(os.environ.get("GLM_API_KEY"))
    return False


def get_tagger_client() -> TaggerClient:
    """Reads TAGGER_PROVIDER once and caches the resulting client. Default is
    "anthropic" if unset, so existing deployments/behavior are unaffected.
    Raises TaggerUnavailableError (not a bare RuntimeError from the provider's
    own __init__) if the required API key is missing, so callers can catch one
    specific exception type to mean "no tagger configured"."""
    global _client
    if _client is None:
        provider = os.environ.get("TAGGER_PROVIDER", "anthropic").strip().lower()
        if provider not in _PROVIDERS:
            raise RuntimeError(
                f"Unknown TAGGER_PROVIDER={provider!r}; must be one of {sorted(_PROVIDERS)}"
            )
        if not tagger_available():
            raise TaggerUnavailableError(
                f"No API key configured for TAGGER_PROVIDER={provider!r}. "
                "Tagging/ranking are optional -- scraping and browsing work "
                "without this; set ANTHROPIC_API_KEY (or GLM_API_KEY) in .env "
                "to enable tagging."
            )
        _client = _PROVIDERS[provider]()
    return _client
