# Jira → Slack Digest Bot

Posts scheduled digests of open Jira tickets to customer Slack channels, twice daily at 9 AM and 9 PM EST. Messages are generated via the Claude API.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in all values
```

## Run

```bash
uvicorn app.main:app --reload
```

Manually trigger a digest (useful for testing):

```bash
curl -X POST http://localhost:8000/run-digest
```

## Configuration

### Adding a new customer

Edit `config/customers.yaml`:

```yaml
customers:
  - name: "Acme Corp"
    jira_customer_name: "Acme Corp"   # must match the Jira "Customer Name" field
    jira_project_key: "PLAT"
    team_name: "Platform Engineering"
    slack_channel_id: "C0456ACME"     # Slack channel ID (not name)
    ticket_mappings:
      PLAT-10: "101"                  # Jira key → Pylon ticket number
      PLAT-11: "102"
```

### Adding new ticket mappings

When a new Jira ticket is created for a customer, add its Pylon ticket number to that customer's `ticket_mappings` in `customers.yaml`:

```yaml
ticket_mappings:
  ORCH-95: "616"
  ORCH-100: "123"
  ORCH-101: "633"
  ORCH-110: "701"   # ← new ticket added here
```

The Pylon ticket number is the number visible in the Pylon UI (e.g. `#616`). If a Jira ticket has no mapping, the digest will show `Pylon Ticket Number = N/A` for that ticket.

## Environment variables

| Variable | Description |
|---|---|
| `JIRA_BASE_URL` | e.g. `https://yourcompany.atlassian.net` |
| `JIRA_EMAIL` | Jira account email |
| `JIRA_API_TOKEN` | Jira API token |
| `PYLON_API_KEY` | Pylon API key |
| `SLACK_BOT_TOKEN` | Slack bot token (`xoxb-...`) |
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `DATABASE_URL` | SQLite default: `sqlite+aiosqlite:///./mappings.db` |

## Slack bot setup

The Slack bot must be **invited to each customer channel** before it can post:

```
/invite @<bot-name>
```

Required Slack scopes: `chat:write`, `channels:read`, `groups:read`
