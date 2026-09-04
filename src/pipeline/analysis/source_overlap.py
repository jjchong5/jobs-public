# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: Claude Code
# Prompt: "oh, did you output your calculated overlaps somewhere for future
#   ref?" (2026-07-03) -- see docs/ai_usage/prompt_log.md#src-pipeline-analysis-source_overlappy
# Usage: Source-overlap analysis module (e.g. linkedin_apify dedup
#   findings) backing docs/SOURCE_OVERLAP.md, re-runnable via
#   python -m pipeline.analysis.source_overlap.
# -------------------------------------------------------------------------

"""Cross-source / within-source job-posting overlap analysis, as documented
in docs/SOURCE_OVERLAP.md. Re-run this whenever the DB has grown a lot and
that doc needs refreshing, rather than re-deriving the queries from scratch.

Matches on the existing `dedup_key` column (normalized "company|title", see
storage/db.py:normalize_dedup_key) -- the only signal that reliably means
"the same job posting"; title-only matching would falsely flag unrelated
companies hiring for the same-sounding role.

Run as: python -m pipeline.analysis.source_overlap
"""
import argparse
from collections import defaultdict

from pipeline.storage.db import get_connection

# No usable `author` (company) field for these -- see docs/SOURCE_OVERLAP.md.
EXCLUDE_NO_COMPANY = {"hn_whoshiring", "weworkremotely"}
EVENT_SOURCES = {"luma_events", "meetup", "eventbrite"}


def per_source_counts(conn) -> list[dict]:
    rows = conn.execute(
        "SELECT source, COUNT(*) c FROM items GROUP BY source ORDER BY c DESC"
    ).fetchall()
    out = []
    for r in rows:
        src, c = r["source"], r["c"]
        dk = conn.execute(
            "SELECT COUNT(*) c FROM items WHERE source=? AND dedup_key IS NOT NULL", (src,)
        ).fetchone()["c"]
        kind = "event" if src in EVENT_SOURCES else "job"
        out.append({"source": src, "count": c, "dedup_key_count": dk, "kind": kind})
    return out


def cross_source_overlap(conn) -> dict[str, dict]:
    """For each source, how many of its distinct dedup_keys also appear under
    a different source (a confident cross-source job-posting match)."""
    rows = conn.execute("SELECT source, dedup_key FROM items WHERE dedup_key IS NOT NULL").fetchall()
    key_to_sources = defaultdict(set)
    src_keys = defaultdict(set)
    for r in rows:
        key_to_sources[r["dedup_key"]].add(r["source"])
        src_keys[r["source"]].add(r["dedup_key"])

    summary = {}
    for src, keys in src_keys.items():
        shared = sum(1 for k in keys if len(key_to_sources[k]) > 1)
        summary[src] = {"shared_keys": shared, "distinct_keys": len(keys)}
    return summary


def pairwise_matrix(conn) -> dict[tuple[str, str], int]:
    """Count of distinct dedup_keys shared between each pair of sources."""
    rows = conn.execute("SELECT source, dedup_key FROM items WHERE dedup_key IS NOT NULL").fetchall()
    key_sources = defaultdict(set)
    for r in rows:
        key_sources[r["dedup_key"]].add(r["source"])

    pair_counts: dict[tuple[str, str], int] = defaultdict(int)
    for srcs in key_sources.values():
        if len(srcs) > 1:
            ordered = sorted(srcs)
            for i in range(len(ordered)):
                for j in range(i + 1, len(ordered)):
                    pair_counts[(ordered[i], ordered[j])] += 1
    return dict(pair_counts)


def within_source_multiplicity(conn) -> dict[str, dict]:
    """Same-source (dedup_key) groups with >1 posting, and what fraction of
    those groups sit at a single location -- a proxy for "true repost" vs.
    "genuinely distinct posting at a different location" (see
    docs/SOURCE_OVERLAP.md's linkedin_apify/indeed_apify comparison)."""
    sources = [r["source"] for r in conn.execute("SELECT DISTINCT source FROM items").fetchall()]
    out = {}
    for src in sources:
        if src in EXCLUDE_NO_COMPANY:
            continue
        total = conn.execute("SELECT COUNT(*) c FROM items WHERE source=?", (src,)).fetchone()["c"]
        dup_rows = conn.execute(
            """SELECT dedup_key, COUNT(*) cnt, COUNT(DISTINCT location) locs
               FROM items WHERE source=? AND dedup_key IS NOT NULL
               GROUP BY dedup_key HAVING cnt > 1""",
            (src,),
        ).fetchall()
        if not dup_rows:
            continue
        groups = len(dup_rows)
        dup_item_rows = sum(r["cnt"] for r in dup_rows)
        single_loc_groups = sum(1 for r in dup_rows if r["locs"] == 1)
        out[src] = {
            "total_items": total,
            "dup_groups": groups,
            "dup_rows": dup_item_rows,
            "single_location_groups": single_loc_groups,
        }
    return out


def print_report() -> None:
    conn = get_connection()
    try:
        counts = per_source_counts(conn)
        total = sum(r["count"] for r in counts)
        print(f"TOTAL ITEMS: {total} across {len(counts)} sources\n")

        overlap = cross_source_overlap(conn)
        print("=== Per-source counts + cross-source job overlap ===")
        for r in counts:
            src, c = r["source"], r["count"]
            if src in EXCLUDE_NO_COMPANY:
                print(f"{src:24s} {c:6d}  {r['kind']:6s}  (no company field, excluded)")
                continue
            o = overlap.get(src, {"shared_keys": 0, "distinct_keys": 0})
            pct = (o["shared_keys"] / o["distinct_keys"] * 100) if o["distinct_keys"] else 0.0
            print(f"{src:24s} {c:6d}  {r['kind']:6s}  "
                  f"cross-source overlap: {o['shared_keys']}/{o['distinct_keys']} ({pct:.1f}%)")

        print("\n=== Pairwise shared-key matrix (>=1 shared key) ===")
        for (a, b), n in sorted(pairwise_matrix(conn).items(), key=lambda x: -x[1]):
            print(f"{a:20s} <-> {b:20s}: {n}")

        print("\n=== Within-source (company+title) multiplicity ===")
        for src, stats in sorted(within_source_multiplicity(conn).items(),
                                  key=lambda x: -x[1]["dup_rows"]):
            pct_of_source = stats["dup_rows"] / stats["total_items"] * 100
            pct_single_loc = stats["single_location_groups"] / stats["dup_groups"] * 100
            print(f"{src:24s} {stats['dup_groups']:4d} dup groups, {stats['dup_rows']:5d} rows "
                  f"({pct_of_source:5.1f}% of source), "
                  f"{stats['single_location_groups']}/{stats['dup_groups']} "
                  f"({pct_single_loc:.0f}%) single-location")
    finally:
        conn.close()


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    print_report()
