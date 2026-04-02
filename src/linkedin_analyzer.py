"""LinkedIn profile analyzer — extracts structured role insights from pasted profile text."""

import json

import anthropic

ANALYSIS_PROMPT = """You are an expert at analyzing LinkedIn profiles to extract actionable sales intelligence.

Given pasted LinkedIn profile content, extract and infer:

1. **Role Analysis**: What does this person actually DO day-to-day? What are their responsibilities and priorities based on their title, experience, and summary?

2. **Decision-Making Power**: Are they a decision-maker, influencer, or end-user for ERP/business software purchases? What budget authority do they likely have?

3. **Pain Points**: Based on their role, industry, and company context, what operational pain points would resonate most? Be specific — not generic.

4. **Career Context**: Are they new to the role (likely making changes), a veteran (focused on optimization), or recently promoted (proving themselves)?

5. **Messaging Hooks**: What specific details from their profile can be referenced naturally in outreach? (Shared connections, posts, accomplishments, education, certifications, volunteer work)

6. **Communication Style**: Based on their profile tone, industry, and seniority — should emails be formal, conversational, technical, or executive-brief?

Return a JSON object with this structure:
{
  "name": "First Last",
  "title": "Their current title",
  "company": "Current company name",
  "role_summary": "2-3 sentence plain-English summary of what they do and what they care about",
  "seniority_level": "C-Suite | VP | Director | Manager | Individual Contributor",
  "decision_role": "Decision Maker | Influencer | Champion | End User",
  "years_in_role": "estimated years in current position, or 'New' if < 6 months",
  "career_trajectory": "Rising fast | Steady | Career change | New to role",
  "top_pain_points": ["pain point 1", "pain point 2", "pain point 3"],
  "messaging_hooks": ["specific hook 1", "specific hook 2", "specific hook 3"],
  "recommended_tone": "Conversational | Executive-brief | Technical | Consultative",
  "recommended_angle": "1-2 sentence suggestion for the best outreach angle for this specific person",
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
    """Analyze pasted LinkedIn profile text and return structured role insights.

    Args:
        profile_text: Raw text pasted from a LinkedIn profile (headline, about,
                      experience, education, etc.)
        api_key: Anthropic API key.

    Returns:
        Dict with structured profile analysis including role_summary,
        pain_points, messaging_hooks, recommended_tone, etc.
    """
    client = anthropic.Anthropic(api_key=api_key)

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        system=ANALYSIS_PROMPT,
        messages=[{
            "role": "user",
            "content": f"Analyze this LinkedIn profile and extract sales intelligence:\n\n{profile_text}",
        }],
    )

    response_text = message.content[0].text.strip()

    if response_text.startswith("```"):
        response_text = response_text.split("\n", 1)[1]
        response_text = response_text.rsplit("```", 1)[0].strip()

    return json.loads(response_text)


def build_profile_context_block(analysis: dict) -> str:
    """Convert a profile analysis dict into a context block for email generation.

    This produces a rich text summary that gets injected into the email
    generation prompt so the AI can write highly tailored messaging.
    """
    lines = []

    lines.append(f"PROSPECT PROFILE (from LinkedIn analysis):")
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
