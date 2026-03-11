from __future__ import annotations

import httpx
from app.config import settings


async def post_to_channel(channel_id: str, message: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://slack.com/api/chat.postMessage",
            headers={
                "Authorization": f"Bearer {settings.slack_bot_token}",
                "Content-Type": "application/json",
            },
            json={
                "channel": channel_id,
                "text": message,
                "unfurl_links": False,
            },
            timeout=15.0,
        )
        data = response.json()
        if not data.get("ok"):
            raise Exception(f"Slack error: {data.get('error')}")
        return data
