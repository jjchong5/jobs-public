# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: Claude Code
# Prompt: Multi-session build/extension of ingest pipeline (2026-06-24 to 2026-07-03), incl. Apify pipelining request, overnight source-connection goal, and events-DB scoping question -- see docs/ai_usage/prompt_log.md#src-pipeline-ingestpy for full session list
# Usage: Core ingest pipeline built and iteratively extended across 13 sessions as new sources (Apify actors, Greenhouse/Lever/etc.) were wired in and dedup/eventing decisions were made.
# -------------------------------------------------------------------------

"""Normalizes raw scraper output into the `items` table shape and writes it
via the single-writer queue. Dedup happens at the DB layer (UNIQUE(source, url));
this module just needs to map each source's raw fields consistently.
"""
import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

from pipeline.scrapers import aijobs_net, ashby, builtin_sf, dice, eventbrite, greenhouse, handshake_email, hn_whoshiring, indeed_apify_old, indeed_radius, indeed_rss, lever, linkedin_apify, luma_events, meetup, remoteok, vc_portfolio, weworkremotely, wellfound, wellfound_apify_old, wellfound_search_apify, yc_workatastartup
from pipeline.storage.db import WriterQueue, init_db, record_run

logger = logging.getLogger(__name__)


def normalize_hn(raw: dict) -> dict:
    return {
        "source": "hn_whoshiring",
        "source_id": str(raw.get("comment_id")),
        "url": raw["url"],
        "title": None,  # HN comments have no title; tagger derives role_type from raw_text
        "author": raw.get("author"),
        "location": None,
        "raw_text": raw.get("text", ""),
        "posted_at": raw.get("created_at"),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "raw_json": raw,
    }


def normalize_luma(raw: dict) -> dict:
    return {
        "source": "luma_events",
        "source_id": raw["url"].rstrip("/").rsplit("/", 1)[-1],
        "url": raw["url"],
        "title": raw.get("title"),
        "author": None,
        "location": raw.get("location"),
        "raw_text": raw.get("description") or raw.get("title", ""),
        "posted_at": None,
        "start_at": raw.get("start_at"),
        "end_at": raw.get("end_at"),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "raw_json": raw,
    }


def normalize_indeed(raw: dict) -> dict:
    return {
        "source": "indeed_rss",
        "source_id": raw.get("link"),
        "url": raw.get("link"),
        "title": raw.get("title"),
        "author": None,
        "location": None,
        "raw_text": raw.get("summary", ""),
        "posted_at": raw.get("published"),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "raw_json": raw,
    }


def normalize_indeed_apify_old(raw: dict) -> dict:
    extras = ", ".join(filter(None, [", ".join(raw.get("jobType") or []), raw.get("salary")]))
    raw_text = raw.get("description", "")
    if extras:
        raw_text = f"{extras}\n{raw_text}"
    return {
        "source": "indeed_apify_old",
        "source_id": raw.get("id"),
        "url": raw.get("url"),
        "title": raw.get("positionName"),
        "author": raw.get("company"),
        "location": raw.get("location"),
        "raw_text": raw_text,
        "posted_at": raw.get("postingDateParsed"),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "raw_json": raw,
    }


def normalize_indeed_radius(raw: dict) -> dict:
    # memo23/apify-indeed-cheerio-ppr's jobType is a single string (e.g.
    # "Full-time"), not a list like misceres/indeed-scraper's -- extras
    # built accordingly, and raw_text prefers the dedicated description
    # field over jobDescriptionHtml.
    extras = ", ".join(filter(None, [raw.get("jobType"), raw.get("salary")]))
    raw_text = raw.get("jobDescription") or ""
    if extras:
        raw_text = f"{extras}\n{raw_text}"
    return {
        "source": "indeed_radius",
        "source_id": raw.get("jobId") or raw.get("sourceId"),
        "url": raw.get("url") or raw.get("jobUrl"),
        "title": raw.get("positionName"),
        "author": raw.get("company"),
        "location": raw.get("location"),
        "raw_text": raw_text,
        "posted_at": raw.get("datePublished"),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "raw_json": raw,
    }


def normalize_builtin(raw: dict) -> dict:
    extras = ", ".join(
        filter(None, [raw.get("work_type"), raw.get("salary"), raw.get("seniority")])
    )
    raw_text = raw.get("snippet", "")
    if extras:
        raw_text = f"{extras}\n{raw_text}"
    return {
        "source": "builtin_sf",
        "source_id": raw.get("url"),
        "url": raw["url"],
        "title": raw.get("title"),
        "author": raw.get("company"),
        "location": raw.get("location"),
        "raw_text": raw_text,
        "posted_at": None,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "raw_json": raw,
    }


