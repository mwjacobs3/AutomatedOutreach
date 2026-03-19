"""Gmail draft creation for email cadences.

This module is designed to work with the Gmail MCP tool available in Claude Code.
When running standalone, it saves drafts as local files for manual sending.
When integrated with Claude Code's Gmail MCP, it creates actual Gmail drafts.
"""

import json
import os
from dataclasses import dataclass
from typing import Optional

from .cadence import Cadence, ScheduledEmail


@dataclass
class DraftResult:
    """Result of creating a draft."""
    sequence_number: int
    subject: str
    status: str  # "created" | "error"
    draft_id: Optional[str] = None
    error: Optional[str] = None


def prepare_draft_content(email: ScheduledEmail, to_email: str) -> dict:
    """Prepare the content needed to create a Gmail draft."""
    return {
        "to": to_email,
        "subject": email.subject,
        "body": email.body,
    }


def save_drafts_locally(cadence: Cadence, output_dir: str = "data/drafts") -> list[str]:
    """Save all cadence emails as local draft files for review before sending.

    Returns list of file paths created.
    """
    safe_name = cadence.prospect_name.lower().replace(" ", "_")
    draft_dir = os.path.join(output_dir, safe_name)
    os.makedirs(draft_dir, exist_ok=True)

    paths = []
    for email in cadence.emails:
        content = prepare_draft_content(email, cadence.prospect_email)
        content["scheduled_date"] = email.scheduled_date
        content["purpose"] = email.purpose
        content["sequence_number"] = email.sequence_number

        filename = f"email_{email.sequence_number}_day_{email.send_day}.json"
        filepath = os.path.join(draft_dir, filename)

        with open(filepath, "w") as f:
            json.dump(content, f, indent=2)

        paths.append(filepath)

    return paths


def format_for_gmail_mcp(cadence: Cadence) -> list[dict]:
    """Format all emails for use with Gmail MCP tool (gmail_create_draft).

    Returns a list of dicts ready to pass to the MCP gmail_create_draft tool.
    Each dict contains: to, subject, body, and metadata.
    """
    drafts = []
    for email in cadence.emails:
        drafts.append({
            "to": [cadence.prospect_email],
            "subject": email.subject,
            "body": email.body,
            "metadata": {
                "sequence_number": email.sequence_number,
                "send_day": email.send_day,
                "scheduled_date": email.scheduled_date,
                "purpose": email.purpose,
            },
        })
    return drafts
