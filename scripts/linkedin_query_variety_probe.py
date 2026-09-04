"""One-off probe: does varying LinkedIn search terms/locations multiply real
volume beyond the ~170-per-search-term plateau found for the single default
query, or do different queries mostly return the same underlying postings?

Not part of the pipeline -- ad hoc script, run manually, prints a report.
Writes each run's raw items to data/raw/probes/linkedin_variety/ for inspection.
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dotenv import load_dotenv
load_dotenv()

from apify_client import ApifyClient

ACTOR_ID = "curious_coder/linkedin-jobs-scraper"
MAX_ITEMS = 200

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = PROJECT_ROOT / "data" / "raw" / "probes" / "linkedin_variety"

QUERIES = {
    "sf_ds_ml_ai": (
        "https://www.linkedin.com/jobs/search/"
        "?keywords=data%20scientist%20OR%20machine%20learning%20OR%20artificial%20intelligence"
        "&location=San%20Francisco%20Bay%20Area"
    ),
    "sf_ai_engineer": (
        "https://www.linkedin.com/jobs/search/"
        "?keywords=AI%20engineer%20OR%20ML%20engineer%20OR%20applied%20scientist"
        "&location=San%20Francisco%20Bay%20Area"
    ),
    "remote_ds_ml_ai": (
        "https://www.linkedin.com/jobs/search/"
        "?keywords=data%20scientist%20OR%20machine%20learning%20OR%20artificial%20intelligence"
        "&location=United%20States&f_WT=2"
    ),
    "sf_freelance_contract": (
        "https://www.linkedin.com/jobs/search/"
        "?keywords=machine%20learning%20OR%20AI%20contract%20OR%20freelance"
        "&location=San%20Francisco%20Bay%20Area"
    ),
}


def run_query(name: str, url: str) -> list[dict]:
    token = os.environ["APIFY_API_TOKEN"]
    client = ApifyClient(token)
    print(f"[{name}] running actor against {url} (max_items={MAX_ITEMS}) ...")
    run = client.actor(ACTOR_ID).call(run_input={"urls": [url], "count": MAX_ITEMS})
    run = run.model_dump() if hasattr(run, "model_dump") else dict(run)
    dataset_id = run["default_dataset_id"]
    items = list(client.dataset(dataset_id).iterate_items())
    cost = run.get("usage_total_usd")
    print(f"[{name}] fetched {len(items)} items, cost_usd={cost}")
    return items


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results: dict[str, list[dict]] = {}

    for name, url in QUERIES.items():
        items = run_query(name, url)
        results[name] = items
        with open(OUT_DIR / f"{name}.json", "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2, ensure_ascii=False)

    print("\n=== Overlap report ===")
    id_sets = {}
    for name, items in results.items():
        ids = {it.get("id") or it.get("link") for it in items}
        id_sets[name] = ids
        print(f"{name}: {len(items)} items, {len(ids)} unique ids")

    all_ids = set()
    for ids in id_sets.values():
        all_ids |= ids
    print(f"\nUnion across all queries: {len(all_ids)} unique job ids")

    names = list(id_sets.keys())
    print("\nPairwise overlap (Jaccard):")
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = id_sets[names[i]], id_sets[names[j]]
            inter = len(a & b)
            union = len(a | b) or 1
            print(f"  {names[i]} vs {names[j]}: {inter} shared / {union} union = {inter/union:.1%}")


if __name__ == "__main__":
    main()
