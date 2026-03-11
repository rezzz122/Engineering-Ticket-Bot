from __future__ import annotations

_DONE_STATUSES = {"Done", "Ready for Release"}


def _strip_customer_prefix(summary: str, customer_name: str) -> str:
    """Remove 'CustomerName - ' prefix from summary if present."""
    first_word = customer_name.split()[0]
    if " - " in summary and summary.split(" - ")[0].strip() in customer_name:
        return summary.split(" - ", 1)[1].strip()
    return summary


def build_blocks(customer_name: str, tickets: list[dict]) -> list[dict]:
    blocks: list[dict] = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "👋 Fin.com Engineering Team Here!", "emoji": True},
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "We're actively working on your issue and will share updates soon. Thanks for your patience!",
            },
        },
        {"type": "divider"},
        {
            "type": "header",
            "text": {"type": "plain_text", "text": customer_name, "emoji": True},
        },
    ]

    for i, t in enumerate(tickets):
        emoji = "✅" if t["status"] in _DONE_STATUSES else "⚠️"
        pylon = f"(Pylon #{t['pylon_id']})" if t.get("pylon_id") else ""
        due = t.get("due_date") or "___"
        summary = _strip_customer_prefix(t["summary"], customer_name)
        text = (
            f"{emoji} *{t['jira_key']}* {pylon}\n"
            f"{summary}\n"
            f"Status: {t['status']}\n"
            f"📅 Due: {due}\n"
            f"⏳ Days Open: {t.get('days_open', 0)}"
        )
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": text}})
        if i < len(tickets) - 1:
            blocks.append({"type": "divider"})

    return blocks
