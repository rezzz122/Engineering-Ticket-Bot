from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import init_db
from app.scheduler import start_scheduler, stop_scheduler
from app.digest_job import run_all_digests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    start_scheduler()
    logger.info("Scheduler started — digests will run at 9AM and 9PM EST")
    yield
    stop_scheduler()


app = FastAPI(title="Jira → Slack Digest Bot", lifespan=lifespan)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/run-digest")
async def trigger_digest() -> dict:
    """Manually trigger a digest run (useful for testing or external cron)."""
    await run_all_digests()
    return {"status": "digest triggered"}
