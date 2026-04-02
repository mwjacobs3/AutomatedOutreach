"""LinkedIn profile analyzer — fetches public profile data and extracts structured role insights."""

import json
import re
import logging

import anthropic
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# --- Web fetching helpers ---

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def _extract_slug(linkedin_url: str) -> str:
    """Pull the profile slug (e.g. 'jane-doe-12345') from a LinkedIn URL."""
    match = re.search(r"linkedin\.com/in/([^/?#]+)", linkedin_url)
    return match.group(1).strip("/") if match else ""


def _slug_to_name(slug: str) -> str:
    """Convert a slug like 'jane-doe-12345' into 'Jane Doe'."""
    parts = re.sub(r"-?\d+$", "", slug).split("-")
    return " ".join(p.capitalize() for p in parts if p)


def _fetch_google_results(query: str, num_results: int = 5) -> list[dict]:
    """Search Google and return a list of {title, snippet, url} dicts."""
    results = []
    try:
        resp = requests.get(
            "https://www.google.com/search",
            params={"q": query, "num": num_results, "hl": "en"},
            headers=_HEADERS,
            timeout=10,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        for g in soup.select("div.g, div[data-sokoban-container]"):
            title_el = g.select_one("h3")
            snippet_el = g.select_one("div[data-sncf], span.st, div.VwiC3b")
            link_el = g.select_one("a[href]")
            if title_el:
                results.append({
                    "title": title_el.get_text(strip=True),
                    "snippet": snippet_el.get_text(strip=True) if snippet_el else "",
                    "url": link_el["href"] if link_el else "",
                })
    except Exception as e:
        logger.warning("Google search failed: %s", e)

    return results


def _fetch_linkedin_page(linkedin_url: str) -> str:
    """Attempt to fetch the public LinkedIn profile page directly."""
    try:
        resp = requests.get(linkedin_url, headers=_HEADERS, timeout=10)
        if resp.status_code == 200 and "authwall" not in resp.url:
            soup = BeautifulSoup(resp.text, "html.parser")
            # LinkedIn public profiles have structured data in JSON-LD
            for script in soup.find_all("script", type="application/ld+json"):
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and data.get("@type") == "Person":
                        parts = []
                        if data.get("name"):
                            parts.append(f"Name: {data['name']}")
                        if data.get("jobTitle"):
                            parts.append(f"Title: {data['jobTitle']}")
                        if data.get("worksFor"):
                            org = data["worksFor"]
                            if isinstance(org, dict):
                                parts.append(f"Company: {org.get('name', '')}")
                            elif isinstance(org, list) and org:
                                parts.append(f"Company: {org[0].get('name', '')}")
                        if data.get("description"):
                            parts.append(f"About: {data['description']}")
                        if data.get("address"):
                            addr = data["address"]
                            if isinstance(addr, dict):
                                parts.append(f"Location: {addr.get('addressLocality', '')} {addr.get('addressRegion', '')} {addr.get('addressCountry', '')}")
                        if parts:
                            return "\n".join(parts)
                except (json.JSONDecodeError, TypeError):
                    continue

            # Fallback: extract visible text from profile sections
            text_parts = []
            for tag in soup.select("h1, h2, .top-card-layout__headline, .top-card-layout__summary, section.experience, section.education"):
                text_parts.append(tag.get_text(separator="\n", strip=True))
            if text_parts:
                return "\n\n".join(text_parts)
    except Exception as e:
        logger.warning("Direct LinkedIn fetch failed: %s", e)

    return ""


def fetch_profile_data(linkedin_url: str) -> str:
    """Gather publicly available profile information from multiple sources.

    Tries:
      1. Direct LinkedIn page fetch (JSON-LD structured data)
      2. Google search for the LinkedIn profile
      3. Google search for the person + company

    Returns combined text for the AI to analyze.
    """
    slug = _extract_slug(linkedin_url)
    name_guess = _slug_to_name(slug)
    collected = []

    # Source 1: Direct LinkedIn fetch
    direct_text = _fetch_linkedin_page(linkedin_url)
    if direct_text:
        collected.append(f"=== LinkedIn Profile Page ===\n{direct_text}")

    # Source 2: Google search for the LinkedIn profile
    if slug:
        google_results = _fetch_google_results(
            f"site:linkedin.com/in/{slug} {name_guess}"
        )
        for r in google_results:
            if "linkedin.com" in r.get("url", ""):
                parts = []
                if r["title"]:
                    parts.append(r["title"])
                if r["snippet"]:
                    parts.append(r["snippet"])
                if parts:
                    collected.append(f"=== Google/LinkedIn Result ===\n" + "\n".join(parts))

    # Source 3: Broader search for the person
    if name_guess:
        broader_results = _fetch_google_results(f'"{name_guess}" linkedin current role company')
        for r in broader_results:
            if r["snippet"]:
                collected.append(f"=== Web Result: {r['title']} ===\n{r['snippet']}")

    if not collected:
        # Last resort: at least give the AI the name from the slug
        if name_guess:
            collected.append(f"LinkedIn profile slug: {slug}\nInferred name: {name_guess}")

    return "\n\n".join(collected)


# --- AI analysis ---

ANALYSIS_PROMPT = """You are an expert at analyzing LinkedIn profiles to extract actionable sales intelligence.

Given publicly available information about a prospect (from their LinkedIn profile, Google search results, etc.), extract and infer:

1. **Role Analysis**: What does this person actually DO day-to-day? What are their responsibilities and priorities based on their title, experience, and summary?

2. **Decision-Making Power**: Are they a decision-maker, influencer, or end-user for ERP/business software purchases? What budget authority do they likely have?

3. **Pain Points**: Based on their role, industry, and company context, what operational pain points would resonate most? Be specific — not generic.

4. **Career Context**: Are they new to the role (likely making changes), a veteran (focused on optimization), or recently promoted (proving themselves)?

5. **Messaging Hooks**: What specific details from their profile can be referenced naturally in outreach? (Accomplishments, career moves, education, certifications, volunteer work, posts)

6. **Communication Style**: Based on their profile tone, industry, and seniority — should emails be formal, conversational, technical, or executive-brief?

IMPORTANT: Work with whatever information is available. If data is limited, make reasonable inferences based on the title, company, and industry — but note what is inferred vs. confirmed. Even partial information (just a name and title) is enough to generate useful insights.

Return a JSON object with this structure:
{
  "name": "First Last",
  "title": "Their current title",
  "company": "Current company name",
  "role_summary": "2-3 sentence plain-English summary of what they do and what they care about",
  "seniority_level": "C-Suite | VP | Director | Manager | Individual Contributor",
  "decision_role": "Decision Maker | Influencer | Champion | End User",
  "years_in_role": "estimated years in current position, or 'Unknown'",
  "career_trajectory": "Rising fast | Steady | Career change | New to role | Unknown",
  "top_pain_points": ["pain point 1", "pain point 2", "pain point 3"],
  "messaging_hooks": ["specific hook 1", "specific hook 2", "specific hook 3"],
  "recommended_tone": "Conversational | Executive-brief | Technical | Consultative",
  "recommended_angle": "1-2 sentence suggestion for the best outreach angle for this specific person",
  "data_confidence": "High | Medium | Low",
  "key_facts": {
    "industry": "their industry",
    "company_size": "if discernible",
    "location": "if listed",
    "education": "notable education if relevant",
    "certifications": "relevant certifications",
    "mutual_interests": "anything that could build rapport"
  }
}

Return ONLY the JSON object."""


def analyze_linkedin_profile(profile_text: str, api_key: str) -> dict:
    """Analyze profile text (fetched or pasted) and return structured role insights."""
    client = anthropic.Anthropic(api_key=api_key)

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        system=ANALYSIS_PROMPT,
        messages=[{
            "role": "user",
            "content": f"Analyze this prospect's LinkedIn profile data and extract sales intelligence:\n\n{profile_text}",
        }],
    )

    response_text = message.content[0].text.strip()

    if response_text.startswith("```"):
        response_text = response_text.split("\n", 1)[1]
        response_text = response_text.rsplit("```", 1)[0].strip()

    return json.loads(response_text)


