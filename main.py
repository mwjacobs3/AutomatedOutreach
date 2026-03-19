"""
AutomatedOutreach — AI-powered NetSuite email sequence generator.

Usage:
    python main.py                     # Interactive mode
    python main.py --from-file prospect.json  # Load prospect from JSON file

This tool generates a personalized 6-email outreach sequence for a prospect
using AI (Claude), then saves it as a cadence with optional Gmail draft creation.
"""

import argparse
import json
import os
import sys

from dotenv import load_dotenv

from src.prospect import Prospect
from src.email_generator import generate_email_sequence
from src.cadence import Cadence
from src.gmail_drafter import save_drafts_locally

load_dotenv()


def prompt_input(label: str, required: bool = False, default: str = "") -> str:
    """Prompt the user for input."""
    suffix = " (required)" if required else f" [{default}]" if default else ""
    while True:
        value = input(f"  {label}{suffix}: ").strip()
        if not value and default:
            return default
        if not value and required:
            print(f"  → {label} is required.")
            continue
        return value


def prompt_list(label: str) -> list[str]:
    """Prompt the user for a comma-separated list."""
    raw = input(f"  {label} (comma-separated, or blank): ").strip()
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def collect_prospect_interactive() -> Prospect:
    """Gather prospect details interactively from the terminal."""
    print("\n── Prospect Contact Info ──")
    first_name = prompt_input("First name", required=True)
    last_name = prompt_input("Last name", required=True)
    email = prompt_input("Email", required=True)
    title = prompt_input("Job title", required=True)
    company_name = prompt_input("Company name", required=True)

    print("\n── LinkedIn & Company Context ──")
    print("  (Paste key details from their LinkedIn profile and company page)")
    linkedin_url = prompt_input("LinkedIn profile URL")
    linkedin_summary = prompt_input("LinkedIn headline/summary")
    years_experience = prompt_input("Years of experience")
    recent_activity = prompt_input("Recent LinkedIn activity (posts, job changes, etc.)")

    company_url = prompt_input("Company website URL")
    company_linkedin_url = prompt_input("Company LinkedIn URL")
    industry = prompt_input("Industry")
    company_size = prompt_input("Company size (e.g. 50-200 employees)")
    company_description = prompt_input("Company description (what they do)")
    tech_stack = prompt_input("Known tech stack / current ERP")
    recent_company_news = prompt_input("Recent company news (funding, growth, etc.)")

    print("\n── Pain Points & Triggers ──")
    pain_points = prompt_list("Pain points")
    trigger_event = prompt_input("Trigger event (e.g. 'just raised Series B')")

    print("\n── Your Info (Sender) ──")
    sender_name = prompt_input("Your name", required=True)
    sender_title = prompt_input("Your title")
    sender_company = prompt_input("Your company")
    sender_email = prompt_input("Your email")
    calendar_link = prompt_input("Calendar booking link")

    return Prospect(
        first_name=first_name,
        last_name=last_name,
        email=email,
        title=title,
        company_name=company_name,
        linkedin_url=linkedin_url or None,
        linkedin_summary=linkedin_summary or None,
        years_experience=years_experience or None,
        recent_activity=recent_activity or None,
        company_url=company_url or None,
        company_linkedin_url=company_linkedin_url or None,
        industry=industry or None,
        company_size=company_size or None,
        company_description=company_description or None,
        tech_stack=tech_stack or None,
        recent_company_news=recent_company_news or None,
        pain_points=pain_points,
        trigger_event=trigger_event or None,
        sender_name=sender_name,
        sender_title=sender_title,
        sender_company=sender_company,
        sender_email=sender_email,
        calendar_link=calendar_link or None,
    )


def load_prospect_from_file(filepath: str) -> Prospect:
    """Load prospect data from a JSON file."""
    with open(filepath) as f:
        data = json.load(f)
    return Prospect(**data)


def main():
    parser = argparse.ArgumentParser(description="Generate AI-powered NetSuite outreach sequences")
    parser.add_argument("--from-file", help="Load prospect from a JSON file")
    parser.add_argument("--output-dir", default="data/cadences", help="Directory to save cadence files")
    parser.add_argument("--drafts", action="store_true", help="Also save individual draft files")
    args = parser.parse_args()

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set. Copy .env.example to .env and add your key.")
        sys.exit(1)

    # Collect prospect info
    if args.from_file:
        print(f"Loading prospect from {args.from_file}...")
        prospect = load_prospect_from_file(args.from_file)
    else:
        print("╔══════════════════════════════════════════════════╗")
        print("║  NetSuite Outreach — AI Email Sequence Generator ║")
        print("╚══════════════════════════════════════════════════╝")
        prospect = collect_prospect_interactive()

    print(f"\n⏳ Generating 6-email sequence for {prospect.full_name}...")

    # Generate the sequence
    sequence = generate_email_sequence(prospect, api_key)

    # Display the sequence
    print("\n" + sequence.display())

    # Create the cadence
    cadence = Cadence.from_sequence(sequence)
    cadence_path = cadence.save(args.output_dir)
    print(f"\n✓ Cadence saved to: {cadence_path}")
    print(cadence.display_schedule())

    # Optionally save individual draft files
    if args.drafts:
        draft_paths = save_drafts_locally(cadence)
        print(f"\n✓ {len(draft_paths)} draft files saved:")
        for p in draft_paths:
            print(f"  → {p}")

    print("\n── Next Steps ──")
    print("  • Review and edit the emails in the cadence JSON file")
    print("  • Use Claude Code with Gmail MCP to create Gmail drafts")
    print("  • Or use the draft files to manually copy into your email client")
    print()


if __name__ == "__main__":
    main()
