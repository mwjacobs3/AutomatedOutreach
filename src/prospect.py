"""Prospect data model for capturing LinkedIn, company, and contact information."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Prospect:
    """Represents a potential NetSuite prospect with all known context."""

    # Contact basics
    first_name: str
    last_name: str
    email: str
    title: str
    company_name: str

    # LinkedIn profile context (user pastes key details)
    linkedin_url: Optional[str] = None
    linkedin_summary: Optional[str] = None
    years_experience: Optional[str] = None
    recent_activity: Optional[str] = None  # posts, comments, job changes

    # Company context
    company_url: Optional[str] = None
    company_linkedin_url: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None  # e.g. "50-200 employees"
    company_description: Optional[str] = None
    tech_stack: Optional[str] = None  # known systems they use
    recent_company_news: Optional[str] = None

    # Pain points / triggers
    pain_points: list[str] = field(default_factory=list)
    trigger_event: Optional[str] = None  # e.g. "just raised Series B", "new CFO"

    # Sender context
    sender_name: str = ""
    sender_title: str = ""
    sender_company: str = ""
    sender_email: str = ""
    calendar_link: Optional[str] = None

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def build_context_summary(self) -> str:
        """Build a rich context string for the AI to use when generating emails."""
        parts = [
            f"Prospect: {self.full_name}",
            f"Title: {self.title}",
            f"Company: {self.company_name}",
        ]

        if self.industry:
            parts.append(f"Industry: {self.industry}")
        if self.company_size:
            parts.append(f"Company Size: {self.company_size}")
        if self.company_description:
            parts.append(f"Company Description: {self.company_description}")
        if self.tech_stack:
            parts.append(f"Current Tech Stack: {self.tech_stack}")
        if self.linkedin_summary:
            parts.append(f"LinkedIn Summary: {self.linkedin_summary}")
        if self.years_experience:
            parts.append(f"Experience: {self.years_experience}")
        if self.recent_activity:
            parts.append(f"Recent LinkedIn Activity: {self.recent_activity}")
        if self.recent_company_news:
            parts.append(f"Recent Company News: {self.recent_company_news}")
        if self.pain_points:
            parts.append(f"Known Pain Points: {', '.join(self.pain_points)}")
        if self.trigger_event:
            parts.append(f"Trigger Event: {self.trigger_event}")

        return "\n".join(parts)
