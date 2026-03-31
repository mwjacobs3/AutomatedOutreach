"""Tests for API routes with mocked email generation."""

import json
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from api.main import app


MOCK_GENERATE_RESULT = {
    "prospect_name": "John Smith",
    "company": "Acme Corp",
    "emails": [
        {
            "sequence_number": i,
            "send_day": day,
            "subject": f"Subject {i}",
            "body": f"Body {i}",
            "purpose": purpose,
        }
        for i, day, purpose in [
            (1, 1, "Relevant Opener"),
            (2, 3, "Value Drop"),
            (3, 7, "Pain Agitator"),
            (4, 10, "Social Proof"),
            (5, 14, "Breakup Tease"),
            (6, 21, "Final Value Add"),
        ]
    ],
}


@pytest.fixture
def client():
    return TestClient(app)


class TestGenerateEndpoint:
    @patch("api.routes.generate_email_sequence_from_urls", return_value=MOCK_GENERATE_RESULT)
    @patch("api.routes.os.getenv", return_value="fake-api-key")
    def test_success_with_required_fields(self, mock_getenv, mock_generate, client):
        resp = client.post("/api/generate", json={
            "linkedin_url": "https://linkedin.com/in/john-smith",
            "company_url": "https://acmecorp.com",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["prospect_name"] == "John Smith"
        assert data["company"] == "Acme Corp"
        assert len(data["emails"]) == 6

    @patch("api.routes.generate_email_sequence_from_urls", return_value=MOCK_GENERATE_RESULT)
    @patch("api.routes.os.getenv", return_value="fake-api-key")
    def test_success_with_optional_fields(self, mock_getenv, mock_generate, client):
        resp = client.post("/api/generate", json={
            "linkedin_url": "https://linkedin.com/in/john-smith",
            "company_url": "https://acmecorp.com",
            "tone": "consultative",
            "pain_points": "Manual processes",
            "call_to_action": "demo",
            "additional_context": "Just raised Series B",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["emails"]) == 6

    def test_missing_linkedin_url_returns_422(self, client):
        resp = client.post("/api/generate", json={
            "company_url": "https://acmecorp.com",
        })
        assert resp.status_code == 422

    def test_missing_company_url_returns_422(self, client):
        resp = client.post("/api/generate", json={
            "linkedin_url": "https://linkedin.com/in/test",
        })
        assert resp.status_code == 422

    def test_empty_body_returns_422(self, client):
        resp = client.post("/api/generate", json={})
        assert resp.status_code == 422

    @patch("api.routes.os.getenv", return_value=None)
    def test_missing_api_key_returns_500(self, mock_getenv, client):
        resp = client.post("/api/generate", json={
            "linkedin_url": "https://linkedin.com/in/test",
            "company_url": "https://example.com",
        })
        assert resp.status_code == 500
        assert "ANTHROPIC_API_KEY" in resp.json()["detail"]

    @patch("api.routes.generate_email_sequence_from_urls", side_effect=Exception("API timeout"))
    @patch("api.routes.os.getenv", return_value="fake-api-key")
    def test_generation_error_returns_500(self, mock_getenv, mock_generate, client):
        resp = client.post("/api/generate", json={
            "linkedin_url": "https://linkedin.com/in/test",
            "company_url": "https://example.com",
        })
        assert resp.status_code == 500
        assert "Email generation failed" in resp.json()["detail"]

    @patch("api.routes.generate_email_sequence_from_urls", return_value=MOCK_GENERATE_RESULT)
    @patch("api.routes.os.getenv", return_value="fake-api-key")
    def test_response_email_structure(self, mock_getenv, mock_generate, client):
        resp = client.post("/api/generate", json={
            "linkedin_url": "https://linkedin.com/in/john-smith",
            "company_url": "https://acmecorp.com",
        })
        data = resp.json()
        email = data["emails"][0]
        assert "sequence_number" in email
        assert "send_day" in email
        assert "subject" in email
        assert "body" in email
        assert "purpose" in email
        assert email["sequence_number"] == 1
        assert email["send_day"] == 1
