# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: Claude Code
# Prompt: "build a scheduler ... best-guess calibrations ... add the todo to calibrate it later" (2026-07-03), later retimed to run overnight ~3:30-4am -- see docs/ai_usage/prompt_log.md#src-pipeline-schedulerpy for full session list
# Usage: APScheduler-based per-source scheduling module built from scratch, later adjusted for overnight run timing across a handful of follow-up sessions.
# -------------------------------------------------------------------------

"""APScheduler wiring for recurring ingest -> tag -> rank runs.

Every source polls daily as a deliberate 2-week calibration trial (see
DAILY_TRIAL_END below) -- not a final per-source cadence. See TODO.md 3b
"Calibrate real per-source cadence" for the follow-up analysis plan.

All source jobs fire once daily at a fixed wall-clock time (RUN_HOUR/RUN_MINUTE
below, default 3:30am local) rather than "every 24h from process start" --
author is awake until 2-3am and wants polls to land overnight while asleep.

Runs as a persistent background process on the Mac mini (always-on, unlike
the Windows machine which sleeps) -- see scripts/run_scheduler.bat launched
via launchd/cron on the Mini, moved there 2026-08-26 specifically so this
process doesn't depend on a machine being awake at 3:30am. The original
Windows Task Scheduler path (scripts/register_scheduler_task.ps1) is kept
but unused; see TODO.md 3b for the registration steps if ever needed again.

Run as: python -m pipeline.scheduler
"""
import asyncio
import datetime
import logging
import time

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from pipeline.ingest import FROZEN_SOURCES, NORMALIZERS, run_ingest
from pipeline.notifications.notifier import notify_run_summary
from pipeline.ranker.rank import rank_items
from pipeline.scrapers.raw_writer import purge_old_history
from pipeline.tagger.run_tagging import run as run_tagging

logger = logging.getLogger(__name__)

# Daily cadence for every source is a deliberate 2-week trial (started when
# this was moved to the always-on Mac mini), not a permanent decision -- see
# TODO.md 3b "Calibrate real per-source cadence". After DAILY_TRIAL_END, pull
# run_log (stage='ingest') per source and simulate keeping only every-Nth run
# to see how many real inserts a weekly/biweekly cadence would have missed,
# then set real per-source SOURCE_INTERVAL_HOURS values from that instead of
# guessing. This constant doesn't stop the scheduler -- it only makes the
# still-daily cadence loudly visible past the trial window so it isn't
# forgotten silently.
DAILY_TRIAL_END = datetime.date(2026, 9, 9)

# Fixed nightly run time -- author is often up past 2-3am, so 3:30am is picked
# to land after they're likely asleep rather than mid-session.
RUN_HOUR = 3
RUN_MINUTE = 30

# Best-guess poll cadence per source, in hours. Default (24h) applies to any
# source not listed here. Deliberately capped at once/day for every source as
# a starting point -- bump individual sources lower only if calibration data
# (see TODO.md) shows real postings are being missed between polls.
#
# hn_whoshiring is a monthly-thread source (comments trickle onto one thread
# for ~a month, a new thread appears monthly) -- polling it daily just re-reads
# the same thread's comment trickle, which is fine/cheap and keeps this table
# simple, but it will never need to go *below* 24h the way a live board might.
SOURCE_INTERVAL_HOURS: dict[str, float] = {
    # Paid (Apify pay-per-result) -- once/day caps spend; verify against
    # calibration data before going lower.
    "indeed_apify_old": 24,
    "indeed_radius": 24,
    "linkedin_apify": 24,
    "wellfound_apify_old": 24,
    "wellfound_search": 24,
    # Free, full-board re-pulls (every poll re-fetches the whole board
    # regardless of cadence; dedup makes extra polls harmless but wasteful).
    "greenhouse": 24,
    "ashby": 24,
    "lever": 24,
    "vc_portfolio": 24,
    # Free, direct scrapes.
    "remoteok": 24,
    "weworkremotely": 24,
    "aijobs_net": 24,
    "dice": 24,
    "builtin_sf": 24,
    "yc_workatastartup": 24,
    "handshake_email": 24,
    # HN "Who's Hiring" -- thread-based, not a live board; monthly cadence is
    # the meaningful unit, but daily polling is cheap and harmless here too.
    "hn_whoshiring": 24,
}

DEFAULT_INTERVAL_HOURS = 24.0

# Confirmed dead/superseded sources (see docs/SOURCES.md "Built, hard-blocked"
# table) -- kept in NORMALIZERS for the record and manual re-enable, but
# scheduling them daily is pure noise since fetch_raw() always returns [].
# indeed_rss: Indeed retired public RSS (superseded by indeed_apify_old, itself
# renamed+frozen 2026-07-03 and now superseded by indeed_radius).
# wellfound: direct scrape hard-blocked by DataDome (superseded by wellfound_apify_old,
# itself renamed+frozen 2026-07-03 and now superseded by wellfound_search).
DEAD_SOURCES = {"indeed_rss", "wellfound"}

