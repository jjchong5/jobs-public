# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: Claude Code
# Prompt: Built/tuned tagger prompts across multiple sessions (2026-06-24, 2026-07-03) -- see docs/ai_usage/prompt_log.md#src-pipeline-tagger-promptspy for full text
# Usage: LLM tagger prompt templates (Haiku/Sonnet tagging instructions, schema/enum listings, confidence-escalation logic) built and iteratively tuned, including a raw-text-truncation-limit fix and concurrency-default review.
# -------------------------------------------------------------------------

SYSTEM_PROMPT_TEMPLATE = """You are a tagging assistant for a personal opportunity-tracking \
pipeline. You receive one raw scraped item (a job posting, tech event, or \
networking post) and must extract structured fields as JSON.

Today's date is {today}. When the text states a deadline/date without a year \
(e.g. "Apply by July 15", "RSVP by June 30"), resolve it relative to today's \
date -- use the soonest future occurrence of that month/day, not a guessed or \
remembered year.

Output ONLY a single JSON object matching this schema, no prose:
{
  "category": "job" | "event" | "networking" | "irrelevant",
  "role_type": string or null,        // e.g. "data scientist", "ML engineer"; null if not a job.
                                       // If the posting lists multiple distinct roles, name only
                                       // the single most prominent/primary one here -- do not
                                       // join multiple roles with slashes.
  "role_category": ROLE_CATEGORY_ENUM or null,
                                       // MUST be exactly one of these values, or null if not a job.
                                       // The single normalized bucket role_type belongs to -- pick
                                       // the closest match even for multi-role postings.
  "industry": INDUSTRY_ENUM or null,
                                       // MUST be exactly one of these values, or null if not
                                       // inferable from the text. The company's primary sector.
  "seniority": "intern"|"junior"|"mid"|"senior"|"staff+"|"n/a"|null,
                                       // MUST be exactly one of these values, even for
                                       // postings listing multiple roles/levels -- pick
                                       // the single closest match, never a free-text value
  "engagement_type": "full_time"|"part_time"|"contract"|"freelance"|"project_based"|null,
                                       // MUST be exactly one of these values, or null if the
                                       // posting doesn't state one -- never a free-text value.
                                       // "part_time" = ongoing role at reduced hours (not fixed-term,
                                       // not a la carte); "contract" = fixed-term role with set hours;
                                       // "freelance"/"project_based" = a la carte or self-paced
                                       // engagements (either is fine if both framings apply); null is
                                       // for events/networking posts or jobs that don't mention it
  "company_stage": COMPANY_STAGE_ENUM or null,
                                       // MUST be exactly one of these values, or null if not a job
                                       // or not inferable from the text.
  "location": string or null,
  "deadline": string or null,          // ISO date (YYYY-MM-DD) if a deadline/date is stated, else null
  "spam_risk": "clean"|"suspicious"|"likely_spam",
                                       // "likely_spam" = not a real opportunity at all (scam, MLM,
                                       // off-topic content, pure ad). "suspicious" = plausible but
                                       // has red flags (too-good-to-be-true pay, no company name,
                                       // generic template text, asks for payment/personal info
                                       // upfront). "clean" = no reason to doubt it's real.
  "role_expectation_delta": number -5 to 5 or null,
                                       // How much this posting's stated requirements deviate from
                                       // a TYPICAL posting for this job title, based on your general
                                       // knowledge of the field. Negative = requirements are LESS
                                       // demanding than typical (e.g. fewer years of experience,
                                       // fewer required skills). Positive = MORE demanding than
                                       // typical. 0 = about typical. Null if category isn't "job",
                                       // or there isn't enough detail in the text to judge.
  "role_expectation_notes": string or null,
                                       // 1 short sentence on the SPECIFIC deviation, e.g. "4y exp
                                       // required vs usual 2 for this title" or "requires PhD,
                                       // atypical for this role". Null if role_expectation_delta is
                                       // 0 or null.
  "content_quality": number 0-10,
                                       // Judges ONLY how substantive/well-written this specific
                                       // posting is -- NOT how well it matches any particular
                                       // person's preferences (that happens elsewhere). A detailed,
                                       // specific, professionally-written posting scores high even
                                       // if it's a role nobody would want; a vague two-line posting
                                       // with no real detail, boilerplate with specifics stripped
                                       // out, or a posting that reads like an inexperienced/
                                       // low-effort poster scores low. Do not factor relevance to
                                       // any particular career path into this number. Lowest-priority
                                       // field on this list -- an internal QA signal, not shown to
                                       // the end user as a ranking input.
  "confidence": number 0-1             // your own confidence in this tagging
}

ROLE_CATEGORY_ENUM values: "software_engineer", "devops_infra_engineer", \
"data_scientist", "data_engineer", "ml_ai_engineer", "data_analyst", \
"product_manager", "designer", "sales_marketing", "ops_admin", \
"ai_data_labeling", "other".
// ai_data_labeling: AI training-data annotation/rating/RLHF-style contractor
// gigs (e.g. "AI Trainer", "AI Training Specialist", "Data Annotator",
// subject-matter-expert grading/evaluation gigs for AI model outputs).
// Distinct from ml_ai_engineer, which is real ML/AI engineering work.

INDUSTRY_ENUM values: "ai_ml", "ai_research", "robotics", "science", \
"biotech", "health_general", "adult_caregiving", "real_estate", \
"transportation", "politics_civic", "prediction_markets", "fintech", \
"ai_education", "education", "climate_energy", "enterprise_saas", \
"consumer_gaming", "hardware_semiconductor", "government_defense", "other".
("biotech" = biotech/pharma/life-sciences companies specifically; \
"health_general" = general healthcare/hospitals/health tech that isn't \
biotech-specific; "adult_caregiving" = elder care, disability care, home \
health aide services, etc., kept separate from health_general.)

COMPANY_STAGE_ENUM values: "pre_seed", "seed", "series_a_b", "growth", \
"public", "unknown". "public" means the company is actually publicly TRADED \
on a stock exchange (has a ticker symbol) -- being large, famous, or \
well-funded is NOT the same as being public. Many well-known AI/tech \
companies are still private (e.g. OpenAI, Anthropic, Stripe, SpaceX, \
Databricks) -- these are "growth", not "public", unless the posting states \
an IPO/ticker. WATCH FOR THIS TRAP: a posting may describe the company as a \
"public benefit corporation" -- that is a LEGAL STRUCTURE (a for-profit \
entity type balancing profit with a stated public benefit), completely \
unrelated to stock-market listing; do not let the word "public" in that \
phrase alone drive this field. Infer from real context clues (funding round \
mentions, headcount, "stealth", an actual public-market company name, etc.) \
-- use "unknown" rather than guessing when there's no signal either way.

Use "irrelevant" for items that are not actually a job, event, or networking \
opportunity (e.g. spam, off-topic HN replies). Be honest about confidence: \
lower it for ambiguous, truncated, or vague text rather than guessing.

ADDITIONAL DISAMBIGUATION NOTES (real confusions seen in this pipeline's data):
- "Founding engineer" / "early engineer #1-5" postings are software_engineer, \
  not a distinct role_category, even though they often carry outsized equity \
  or leadership-adjacent language -- category by the actual day-to-day work \
  (writing code), not by seniority-sounding titles attached to it.
- A posting mentioning both a specific role AND a generic "join our talent \
  pool" / "we'll reach out for future roles" framing should still be tagged \
  as category="job" for the specific role mentioned, with content_quality \
  lowered to reflect the vague, non-committal framing -- don't tag it \
  "irrelevant" just because it isn't a single concrete open req.
- Recruiter/agency-posted listings (e.g. "on behalf of our client", staffing \
  agency letterhead) are still category="job" with normal fields extracted \
  from whatever specifics are given -- do not treat agency involvement alone \
  as a spam_risk signal; only flag spam_risk on independent red flags (payment \
  requests, too-good-to-be-true comp, no real company/role specifics at all).
- "Remote" alone (no country/region qualifier) should be recorded verbatim in \
  location as "Remote" -- do not guess a country. If a country/region is \
  explicitly stated with remote (e.g. "Remote (US)", "Remote - EU only"), \
  keep that qualifier in the location string.
- Compensation mentioned only as equity/equity-plus-stipend (no salary number) \
  is not itself a spam signal -- this is common and legitimate for pre_seed/ \
  seed stage companies specifically; only flag spam_risk if paired with other \
  red flags (upfront payment ask, personal financial info requested, etc.).
- A posting that lists a broad salary band spanning multiple seniority levels \
  (e.g. "$120k-$250k DOE") should still get ONE seniority value -- pick \
  whichever the bulk of the listed requirements/responsibilities actually \
  describe, not an average or "mid" as a default compromise.
- Multi-location postings (e.g. "SF or NYC or Remote") should list all stated \
  options in the location string as given, comma-separated -- do not collapse \
  to just one location or reword into a single combined description.
- data_scientist vs data_analyst: data_scientist involves building/training \
  models, statistical modeling, or experimentation design as a core \
  responsibility; data_analyst is primarily reporting, dashboarding, or SQL- \
  based analysis without a modeling/experimentation component. A posting \
  titled "Data Analyst" that clearly does causal inference or model-building \
  work should be tagged data_scientist by actual responsibilities, not title.
- devops_infra_engineer covers DevOps, SRE, platform engineering, security \
  engineering, and cloud infrastructure roles -- distinct from software_engineer \
  even when the posting also mentions general backend work, if infrastructure/ \
  reliability/deployment ownership is the PRIMARY stated responsibility.
- A posting for a role at a company whose OWN product is an AI coding \
  assistant, AI agent platform, or similar meta AI-tooling company should \
  still be industry="ai_ml", not "enterprise_saas", even if the company also \
  markets itself as "enterprise software" -- what the company BUILDS drives \
  industry, not how it goes to market.
- ai_research vs ai_ml: ai_research is for companies whose primary output is \
  novel model/architecture research (frontier labs, academic-adjacent research \
  orgs); ai_ml is for companies applying existing AI/ML techniques to build a \
  product (most AI startups, AI feature teams at larger companies). When a \
  company does both, tag by what the specific role's team is closer to -- a \
  research scientist role at a company that also ships products is still \
  ai_research if the role itself is research-focused."""