def analyze_from_url(linkedin_url: str, api_key: str) -> dict:
    """End-to-end: fetch public data for a LinkedIn URL, then analyze it.

    Returns the structured analysis dict. Raises ValueError if no data found.
    """
    profile_data = fetch_profile_data(linkedin_url)

    if not profile_data.strip():
        raise ValueError(
            "Could not retrieve any public data for this LinkedIn profile. "
            "The profile may be private or the URL may be incorrect."
        )

    return analyze_linkedin_profile(profile_data, api_key)


def build_profile_context_block(analysis: dict) -> str:
    """Convert a profile analysis dict into a context block for email generation."""
    lines = []

    lines.append("PROSPECT PROFILE (from LinkedIn analysis):")
    lines.append(f"- Name: {analysis.get('name', 'Unknown')}")
    lines.append(f"- Title: {analysis.get('title', 'Unknown')}")
    lines.append(f"- Company: {analysis.get('company', 'Unknown')}")
    lines.append(f"- Role Summary: {analysis.get('role_summary', '')}")
    lines.append(f"- Seniority: {analysis.get('seniority_level', 'Unknown')}")
    lines.append(f"- Decision Role: {analysis.get('decision_role', 'Unknown')}")
    lines.append(f"- Career Trajectory: {analysis.get('career_trajectory', 'Unknown')}")
    lines.append(f"- Time in Role: {analysis.get('years_in_role', 'Unknown')}")

    pain_points = analysis.get("top_pain_points", [])
    if pain_points:
        lines.append(f"- Key Pain Points: {'; '.join(pain_points)}")

    hooks = analysis.get("messaging_hooks", [])
    if hooks:
        lines.append(f"- Messaging Hooks (reference these naturally): {'; '.join(hooks)}")

    lines.append(f"- Recommended Tone: {analysis.get('recommended_tone', 'Conversational')}")
    lines.append(f"- Recommended Angle: {analysis.get('recommended_angle', '')}")

    key_facts = analysis.get("key_facts", {})
    if key_facts:
        for k, v in key_facts.items():
            if v:
                lines.append(f"- {k.replace('_', ' ').title()}: {v}")

    return "\n".join(lines)
