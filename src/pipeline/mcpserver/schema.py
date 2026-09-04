"""Pydantic models for the MCP server's public surface: the exposed item
shape (allowlist -- see CLAUDE.md/plan for what's excluded and why) and the
caller-supplied weights model for rank_items.
"""
from typing import Optional

from pydantic import BaseModel, Field

from pipeline.tagger.schema import (
    COMPANY_STAGE_VALUES,
    ENGAGEMENT_TYPE_VALUES,
    INDUSTRY_VALUES,
    ROLE_CATEGORY_VALUES,
    SENIORITY_VALUES,
)

# Explicit allowlist. Deliberately excludes: raw_text (own field, truncated,
# not in list views), spam_risk/content_quality/tagger_model/dedup_key/
# alt_listings/feedback/not_interested_reason/application_status (the author's
# internal QA + personal workflow state, not for other users), and the
# DB-stored preference_score/urgency_score/general_score (those reflect
# the author's own tuned weights -- callers get scores recomputed under their own
# weights instead, via rank_items).
PUBLIC_ITEM_FIELDS = (
    "id", "source", "url", "title", "author", "location", "posted_at",
    "category", "role_type", "role_category", "industry", "seniority",
    "engagement_type", "company_stage", "deadline", "remote_type",
)


class PublicItem(BaseModel):
    id: int
    source: str
    url: str
    title: Optional[str] = None
    author: Optional[str] = None
    location: Optional[str] = None
    posted_at: Optional[str] = None
    category: Optional[str] = None
    role_type: Optional[str] = None
    role_category: Optional[str] = None
    industry: Optional[str] = None
    seniority: Optional[str] = None
    engagement_type: Optional[str] = None
    company_stage: Optional[str] = None
    deadline: Optional[str] = None
    remote_type: Optional[str] = None


class RankedItem(PublicItem):
    score: float


class CallerWeights(BaseModel):
    """Caller's own weight tables for rank_items -- same shape as
    preference_profiles' weight columns, but never merged with or allowed to
    read the author's actual active profile. All optional; unset tables default to
    neutral (1.0 for every value) in scores.py's preference_multiplier.
    Keys are validated against the same enums the tagger uses, so a typo'd
    key just gets ignored (matches an unknown item value -> default 1.0)
    rather than silently doing nothing useful.
    """
    engagement_weights: dict[str, float] = Field(default_factory=dict)
    seniority_weights: dict[str, float] = Field(default_factory=dict)
    location_weights: dict[str, float] = Field(default_factory=dict)
    sector_weights: dict[str, float] = Field(default_factory=dict)
    stage_weights: dict[str, float] = Field(default_factory=dict)
    role_category_weights: dict[str, float] = Field(default_factory=dict)
    category_weights: dict[str, float] = Field(default_factory=dict)

    def as_profile_dict(self) -> dict:
        return self.model_dump()


VALID_ENUMS = {
    "seniority": set(SENIORITY_VALUES),
    "engagement_type": set(ENGAGEMENT_TYPE_VALUES),
    "company_stage": set(COMPANY_STAGE_VALUES),
    "role_category": set(ROLE_CATEGORY_VALUES),
    "industry": set(INDUSTRY_VALUES),
}
