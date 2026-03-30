"""AutomatedOutreach — AI-Powered NetSuite Touch Plan Generator."""

import json
import os

import anthropic
import streamlit as st

# --- Optional Supabase integration ---
try:
    from supabase import create_client

    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False


def get_supabase_client():
    """Return a Supabase client if credentials are configured."""
    url = st.secrets.get("SUPABASE_URL", os.environ.get("SUPABASE_URL"))
    key = st.secrets.get("SUPABASE_KEY", os.environ.get("SUPABASE_KEY"))
    if SUPABASE_AVAILABLE and url and key:
        return create_client(url, key)
    return None


def save_to_supabase(client, linkedin_url, company_url, result):
    """Persist a generated sequence to the Supabase 'sequences' table."""
    client.table("sequences").insert({
        "linkedin_url": linkedin_url,
        "company_url": company_url,
        "prospect_name": result.get("prospect_name", ""),
        "company_name": result.get("company", ""),
        "emails": result.get("emails", []),
    }).execute()


def load_history(client, limit=10):
    """Load recent sequences from Supabase."""
    resp = (
        client.table("sequences")
        .select("*")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return resp.data


# ---------------------------------------------------------------------------
# Email generation (reuses core logic from src/email_generator.py)
# ---------------------------------------------------------------------------

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


def generate_sequence(linkedin_url: str, company_url: str, api_key: str) -> dict:
    """Generate a 6-email personalized touch plan from two URLs."""
    client = anthropic.Anthropic(api_key=api_key)

    user_prompt = f"""I need you to generate a 6-email NetSuite outreach sequence for a prospect.

Here are the only two inputs I have:
- LinkedIn Profile URL: {linkedin_url}
- Company Website URL: {company_url}

Based on the URLs, infer what you can about:
- The prospect's name, title, and role (extract from LinkedIn slug)
- The company name, industry, size, and what they do (extract from domain)
- Likely pain points that NetSuite could solve for this type of company/role

Then generate a personalized 6-email outreach sequence.

Return your response as a JSON object with this exact structure:
{{
  "prospect_name": "First Last",
  "company": "Company Name",
  "emails": [
    {{
      "sequence_number": 1,
      "send_day": 1,
      "subject": "subject line here",
      "body": "Full email body here. Use actual line breaks for paragraphs.",
      "purpose": "Relevant Opener"
    }},
    ... (6 emails total with send_days: 1, 3, 7, 10, 14, 21)
  ]
}}

Return ONLY the JSON object, no other text."""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=SEQUENCE_STRATEGY,
        messages=[{"role": "user", "content": user_prompt}],
    )

    response_text = message.content[0].text.strip()

    if response_text.startswith("```"):
        response_text = response_text.split("\n", 1)[1]
        response_text = response_text.rsplit("```", 1)[0].strip()

    return json.loads(response_text)


# ---------------------------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="AutomatedOutreach — NetSuite Touch Plans",
    page_icon="📧",
    layout="wide",
)

# --- Custom CSS ---
st.markdown("""
<style>
    .main .block-container { max-width: 900px; padding-top: 2rem; }
    .email-card {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border-left: 4px solid #2563eb;
    }
    .email-header {
        display: flex;
        gap: 0.5rem;
        margin-bottom: 0.75rem;
        flex-wrap: wrap;
    }
    .badge {
        background: #2563eb;
        color: white;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-outline {
        background: transparent;
        color: #2563eb;
        border: 1px solid #2563eb;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
    }
    .subject-line {
        font-weight: 600;
        font-size: 1.05rem;
        margin-bottom: 0.5rem;
        color: #1a1a1a;
    }
    .email-body {
        white-space: pre-wrap;
        line-height: 1.6;
        color: #333;
    }
    div.stButton > button[kind="primary"] {
        background-color: #2563eb;
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.title("AutomatedOutreach")
st.markdown("Generate a personalized 6-email NetSuite touch plan from just a LinkedIn profile and company website.")

# --- API key handling ---
api_key = st.secrets.get("ANTHROPIC_API_KEY", os.environ.get("ANTHROPIC_API_KEY", ""))
if not api_key:
    api_key = st.sidebar.text_input("Anthropic API Key", type="password", help="Required to generate sequences")
    if not api_key:
        st.info("Enter your Anthropic API key in the sidebar to get started.")
        st.stop()

# --- Supabase client ---
sb = get_supabase_client()

# --- Input form ---
with st.form("prospect_form"):
    col1, col2 = st.columns(2)
    with col1:
        linkedin_url = st.text_input(
            "LinkedIn Profile URL",
            placeholder="https://linkedin.com/in/jane-doe",
        )
    with col2:
        company_url = st.text_input(
            "Company Website URL",
            placeholder="https://acmecorp.com",
        )
    submitted = st.form_submit_button("Generate Touch Plan", type="primary")

# --- Generation ---
if submitted:
    if not linkedin_url or not company_url:
        st.error("Please fill in both fields.")
    else:
        with st.spinner("Generating your personalized 6-email touch plan..."):
            try:
                result = generate_sequence(linkedin_url, company_url, api_key)
                st.session_state["result"] = result
                st.session_state["linkedin_url"] = linkedin_url
                st.session_state["company_url"] = company_url

                # Save to Supabase if available
                if sb:
                    try:
                        save_to_supabase(sb, linkedin_url, company_url, result)
                    except Exception:
                        pass  # Don't block UI if save fails

            except json.JSONDecodeError:
                st.error("Failed to parse the AI response. Please try again.")
            except anthropic.APIError as e:
                st.error(f"API error: {e.message}")
            except Exception as e:
                st.error(f"Something went wrong: {e}")

# --- Display results ---
if "result" in st.session_state:
    result = st.session_state["result"]
    prospect_name = result.get("prospect_name", "Prospect")
    company = result.get("company", "Company")

    st.markdown("---")
    st.subheader(f"Touch Plan for {prospect_name} at {company}")

    for email in result.get("emails", []):
        seq = email["sequence_number"]
        day = email["send_day"]
        purpose = email["purpose"]
        subject = email["subject"]
        body = email["body"]

        st.markdown(
            f"""<div class="email-card">
            <div class="email-header">
                <span class="badge">Email {seq}</span>
                <span class="badge-outline">Day {day}</span>
                <span class="badge-outline">{purpose}</span>
            </div>
            <div class="subject-line">Subject: {subject}</div>
            <div class="email-body">{body}</div>
            </div>""",
            unsafe_allow_html=True,
        )

        # Copy buttons
        col_subj, col_body, _ = st.columns([1, 1, 2])
        with col_subj:
            st.code(subject, language=None)
        with col_body:
            st.code(body, language=None)

    st.markdown("---")
    if st.button("Start New Touch Plan"):
        for key in ["result", "linkedin_url", "company_url"]:
            st.session_state.pop(key, None)
        st.rerun()

# --- Sidebar: History (Supabase only) ---
if sb:
    with st.sidebar:
        st.markdown("### Recent Touch Plans")
        try:
            history = load_history(sb)
            if history:
                for row in history:
                    label = f"{row.get('prospect_name', 'Unknown')} — {row.get('company_name', '')}"
                    if st.sidebar.button(label, key=row["id"]):
                        st.session_state["result"] = {
                            "prospect_name": row["prospect_name"],
                            "company": row["company_name"],
                            "emails": row["emails"],
                        }
                        st.rerun()
            else:
                st.caption("No history yet.")
        except Exception:
            st.caption("History unavailable.")
