from __future__ import annotations

from datetime import date, datetime
import httpx
from app.config import settings


async def get_open_tickets(customer_name: str, project_key: str) -> list[dict]:
    jql = (
        f'project = "{project_key}" '
        f'AND cf[10389] = "{customer_name}" '
        f'AND (statusCategory != Done OR status = "Ready for Release") '
        f"ORDER BY status ASC, priority DESC"
    )

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.jira_base_url}/rest/api/3/search/jql",
            json={
                "jql": jql,
                "fields": ["summary", "status", "duedate", "priority", "customfield_10389", "created"],
                "maxResults": 50,
            },
            auth=(settings.jira_email, settings.jira_api_token),
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()

    today = date.today()
    tickets = []
    for issue in data.get("issues", []):
        # Skip tickets with no customer name set
        if not issue["fields"].get("customfield_10389"):
            continue
        created_str = issue["fields"].get("created", "")
        if created_str:
            created_date = datetime.fromisoformat(created_str[:10]).date()
            days_open = (today - created_date).days
        else:
            days_open = 0
        tickets.append({
            "key": issue["key"],
            "summary": issue["fields"]["summary"],
            "status": issue["fields"]["status"]["name"],
            "due_date": issue["fields"].get("duedate", "") or "",
            "priority": issue["fields"]["priority"]["name"],
            "days_open": days_open,
        })
    return tickets
