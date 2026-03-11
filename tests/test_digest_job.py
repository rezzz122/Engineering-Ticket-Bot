from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch


SAMPLE_CUSTOMERS = [
    {
        "name": "Aurex Capital",
        "jira_customer_name": "Aurex Capital",
        "jira_project_key": "ORCH",
        "team_name": "Fin Technology",
        "slack_channel_id": "C0123AUREX",
        "schedule": "9am_9pm_est",
    }
]

SAMPLE_JIRA_TICKETS = [
    {
        "key": "ORCH-95",
        "summary": "Aurex - USD VIBAN enablement",
        "status": "Work in Progress",
        "due_date": "",
        "priority": "High",
    }
]


@pytest.mark.asyncio
async def test_run_all_digests_full_flow():
    with (
        patch("app.digest_job.get_customers", new=AsyncMock(return_value=SAMPLE_CUSTOMERS)),
        patch("app.digest_job.get_open_tickets", new=AsyncMock(return_value=SAMPLE_JIRA_TICKETS)),
        patch("app.digest_job.get_pylon_ticket_id", new=AsyncMock(return_value="616")),
        patch("app.digest_job.generate_digest", new=AsyncMock(return_value=":wave: Digest message")),
        patch("app.digest_job.post_to_channel", new=AsyncMock()) as mock_post,
    ):
        from app.digest_job import run_all_digests

        await run_all_digests()

    mock_post.assert_called_once_with("C0123AUREX", ":wave: Digest message")


@pytest.mark.asyncio
async def test_run_all_digests_skips_empty_customers():
    with (
        patch("app.digest_job.get_customers", new=AsyncMock(return_value=SAMPLE_CUSTOMERS)),
        patch("app.digest_job.get_open_tickets", new=AsyncMock(return_value=[])),
        patch("app.digest_job.post_to_channel", new=AsyncMock()) as mock_post,
    ):
        from app.digest_job import run_all_digests

        await run_all_digests()

    mock_post.assert_not_called()


@pytest.mark.asyncio
async def test_run_all_digests_handles_errors():
    with (
        patch("app.digest_job.get_customers", new=AsyncMock(return_value=SAMPLE_CUSTOMERS)),
        patch("app.digest_job.get_open_tickets", new=AsyncMock(side_effect=Exception("Jira down"))),
        patch("app.digest_job.post_to_channel", new=AsyncMock()) as mock_post,
    ):
        from app.digest_job import run_all_digests

        # Should not raise — errors are caught and logged
        await run_all_digests()

    mock_post.assert_not_called()
