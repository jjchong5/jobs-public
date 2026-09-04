# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: Claude Code
# Prompt: Schema iterated across 4 sessions (2026-06-24, 2026-07-03); clearest recoverable prompts are go-ahead/build confirmations ("I think it's good now, go ahead"; "build it, I'll review the prompts after") -- see docs/ai_usage/prompt_log.md#src-pipeline-tagger-schemapy for full session list
# Usage: Pydantic tagger output schema built and extended (including 2026-07-03 ranking-rework fields per CLAUDE.md) across multiple sessions.
# -------------------------------------------------------------------------

from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

SENIORITY_VALUES = ("intern", "junior", "mid", "senior", "staff+", "n/a")
ENGAGEMENT_TYPE_VALUES = ("full_time", "part_time", "contract", "freelance", "project_based")
SPAM_RISK_VALUES = ("clean", "suspicious", "likely_spam")
COMPANY_STAGE_VALUES = ("pre_seed", "seed", "series_a_b", "growth", "public", "unknown")

# Starting taxonomy derived from the real distribution of already-tagged
# role_type free text (253 distinct values across 566 tagged items as of
# 2026-07-02 -- "software engineer" 61, "data scientist" 26, "DevOps engineer"
# 19, etc.). role_type stays free text for detail/display; role_category is
# the normalized bucket used for grouping/tracking over time. Expected to
# need new buckets as more job titles show up -- add them here when a common
# title doesn't fit "other" well.
ROLE_CATEGORY_VALUES = (
    "software_engineer",     # SWE, full-stack, backend, frontend, founding/product engineer
    "devops_infra_engineer", # DevOps, infrastructure, SRE, security engineer
    "data_scientist",
    "data_engineer",
    "ml_ai_engineer",        # ML engineer, machine learning engineer, AI engineer
    "data_analyst",
    "product_manager",       # PM, project manager
    "designer",
    "sales_marketing",       # sales, business development, marketing, business analyst
    "ops_admin",             # executive/virtual assistant, customer service, coordinator roles
    # Added 2026-07-05: AI data-labeling/RLHF-rater contractor gigs (Scale AI-
    # style "AI Trainer" / "AI Training Specialist" postings). Distinct from
    # ml_ai_engineer -- these are non-engineering contract annotation/grading
    # work that was inadvertently ranking high under the freelance(1.5x) x
    # ai_ml-sector(1.4x) weight stack meant for real freelance AI eng work.
    # See ranker/scores.py role_category_weights for the derank.
    "ai_data_labeling",
    "other",
)

# Expanded 2026-07-03 alongside the preference-weighted ranking rework (see
# ranker/scores.py SECTOR_WEIGHTS) -- old "biotech_health" is split into
# biotech / health_general / adult_caregiving since the user wants biotech and
# caregiving surfaced as distinct favored buckets while general health stays
# unfavored. Same "adjust/expand as real items surface sectors that don't
# fit" spirit as before.
INDUSTRY_VALUES = (
    "ai_ml",
    "ai_research",
    "robotics",
    "science",
    "biotech",
    "health_general",
    "adult_caregiving",
    "real_estate",
    "transportation",
    "politics_civic",
    "prediction_markets",
    "fintech",
    "ai_education",
    "education",
    "climate_energy",
    "enterprise_saas",
    "consumer_gaming",
    "hardware_semiconductor",
    "government_defense",
    "other",
)


class TagResult(BaseModel):
    category: Literal["job", "event", "networking", "irrelevant"]
    role_type: Optional[str] = None
    role_category: Optional[str] = None
    industry: Optional[str] = None
    seniority: Optional[Literal["intern", "junior", "mid", "senior", "staff+", "n/a"]] = None
    engagement_type: Optional[Literal["full_time", "part_time", "contract", "freelance", "project_based"]] = None
    company_stage: Optional[Literal["pre_seed", "seed", "series_a_b", "growth", "public", "unknown"]] = None
    location: Optional[str] = None
    deadline: Optional[str] = None  # ISO date string if extractable, else null
    # Narrowed 2026-07-03: used to be an all-purpose "relevance" number that
    # conflated content quality, spam-likelihood, and personal preference fit.
    # Now scoped to ONE thing -- is this a real, substantive, well-written
    # posting (vs. low-effort/vague/inexperienced-poster junk that isn't
    # spam but also isn't worth much). Personal preference weighting happens
    # separately at rank-time (see ranker/scores.py); spam is its own field
    # below; requirement-oddity is its own field below.
    content_quality: float = Field(ge=0, le=10)
    spam_risk: Literal["clean", "suspicious", "likely_spam"] = "clean"
    # Signed: negative = requirements LESS demanding than typical for this
    # title, positive = MORE demanding than typical. Null if category isn't
    # "job" or there's not enough text to judge against a typical posting.
    role_expectation_delta: Optional[float] = Field(default=None, ge=-5, le=5)
    role_expectation_notes: Optional[str] = None  # e.g. "4y exp vs usual 2"
    confidence: float = Field(ge=0, le=1)  # LLM self-reported heuristic, not calibrated

    @field_validator("seniority", mode="before")
    @classmethod
    def _coerce_unknown_seniority(cls, v):
        # Multi-role postings sometimes get a free-text seniority like "mixed"
        # or "various" instead of one of our fixed values. Treat that as
        # "unknown" rather than failing the whole item -- losing a real
        # job posting over one free-text field is worse than a null seniority.
        if v is not None and v not in SENIORITY_VALUES:
            return None
        return v

    @field_validator("engagement_type", mode="before")
    @classmethod
    def _coerce_unknown_engagement_type(cls, v):
        # Same rationale as seniority above: don't fail the whole item over a
        # free-text engagement_type value outside our fixed enum.
        if v is not None and v not in ENGAGEMENT_TYPE_VALUES:
            return None
        return v

    @field_validator("role_category", mode="before")
    @classmethod
    def _coerce_unknown_role_category(cls, v):
        if v is not None and v not in ROLE_CATEGORY_VALUES:
            return None
        return v

    @field_validator("industry", mode="before")
    @classmethod
    def _coerce_unknown_industry(cls, v):
        if v is not None and v not in INDUSTRY_VALUES:
            return None
        return v

    @field_validator("company_stage", mode="before")
    @classmethod
    def _coerce_unknown_company_stage(cls, v):
        if v is not None and v not in COMPANY_STAGE_VALUES:
            return None
        return v

    @field_validator("spam_risk", mode="before")
    @classmethod
    def _coerce_unknown_spam_risk(cls, v):
        # Default to "clean" rather than failing the whole item over one bad
        # enum value, same rationale as seniority/engagement_type above.
        if v not in SPAM_RISK_VALUES:
            return "clean"
        return v
