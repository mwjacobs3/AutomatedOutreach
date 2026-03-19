"""Email cadence manager — schedules and tracks the 6-email sequence."""

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Optional

from .email_generator import EmailSequence, GeneratedEmail


@dataclass
class ScheduledEmail:
    """An email scheduled within a cadence."""
    sequence_number: int
    send_day: int
    scheduled_date: str  # ISO format
    subject: str
    body: str
    purpose: str
    status: str = "draft"  # draft | sent | skipped
    gmail_draft_id: Optional[str] = None

    @classmethod
    def from_generated(cls, email: GeneratedEmail, start_date: datetime) -> "ScheduledEmail":
        send_date = start_date + timedelta(days=email.send_day - 1)
        return cls(
            sequence_number=email.sequence_number,
            send_day=email.send_day,
            scheduled_date=send_date.isoformat(),
            subject=email.subject,
            body=email.body,
            purpose=email.purpose,
        )


@dataclass
class Cadence:
    """A full email cadence for a prospect."""
    prospect_name: str
    prospect_email: str
    company: str
    created_at: str
    emails: list[ScheduledEmail]

    @classmethod
    def from_sequence(cls, sequence: EmailSequence, start_date: Optional[datetime] = None) -> "Cadence":
        if start_date is None:
            start_date = datetime.now()

        scheduled = [
            ScheduledEmail.from_generated(email, start_date)
            for email in sequence.emails
        ]

        return cls(
            prospect_name=sequence.prospect.full_name,
            prospect_email=sequence.prospect.email,
            company=sequence.prospect.company_name,
            created_at=datetime.now().isoformat(),
            emails=scheduled,
        )

    def save(self, directory: str = "data/cadences") -> str:
        """Save cadence to a JSON file. Returns the file path."""
        os.makedirs(directory, exist_ok=True)
        safe_name = self.prospect_name.lower().replace(" ", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_name}_{timestamp}.json"
        filepath = os.path.join(directory, filename)

        with open(filepath, "w") as f:
            json.dump(asdict(self), f, indent=2)

        return filepath

    @classmethod
    def load(cls, filepath: str) -> "Cadence":
        """Load a cadence from a JSON file."""
        with open(filepath) as f:
            data = json.load(f)

        data["emails"] = [ScheduledEmail(**e) for e in data["emails"]]
        return cls(**data)

    def display_schedule(self) -> str:
        """Show a summary of the cadence schedule."""
        lines = [
            f"Cadence for {self.prospect_name} ({self.prospect_email})",
            f"Company: {self.company}",
            f"Created: {self.created_at[:10]}",
            "",
        ]
        for e in self.emails:
            status_icon = {"draft": "[ ]", "sent": "[x]", "skipped": "[-]"}[e.status]
            lines.append(
                f"  {status_icon} Email {e.sequence_number} — Day {e.send_day} — "
                f"{e.scheduled_date[:10]} — \"{e.subject}\" ({e.purpose})"
            )
        return "\n".join(lines)