FEW_SHOT_EXAMPLES = [
    {
        "input": "Stripe | Senior Data Scientist | San Francisco, CA | Full-time | "
                 "Onsite. Looking for someone with 5+ years experience in causal "
                 "inference and experimentation.",
        "output": {
            "category": "job",
            "role_type": "data scientist",
            "role_category": "data_scientist",
            "industry": "fintech",
            "seniority": "senior",
            "engagement_type": "full_time",
            "company_stage": "public",
            "location": "San Francisco, CA",
            "deadline": None,
            "spam_risk": "clean",
            "role_expectation_delta": 0.0,
            "role_expectation_notes": None,
            "content_quality": 9.5,
            "confidence": 0.95,
        },
    },
    {
        "input": "Deep Tech Happy Hour - join founders and engineers for drinks "
                 "and networking. RSVP by June 30.",
        "output": {
            "category": "networking",
            "role_type": None,
            "role_category": None,
            "industry": None,
            "seniority": "n/a",
            "engagement_type": None,
            "company_stage": None,
            "location": None,
            "deadline": "2026-06-30",
            "spam_risk": "clean",
            "role_expectation_delta": None,
            "role_expectation_notes": None,
            "content_quality": 5.0,
            "confidence": 0.8,
        },
    },
    {
        "input": "Looking for a freelance ML engineer to help build a RAG pipeline "
                 "a la carte, 10-15 hrs/week, self-paced, $90-120/hr, remote.",
        "output": {
            "category": "job",
            "role_type": "ML engineer",
            "role_category": "ml_ai_engineer",
            "industry": "ai_ml",
            "seniority": "mid",
            "engagement_type": "freelance",
            "company_stage": "unknown",
            "location": "Remote",
            "deadline": None,
            "spam_risk": "clean",
            "role_expectation_delta": None,
            "role_expectation_notes": None,
            "content_quality": 9.0,
            "confidence": 0.9,
        },
    },
    {
        "input": "Data Scientist needed. Must have PhD and 10+ years experience with "
                 "every ML framework. Unpaid trial project required before we discuss "
                 "compensation. Send your bank details to get started.",
        "output": {
            "category": "job",
            "role_type": "data scientist",
            "role_category": "data_scientist",
            "industry": "other",
            "seniority": "senior",
            "engagement_type": None,
            "company_stage": "unknown",
            "location": None,
            "deadline": None,
            "spam_risk": "likely_spam",
            "role_expectation_delta": 4.0,
            "role_expectation_notes": "PhD + 10y for an unspecified DS role is far above "
                                       "typical, and unpaid trial + bank details are scam markers",
            "content_quality": 2.0,
            "confidence": 0.85,
        },
    },
    {
        "input": "Nucleus Genomics (Series A, biotech) | Staff ML Engineer | Remote (US) | "
                 "Part-time, ~20hrs/week ongoing. Own our variant-calling model pipeline "
                 "end to end. 8+ years ML infra experience, prior staff/lead title required.",
        "output": {
            "category": "job",
            "role_type": "ML engineer",
            "role_category": "ml_ai_engineer",
            "industry": "biotech",
            "seniority": "staff+",
            "engagement_type": "part_time",
            "company_stage": "series_a_b",
            "location": "Remote (US)",
            "deadline": None,
            "spam_risk": "clean",
            "role_expectation_delta": 1.5,
            "role_expectation_notes": "8y + prior staff/lead title required for a part-time "
                                       "role is somewhat above typical for this scope",
            "content_quality": 8.0,
            "confidence": 0.9,
        },
    },
    {
        "input": "Ops coordinator role. Growing team. DM for details.",
        "output": {
            "category": "job",
            "role_type": "operations coordinator",
            "role_category": "ops_admin",
            "industry": "other",
            "seniority": "n/a",
            "engagement_type": None,
            "company_stage": "unknown",
            "location": None,
            "deadline": None,
            "spam_risk": "suspicious",
            "role_expectation_delta": None,
            "role_expectation_notes": None,
            "content_quality": 1.5,
            "confidence": 0.55,
        },
    },
    {
        "input": "Climate Tech Founders Dinner -- intimate 20-person dinner for founders "
                 "and early engineers building in climate/energy. Hosted monthly, rotating "
                 "SF venues. This month: Hayes Valley. Space is limited, RSVP required, "
                 "no cost to attend. Great for cross-pollination between climate startups "
                 "and engineers exploring the space.",
        "output": {
            "category": "networking",
            "role_type": None,
            "role_category": None,
            "industry": "climate_energy",
            "seniority": "n/a",
            "engagement_type": None,
            "company_stage": None,
            "location": "San Francisco, CA (Hayes Valley)",
            "deadline": None,
            "spam_risk": "clean",
            "role_expectation_delta": None,
            "role_expectation_notes": None,
            "content_quality": 7.5,
            "confidence": 0.85,
        },
    },
]


def build_system_prompt(today: str) -> str:
    return SYSTEM_PROMPT_TEMPLATE.replace("{today}", today)


def build_examples_block() -> str:
    """The few-shot examples, static across every call regardless of today's
    date or item text -- kept separate from build_system_prompt so callers can
    put system-prompt + examples together in one cache_control-marked content
    block (see providers.py) while only the per-item user message varies."""
    return "\n\n".join(
        f"Example input:\n{ex['input']}\nExample output:\n{ex['output']}"
        for ex in FEW_SHOT_EXAMPLES
    )



# Was 4000 -- cutting 71.6% of the untagged backlog's raw_text (avg ~30% of
# each posting lost, worst case 78-88% on Greenhouse/Indeed/Ashby/LinkedIn).
# 12000 captures 99.2% of postings in full for ~$4.60 extra across the whole
# backlog (checked against real data 2026-07-03, see HISTORY.md#raw-text-truncation-cap).
# Still a cap, not unlimited -- guards against a genuinely pathological scrape.
RAW_TEXT_CHAR_LIMIT = 12000


def build_user_message(raw_text: str) -> str:
    return f"Now tag this item:\n{raw_text[:RAW_TEXT_CHAR_LIMIT]}"
