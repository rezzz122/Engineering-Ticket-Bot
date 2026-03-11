from __future__ import annotations

import anthropic
from app.config import settings

client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

SYSTEM_PROMPT = """\
You are a customer-facing bot that posts engineering ticket status updates in Slack.
Generate a digest message using EXACTLY this format:

:wave: Here is a status of the items that require work from the {team_name} team:

*{customer_name}*
{JIRA_KEY} (*Pylon Ticket Number = {PYLON_ID}*)
• Summary: {summary}
• Status = {status}
• Due Date = {due_date or '___'}
• Days Open = {days_open}

Rules:
- The intro line starts with :wave: and mentions the team name
- Customer name appears ONCE on its own line after the intro — in Slack bold using *customer_name* syntax, do NOT repeat it before each ticket
- Then list ALL tickets one after another
- Jira key is followed by (*Pylon Ticket Number = X*) — bold using Slack *bold* syntax
- Each detail line (Summary, Status, Due Date, Days Open) starts with "• " (unicode bullet U+2022)
- Separate each ticket with a blank line
- If due_date is null or empty, show ___
- If Pylon number is unknown, show (*Pylon Ticket Number = N/A*)
- Do NOT add any commentary, greetings, or sign-offs beyond the :wave: intro line
- Keep it clean and scannable\
"""


async def generate_digest(
    customer_name: str,
    team_name: str,
    tickets: list[dict],
) -> str:
    ticket_data = "\n".join(
        [
            f"- Jira Key: {t['jira_key']}, "
            f"Pylon ID: {t['pylon_id']}, "
            f"Summary: {t['summary']}, "
            f"Status: {t['status']}, "
            f"Due Date: {t.get('due_date', '')}, "
            f"Days Open: {t.get('days_open', 0)}"
            for t in tickets
        ]
    )

    user_prompt = f"""\
Customer: {customer_name}
Team: {team_name}
Open tickets:
{ticket_data}

Generate the Slack digest message now.\
"""

    message = await client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return message.content[0].text
