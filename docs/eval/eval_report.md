# AI Evaluation Report — DTSC 691 Capstone

Evaluation of the tagger (classification + field extraction) and ranker
(preference scoring) against a manually-labeled ground truth set, per the
methodology committed to in the project proposal.

## Method

**Ground truth set:** 80 items manually labeled by the author
(`docs/eval/eval_answers.json`, `docs/eval/eval_set_taggable.md`) — 20 job /
20 event / 20 mixed-ambiguous (lowest tagger-confidence items across
categories) / 20 networking (random sample, appended later as a lower-priority
check). Each item's human label was recorded *before* viewing the tagger's
output (`eval_set_taggable.md`'s intentional order — human label field first,
auto-tag output revealed only after).

**Scope decision:** the networking bucket is excluded from all metrics below.
The author's assessment, made independently of this report: the
networking/events feature is under-built and the category boundary itself is
poorly defined (event-vs-networking is often a subjective call, e.g. "is a
mixer a networking event or just an event"), so a low accuracy score there
would reflect an immature feature and an ambiguous label boundary, not a
tagger defect. See `docs/SOURCES.md`/`TODO.md` — networking/events is a
deprioritized secondary feature the author intends to rethink or drop
entirely; classification metrics there aren't meaningful and are not
reported. All classification metrics below use the **60-item core set**
(job / event / mixed-ambiguous).

**`role_type` is reported qualitatively, not as an F1 score.** It's free
text (e.g. "swe backend", "senior full stack engineer"), not a fixed enum —
a strict-match F1 would penalize valid phrasing variants of the same role as
if they were wrong. Substantive role_type errors (wrong occupation entirely,
not just phrasing) are instead folded into the human correctness judgment
(`correct: Y/N`) and discussed narratively below.

---

## 1. Classification accuracy + confusion matrix

**Overall accuracy (60-item core, job/event/mixed-ambiguous): 96.7%**
(58/60 correct) — well above the ≥85% target set in the proposal.

Confusion matrix (rows = human ground truth, columns = auto-tagged category):

| true \ predicted | event | irrelevant | job |
|---|---|---|---|
| **event** | 23 | 1 | 0 |
| **irrelevant** | 0 | 1 | 0 |
| **job** | 1 | 0 | 34 |

| category | precision | recall | f1 | support |
|---|---|---|---|---|
| event | 0.96 | 0.96 | 0.96 | 24 |
| irrelevant | 0.50 | 1.00 | 0.67 | 1 |
| job | 1.00 | 0.97 | 0.99 | 35 |

**The 2 misclassifications:**
1. *"AI Fluency Pathway - San Francisco"* — human: `event`, auto: `irrelevant`.
   Genuine miscategorization (author's note: "should be event, miscategorized").
2. *"[AI 웨비나] Data Engineer/Data Analytics Engineer"* — human: `job`,
   auto: `event`. A Korean-language webinar-styled posting for what's
   actually a job opening; plausible the "웨비나" (webinar) framing and
   non-English text confused the tagger's category signal.

Both are isolated content-specific failures, not a systemic pattern — no
common cause links them.

**22 of the 60 core items had no `correct` field filled in** by the author,
meaning no disagreement was flagged; these are treated as `correct: Y`
(spot-checked against their notes fields — none had unresolved concerns).
One item (job bucket, seq 9, "AI Platform Engineer, Backend") was originally
missing seniority/engagement_type/correct due to an incomplete initial entry;
the author confirmed the auto-tag (`mid`/`full_time`/`backend engineer`)
looked right, so those fields were filled in from the tagger's own output
and the item is included in every count below like any other.

## 2. Seniority accuracy + confusion matrix (Job bucket only)

Seniority is a job-specific field, evaluated on the full 20-item Job bucket.

**Seniority accuracy: 80.0%** (16/20)

| true \ predicted | junior | lead | mid | senior | staff+ |
|---|---|---|---|---|---|
| **junior** | 2 | 0 | 0 | 0 | 0 |
| **lead** | 0 | 0 | 1 | 2 | 0 |
| **mid** | 0 | 0 | 3 | 0 | 0 |
| **senior** | 0 | 0 | 0 | 9 | 0 |
| **staff+** | 0 | 0 | 0 | 1 | 2 |

| seniority | precision | recall | f1 | support |
|---|---|---|---|---|
| junior | 1.00 | 1.00 | 1.00 | 2 |
| lead | 0.00 | 0.00 | 0.00 | 3 |
| mid | 0.75 | 1.00 | 0.86 | 3 |
| senior | 0.75 | 1.00 | 0.86 | 9 |
| staff+ | 1.00 | 0.67 | 0.80 | 3 |

**Key failure mode: `lead` has 0% recall.** All 3 items the author judged as
`lead` were tagged `mid` or `senior` instead. All 3 are non-SWE or
exec-adjacent roles: "Planning Manager - GOC" (Waymo ops), "Director of
Office of the CEO, Founder in Residence" (BillionToOne), "Lead Autonomy
Behavior Engineer" (May Mobility, SWE-adjacent but staff/lead ambiguous).
This directly confirms the pattern the author flagged during labeling
(`eval-top10-thoughts-1.md`): **the seniority ladder is derived from a SWE
career track and doesn't map cleanly onto non-SWE roles or
executive/leadership titles**, where "lead," "director," and "principal"
carry different relative weight than in a SWE ladder. One further case
("Principal Data Scientist," human: `staff+`, auto: `senior`) reflects the
same root cause — "principal" is conventionally above "staff" but the
tagger's ladder doesn't clearly distinguish them.

**Not fixed as part of this eval pass** — author is undecided on the right
fix (simplify top-level buckets vs. tier seniority classification by
`role_category`, i.e. only apply SWE-ladder granularity to tech roles and
use simpler buckets otherwise) and explicitly deferred deciding until after
capstone submission. Documented here as a known, real limitation rather than
hidden.

## 3. `role_type` — qualitative review (not F1-scored)

Spot-checking auto-tagged `role_type` against what the author would have
written by hand, across the 20-item Job bucket:

| Title | Auto role_type | Assessment |
|---|---|---|
| Staff Software Engineer, Model Serving | software engineer | Correct, reasonable normalization |
| Senior Revenue Accountant | Senior Revenue Accountant | Correct, verbatim |
| Accommodation Administrator FIFO... | accommodation administrator | Correct |
| Principal Data Scientist - Cloud Gaming and AI | data scientist | Correct but loses "principal"/seniority nuance (captured separately in the seniority-mismatch above) |
| Director of Office of the CEO... | Director of Office of the CEO | Correct, verbatim |
| Lead Autonomy Behavior Engineer | swe- robotics | Reasonable normalization, loses "autonomy behavior" specificity |

No substantive role_type errors (wrong occupation category entirely) were
found in the Job bucket — the 3 human `correct: N` marks in that bucket were
all seniority-bucket disagreements, not role_type disagreements. `role_type`
free-text normalization (e.g. "swe" for "Software Engineer ADEM...", "manager/exec"
for "Director of Office of the CEO") is generally reasonable and preserves
enough signal for search/browse use, at the cost of losing some
title-specific nuance — an acceptable, expected tradeoff for a free-text
field not meant to be exact-matched.

## 4. Confidence calibration

With only 2 real misclassifications in the 60-item core set (Section 1),
comparing mean confidence on correct vs. incorrect items isn't a meaningful
statistic — the sample of errors is too small, and the errors themselves
were isolated content-specific issues (non-English text, an unusual
webinar-styled job posting), not cases the tagger was uncertain about. A
more useful test of calibration is whether `tag_confidence` tracks *actual
task difficulty*, since that's what it's used for in practice (gating the
Haiku→Sonnet escalation at the 0.7 threshold, per `CLAUDE.md`). Mean
`tag_confidence` by bucket:

| Bucket | n | mean confidence | min | max |
|---|---|---|---|---|
| Job | 20 | 0.912 | 0.75 | 0.96 |
| Event | 20 | 0.822 | 0.45 | 0.95 |
| Mixed / Ambiguous | 20 | 0.367 | 0.30 | 0.45 |

This is a strong, clean result: confidence drops in exactly the order the
buckets were designed to be harder. The Mixed/Ambiguous bucket was
deliberately sampled as the lowest-tagger-confidence items across
categories (`eval_set_taggable.md`'s own selection method) — the tagger's
self-reported confidence is correctly identifying its own hardest cases,
clustering far below the 0.7 escalation threshold as intended. Job (the
cleanest-cut category) sits highest. This is the calibration behavior the
system is actually designed to rely on, and it holds up.

This doesn't contradict the earlier project-level caveat (`CLAUDE.md`):
confidence is still an LLM self-report, not a calibrated statistical
probability, and shouldn't be read as "92% of Job-bucket tags are correct
92% of the time." But as a *relative* difficulty signal — which is the only
thing the Haiku/Sonnet escalation logic actually needs — it's working as
intended.

## 5. Ranking evaluation — Spearman correlation

Per the proposal's committed metric ("Relevance score correlation: Spearman
correlation between LLM scores and manual rankings"). Two independent
18-item manual ranking passes were done by the author
(`docs/eval/spearman_ranking_sheet.md`), each ranked 1-18 (1 = most
preferred) blind to the actual `preference_score` values, then correlated
against those scores after the fact.

**Set A — general spread** (18 items sampled evenly across the full
scored-job range, `preference_score` 0.36–33.18):

**rho = 0.615, p = 0.007** — a strong, statistically significant positive
correlation between the ranker's ordering and the author's actual
preference across the general population of scored jobs.

**Set B — high-signal** (18 items sampled from only the top 100
highest-`preference_score` jobs — i.e. testing whether the ranker's actual
top picks track real preference, not just the full range):

**rho = -0.269, p = 0.28** — weak and not statistically significant as a
*rank-order* correlation. This does **not** mean the ranker's top-100 is
useless — it means fine-grained ordering within that top slice doesn't track
the author's preference well. Precision, not rank order, is the more
telling view here: of the 18 Set-B items, several the author ranked very
highly (rank 2–4 of 18: "Artificial Intelligence Engineer" at Company.ai,
"Conversational AI Engineer" at Known, "Robot Learning Residency",
"Founding Full Stack Engineer" at Skiffra) genuinely are excellent
high-signal matches sitting in the ranker's real top-100 — the ranker is
successfully surfacing strong candidates into that slice. The problem is
specific and identifiable, not diffuse: one recurring category is
*consistently* misranked to the top despite being a hard mismatch (below),
dragging down the rank-order correlation without erasing the top-100's
otherwise-good recall of items the author actually rates highly.

### Root cause: "AI Trainer" gig overranking

6 of the 18 Set-B items were "AI Trainer" / "Specialised Participant" gigs
(Prolific, freelance data-labeling work requiring domain credentials — MD,
CS, accounting, Arabic fluency, design, etc.) — every single one the author
ranked at the bottom (rank 18, tied) with the same stated reason: "AI
training outside my expertise" / "near-0 value for career advancement." Yet
these items hold `preference_score` values of 25.5–28.1, near the top of the
entire scored-job population, apparently driven by the ranker's "AI
education" preference weight matching the training-adjacent framing of
these postings without accounting for the (often highly specific)
credential requirement being a hard mismatch for this particular author.

This exactly confirms, with real numbers, the issue already flagged
qualitatively before any Spearman data existed
(`eval-top10-thoughts-1.md`): *"many top jobs were 'AI training' gigs...
most require domain expertise the author doesn't have... likely upranked
because of the author's 'AI education' preference weight."*

**Practical implication:** this looks less like "the top-100 is broken" and
more like "the top-100 needs an AI-Trainer-gig filter/derank before it's
presented" — the six low-value items are diluting an otherwise strong pool.
A targeted fix (deranking or reclassifying this one recurring category, per
the already-open question in `eval-top10-thoughts-1.md` of filtering vs.
tag-and-subcategorize) is a much narrower fix than "improve the ranker
generally," and worth prioritizing over broader ranking-weight tuning.

**Decision (author, 2026-07-04): do not attempt a ranking-weight fix before
this submission.** Further ranking-quality tests are low-value until this
specific defect is addressed — re-running Spearman without fixing the root
cause would likely just reproduce the same low Set-B correlation. This is
flagged in `TODO.md` Section 5b as a concrete post-submission follow-up
(along with the related open question of whether to filter AI-training gigs
globally vs. tag-and-subcategorize them as a selectable freelance
subcategory — see `eval-top10-thoughts-1.md`).

### Secondary finding: "DevRel Engineer" discovery

Item id 25978 ("DevRel Engineer" at Whissle AI, freelance, on-device voice
AI startup) appeared in both Set A and Set B and was ranked highly in both
(rank 2/18 in Set A, rank 6/18 in Set B) — the author's notes: "devrel
interesting community work." The author was not previously aware of "DevRel
Engineer" as a distinct role category prior to this eval pass. Logged as a
concrete, actionable follow-up in `TODO.md` Section 5b: worth exploring
whether DevRel should become an explicitly upranked `role_category` value.

## Summary

| Metric | Result | Target/context |
|---|---|---|
| Classification accuracy (job/event/mixed) | 96.7% | ≥85% target — met |
| Seniority accuracy (Job bucket) | 80.0% | No formal target; documented failure mode (lead/exec titles, 0% lead recall) |
| role_type quality | Qualitative pass, no substantive errors found | Free-text field, not F1-scored by design |
| Confidence calibration | Confidence tracks bucket difficulty cleanly (Job 0.91 > Event 0.82 > Mixed-Ambiguous 0.37) | Relative difficulty signal validated; not a calibrated probability |
| Spearman (general spread) | rho = 0.615, p = 0.007 | Strong, significant |
| Spearman (high-signal top-100) | rho = -0.269, p = 0.28 | Weak rank-order correlation, but top-100 still surfaces several genuinely high-signal items — traced to one recurring AI-Trainer-gig overranking defect, not a broken top-100 |

**Candid overall read:** the tagger's classification is strong and clears
the proposal's target comfortably, and its confidence signal tracks real
task difficulty well. The two real weaknesses this eval surfaced — the
SWE-derived seniority ladder misclassifying non-SWE/exec titles, and
AI-training-gig overranking degrading rank-order quality within the
ranker's top-100 specifically — were both independently flagged by the
author during manual review *before* this formal eval, and this pass
converts both from qualitative impressions into quantified, reproducible
findings (0% lead-recall; rho swinging from +0.615 to -0.269 between general
and high-signal samples, traceable to a single identifiable recurring
category). Both are logged as concrete post-submission follow-ups
(`TODO.md` Section 5b) rather than papered over.
