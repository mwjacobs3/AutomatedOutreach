"""Pydantic models for API request/response validation."""

from pydantic import BaseModel


class ProspectRequest(BaseModel):
    """Input schema — just two URLs, the AI does the rest."""

    linkedin_url: str
    company_url: str


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
