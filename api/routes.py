"""API route handlers."""

import os

from fastapi import APIRouter, HTTPException

from src.email_generator import generate_email_sequence_from_urls

from .schemas import ProspectRequest, EmailSequenceResponse, GeneratedEmailResponse

router = APIRouter()


@router.post("/generate", response_model=EmailSequenceResponse)
def generate_cadence(request: ProspectRequest):
    """Generate a 6-email outreach cadence from LinkedIn and company URLs."""

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not configured")

    try:
        result = generate_email_sequence_from_urls(
            linkedin_url=request.linkedin_url,
            company_url=request.company_url,
            api_key=api_key,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email generation failed: {e}")

    return EmailSequenceResponse(
        prospect_name=result["prospect_name"],
        company=result["company"],
        emails=[
            GeneratedEmailResponse(
                sequence_number=email["sequence_number"],
                send_day=email["send_day"],
                subject=email["subject"],
                body=email["body"],
                purpose=email["purpose"],
            )
            for email in result["emails"]
        ],
    )
