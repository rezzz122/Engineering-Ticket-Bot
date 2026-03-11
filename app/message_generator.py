from __future__ import annotations

import anthropic
from app.config import settings

client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

SYSTEM_PROMPT = """\
You are a customer-facing bot that posts engineering ticket status updates in Slack.
Generate a digest message using EXACTLY this format:

👋 Fin.com Engineering Team Here!
We're actively working on your issue and will share 
updates soon. Thanks for your patience!

✅ ORCH-116 (Pylon #691)
• Fin API - Stability Improvements (Phase 1)
• Status: Done
• 📅 Due: ___
• ⏳ Days Open: 6

⚠️ ORCH-107 (Pylon #819)
• nSave - PDF upload rejecting proof_of_address
• Status: In Progress
• 📅 Due: ___
• ⏳ Days Open: 6

Rules:
- Use ✅ emoji for tickets with status "Done" or "Ready for Release"
- Use ⚠️ emoji for everything else (Backlog, To-Do, In Progress, Work In Progress)
- Use "Pylon #X" not "Pylon Ticket Number = X"
- Use • (unicode bullet) not * for detail lines
- Add 📅 before Due and ⏳ before Days Open
- Keep the intro message exactly as shown
- Blank line between each ticket
- Group by customer name if multiple customers
- No bold on Pylon number anymore\
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
