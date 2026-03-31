"""Pydantic models for API request/response validation."""

from typing import Optional

from pydantic import BaseModel


class ProspectRequest(BaseModel):
    """Input schema — two required URLs plus optional personalization."""

    linkedin_url: str
    company_url: str
    pain_points: Optional[str] = None
    tone: Optional[str] = None
    call_to_action: Optional[str] = None
    additional_context: Optional[str] = None


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
