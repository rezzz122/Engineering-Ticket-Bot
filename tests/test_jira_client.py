from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch, MagicMock


SAMPLE_JIRA_RESPONSE = {
    "issues": [
        {
            "key": "ORCH-95",
            "fields": {
                "summary": "Aurex - USD VIBAN enablement and approval delays",
                "status": {"name": "Work in Progress"},
                "duedate": None,
                "priority": {"name": "High"},
                "customfield_10389": "Aurex Capital",
                "created": "2026-03-05T10:00:00.000+0000",
            },
        },
        {
            "key": "ORCH-100",
            "fields": {
                "summary": "Aurex - Confusing Old vs. New Rejection Status in UI",
                "status": {"name": "Backlog"},
                "duedate": None,
                "priority": {"name": "Medium"},
                "customfield_10389": "Aurex Capital",
                "created": "2026-03-07T10:00:00.000+0000",
            },
        },
    ]
}


@pytest.mark.asyncio
async def test_get_open_tickets_returns_parsed_results():
    mock_response = MagicMock()
    mock_response.json.return_value = SAMPLE_JIRA_RESPONSE
    mock_response.raise_for_status = MagicMock()

    with patch("app.jira_client.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        mock_client.post.return_value = mock_response

        from app.jira_client import get_open_tickets

        tickets = await get_open_tickets("Aurex Capital", "ORCH")

    assert len(tickets) == 2
    assert tickets[0]["key"] == "ORCH-95"
    assert tickets[0]["status"] == "Work in Progress"
    assert tickets[0]["due_date"] == ""
    assert tickets[1]["key"] == "ORCH-100"


@pytest.mark.asyncio
async def test_get_open_tickets_uses_correct_jql():
    mock_response = MagicMock()
    mock_response.json.return_value = {"issues": []}
    mock_response.raise_for_status = MagicMock()

    with patch("app.jira_client.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        mock_client.post.return_value = mock_response

        from app.jira_client import get_open_tickets

        await get_open_tickets("Aurex Capital", "ORCH")

    call_kwargs = mock_client.post.call_args.kwargs
    jql = call_kwargs["json"]["jql"]
    assert 'project = "ORCH"' in jql
    assert "Aurex Capital" in jql
    assert "statusCategory != Done" in jql


@pytest.mark.asyncio
async def test_get_open_tickets_empty_response():
    mock_response = MagicMock()
    mock_response.json.return_value = {"issues": []}
    mock_response.raise_for_status = MagicMock()

    with patch("app.jira_client.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        mock_client.post.return_value = mock_response

        from app.jira_client import get_open_tickets

        tickets = await get_open_tickets("Unknown Customer", "ORCH")

    assert tickets == []