# Frozen event sources (luma_events, meetup, eventbrite) are excluded from the
# schedule the same way they're excluded from run_ingest()'s default -- see
# ingest.py FROZEN_SOURCES. Not scheduled at all here; re-enable by removing
# from FROZEN_SOURCES upstream, not by editing this file.
SCHEDULABLE_SOURCES = [s for s in NORMALIZERS if s not in FROZEN_SOURCES and s not in DEAD_SOURCES]


def _run_source_ingest(source: str) -> None:
    if datetime.date.today() > DAILY_TRIAL_END:
        logger.warning(
            "Daily-cadence trial window (ended %s) has passed -- calibrate "
            "real per-source SOURCE_INTERVAL_HOURS from run_log now instead "
            "of continuing to poll everything daily by default (see TODO.md "
            "3b, DAILY_TRIAL_END docstring in this file).",
            DAILY_TRIAL_END,
        )
    try:
        result = asyncio.run(run_ingest(sources=[source]))
        logger.info("Scheduled ingest done source=%s result=%s", source, result)
    except Exception:
        logger.exception("Scheduled ingest failed source=%s", source)


def _run_tag_and_rank() -> None:
    try:
        tag_result = run_tagging()
        if tag_result.get("skipped_reason") == "no_provider_configured":
            logger.info("Scheduled tagging skipped: no tagger provider configured")
        else:
            logger.info("Scheduled tagging done result=%s", tag_result)
    except Exception:
        logger.exception("Scheduled tagging failed")
    try:
        # rank_items() only scores items with a non-null category, so with no
        # tagger configured this is a correct, cheap no-op -- not a bug.
        ranked = rank_items()
        logger.info("Scheduled ranking done: %d items ranked", len(ranked))
    except Exception:
        logger.exception("Scheduled ranking failed")

    try:
        notify_run_summary()
    except Exception:
        logger.exception("Run-summary notification failed")


def _purge_raw_history() -> None:
    try:
        purge_old_history()
    except Exception:
        logger.exception("Scheduled raw-history purge failed")


def build_scheduler(interval_overrides: dict[str, float] | None = None) -> BackgroundScheduler:
    """Build (but don't start) a scheduler with one job per source plus a
    tag+rank job, all anchored to a fixed nightly time (RUN_HOUR:RUN_MINUTE)
    instead of an interval from process-start.

    Every source here is daily (SOURCE_INTERVAL_HOURS/DEFAULT_INTERVAL_HOURS
    are both 24h -- see module docstring), so all source jobs share the same
    CronTrigger time; tag+rank and the history purge run 15/30 min after so
    they pick up that night's freshly-ingested rows.

    interval_overrides lets a caller tweak individual source cadences without
    editing SOURCE_INTERVAL_HOURS, e.g. build_scheduler({"greenhouse": 6}) --
    any source not on 24h falls back to an interval trigger instead of the
    shared nightly cron slot, since it needs to fire more than once/day."""
    intervals = dict(SOURCE_INTERVAL_HOURS)
    if interval_overrides:
        intervals.update(interval_overrides)

    scheduler = BackgroundScheduler()
    for source in SCHEDULABLE_SOURCES:
        hours = intervals.get(source, DEFAULT_INTERVAL_HOURS)
        if hours == 24:
            scheduler.add_job(
                _run_source_ingest,
                CronTrigger(hour=RUN_HOUR, minute=RUN_MINUTE),
                args=[source],
                id=f"ingest_{source}",
                misfire_grace_time=3600,
            )
        else:
            scheduler.add_job(
                _run_source_ingest,
                "interval",
                hours=hours,
                args=[source],
                id=f"ingest_{source}",
                misfire_grace_time=3600,
            )

    # Tag + rank 15 min after the nightly ingest wave, so newly-inserted rows
    # get tagged/ranked the same night rather than waiting for a same-time
    # cron slot that would race the ingest jobs.
    tag_rank_hour, tag_rank_minute = RUN_HOUR, RUN_MINUTE + 15
    if tag_rank_minute >= 60:
        tag_rank_hour, tag_rank_minute = tag_rank_hour + 1, tag_rank_minute - 60
    scheduler.add_job(
        _run_tag_and_rank,
        CronTrigger(hour=tag_rank_hour, minute=tag_rank_minute),
        id="tag_and_rank",
        misfire_grace_time=3600,
    )

    # Raw-history purge 30 min after ingest -- deletes timestamped
    # data/raw/history/*.json files older than DEFAULT_RETENTION_DAYS (14).
    purge_hour, purge_minute = RUN_HOUR, RUN_MINUTE + 30
    if purge_minute >= 60:
        purge_hour, purge_minute = purge_hour + 1, purge_minute - 60
    scheduler.add_job(
        _purge_raw_history,
        CronTrigger(hour=purge_hour, minute=purge_minute),
        id="purge_raw_history",
        misfire_grace_time=3600,
    )

    return scheduler


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    scheduler = build_scheduler()
    scheduler.start()
    logger.info(
        "Scheduler started: %d sources, default interval %sh (see SOURCE_INTERVAL_HOURS for per-source overrides)",
        len(SCHEDULABLE_SOURCES),
        DEFAULT_INTERVAL_HOURS,
    )
    try:
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()


if __name__ == "__main__":
    main()
