"""Tests for email generation with mocked Claude API responses."""

import json
from unittest.mock import patch, MagicMock

from src.prospect import Prospect
from src.email_generator import (
    generate_email_sequence,
    generate_email_sequence_from_urls,
    GeneratedEmail,
    EmailSequence,
)


MOCK_EMAILS_JSON = json.dumps([
    {
        "sequence_number": i,
        "send_day": day,
        "subject": f"Subject {i}",
        "body": f"Hi Sarah,\n\nEmail body {i}.",
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
])

MOCK_URL_RESPONSE_JSON = json.dumps({
    "prospect_name": "John Smith",
    "company": "Acme Corp",
    "emails": [
        {
            "sequence_number": i,
            "send_day": day,
            "subject": f"Subject {i}",
            "body": f"Hi John,\n\nEmail body {i}.",
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
})


def _mock_claude_response(text):
    """Create a mock Anthropic API response."""
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text=text)]
    return mock_msg


def _make_prospect(**overrides):
    defaults = dict(
        first_name="Sarah",
        last_name="Chen",
        email="sarah@example.com",
        title="VP of Finance",
        company_name="GrowthCo Industries",
    )
    defaults.update(overrides)
    return Prospect(**defaults)


class TestGenerateEmailSequence:
    @patch("src.email_generator.anthropic.Anthropic")
    def test_returns_six_emails(self, mock_anthropic_cls):
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.return_value = _mock_claude_response(MOCK_EMAILS_JSON)

        prospect = _make_prospect()
        result = generate_email_sequence(prospect, api_key="test-key")

        assert isinstance(result, EmailSequence)
        assert len(result.emails) == 6
        assert result.prospect.full_name == "Sarah Chen"

    @patch("src.email_generator.anthropic.Anthropic")
    def test_email_sequence_numbers(self, mock_anthropic_cls):
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.return_value = _mock_claude_response(MOCK_EMAILS_JSON)

        result = generate_email_sequence(_make_prospect(), api_key="test-key")
        for i, email in enumerate(result.emails, start=1):
            assert email.sequence_number == i

    @patch("src.email_generator.anthropic.Anthropic")
    def test_send_days(self, mock_anthropic_cls):
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.return_value = _mock_claude_response(MOCK_EMAILS_JSON)

        result = generate_email_sequence(_make_prospect(), api_key="test-key")
        expected_days = [1, 3, 7, 10, 14, 21]
        actual_days = [e.send_day for e in result.emails]
        assert actual_days == expected_days

    @patch("src.email_generator.anthropic.Anthropic")
    def test_handles_markdown_fenced_json(self, mock_anthropic_cls):
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        fenced = f"```json\n{MOCK_EMAILS_JSON}\n```"
        mock_client.messages.create.return_value = _mock_claude_response(fenced)

        result = generate_email_sequence(_make_prospect(), api_key="test-key")
        assert len(result.emails) == 6

    @patch("src.email_generator.anthropic.Anthropic")
    def test_linkedin_context_sent_to_claude(self, mock_anthropic_cls):
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.return_value = _mock_claude_response(MOCK_EMAILS_JSON)

        prospect = _make_prospect(
            linkedin_url="https://linkedin.com/in/sarahchen",
            linkedin_summary="Finance leader with 15+ years",
            recent_activity="Posted about month-end close challenges",
        )
        generate_email_sequence(prospect, api_key="test-key")

        call_args = mock_client.messages.create.call_args
        user_msg = call_args.kwargs["messages"][0]["content"]
        assert "Finance leader with 15+ years" in user_msg
        assert "month-end close" in user_msg

    @patch("src.email_generator.anthropic.Anthropic")
    def test_pain_points_sent_to_claude(self, mock_anthropic_cls):
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.return_value = _mock_claude_response(MOCK_EMAILS_JSON)

        prospect = _make_prospect(
            pain_points=["Manual consolidation", "No real-time inventory"],
        )
        generate_email_sequence(prospect, api_key="test-key")

        call_args = mock_client.messages.create.call_args
        user_msg = call_args.kwargs["messages"][0]["content"]
        assert "Manual consolidation" in user_msg
        assert "No real-time inventory" in user_msg

    @patch("src.email_generator.anthropic.Anthropic")
    def test_display_output(self, mock_anthropic_cls):
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.return_value = _mock_claude_response(MOCK_EMAILS_JSON)

        result = generate_email_sequence(_make_prospect(), api_key="test-key")
        display = result.display()
        assert "Sarah Chen" in display
        assert "Email 1" in display
        assert "Email 6" in display


class TestGenerateEmailSequenceFromUrls:
    @patch("src.email_generator.anthropic.Anthropic")
    def test_returns_prospect_and_emails(self, mock_anthropic_cls):
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.return_value = _mock_claude_response(MOCK_URL_RESPONSE_JSON)

        result = generate_email_sequence_from_urls(
            linkedin_url="https://linkedin.com/in/john-smith",
            company_url="https://acmecorp.com",
            api_key="test-key",
        )

        assert result["prospect_name"] == "John Smith"
        assert result["company"] == "Acme Corp"
        assert len(result["emails"]) == 6

    @patch("src.email_generator.anthropic.Anthropic")
    def test_linkedin_url_passed_to_prompt(self, mock_anthropic_cls):
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.return_value = _mock_claude_response(MOCK_URL_RESPONSE_JSON)

        generate_email_sequence_from_urls(
            linkedin_url="https://linkedin.com/in/jane-doe-cfo",
            company_url="https://bigcorp.com",
            api_key="test-key",
        )

        call_args = mock_client.messages.create.call_args
        user_msg = call_args.kwargs["messages"][0]["content"]
        assert "https://linkedin.com/in/jane-doe-cfo" in user_msg
        assert "https://bigcorp.com" in user_msg

    @patch("src.email_generator.anthropic.Anthropic")
    def test_handles_markdown_fenced_json(self, mock_anthropic_cls):
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        fenced = f"```json\n{MOCK_URL_RESPONSE_JSON}\n```"
        mock_client.messages.create.return_value = _mock_claude_response(fenced)

        result = generate_email_sequence_from_urls(
            linkedin_url="https://linkedin.com/in/test",
            company_url="https://test.com",
            api_key="test-key",
        )
        assert len(result["emails"]) == 6

    @patch("src.email_generator.anthropic.Anthropic")
    def test_email_purposes_present(self, mock_anthropic_cls):
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.return_value = _mock_claude_response(MOCK_URL_RESPONSE_JSON)

        result = generate_email_sequence_from_urls(
            linkedin_url="https://linkedin.com/in/test",
            company_url="https://test.com",
            api_key="test-key",
        )
        purposes = [e["purpose"] for e in result["emails"]]
        assert "Relevant Opener" in purposes
        assert "Value Drop" in purposes
        assert "Final Value Add" in purposes