def normalize_wellfound(raw: dict) -> dict:
    return {
        "source": "wellfound",
        "source_id": raw.get("url"),
        "url": raw["url"],
        "title": raw.get("title"),
        "author": raw.get("company"),
        "location": raw.get("location"),
        "raw_text": raw.get("description", ""),
        "posted_at": None,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "raw_json": raw,
    }


def normalize_weworkremotely(raw: dict) -> dict:
    extras = ", ".join(filter(None, [raw.get("region"), raw.get("category")]))
    raw_text = raw.get("summary", "")
    if extras:
        raw_text = f"{extras}\n{raw_text}"
    return {
        "source": "weworkremotely",
        "source_id": raw.get("link"),
        "url": raw.get("link"),
        "title": raw.get("title"),
        "author": None,
        "location": raw.get("region"),
        "raw_text": raw_text,
        "posted_at": raw.get("published"),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "raw_json": raw,
    }


def normalize_handshake(raw: dict) -> dict:
    # Handshake's link is a one-time email-tracking redirect, not a stable
    # per-job URL -- the same job re-sent in a later email gets a different
    # encoded link, so it can't be used for UNIQUE(source, url) dedup. Use a
    # content hash of company+title+work_type instead; the real tracking_url
    # is preserved in raw_json for manual click-through.
    import hashlib

    key = f"{raw.get('company', '')}|{raw.get('title', '')}|{raw.get('work_type', '')}"
    content_hash = hashlib.sha1(key.encode("utf-8")).hexdigest()
    extras = ", ".join(filter(None, [raw.get("pay"), raw.get("work_type")]))
    return {
        "source": "handshake_email",
        "source_id": content_hash,
        "url": f"handshake://{content_hash}",
        "title": raw.get("title"),
        "author": raw.get("company"),
        "location": raw.get("location"),
        "raw_text": extras,
        "posted_at": raw.get("email_sent_at"),  # proxy: when the Handshake alert was sent, not job-posted date
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "raw_json": raw,
    }


def normalize_remoteok(raw: dict) -> dict:
    tags = raw.get("tags") or []
    raw_text = raw.get("description", "")
    if tags:
        raw_text = f"Tags: {', '.join(tags)}\n{raw_text}"
    return {
        "source": "remoteok",
        "source_id": raw.get("url"),
        "url": raw.get("url"),
        "title": raw.get("title"),
        "author": raw.get("company"),
        "location": raw.get("location"),
        "raw_text": raw_text,
        "posted_at": raw.get("posted_at"),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "raw_json": raw,
    }


def normalize_wellfound_apify_old(raw: dict) -> dict:
    extras = ", ".join(filter(None, [raw.get("compensation"), "remote" if raw.get("remote") else None]))
    raw_text = extras
    return {
        "source": "wellfound_apify_old",
        "source_id": raw.get("jobId"),
        "url": raw.get("jobUrl"),
        "title": raw.get("title"),
        "author": raw.get("companyName"),
        "location": ", ".join(raw.get("locations") or []) or None,
        "raw_text": raw_text,
        "posted_at": raw.get("postedAt"),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "raw_json": raw,
    }


def normalize_wellfound_search_apify(raw: dict) -> dict:
    extras = ", ".join(
        filter(
            None,
            [
                raw.get("compensation") or None,
                "remote" if raw.get("remote") else None,
                raw.get("job_type"),
                f"via role search: {raw.get('source_role_slug')}" if raw.get("source_role_slug") else None,
            ],
        )
    )
    raw_text = f"{extras}\n{raw.get('description', '')}" if extras else raw.get("description", "")
    return {
        "source": "wellfound_search",
        "source_id": raw.get("id"),
        "url": raw.get("url"),
        "title": raw.get("title"),
        "author": raw.get("company_name"),
        "location": ", ".join(raw.get("location_names") or []) or None,
        "raw_text": raw_text,
        "posted_at": raw.get("live_start_at"),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "raw_json": raw,
    }


def normalize_greenhouse(raw: dict) -> dict:
    import html

    from bs4 import BeautifulSoup

    content_html = html.unescape(raw.get("content") or "")
    raw_text = BeautifulSoup(content_html, "html.parser").get_text(separator="\n").strip()
    return {
        "source": "greenhouse",
        "source_id": raw.get("url"),
        "url": raw.get("url"),
        "title": raw.get("title"),
        "author": raw.get("company"),
        "location": raw.get("location"),
        "raw_text": raw_text,
        "posted_at": raw.get("updated_at"),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "raw_json": raw,
    }


