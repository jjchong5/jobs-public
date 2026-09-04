# Manual ranking eval — top 10, batch 1 (2026-07-04)

Manual review of the top-10 preference-ranked jobs from the first batch.
Raw notes from the author, captured verbatim (lightly organized) — **nothing
in this doc has been built yet**, this is eval feedback only.

## Performance

0. **Load time** — DB is now ~20k items, UI feels slow. Probably needs
   batch-loading rather than loading everything at once.

## Ranking / relevance issues

1. Top 2 preference-ranked jobs (and several others) require a degree
   (psych) or specific experience ("formal design education") the author
   doesn't have. Similarly the DevSecOps job ranked high but requires
   TypeScript fluency the author doesn't have. In general: highly specific
   hard requirements the author doesn't meet make a listing much less
   pertinent, and current scoring doesn't capture this. Proposed fix:
   weights (probably) or a filter to derank these — weights preferred over
   a hard filter.

   a. Related: many top jobs were "AI training" gigs (temp jobs encoding
      human domain expertise into AI/LLM training data) — likely
      upranked because of the author's "AI education" preference weight.
      But most of these require domain expertise (e.g. specific
      professional/academic backgrounds) the author doesn't have, so most
      are irrelevant to him personally — he only wants ones relevant to
      his own domains upranked. Open question: filter at the tagger level
      or a pre-tagger filter? Author is undecided whether to derank these
      globally. Ideally: tag them, and let the UI surface them as a
      selectable freelance subcategory instead of folding them into main
      ranking. **-> post-submission TODO.**

   b. A few top jobs were the same underlying job posted at different
      locations (duplicate/near-duplicate grouping). Affects a small
      enough percentage of results that no fix is needed yet.

## Feedback buttons (thumbs up/down)

2. What does the like/dislike button currently do, if anything? Author can
   imagine using it to fine-tune preferences/weights automatically, but
   isn't sure he wants that complexity yet. If a feedback-driven
   fine-tuner is built later, he'd want it more sophisticated than a
   simple thumbs signal — something closer to logging actual issues per
   item (like this eval doc). Implementation to be brainstormed later, not
   now.

## Applicant count / posting age

3. LinkedIn job pages show number of applicants — could be useful for
   filtering toward less-competitive listings, ideally compared against
   how long the job has been posted (another field worth extracting from
   LinkedIn scrapes, at least). **-> TODO** (both the applicant-count
   signal and posting-age extraction).

## Other UI feedback

- Author may eventually want a full UI redesign for better space usage and
  visual polish — not now.
- The "events/networking" tab is currently pointless. Open question: is
  this functionality actually committed to in the capstone rubric? If not,
  hide the tab for now.
- The "digest" view is clunky / feels vibe-coded. Author will need to
  rethink whether to ditch or substantially modify it.
- Biggest real UI priority going forward is **workflow**: ability to hide
  jobs already seen/dismissed (ideally capturing feedback to assist future
  ranking), and a way to tag/track jobs already applied to.

## 20/20/20 ground-truth eval — classification failure notes

(Feedback from the labeled eval set, flagged for the future, not acted on
yet.)

- **Networking/events bucket** is poorly defined and a source of
  misclassification. Author intends to jettison/rethink the whole
  networking/events feature regardless, so this is lower priority, but
  flagging for when that happens.
- **Seniority buckets** are clearly derived from a SWE career ladder and
  don't map well onto non-SWE jobs, especially at higher levels. Some
  misclassification also happened on SWE-adjacent exec/exec-adjacent
  levels. Author isn't sure yet how to fix this while preserving useful
  sorting for jobs he'd actually apply to — possible direction is
  simplifying the top-level buckets, but undecided.
