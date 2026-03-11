# How the System Works

## Overview

This bot runs twice daily (9 AM and 9 PM EST) and posts a Slack digest of open Jira tickets for each configured customer. Messages are formatted by the Claude API and posted directly to a Slack channel.

---

## End-to-End Flow

```
customers.yaml
     │
     ▼
1. Read customer config
     │
     ▼
2. Query Jira API  ──────────────────────────────────────────────────────┐
   JQL: project = "ORCH"                                                 │
        AND cf[10389] = "Aurex Capital"                                  │
        AND (statusCategory != Done                                      │
             OR status = "Ready for Release")                            │
   Returns: ticket key, summary, status, due date, created date         │
                                                                         │
     │                                                                   │
     ▼                                                                   │
3. For each ticket — look up Pylon number (3-step cascade):             │
                                                                         │
   Step 1: Check DB cache                                                │
           └─ Found? → use it, skip Steps 2 & 3                         │
                                                                         │
   Step 2: Scan Pylon API (6 x 30-day windows = 6 months)               │
           GET /issues?start_time=...&end_time=...                       │
           Check external_issues[].link for ".../browse/ORCH-XX"        │
           └─ Found? → cache in DB, use it                              │
                                                                         │
   Step 3: Parse Jira ticket description (fallback)                     │
           GET /rest/api/3/issue/ORCH-XX                                 │
           Regex: "Pylon Ticket Number: 123" or "issueNumber=123"       │
           └─ Found? → cache in DB, use it                              │
           └─ Still not found? → show N/A                               │
                                                                         │
     │                                                                   │
     ▼                                                                   │
4. Generate message via Claude API (claude-sonnet-4-5)                  │
   Input:  customer name, team name, list of enriched tickets           │
   Output: formatted Slack message                                       │
                                                                         │
     │                                                                   │
     ▼                                                                   │
5. Post to Slack                                                         │
   POST https://slack.com/api/chat.postMessage                          │
   channel: slack_channel_id from customers.yaml                        │
                                                                         │
     └───────────────── repeat for next customer ──────────────────────┘
```

---

## Slack Message Format

```
:wave: Here is a status of the items that require work from the Fin Technology team:

*Aurex Capital*
ORCH-95 (*Pylon Ticket Number = 616*)
• Summary: Aurex - USD VIBAN enablement and approval delays
• Status = Work In Progress
• Due Date = ___
• Days Open = 14

ORCH-100 (*Pylon Ticket Number = 123*)
• Summary: Aurex - Confusing Old vs. New Rejection Status in UI
• Status = Backlog
• Due Date = ___
• Days Open = 14
```

---

## Components

### `config/customers.yaml`
The only file you edit to add or change customers. Each entry defines:
- `name` — display name used in the Slack message
- `jira_customer_name` — value matched against Jira's `cf[10389]` (Customer name field)
- `jira_project_key` — Jira project to search (e.g. `ORCH`)
- `team_name` — appears in the intro line of the digest
- `slack_channel_id` — Slack channel ID to post to

### `app/jira_client.py`
Queries Jira REST API v3 (`POST /rest/api/3/search/jql`) with a JQL filter. Returns all open tickets for the customer including summary, status, due date, priority, and created date. Calculates **Days Open** from the created date.

### `app/pylon_client.py`
Resolves the Pylon ticket number for each Jira key using a 3-step cascade:
1. DB cache (SQLite via SQLAlchemy)
2. Pylon `GET /issues` scan — looks for Jira key in `external_issues[].link`
3. Jira description parse — extracts "Pylon Ticket Number: X" from the ticket body

Once found, the result is cached in the DB so future runs are instant.

### `app/message_generator.py`
Calls the Claude API (`claude-sonnet-4-5`) with a strict system prompt that enforces the exact Slack message format. Receives a list of enriched ticket dicts and returns the formatted message string.

### `app/digest_job.py`
Orchestrates the full flow for every customer: Jira → Pylon lookup → Claude → Slack. Errors for one customer are caught and logged so other customers still get their digests.

### `app/scheduler.py`
APScheduler runs `run_all_digests()` at 9 AM and 9 PM EST using `CronTrigger`. Starts automatically when the FastAPI app boots.

### `app/main.py`
FastAPI app with two endpoints:
- `GET /health` — health check
- `POST /run-digest` — manually trigger a digest run (useful for testing or external cron)

### `app/database.py` + `app/models.py`
SQLite database with a `TicketMapping` table that caches Jira key → Pylon ticket number mappings. Avoids re-scanning Pylon on every digest run.

---

## What is Dynamic vs Static

| Data | Source | Dynamic? |
|---|---|---|
| Ticket keys (ORCH-95 etc.) | Jira API | ✅ Live |
| Summary | Jira API | ✅ Live |
| Status | Jira API | ✅ Live |
| Due Date | Jira API | ✅ Live |
| Days Open | Calculated from Jira `created` | ✅ Live |
| Pylon ticket number | Pylon API + Jira description + DB cache | ✅ Auto-discovered |
| Customer name | `customers.yaml` | Manual |
| Team name | `customers.yaml` | Manual |
| Slack channel | `customers.yaml` | Manual |
| Message format | Claude API system prompt | Manual |

---

## Adding a New Customer

1. Edit `config/customers.yaml` and add a new entry:
```yaml
- name: "Acme Corp"
  jira_customer_name: "Acme Corp"   # must match Jira cf[10389] exactly
  jira_project_key: "ORCH"
  team_name: "Fin Technology"
  slack_channel_id: "CXXXXXXXXX"    # Slack channel ID
```

2. Invite the Slack bot to the channel: `/invite @<bot-name>`

3. That's it — the bot will auto-discover Pylon ticket numbers on the next run.

---

## Adding a New Ticket Mapping

Nothing to do. When a new Jira ticket appears:
- It is automatically picked up by the JQL query
- Pylon number is auto-discovered via the Pylon API or Jira description
- Result is cached in DB for all future runs

If auto-discovery fails (no Pylon link and no mention in description), the digest shows `Pylon Ticket Number = N/A`. Fix by either:
- Linking the Jira ticket in the Pylon UI
- Adding "Pylon Ticket Number: XXX" to the Jira ticket description

---

## Scheduler Timing

| Job | Cron | UTC equivalent |
|---|---|---|
| Morning digest | 9:00 AM EST | 14:00 UTC |
| Evening digest | 9:00 PM EST | 02:00 UTC (next day) |

---

## Running Locally

```bash
# Install dependencies
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Start the server (scheduler runs automatically)
uvicorn app.main:app --reload

# Manually trigger a digest
curl -X POST http://localhost:8000/run-digest
```

---

## Environment Variables (`.env`)

| Variable | Description |
|---|---|
| `JIRA_BASE_URL` | e.g. `https://yourcompany.atlassian.net` |
| `JIRA_EMAIL` | Jira account email |
| `JIRA_API_TOKEN` | Jira API token |
| `PYLON_API_KEY` | Pylon API key |
| `PYLON_API_BASE_URL` | `https://api.usepylon.com` |
| `SLACK_BOT_TOKEN` | Slack bot token (`xoxb-...`) |
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `DATABASE_URL` | `sqlite+aiosqlite:///./mappings.db` |