def normalize_lever(raw: dict) -> dict:
    extras = raw.get("commitment") or ""
    raw_text = raw.get("description", "")
    if extras:
        raw_text = f"{extras}\n{raw_text}"
    return {
        "source": "lever",
        "source_id": raw.get("url"),
        "url": raw.get("url"),
        "title": raw.get("title"),
        "author": raw.get("company"),
        "location": raw.get("location"),
        "raw_text": raw_text,
        "posted_at": raw.get("created_at"),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "raw_json": raw,
    }


def normalize_yc_workatastartup(raw: dict) -> dict:
    extras = ", ".join(filter(None, [raw.get("roleType"), raw.get("jobType"), raw.get("salary")]))
    raw_text = ", ".join(filter(None, [raw.get("companyOneLiner"), extras]))
    return {
        "source": "yc_workatastartup",
        "source_id": str(raw.get("id")),
        "url": f"https://www.workatastartup.com/companies/{raw.get('companySlug')}?jobId={raw.get('id')}",
        "title": raw.get("title"),
        "author": raw.get("companyName"),
        "location": raw.get("location"),
        "raw_text": raw_text,
        "posted_at": None,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "raw_json": raw,
    }


def normalize_dice(raw: dict) -> dict:
    raw_text = raw.get("posted") or ""
    return {
        "source": "dice",
        "source_id": raw.get("url"),
        "url": raw.get("url"),
        "title": raw.get("title"),
        "author": raw.get("company"),
        "location": raw.get("location"),
        "raw_text": raw_text,
        "posted_at": raw.get("posted"),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "raw_json": raw,
    }


def normalize_meetup(raw: dict) -> dict:
    venue = raw.get("venue") or {}
    group = raw.get("group") or {}
    location = ", ".join(filter(None, [venue.get("city"), venue.get("state")])) or None
    return {
        "source": "meetup",
        "source_id": raw.get("id"),
        "url": raw.get("eventUrl"),
        "title": raw.get("title"),
        "author": group.get("name"),
        "location": location,
        "raw_text": raw.get("description") or "",
        "posted_at": None,
        "start_at": raw.get("dateTime"),
        "end_at": raw.get("endTime"),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "raw_json": raw,
    }


def normalize_eventbrite(raw: dict) -> dict:
    venue = raw.get("primary_venue") or {}
    address = venue.get("address") or {}
    location = address.get("localized_area_display") or venue.get("name")
    start_at = None
    if raw.get("start_date"):
        start_at = f"{raw['start_date']}T{raw.get('start_time', '00:00')}:00"
    end_at = None
    if raw.get("end_date"):
        end_at = f"{raw['end_date']}T{raw.get('end_time', '00:00')}:00"
    return {
        "source": "eventbrite",
        "source_id": str(raw.get("id")),
        "url": raw.get("url"),
        "title": raw.get("name"),
        "author": None,
        "location": location,
        "raw_text": raw.get("summary") or "",
        "posted_at": raw.get("published"),
        "start_at": start_at,
        "end_at": end_at,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "raw_json": raw,
    }


def normalize_linkedin_apify(raw: dict) -> dict:
    extras = ", ".join(
        filter(None, [raw.get("seniorityLevel"), raw.get("employmentType")])
    )
    raw_text = raw.get("descriptionText") or raw.get("descriptionHtml") or ""
    if extras:
        raw_text = f"{extras}\n{raw_text}"
    return {
        "source": "linkedin_apify",
        "source_id": raw.get("id") or raw.get("link"),
        "url": raw.get("link") or raw.get("applyUrl"),
        "title": raw.get("title"),
        "author": raw.get("companyName"),
        "location": raw.get("location"),
        "raw_text": raw_text,
        "posted_at": raw.get("postedAt"),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "raw_json": raw,
    }


def normalize_ashby(raw: dict) -> dict:
    import html

    from bs4 import BeautifulSoup

    content_html = html.unescape(raw.get("content") or "")
    raw_text = BeautifulSoup(content_html, "html.parser").get_text(separator="\n").strip()
    extras = ", ".join(filter(None, [raw.get("department"), raw.get("employment_type")]))
    if extras:
        raw_text = f"{extras}\n{raw_text}"
    return {
        "source": "ashby",
        "source_id": raw.get("url"),
        "url": raw.get("url"),
        "title": raw.get("title"),
        "author": raw.get("company"),
        "location": raw.get("location"),
        "raw_text": raw_text,
        "posted_at": raw.get("updated_at"),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "raw_json": raw,
    }


