"""AI-powered email sequence generator using Claude API."""

import json
from dataclasses import dataclass

import anthropic

from .prospect import Prospect

SEQUENCE_STRATEGY = """You are an expert B2B sales copywriter specializing in NetSuite ERP outreach.
You write emails that are short, direct, personalized, and feel like they came from a real human — not a template.

You are generating a 6-email sequence for a prospect. Each email has a specific purpose:

Email 1 — "The Relevant Opener" (Day 1)
- Reference something specific about their company, role, or recent activity
- Briefly connect it to a NetSuite-relevant pain point
- End with a soft question, not a hard CTA
- 3-5 sentences max

Email 2 — "The Value Drop" (Day 3)
- Share a specific insight, stat, or mini case study relevant to their industry
- Show you understand their world without being salesy
- 3-4 sentences max

Email 3 — "The Pain Agitator" (Day 7)
- Call out a specific operational challenge companies like theirs face
- Connect it to the cost of inaction (time, money, errors)
- Light mention of how NetSuite addresses it
- 4-5 sentences max

Email 4 — "The Social Proof" (Day 10)
- Lead with a result a similar company achieved with NetSuite
- Make it concrete (numbers, timeframes, outcomes)
- Ask if they'd be open to seeing how it could work for them
- 3-4 sentences max

Email 5 — "The Breakup Tease" (Day 14)
- Acknowledge you've reached out a few times
- Restate value in one sentence
- Give them an easy out ("If this isn't a priority, no worries — just let me know")
- 2-3 sentences max

Email 6 — "The Final Value Add" (Day 21)
- Share one last piece of genuinely useful content (report, checklist, article)
- No pressure, pure value
- Leave the door open
- 2-3 sentences max

RULES:
- Each email must feel like a DIFFERENT conversation, not a repeat
- Use the prospect's first name naturally
- Reference specific details about their company, role, industry, or recent activity
- Keep subject lines short (3-7 words), curiosity-driven, lowercase feels more personal
- NEVER use buzzwords like "synergy", "leverage", "circle back", "touch base"
- NEVER use generic openers like "Hope this finds you well" or "I wanted to reach out"
- Write like a smart, helpful human — not a sales robot
- Each email should stand on its own (prospect may not have read the others)
- Include a clear but natural signature with sender info
"""


@dataclass
class GeneratedEmail:
    """A single generated email in the sequence."""
    sequence_number: int
    send_day: int
    subject: str
    body: str
    purpose: str


@dataclass
class EmailSequence:
    """A complete 6-email sequence for a prospect."""
    prospect: Prospect
    emails: list[GeneratedEmail]

    def display(self) -> str:
        """Format the full sequence for display."""
        lines = [
            f"{'='*60}",
            f"Email Sequence for {self.prospect.full_name}",
            f"{self.prospect.title} at {self.prospect.company_name}",
            f"{'='*60}",
        ]
        for email in self.emails:
            lines.extend([
                "",
                f"--- Email {email.sequence_number} | Day {email.send_day} | {email.purpose} ---",
                f"Subject: {email.subject}",
                "",
                email.body,
                "",
            ])
        return "\n".join(lines)


def generate_email_sequence(prospect: Prospect, api_key: str) -> EmailSequence:
    """Generate a 6-email personalized sequence for a prospect using Claude."""

    client = anthropic.Anthropic(api_key=api_key)

    context = prospect.build_context_summary()

    sender_block = ""
    if prospect.sender_name:
        sender_parts = [prospect.sender_name]
        if prospect.sender_title:
            sender_parts.append(prospect.sender_title)
        if prospect.sender_company:
            sender_parts.append(prospect.sender_company)
        if prospect.sender_email:
            sender_parts.append(prospect.sender_email)
        if prospect.calendar_link:
            sender_parts.append(f"Book a time: {prospect.calendar_link}")
        sender_block = f"\n\nSender signature info:\n" + "\n".join(sender_parts)

    user_prompt = f"""Generate a 6-email outreach sequence for this prospect about NetSuite.

PROSPECT CONTEXT:
{context}
{sender_block}

Return your response as a JSON array with exactly 6 objects, each with these fields:
- "sequence_number": (1-6)
- "send_day": (1, 3, 7, 10, 14, 21)
- "subject": the email subject line
- "body": the full email body (plain text, use \\n for line breaks)
- "purpose": short label for the email's strategy (e.g. "Relevant Opener")

Return ONLY the JSON array, no other text."""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=SEQUENCE_STRATEGY,
        messages=[{"role": "user", "content": user_prompt}],
    )

    response_text = message.content[0].text.strip()

    # Parse JSON - handle potential markdown code fences
    if response_text.startswith("```"):
        response_text = response_text.split("\n", 1)[1]
        response_text = response_text.rsplit("```", 1)[0].strip()

    raw_emails = json.loads(response_text)

    emails = [
        GeneratedEmail(
            sequence_number=e["sequence_number"],
            send_day=e["send_day"],
            subject=e["subject"],
            body=e["body"],
            purpose=e["purpose"],
        )
        for e in raw_emails
    ]

    return EmailSequence(prospect=prospect, emails=emails)
