# CLAUDE.md

## Project Overview
Slack bot that posts scheduled digests of Jira ticket statuses to customer Slack channels via Pylon, using Claude API for message generation.

## Tech Stack
- Python 3.11+ with FastAPI
- SQLAlchemy for DB (SQLite dev, PostgreSQL prod)
- httpx for async HTTP calls
- Anthropic Python SDK for Claude API
- APScheduler for cron-like scheduling

## Conventions
- Use async/await everywhere
- Type hints on all functions
- Pydantic models for data validation
- .env for secrets (never commit)

## Important Commands
- Run: uvicorn app.main:app --reload
- Test: pytest tests/
- Lint: ruff check .
