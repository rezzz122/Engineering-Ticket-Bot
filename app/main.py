from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import init_db
from app.digest_job import run_all_digests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Jira → Slack Digest Bot", lifespan=lifespan)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/run-digest")
async def trigger_digest() -> dict:
    """Manually trigger a digest run (useful for testing or external cron)."""
    await run_all_digests()
    return {"status": "digest triggered"}
