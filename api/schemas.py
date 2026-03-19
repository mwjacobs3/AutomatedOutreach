"""Pydantic models for API request/response validation."""

from pydantic import BaseModel
from typing import Optional


class ProspectRequest(BaseModel):
    """Input schema — mirrors the Prospect dataclass fields."""

    # Contact basics (required)
    first_name: str
    last_name: str
    email: str
    title: str
    company_name: str

    # LinkedIn profile context (user pastes text)
    linkedin_url: Optional[str] = None
    linkedin_summary: Optional[str] = None
    years_experience: Optional[str] = None
    recent_activity: Optional[str] = None

    # Company context (user pastes text)
    company_url: Optional[str] = None
    company_linkedin_url: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    company_description: Optional[str] = None
    tech_stack: Optional[str] = None
    recent_company_news: Optional[str] = None

    # Pain points / triggers
    pain_points: list[str] = []
    trigger_event: Optional[str] = None

    # Sender context
    sender_name: str = ""
    sender_title: str = ""
    sender_company: str = ""
    sender_email: str = ""
    calendar_link: Optional[str] = None


class GeneratedEmailResponse(BaseModel):
    """A single email in the generated sequence."""

    sequence_number: int
    send_day: int
    subject: str
    body: str
    purpose: str


class EmailSequenceResponse(BaseModel):
    """The full 6-email cadence returned to the frontend."""

    prospect_name: str
    company: str
    emails: list[GeneratedEmailResponse]
