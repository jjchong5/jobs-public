# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: Claude Code
# Prompt: AI-assisted; automated transcript reconstruction couldn't isolate one triggering message (edits trace probably to the 2026-07-03 ranking-rework conversation documented in HISTORY.md#ranking-rework) -- the real prompt exists verbatim in the raw session transcripts at docs/ai_usage/transcripts/, see docs/ai_usage/prompt_log.md#src-pipeline-ranker-rankpy
# Usage: Ranker entrypoint -- recomputes preference_score/urgency_score/general_score for tagged items using the 5 weight tables from the active preference_profiles row
# -------------------------------------------------------------------------

"""Computes and persists urgency_score/preference_score/general_score for
every tagged item using the active preference profile (see ranker/scores.py
for the formulas). Run as: python -m pipeline.ranker.rank [--limit N] [--sort-by preference_score]
"""
import argparse
import json
import time
from datetime import datetime, timezone

from pipeline.ranker.scores import compute_scores
from pipeline.storage.db import get_connection, record_run

SORT_KEYS = ("urgency_score", "preference_score", "general_score")


def _get_active_profile(conn) -> dict:
    row = conn.execute(
        "SELECT * FROM preference_profiles WHERE is_active = 1 LIMIT 1"
    ).fetchone()
    if row is None:
        raise RuntimeError("No active preference profile found. Run pipeline.storage.db init_db().")
    return {
        "name": row["name"],
        "category_weights": json.loads(row["category_weights"] or "{}"),
        "engagement_weights": json.loads(row["engagement_weights"] or "{}"),
        "seniority_weights": json.loads(row["seniority_weights"] or "{}"),
        "location_weights": json.loads(row["location_weights"] or "{}"),
        "sector_weights": json.loads(row["sector_weights"] or "{}"),
        "stage_weights": json.loads(row["stage_weights"] or "{}"),
        "role_category_weights": json.loads(row["role_category_weights"] or "{}"),
        "role_keywords": json.loads(row["role_keywords"] or "[]"),
        "location_keywords": json.loads(row["location_keywords"] or "[]"),
    }


def rank_items(limit: int | None = None, sort_by: str = "preference_score") -> list[dict]:
    if sort_by not in SORT_KEYS:
        raise ValueError(f"sort_by must be one of {SORT_KEYS}, got {sort_by!r}")

    started = time.monotonic()
    conn = get_connection()
    profile = _get_active_profile(conn)
    rows = conn.execute(
        "SELECT * FROM items WHERE category IS NOT NULL AND category != 'irrelevant'"
    ).fetchall()

    now = datetime.now(timezone.utc).isoformat()
    ranked = []
    for row in rows:
        item = dict(row)
        scores = compute_scores(item, profile)
        item.update(scores)
        conn.execute(
            """UPDATE items SET urgency_score=?, preference_score=?, general_score=?, ranked_at=?
               WHERE id=?""",
            (scores["urgency_score"], scores["preference_score"], scores["general_score"],
             now, item["id"]),
        )
        ranked.append(item)
    conn.commit()
    conn.close()

    ranked.sort(key=lambda i: i[sort_by], reverse=True)

    # No LLM cost at this stage -- just cheap visibility into rank runs over
    # time (item volume, top score, which profile was active).
    record_run(
        stage="rank",
        duration_seconds=round(time.monotonic() - started, 3),
        status="ok",
        metrics={
            "items_ranked": len(ranked),
            "top_scores": {k: ranked[0][k] for k in SORT_KEYS} if ranked else None,
            "profile": profile["name"],
        },
    )
    return ranked[:limit] if limit else ranked


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--sort-by", choices=SORT_KEYS, default="preference_score")
    args = parser.parse_args()
    for item in rank_items(limit=args.limit, sort_by=args.sort_by):
        print(f"{item[args.sort_by]:.2f}  [{item['category']}]  {item['title'] or item['raw_text'][:60]}")
