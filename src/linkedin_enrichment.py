"""Fetch LinkedIn profile data via Proxycurl API."""

import logging
from dataclasses import dataclass
from typing import Optional

import requests

logger = logging.getLogger(__name__)

PROXYCURL_PERSON_ENDPOINT = "https://nubela.co/proxycurl/api/v2/linkedin"


@dataclass
class LinkedInProfile:
    """Structured data returned from a LinkedIn profile lookup."""

    full_name: str
    first_name: str
    last_name: str
    headline: Optional[str] = None
    summary: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    current_company: Optional[str] = None
    current_title: Optional[str] = None
    industry: Optional[str] = None
    connections: Optional[int] = None


def fetch_linkedin_profile(
    linkedin_url: str,
    proxycurl_api_key: str,
    timeout: int = 30,
) -> Optional[LinkedInProfile]:
    """Fetch a LinkedIn profile via Proxycurl and return structured data.

    Returns None if the request fails or the profile cannot be found.
    """
    headers = {"Authorization": f"Bearer {proxycurl_api_key}"}
    params = {
        "url": linkedin_url,
        "fallback_to_cache": "on-error",
        "use_cache": "if-present",
    }

    try:
        resp = requests.get(
            PROXYCURL_PERSON_ENDPOINT,
            params=params,
            headers=headers,
            timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        logger.warning("Proxycurl request failed for %s: %s", linkedin_url, exc)
        return None

    full_name = data.get("full_name") or ""
    if not full_name:
        return None

    name_parts = full_name.strip().split()
    first_name = name_parts[0] if name_parts else ""
    last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

    # Extract current position from experiences list
    current_title = None
    current_company = None
    experiences = data.get("experiences") or []
    for exp in experiences:
        if exp.get("ends_at") is None:  # current role has no end date
            current_title = exp.get("title")
            current_company = exp.get("company")
            break

    return LinkedInProfile(
        full_name=full_name.strip(),
        first_name=first_name,
        last_name=last_name,
        headline=data.get("headline"),
        summary=data.get("summary"),
        city=data.get("city"),
        country=data.get("country_full_name"),
        current_company=current_company,
        current_title=current_title,
        industry=data.get("industry"),
        connections=data.get("connections"),
    )
