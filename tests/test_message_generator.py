from __future__ import annotations

from app.message_generator import build_blocks, _strip_customer_prefix

CUSTOMER = "Aurex Capital"

SAMPLE_TICKETS = [
    {
        "jira_key": "ORCH-95",
        "pylon_id": "616",
        "summary": "Aurex - USD VIBAN enablement and approval delays",
        "status": "Work in Progress",
        "due_date": "",
        "days_open": 5,
    },
    {
        "jira_key": "ORCH-100",
        "pylon_id": "123",
        "summary": "Aurex - Confusing Old vs. New Rejection Status in UI",
        "status": "Backlog",
        "due_date": "",
        "days_open": 3,
    },
    {
        "jira_key": "ORCH-101",
        "pylon_id": "633",
        "summary": 'Aurex - "Failed to fetch" error - Dashboard Upload',
        "status": "Ready for Release",
        "due_date": "2026-03-20",
        "days_open": 10,
    },
]


def test_build_blocks_structure():
    blocks = build_blocks(CUSTOMER, SAMPLE_TICKETS)
    types = [b["type"] for b in blocks]
    assert types[0] == "header"
    assert types[1] == "section"
    assert types[2] == "divider"


def test_build_blocks_customer_name_header():
    blocks = build_blocks(CUSTOMER, SAMPLE_TICKETS)
    header_blocks = [b for b in blocks if b["type"] == "header"]
    header_texts = [b["text"]["text"] for b in header_blocks]
    assert CUSTOMER in header_texts


def test_build_blocks_ticket_count():
    blocks = build_blocks(CUSTOMER, SAMPLE_TICKETS)
    section_blocks = [b for b in blocks if b["type"] == "section"]
    # 1 intro + 3 ticket sections
    assert len(section_blocks) == 4


def test_build_blocks_done_emoji():
    blocks = build_blocks(CUSTOMER, SAMPLE_TICKETS)
    ticket_sections = [b for b in blocks if b["type"] == "section" and "ORCH-" in b["text"]["text"]]
    ready_block = next(b for b in ticket_sections if "ORCH-101" in b["text"]["text"])
    assert ready_block["text"]["text"].startswith("✅")


def test_build_blocks_in_progress_emoji():
    blocks = build_blocks(CUSTOMER, SAMPLE_TICKETS)
    ticket_sections = [b for b in blocks if b["type"] == "section" and "ORCH-" in b["text"]["text"]]
    wip_block = next(b for b in ticket_sections if "ORCH-95" in b["text"]["text"])
    assert wip_block["text"]["text"].startswith("⚠️")


def test_build_blocks_pylon_format():
    blocks = build_blocks(CUSTOMER, SAMPLE_TICKETS)
    ticket_sections = [b for b in blocks if b["type"] == "section" and "ORCH-" in b["text"]["text"]]
    assert "Pylon #" in ticket_sections[0]["text"]["text"]


def test_build_blocks_dividers_between_tickets():
    blocks = build_blocks(CUSTOMER, SAMPLE_TICKETS)
    divider_count = sum(1 for b in blocks if b["type"] == "divider")
    # 1 after intro + 2 between 3 tickets = 3
    assert divider_count == 3


def test_build_blocks_empty_tickets():
    blocks = build_blocks(CUSTOMER, [])
    types = [b["type"] for b in blocks]
    assert types == ["header", "section", "divider", "header"]


def test_build_blocks_due_date_fallback():
    blocks = build_blocks(CUSTOMER, SAMPLE_TICKETS)
    ticket_sections = [b for b in blocks if b["type"] == "section" and "ORCH-" in b["text"]["text"]]
    no_due = next(b for b in ticket_sections if "ORCH-95" in b["text"]["text"])
    assert "📅 Due: ___" in no_due["text"]["text"]


def test_build_blocks_due_date_present():
    blocks = build_blocks(CUSTOMER, SAMPLE_TICKETS)
    ticket_sections = [b for b in blocks if b["type"] == "section" and "ORCH-" in b["text"]["text"]]
    with_due = next(b for b in ticket_sections if "ORCH-101" in b["text"]["text"])
    assert "📅 Due: 2026-03-20" in with_due["text"]["text"]


def test_strip_customer_prefix_removes_prefix():
    assert _strip_customer_prefix("Aurex - Some Issue", "Aurex Capital") == "Some Issue"


def test_strip_customer_prefix_no_prefix():
    assert _strip_customer_prefix("Some Issue Without Prefix", "Aurex Capital") == "Some Issue Without Prefix"


def test_strip_customer_prefix_not_in_summary():
    assert _strip_customer_prefix("nSave - PDF upload issue", "Aurex Capital") == "nSave - PDF upload issue"


def test_summary_stripped_in_blocks():
    blocks = build_blocks(CUSTOMER, SAMPLE_TICKETS)
    ticket_sections = [b for b in blocks if b["type"] == "section" and "ORCH-95" in b["text"]["text"]]
    text = ticket_sections[0]["text"]["text"]
    assert "Aurex -" not in text
    assert "USD VIBAN enablement and approval delays" in text
