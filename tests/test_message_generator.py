from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


SAMPLE_TICKETS = [
    {
        "jira_key": "ORCH-95",
        "pylon_id": "616",
        "summary": "Aurex - USD VIBAN enablement and approval delays",
        "status": "Work in Progress",
        "due_date": "",
    },
    {
        "jira_key": "ORCH-100",
        "pylon_id": "123",
        "summary": "Aurex - Confusing Old vs. New Rejection Status in UI",
        "status": "Backlog",
        "due_date": "",
    },
    {
        "jira_key": "ORCH-101",
        "pylon_id": "633",
        "summary": 'Aurex - "Failed to fetch" error - Dashboard Upload',
        "status": "Ready for Release",
        "due_date": "",
    },
]


@pytest.mark.asyncio
async def test_generate_digest_calls_claude():
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=":wave: Here is a status")]

    with patch("app.message_generator.client") as mock_client:
        mock_client.messages.create.return_value = mock_response

        from app.message_generator import generate_digest

        result = await generate_digest("Aurex Capital", "Fin Technology", SAMPLE_TICKETS)

    assert ":wave:" in result
    mock_client.messages.create.assert_called_once()
    call_kwargs = mock_client.messages.create.call_args.kwargs
    assert call_kwargs["model"] == "claude-sonnet-4-5"
    assert "Aurex Capital" in call_kwargs["messages"][0]["content"]
    assert "ORCH-95" in call_kwargs["messages"][0]["content"]


@pytest.mark.asyncio
async def test_generate_digest_includes_all_tickets():
    captured = {}

    def fake_create(**kwargs):
        captured.update(kwargs)
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="fake output")]
        return mock_response

    with patch("app.message_generator.client") as mock_client:
        mock_client.messages.create.side_effect = fake_create

        from app.message_generator import generate_digest

        await generate_digest("Aurex Capital", "Fin Technology", SAMPLE_TICKETS)

    user_content = captured["messages"][0]["content"]
    for ticket in SAMPLE_TICKETS:
        assert ticket["jira_key"] in user_content
        assert ticket["pylon_id"] in user_content


@pytest.mark.asyncio
async def test_generate_digest_empty_tickets():
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=":wave: Here is a status\n\nNo open tickets.")]

    with patch("app.message_generator.client") as mock_client:
        mock_client.messages.create.return_value = mock_response

        from app.message_generator import generate_digest

        result = await generate_digest("Aurex Capital", "Fin Technology", [])

    assert result is not None
