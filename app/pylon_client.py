from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone
import httpx
from sqlalchemy import select
from app.config import settings
from app.database import AsyncSessionLocal
from app.models import TicketMapping

logger = logging.getLogger(__name__)


async def get_pylon_ticket_id(jira_key: str) -> str:
    # Check DB cache first
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(TicketMapping).where(TicketMapping.jira_key == jira_key)
        )
        mapping = result.scalar_one_or_none()
        if mapping and mapping.pylon_ticket_id:
            return mapping.pylon_ticket_id

    # Search Pylon issues by scanning external_issues for matching Jira link
    # Pylon GET /issues accepts max 30-day windows — scan in chunks going back 6 months
    try:
        async with httpx.AsyncClient() as client:
            end = datetime.now(tz=timezone.utc)
            for _ in range(6):  # 6 x 30-day chunks = 6 months
                start = end - timedelta(days=30)
                response = await client.get(
                    f"{settings.pylon_api_base_url}/issues",
                    params={
                        "start_time": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "end_time": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    },
                    headers={"Authorization": f"Bearer {settings.pylon_api_key}"},
                    timeout=30.0,
                )
                response.raise_for_status()
                issues = response.json().get("data", [])

                for issue in issues:
                    for ext in issue.get("external_issues", []):
                        if ext.get("source") == "jira" and ext.get("link", "").endswith(f"/{jira_key}"):
                            pylon_number = str(issue["number"])
                            await _cache_mapping(jira_key, pylon_number)
                            return pylon_number

                end = start  # move window back

        # Fallback: parse Pylon number from Jira ticket description
        pylon_number = await _extract_pylon_from_jira_description(jira_key)
        if pylon_number:
            logger.info(f"Found Pylon #{pylon_number} for {jira_key} via Jira description")
            await _cache_mapping(jira_key, pylon_number)
            return pylon_number

        logger.warning(f"No Pylon ticket found for {jira_key}")
        return "N/A"

    except Exception as e:
        logger.error(f"Pylon lookup failed for {jira_key}: {e}")
        return "N/A"


async def _extract_pylon_from_jira_description(jira_key: str) -> str | None:
    """Parse 'Pylon Ticket Number: 123' or Pylon URLs from the Jira ticket description."""
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{settings.jira_base_url}/rest/api/3/issue/{jira_key}",
                params={"fields": "description,renderedFields"},
                auth=(settings.jira_email, settings.jira_api_token),
                timeout=15.0,
            )
            r.raise_for_status()
            import json
            raw = json.dumps(r.json())

        # Match "Pylon Ticket Number: 123" or "issueNumber=123"
        for pattern in [
            r"[Pp]ylon\s+[Tt]icket\s+[Nn]umber[:\s]+(\d+)",
            r"issueNumber=(\d+)",
        ]:
            match = re.search(pattern, raw)
            if match:
                return match.group(1)
    except Exception as e:
        logger.error(f"Jira description fallback failed for {jira_key}: {e}")
    return None


async def _cache_mapping(jira_key: str, pylon_number: str) -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(TicketMapping).where(TicketMapping.jira_key == jira_key)
        )
        mapping = result.scalar_one_or_none()
        if mapping:
            mapping.pylon_ticket_id = pylon_number
        else:
            session.add(TicketMapping(jira_key=jira_key, pylon_ticket_id=pylon_number))
        await session.commit()


async def send_message(pylon_ticket_id: str, message: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.pylon_api_base_url}/issues/{pylon_ticket_id}/messages",
            headers={
                "Authorization": f"Bearer {settings.pylon_api_key}",
                "Content-Type": "application/json",
            },
            json={"body": message, "type": "customer"},
            timeout=15.0,
        )
        response.raise_for_status()
        return response.json()