def normalize_vc_portfolio(raw: dict) -> dict:
    salary = raw.get("salary") or {}
    salary_str = None
    if salary.get("minValue") and salary.get("maxValue"):
        salary_str = f"${salary['minValue']}-${salary['maxValue']}/{(salary.get('period') or {}).get('label', 'yr')}"
    extras = ", ".join(
        filter(
            None,
            [
                f"via {raw.get('vc_firm')} portfolio",
                salary_str,
                "remote" if raw.get("remote") else None,
                ", ".join(raw.get("job_functions") or []) or None,
            ],
        )
    )
    return {
        "source": "vc_portfolio",
        "source_id": raw.get("url"),
        "url": raw.get("url"),
        "title": raw.get("title"),
        "author": raw.get("company"),
        "location": raw.get("location"),
        "raw_text": extras,
        "posted_at": raw.get("posted_at"),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "raw_json": raw,
    }


def normalize_aijobs_net(raw: dict) -> dict:
    extras = ", ".join(
        filter(
            None,
            [
                raw.get("salary"),
                raw.get("seniority"),
                raw.get("job_type"),
                "remote" if raw.get("remote") else None,
                ", ".join(raw.get("tags") or []) or None,
            ],
        )
    )
    raw_text = f"{extras}\n{raw.get('description', '')}" if extras else raw.get("description", "")
    return {
        "source": "aijobs_net",
        "source_id": raw.get("url"),
        "url": raw.get("url"),
        "title": raw.get("title"),
        "author": raw.get("company"),
        "location": raw.get("location"),
        "raw_text": raw_text,
        "posted_at": raw.get("posted_ago"),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "raw_json": raw,
    }


NORMALIZERS = {
    "hn_whoshiring": (hn_whoshiring.fetch_raw, normalize_hn),
    "luma_events": (luma_events.fetch_raw, normalize_luma),
    "indeed_rss": (indeed_rss.fetch_raw, normalize_indeed),
    "indeed_apify_old": (indeed_apify_old.fetch_raw, normalize_indeed_apify_old),
    "indeed_radius": (indeed_radius.fetch_raw, normalize_indeed_radius),
    "builtin_sf": (builtin_sf.fetch_raw, normalize_builtin),
    "wellfound": (wellfound.fetch_raw, normalize_wellfound),
    "handshake_email": (handshake_email.fetch_raw, normalize_handshake),
    "weworkremotely": (weworkremotely.fetch_raw, normalize_weworkremotely),
    "remoteok": (remoteok.fetch_raw, normalize_remoteok),
    "linkedin_apify": (linkedin_apify.fetch_raw, normalize_linkedin_apify),
    "wellfound_apify_old": (wellfound_apify_old.fetch_raw, normalize_wellfound_apify_old),
    "wellfound_search": (wellfound_search_apify.fetch_raw, normalize_wellfound_search_apify),
    "greenhouse": (greenhouse.fetch_raw, normalize_greenhouse),
    "lever": (lever.fetch_raw, normalize_lever),
    "yc_workatastartup": (yc_workatastartup.fetch_raw, normalize_yc_workatastartup),
    "dice": (dice.fetch_raw, normalize_dice),
    "meetup": (meetup.fetch_raw, normalize_meetup),
    "eventbrite": (eventbrite.fetch_raw, normalize_eventbrite),
    "ashby": (ashby.fetch_raw, normalize_ashby),
    "vc_portfolio": (vc_portfolio.fetch_raw, normalize_vc_portfolio),
    "aijobs_net": (aijobs_net.fetch_raw, normalize_aijobs_net),
}


# Event sources frozen 2026-07-02: author's priority is the job tracker, and
# events (Luma/Meetup/Eventbrite) belong in a calendar tool, not this DB, per
# author decision. Left in NORMALIZERS (not deleted) so this is reversible --
# pass sources=[...] explicitly to re-enable one.
#
# wellfound_apify_old (renamed 2026-07-03 from wellfound_apify) frozen the same
# day: superseded by wellfound_search (real per-role search, 84% relevance>=5)
# after live-tagging showed the old flat /jobs feed only hits 14% relevance>=5
# -- see docs/SOURCES.md. Same reversible mothball pattern, not a deletion.
#
# indeed_apify_old (renamed 2026-07-03 from indeed_apify) frozen the same day:
# superseded by indeed_radius, which is ~4x cheaper and has a native radius
# param closing a real coverage gap (SF vs San Jose searches were ~92%
# non-overlapping without one). Not frozen for being broken, unlike the other
# two above -- kept live in the codebase specifically as a fallback in case
# indeed_radius's actor (which authenticates via harvested third-party mobile
# session tokens, not its own dedicated login) gets its token pool blocked.
# See indeed_radius.py and indeed_apify_old.py docstrings for the full tradeoff.
FROZEN_SOURCES = {"luma_events", "meetup", "eventbrite", "wellfound_apify_old", "indeed_apify_old"}


