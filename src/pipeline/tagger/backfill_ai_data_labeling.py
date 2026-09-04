# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: Claude Code
# Prompt: written 2026-07-05 in response to the AI-Trainer-gig ranking
#   derank fix -- see TODO.md section 5b / CHANGELOG.md for the fix this
#   backfill is part of.
# Usage: One-off backfill script, regex-matches already-tagged items whose
#   title/role_type look like AI data-labeling/RLHF-rater contractor gigs
#   and sets role_category='ai_data_labeling' directly via SQL. No LLM call
#   -- these titles are regular enough for a keyword rule to classify with
#   high precision, so a full re-tag isn't needed just for this.
# -------------------------------------------------------------------------

"""Backfills role_category='ai_data_labeling' on already-tagged items whose
title/role_type match AI-Trainer/data-annotation contractor gig patterns.
Run once: python -m pipeline.tagger.backfill_ai_data_labeling
Then re-run python -m pipeline.ranker.rank to apply the new derank weight.
"""
import logging
import re

from pipeline.storage.db import get_connection

logger = logging.getLogger(__name__)

# Matches "AI Trainer", "AI Training Specialist", "AI Training - X", etc.,
# plus generic data-annotation/RLHF-rater titles independent of the "AI"
# prefix (e.g. "Data Annotator", "Data Labeling Analyst").
PATTERN = re.compile(
    r"\bAI\s*Train(?:er|ing)\b|\bData\s*Annotat(?:or|ion)\b|\bData\s*Label(?:ing|er)\b|\bRLHF\b",
    re.IGNORECASE,
)


def find_matches(conn) -> list[dict]:
    rows = conn.execute(
        """SELECT id, title, role_type, role_category FROM items
           WHERE tagged_at IS NOT NULL
             AND (role_category IS NULL OR role_category != 'ai_data_labeling')"""
    ).fetchall()
    return [
        dict(row) for row in rows
        if PATTERN.search(row["title"] or "") or PATTERN.search(row["role_type"] or "")
    ]


def backfill(dry_run: bool = False) -> int:
    conn = get_connection()
    try:
        matches = find_matches(conn)
        if dry_run:
            for m in matches:
                logger.info("Would tag id=%s title=%r role_type=%r (was role_category=%r)",
                            m["id"], m["title"], m["role_type"], m["role_category"])
            return len(matches)
        for m in matches:
            conn.execute(
                "UPDATE items SET role_category = 'ai_data_labeling' WHERE id = ?",
                (m["id"],),
            )
        conn.commit()
        logger.info("Backfilled role_category='ai_data_labeling' for %d items", len(matches))
        return len(matches)
    finally:
        conn.close()


if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    count = backfill(dry_run=args.dry_run)
    print(f"{'Would backfill' if args.dry_run else 'Backfilled'} {count} items.")
