from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.digest_job import run_all_digests

scheduler = AsyncIOScheduler()


def start_scheduler() -> None:
    # 9:00 AM EST
    scheduler.add_job(
        run_all_digests,
        CronTrigger(hour=9, minute=0, timezone="US/Eastern"),
        id="morning_digest",
        replace_existing=True,
    )
    # 9:00 PM EST
    scheduler.add_job(
        run_all_digests,
        CronTrigger(hour=21, minute=0, timezone="US/Eastern"),
        id="evening_digest",
        replace_existing=True,
    )
    scheduler.start()


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown()