async def run_ingest(sources: list[str] | None = None) -> dict:
    """Fetch raw items from the given sources (default: all non-frozen), normalize,
    and write them through the single-writer queue. Returns {inserted, skipped}.

    Logs one run_log row per source (stage="ingest") with fetched/inserted/skipped
    counts and fetch duration -- this is cheap metadata already known at this
    stage (no LLM cost), so it's recorded here rather than waiting on tagging."""
    init_db()
    queue = WriterQueue()
    await queue.start()

    sources = sources or [s for s in NORMALIZERS if s not in FROZEN_SOURCES]
    fetched_counts: dict[str, int] = {}
    fetch_durations: dict[str, float] = {}
    fetch_errors: dict[str, str] = {}

    async def _fetch_and_queue(source: str) -> None:
        fetch_fn, normalize_fn = NORMALIZERS[source]
        start = time.monotonic()
        try:
            # Run in a thread: scrapers use blocking I/O (requests, sync
            # Playwright), and sync Playwright cannot run inside a running
            # asyncio event loop on the main thread.
            raw_items = await asyncio.to_thread(fetch_fn)
        except Exception as exc:
            fetch_durations[source] = time.monotonic() - start
            fetch_errors[source] = str(exc)
            logger.exception("Fetch failed for source=%s", source)
            return
        fetch_durations[source] = time.monotonic() - start
        fetched_counts[source] = len(raw_items)
        for raw in raw_items:
            try:
                item = normalize_fn(raw)
                await queue.put(item)
            except Exception:
                logger.exception("Normalize failed for source=%s item=%r", source, raw)

    # Sources are independent (own fetch/normalize, own dict entries above),
    # and WriterQueue is built for concurrent producers -- run every source's
    # fetch concurrently instead of waiting on each one in turn, so overall
    # time is bounded by the slowest single source rather than their sum.
    await asyncio.gather(*(_fetch_and_queue(source) for source in sources))

    await queue.stop()

    for source in sources:
        record_run(
            stage="ingest",
            source=source,
            duration_seconds=round(fetch_durations.get(source, 0.0), 3),
            status="error" if source in fetch_errors else "ok",
            error=fetch_errors.get(source),
            metrics={
                "fetched": fetched_counts.get(source, 0),
                "inserted": queue.inserted_by_source.get(source, 0),
                "skipped": queue.skipped_by_source.get(source, 0),
            },
        )

    logger.info("Ingest complete: inserted=%d skipped=%d", queue.inserted, queue.skipped)
    return {"inserted": queue.inserted, "skipped": queue.skipped}


async def ingest_raw_file(source: str, path: str | Path) -> dict:
    """Normalize and write raw items already saved on disk (e.g. by
    `write_raw_output`) without calling that source's live `fetch_fn`.

    Use this for backfilling/re-processing a paid Apify pull (or any other
    scrape) you already have -- calling `run_ingest(sources=[...])` always
    re-invokes the live fetch with that source's *default* params, which can
    silently trigger an unwanted second paid run instead of reusing the file
    you meant to ingest.
    """
    init_db()
    _, normalize_fn = NORMALIZERS[source]

    with open(path, encoding="utf-8") as f:
        raw_items = json.load(f)

    queue = WriterQueue()
    await queue.start()
    for raw in raw_items:
        try:
            item = normalize_fn(raw)
            await queue.put(item)
        except Exception:
            logger.exception("Normalize failed for source=%s item=%r", source, raw)
    await queue.stop()

    record_run(
        stage="ingest",
        source=source,
        duration_seconds=0.0,
        status="ok",
        error=None,
        metrics={
            "fetched": len(raw_items),
            "inserted": queue.inserted_by_source.get(source, 0),
            "skipped": queue.skipped_by_source.get(source, 0),
        },
    )
    logger.info("Ingest from file complete: source=%s inserted=%d skipped=%d",
                source, queue.inserted, queue.skipped)
    return {"fetched": len(raw_items), "inserted": queue.inserted, "skipped": queue.skipped}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = asyncio.run(run_ingest())
    print(result)
