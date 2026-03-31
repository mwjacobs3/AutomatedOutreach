"""Tests for LinkedIn profile enrichment via Proxycurl."""

from unittest.mock import patch, MagicMock

from src.linkedin_enrichment import fetch_linkedin_profile, LinkedInProfile


MOCK_PROXYCURL_RESPONSE = {
    "full_name": "Jane Doe",
    "headline": "VP of Finance at GrowthCo",
    "summary": "Experienced finance leader with 15 years in SaaS.",
    "city": "San Francisco",
    "country_full_name": "United States",
    "industry": "Software",
    "connections": 500,
    "experiences": [
        {
            "title": "VP of Finance",
            "company": "GrowthCo Industries",
            "ends_at": None,
        },
        {
            "title": "Controller",
            "company": "OldCorp",
            "ends_at": {"day": 1, "month": 6, "year": 2020},
        },
    ],
}


class TestFetchLinkedInProfile:
    @patch("src.linkedin_enrichment.requests.get")
    def test_returns_profile_on_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = MOCK_PROXYCURL_RESPONSE
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        profile = fetch_linkedin_profile(
            "https://linkedin.com/in/jane-doe", "test-key"
        )

        assert isinstance(profile, LinkedInProfile)
        assert profile.full_name == "Jane Doe"
        assert profile.first_name == "Jane"
        assert profile.last_name == "Doe"
        assert profile.current_title == "VP of Finance"
        assert profile.current_company == "GrowthCo Industries"
        assert profile.headline == "VP of Finance at GrowthCo"
        assert profile.industry == "Software"

    @patch("src.linkedin_enrichment.requests.get")
    def test_sends_correct_headers(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = MOCK_PROXYCURL_RESPONSE
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        fetch_linkedin_profile("https://linkedin.com/in/jane-doe", "my-secret-key")

        call_kwargs = mock_get.call_args.kwargs
        assert call_kwargs["headers"]["Authorization"] == "Bearer my-secret-key"

    @patch("src.linkedin_enrichment.requests.get")
    def test_returns_none_on_http_error(self, mock_get):
        import requests as req
        mock_get.side_effect = req.RequestException("Connection failed")

        profile = fetch_linkedin_profile(
            "https://linkedin.com/in/jane-doe", "test-key"
        )
        assert profile is None

    @patch("src.linkedin_enrichment.requests.get")
    def test_returns_none_when_no_name(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"full_name": "", "experiences": []}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        profile = fetch_linkedin_profile(
            "https://linkedin.com/in/unknown", "test-key"
        )
        assert profile is None

    @patch("src.linkedin_enrichment.requests.get")
    def test_handles_no_current_role(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "full_name": "John Smith",
            "headline": "Looking for opportunities",
            "experiences": [
                {
                    "title": "Engineer",
                    "company": "PastCo",
                    "ends_at": {"day": 1, "month": 1, "year": 2023},
                }
            ],
        }
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        profile = fetch_linkedin_profile(
            "https://linkedin.com/in/john-smith", "test-key"
        )
        assert profile.full_name == "John Smith"
        assert profile.current_title is None
        assert profile.current_company is None

    @patch("src.linkedin_enrichment.requests.get")
    def test_handles_three_part_name(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "full_name": "Mary Jane Watson",
            "experiences": [],
        }
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        profile = fetch_linkedin_profile(
            "https://linkedin.com/in/mary-jane-watson", "test-key"
        )
        assert profile.first_name == "Mary"
        assert profile.last_name == "Jane Watson"
