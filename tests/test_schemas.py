"""Tests for API request/response schema validation."""

import pytest
from pydantic import ValidationError

from api.schemas import ProspectRequest, EmailSequenceResponse, GeneratedEmailResponse


class TestProspectRequest:
    def test_required_fields_only(self):
        req = ProspectRequest(
            linkedin_url="https://linkedin.com/in/john-smith",
            company_url="https://example.com",
        )
        assert req.linkedin_url == "https://linkedin.com/in/john-smith"
        assert req.company_url == "https://example.com"
        assert req.pain_points is None
        assert req.tone is None
        assert req.call_to_action is None
        assert req.additional_context is None

    def test_all_optional_fields(self):
        req = ProspectRequest(
            linkedin_url="https://linkedin.com/in/jane-doe",
            company_url="https://acme.com",
            pain_points="Manual processes, disconnected systems",
            tone="consultative",
            call_to_action="demo",
            additional_context="Recently acquired a competitor",
        )
        assert req.pain_points == "Manual processes, disconnected systems"
        assert req.tone == "consultative"
        assert req.call_to_action == "demo"
        assert req.additional_context == "Recently acquired a competitor"

    def test_missing_linkedin_url_fails(self):
        with pytest.raises(ValidationError):
            ProspectRequest(company_url="https://example.com")

    def test_missing_company_url_fails(self):
        with pytest.raises(ValidationError):
            ProspectRequest(linkedin_url="https://linkedin.com/in/test")

    def test_partial_optional_fields(self):
        req = ProspectRequest(
            linkedin_url="https://linkedin.com/in/test",
            company_url="https://example.com",
            tone="formal",
        )
        assert req.tone == "formal"
        assert req.pain_points is None
        assert req.call_to_action is None


class TestGeneratedEmailResponse:
    def test_valid_email(self):
        email = GeneratedEmailResponse(
            sequence_number=1,
            send_day=1,
            subject="Quick question about operations",
            body="Hi Sarah,\n\nNoticed GrowthCo is expanding...",
            purpose="Relevant Opener",
        )
        assert email.sequence_number == 1
        assert email.send_day == 1


class TestEmailSequenceResponse:
    def test_full_response(self):
        emails = [
            GeneratedEmailResponse(
                sequence_number=i,
                send_day=day,
                subject=f"Subject {i}",
                body=f"Body {i}",
                purpose=f"Purpose {i}",
            )
            for i, day in enumerate([1, 3, 7, 10, 14, 21], start=1)
        ]
        resp = EmailSequenceResponse(
            prospect_name="Sarah Chen",
            company="GrowthCo Industries",
            emails=emails,
        )
        assert resp.prospect_name == "Sarah Chen"
        assert len(resp.emails) == 6
        assert resp.emails[0].send_day == 1
        assert resp.emails[-1].send_day == 21
