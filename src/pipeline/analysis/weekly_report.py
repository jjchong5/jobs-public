# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: Claude Code
# Prompt: "meta-analyze the data ... make this a regular feature (weekly summary)" (2026-07-03) -- see docs/ai_usage/prompt_log.md#src-pipeline-analysis-weekly_reportpy for full text
# Usage: Built the weekly summary report generator (counts per scraper, remote/location breakdowns, etc.) as a recurring analysis feature over tagged pipeline data.
# -------------------------------------------------------------------------

"""Weekly meta-analysis report: what did the pipeline pull in, from where,
tagged how. Covers a rolling window (default 7 days, by tagged_at) with
all-time totals alongside for comparison -- derived fresh from the DB each
run (fetched_at/tagged_at timestamps already exist on every row, so there's
no need for a separately maintained running-tally file).

Run as: python -m pipeline.analysis.weekly_report [--days 7] [--out docs/reports/weekly_2026-07-03.md]
"""
import argparse
import re
from collections import Counter
from datetime import datetime, timedelta, timezone

from pipeline.storage.db import get_connection

# Cheap city-name normalization for the free-text `location` column. Not
# meant to be exhaustive -- just enough to collapse the dominant "San
# Francisco" / "San Francisco, CA" / "San Francisco, CA, USA" variants seen
# in the data (see analysis discussion 2026-07-03) into one bucket. Splits
# multi-location strings ("SF | NYC", "SF, NYC, Seattle") into separate
# counts since those represent multiple real locations for one posting.
_SPLIT_RE = re.compile(r"\s*[|;]\s*|,\s*(?=[A-Z])")
_STATE_SUFFIX_RE = re.compile(
    r",?\s*\b(CA|NY|WA|DC|MA|TX|IL|FL|GA|PA|VA|OR|CO|USA?|US)\b\.?$", re.IGNORECASE
)
_ZIP_RE = re.compile(r"\s*\d{5}(-\d{4})?$")

_CANONICAL = {
    "sf": "San Francisco", "san francisco": "San Francisco",
    "san francisco bay area": "San Francisco", "san francisco, california": "San Francisco",
    "nyc": "New York", "new york city": "New York", "new york": "New York",
    "washington": "Washington, D.C.", "washington dc": "Washington, D.C.",
    "washington, d.c.": "Washington, D.C.",
    "anywhere in the world": "Remote (unspecified)",
    "remote": "Remote (unspecified)", "united states": "United States (unspecified)",
}

# Protect known multi-part place names from the comma-split before it runs.
_PROTECTED = {"washington, d.c.": "Washington, D.C.", "washington, dc": "Washington, D.C."}


def normalize_location(raw: str) -> list[str]:
    """Split a possibly-multi-location free-text field and normalize each part."""
    if not raw or not raw.strip():
        return []
    protected = _PROTECTED.get(raw.strip().lower())
    if protected:
        return [protected]
    parts = [p.strip() for p in _SPLIT_RE.split(raw) if p.strip()]
    out = []
    for p in parts:
        p = _ZIP_RE.sub("", p)
        p = _STATE_SUFFIX_RE.sub("", p).strip().rstrip(",").strip()
        if not p:
            continue
        key = p.lower()
        out.append(_CANONICAL.get(key, p))
    return out


