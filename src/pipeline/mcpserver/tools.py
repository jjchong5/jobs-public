"""MCP tool implementations: search_items, rank_items, export_top_n. All
read-only (see db_read.get_read_connection) and all query construction uses
parameterized SQL -- never string-interpolates caller input, even though
values are also validated against known enums before use.
"""
from pipeline.mcpserver.db_read import get_read_connection
from pipeline.mcpserver.schema import PUBLIC_ITEM_FIELDS, VALID_ENUMS
from pipeline.ranker.scores import compute_scores

EXPORT_MAX_N = 50
SEARCH_MAX_LIMIT = 200

_SELECT_COLS = ", ".join(PUBLIC_ITEM_FIELDS)

# Columns compute_scores() actually reads from an item dict (see
# ranker/scores.py) -- fetched alongside the public fields for ranking, but
# never included in what's returned to the caller (content_quality/deadline
# aside, deadline IS public; content_quality is deliberately withheld, see
# schema.py PUBLIC_ITEM_FIELDS comment).
_SCORE_INPUT_COLS = ("content_quality", "deadline", "category", "engagement_type",
                      "seniority", "remote_type", "industry", "company_stage", "role_category")


def _build_filters(filters: dict) -> tuple[str, list]:
    clauses, params = [], []
    for field in ("category", "role_category", "industry", "seniority",
                  "engagement_type", "company_stage", "remote_type", "source"):
        val = filters.get(field)
        if val is None:
            continue
        if field in VALID_ENUMS and val not in VALID_ENUMS[field]:
            continue  # silently ignore invalid enum values rather than erroring the whole query
        clauses.append(f"{field} = ?")
        params.append(val)
    query_text = filters.get("q")
    if query_text:
        clauses.append("(title LIKE ? OR author LIKE ?)")
        like = f"%{query_text}%"
        params.extend([like, like])
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    return where, params


def search_items(filters: dict, limit: int = 50) -> list[dict]:
    limit = min(max(limit, 1), SEARCH_MAX_LIMIT)
    where, params = _build_filters(filters)
    conn = get_read_connection()
    try:
        rows = conn.execute(
            f"SELECT {_SELECT_COLS} FROM items {where} "
            f"ORDER BY (posted_at IS NULL), posted_at DESC LIMIT ?",
            (*params, limit),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def rank_items(filters: dict, weights: dict, limit: int = 50) -> list[dict]:
    limit = min(max(limit, 1), SEARCH_MAX_LIMIT)
    where, params = _build_filters(filters)
    conn = get_read_connection()
    try:
        cols = ", ".join(PUBLIC_ITEM_FIELDS + _SCORE_INPUT_COLS)
        rows = conn.execute(f"SELECT {cols} FROM items {where}", params).fetchall()
    finally:
        conn.close()

    scored = []
    for row in rows:
        item = dict(row)
        scores = compute_scores(item, weights)
        public = {k: item[k] for k in PUBLIC_ITEM_FIELDS}
        public["score"] = scores["preference_score"]
        scored.append(public)
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:limit]


def export_top_n(filters: dict, weights: dict, n: int = EXPORT_MAX_N) -> list[dict]:
    n = min(max(n, 1), EXPORT_MAX_N)  # hard server-side cap, not caller-adjustable past this
    return rank_items(filters, weights, limit=n)
