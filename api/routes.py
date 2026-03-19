"""API route handlers."""

import os

from fastapi import APIRouter, HTTPException

from src.prospect import Prospect
from src.email_generator import generate_email_sequence

from .schemas import ProspectRequest, EmailSequenceResponse, GeneratedEmailResponse

router = APIRouter()


@router.post("/generate", response_model=EmailSequenceResponse)
def generate_cadence(request: ProspectRequest):
    """Generate a 6-email outreach cadence from prospect details."""

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not configured")

    # Convert Pydantic model → Prospect dataclass
    prospect = Prospect(**request.model_dump())

    try:
        sequence = generate_email_sequence(prospect, api_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email generation failed: {e}")

    return EmailSequenceResponse(
        prospect_name=prospect.full_name,
        company=prospect.company_name,
        emails=[
            GeneratedEmailResponse(
                sequence_number=email.sequence_number,
                send_day=email.send_day,
                subject=email.subject,
                body=email.body,
                purpose=email.purpose,
            )
            for email in sequence.emails
        ],
    )