def _since(days: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


def counts_by_source(conn, since: str | None) -> list[tuple[str, int]]:
    if since:
        rows = conn.execute(
            "SELECT source, COUNT(*) c FROM items WHERE fetched_at >= ? GROUP BY source ORDER BY c DESC",
            (since,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT source, COUNT(*) c FROM items GROUP BY source ORDER BY c DESC"
        ).fetchall()
    return [(r["source"], r["c"]) for r in rows]


def counts_by_category(conn, since: str | None) -> list[tuple[str, int]]:
    where = "WHERE tagged_at >= ?" if since else ""
    params = (since,) if since else ()
    rows = conn.execute(
        f"SELECT category, COUNT(*) c FROM items {where} GROUP BY category ORDER BY c DESC",
        params,
    ).fetchall()
    return [(r["category"] or "untagged", r["c"]) for r in rows]


def remote_type_counts(conn, since: str | None) -> list[tuple[str, int]]:
    where = "WHERE tagged_at >= ?" if since else ""
    params = (since,) if since else ()
    rows = conn.execute(
        f"SELECT remote_type, COUNT(*) c FROM items {where} GROUP BY remote_type ORDER BY c DESC",
        params,
    ).fetchall()
    return [(r["remote_type"] or "untagged", r["c"]) for r in rows]


def top_locations(conn, since: str | None, limit: int = 15) -> list[tuple[str, int]]:
    where = "WHERE location IS NOT NULL AND location != ''"
    params: tuple = ()
    if since:
        where += " AND tagged_at >= ?"
        params = (since,)
    rows = conn.execute(f"SELECT location FROM items {where}", params).fetchall()
    counter: Counter = Counter()
    for r in rows:
        for loc in normalize_location(r["location"]):
            counter[loc] += 1
    return counter.most_common(limit)


def spam_risk_counts(conn, since: str | None) -> list[tuple[str, int]]:
    where = "WHERE tagged_at >= ?" if since else ""
    params = (since,) if since else ()
    rows = conn.execute(
        f"SELECT spam_risk, COUNT(*) c FROM items {where} GROUP BY spam_risk ORDER BY c DESC",
        params,
    ).fetchall()
    # null spam_risk on a tagged item means it predates the 2026-07-03
    # ranking-rework schema addition, not that tagging is incomplete --
    # see CLAUDE.md "Known data gaps".
    return [(r["spam_risk"] or "null (pre-rework tag, field didn't exist yet)", r["c"]) for r in rows]


def tagging_progress(conn) -> dict:
    total = conn.execute("SELECT COUNT(*) c FROM items").fetchone()["c"]
    tagged = conn.execute("SELECT COUNT(*) c FROM items WHERE tagged_at IS NOT NULL").fetchone()["c"]
    return {"total": total, "tagged": tagged, "pct": (tagged / total * 100) if total else 0.0}


def _fmt_table(rows: list[tuple[str, int]], col1: str, col2: str = "count") -> str:
    if not rows:
        return "_(none)_\n"
    total = sum(c for _, c in rows)
    lines = [f"| {col1} | {col2} | % |", "|---|---|---|"]
    for name, c in rows:
        pct = (c / total * 100) if total else 0.0
        lines.append(f"| {name} | {c} | {pct:.1f}% |")
    return "\n".join(lines) + "\n"


def build_report(days: int) -> str:
    conn = get_connection()
    try:
        since = _since(days)
        now = datetime.now(timezone.utc)
        progress = tagging_progress(conn)

        week_source = counts_by_source(conn, since)
        all_source = counts_by_source(conn, None)
        week_category = counts_by_category(conn, since)
        week_remote = remote_type_counts(conn, since)
        week_locations = top_locations(conn, since)
        week_spam = spam_risk_counts(conn, since)

        week_total_ingested = sum(c for _, c in week_source)
        week_total_tagged = sum(c for _, c in week_category)
        all_total = sum(c for _, c in all_source)

        lines = [
            f"# Weekly Pipeline Report — {now.date().isoformat()}",
            "",
            f"Window: last {days} days (since {since[:10]}). "
            f"All-time totals shown alongside for comparison.",
            "",
            "## Volume",
            "",
            f"- Ingested this window: **{week_total_ingested}** "
            f"(all-time: {all_total})",
            f"- Tagged this window: **{week_total_tagged}**",
            f"- Overall tagging progress: **{progress['tagged']}/{progress['total']}** "
            f"({progress['pct']:.1f}%)",
            "",
            "## Ingested by source (this window)",
            "",
            _fmt_table(week_source, "source"),
            "## Ingested by source (all-time, for comparison)",
            "",
            _fmt_table(all_source, "source"),
            "## Tagged by category (this window)",
            "",
            _fmt_table(week_category, "category"),
            "## Remote-type breakdown (this window, tagged items)",
            "",
            _fmt_table(week_remote, "remote_type"),
            "## Top locations (this window, normalized, tagged items)",
            "",
            _fmt_table(week_locations, "location"),
            "## Spam/quality signal (this window, tagged items)",
            "",
            _fmt_table(week_spam, "spam_risk"),
        ]
        return "\n".join(lines)
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--out", type=str, default=None,
                         help="Write markdown to this path instead of stdout")
    args = parser.parse_args()

    report = build_report(args.days)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"Wrote {args.out}")
    else:
        import sys
        sys.stdout.buffer.write(report.encode("utf-8"))
        sys.stdout.buffer.write(b"\n")


if __name__ == "__main__":
    main()
