from __future__ import annotations

import logging
from app.jira_client import get_open_tickets
from app.pylon_client import get_pylon_ticket_id
from app.message_generator import build_blocks
from app.slack_client import post_to_channel
from app.database import get_customers

logger = logging.getLogger(__name__)


async def run_all_digests() -> None:
    customers = await get_customers()

    for customer in customers:
        customer_name = customer["name"]
        try:
            # 1. Get open Jira tickets for this customer
            jira_tickets = await get_open_tickets(
                customer["jira_customer_name"],
                customer["jira_project_key"],
            )

            if not jira_tickets:
                logger.info(f"No open tickets for {customer_name}")
                continue

            # 2. Enrich with Pylon ticket numbers (auto-lookup via Pylon API, cached in DB)
            enriched: list[dict] = []
            for ticket in jira_tickets:
                pylon_id = await get_pylon_ticket_id(ticket["key"])
                enriched.append(
                    {
                        "jira_key": ticket["key"],
                        "pylon_id": pylon_id,
                        "summary": ticket["summary"],
                        "status": ticket["status"],
                        "due_date": ticket.get("due_date", ""),
                        "days_open": ticket.get("days_open", 0),
                    }
                )

            # 3. Build Slack Block Kit blocks
            blocks = build_blocks(customer_name, enriched)

            # 4. Post to Slack channel
            await post_to_channel(customer["slack_channel_id"], blocks)

            logger.info(
                f"Digest posted for {customer_name} ({len(enriched)} tickets)"
            )

        except Exception as e:
            logger.error(f"Digest failed for {customer_name}: {e}")
