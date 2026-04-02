"""AutomatedOutreach — AI-Powered NetSuite Touch Plan Generator."""

import json
import os

import anthropic
import streamlit as st

from src.linkedin_analyzer import analyze_from_url, build_profile_context_block

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


def generate_sequence(
    linkedin_url: str,
    company_url: str,
    api_key: str,
    industry: str = "",
    company_size: str = "",
    prospect_role: str = "",
    current_system: str = "",
    pain_point: str = "",
    trigger_event: str = "",
    tone: str = "Conversational",
    sender_name: str = "",
    sender_title: str = "",
    sender_company: str = "",
    sender_email: str = "",
    linkedin_profile_context: str = "",
) -> dict:
    """Generate a 6-email personalized touch plan with context parameters."""
    client = anthropic.Anthropic(api_key=api_key)

    # Build context block from parameters
    context_lines = []
    if industry and industry != "Auto-detect from website":
        context_lines.append(f"- Industry: {industry}")
    if company_size and company_size != "Auto-detect":
        context_lines.append(f"- Company size: {company_size}")
    if prospect_role and prospect_role != "Auto-detect from LinkedIn":
        context_lines.append(f"- Prospect's role/persona: {prospect_role}")
    if current_system and current_system != "Unknown":
        context_lines.append(f"- Current ERP/accounting system: {current_system}")
    if pain_point and pain_point != "Auto-detect":
        context_lines.append(f"- Primary pain point to focus on: {pain_point}")
    if trigger_event and trigger_event != "None":
        context_lines.append(f"- Recent trigger event: {trigger_event}")

    context_block = ""
    if context_lines:
        context_block = "\n\nADDITIONAL CONTEXT (use this to sharpen personalization):\n" + "\n".join(context_lines)

    # LinkedIn profile analysis block (rich insights from pasted profile)
    profile_block = ""
    if linkedin_profile_context:
        profile_block = f"\n\n{linkedin_profile_context}\n\nIMPORTANT: Use the LinkedIn profile analysis above as your PRIMARY source for personalization. Reference specific details from their profile naturally — their role, career trajectory, pain points, and messaging hooks. The profile analysis has already identified the best outreach angle and tone."

    tone_instruction = ""
    if tone and tone != "Conversational":
        tone_instruction = f"\n\nTONE: Write in a {tone.lower()} tone throughout all emails."

    sender_block = ""
    if sender_name:
        sig_parts = [sender_name]
        if sender_title:
            sig_parts.append(sender_title)
        if sender_company:
            sig_parts.append(sender_company)
        if sender_email:
            sig_parts.append(sender_email)
        sender_block = "\n\nSENDER SIGNATURE (use this in every email):\n" + "\n".join(sig_parts)

    user_prompt = f"""I need you to generate a 6-email NetSuite outreach sequence for a prospect.

PROSPECT INPUTS:
- LinkedIn Profile URL: {linkedin_url}
- Company Website URL: {company_url}
{profile_block}{context_block}{tone_instruction}{sender_block}

Generate a personalized 6-email outreach sequence that feels specific to THIS person and company.

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
    st.error("Anthropic API key not configured. Please add it to Streamlit secrets.")
    st.stop()

# --- Supabase client ---
sb = get_supabase_client()

# --- Prospect Info & LinkedIn Analysis (outside form) ---
st.markdown(
    """<div style="background:#fff;border:1.5px solid #d1d5db;border-radius:12px;
    padding:1.5rem;margin-bottom:0.5rem;box-shadow:0 1px 4px rgba(0,0,0,0.06)">
    <p style="font-weight:600;font-size:1.05rem;margin-bottom:0.75rem;color:#374151">
    Prospect Info</p></div>""",
    unsafe_allow_html=True,
)
col1, col2 = st.columns(2)
with col1:
    linkedin_url = st.text_input(
        "LinkedIn Profile URL *",
        placeholder="https://linkedin.com/in/jane-doe",
    )
with col2:
    company_url = st.text_input(
        "Company Website URL *",
        placeholder="https://acmecorp.com",
    )

# --- Analyze Profile button ---
if linkedin_url and "linkedin.com/in/" in linkedin_url:
    if st.button("Analyze LinkedIn Profile", type="secondary"):
        with st.spinner("Searching for public profile data and analyzing..."):
            try:
                analysis = analyze_from_url(linkedin_url, api_key)
                st.session_state["linkedin_analysis"] = analysis
            except ValueError as e:
                st.warning(str(e))
            except Exception as e:
                st.error(f"Profile analysis failed: {e}")

# --- Display analysis results ---
if "linkedin_analysis" in st.session_state:
    analysis = st.session_state["linkedin_analysis"]
    confidence = analysis.get("data_confidence", "Unknown")
    confidence_color = {"High": "#16a34a", "Medium": "#d97706", "Low": "#dc2626"}.get(confidence, "#6b7280")

    with st.expander("LinkedIn Profile Analysis", expanded=True):
        st.markdown(
            f'<span style="background:{confidence_color};color:white;padding:2px 8px;'
            f'border-radius:8px;font-size:0.75rem;font-weight:600">'
            f'Data Confidence: {confidence}</span>',
            unsafe_allow_html=True,
        )
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f"**{analysis.get('name', 'Unknown')}** — {analysis.get('title', '')}")
            st.markdown(f"*{analysis.get('role_summary', '')}*")
            st.markdown(f"**Seniority:** {analysis.get('seniority_level', 'N/A')} · **Decision Role:** {analysis.get('decision_role', 'N/A')}")
            st.markdown(f"**Career:** {analysis.get('career_trajectory', 'N/A')} · **Time in Role:** {analysis.get('years_in_role', 'N/A')}")
        with col_b:
            st.markdown("**Top Pain Points:**")
            for pp in analysis.get("top_pain_points", []):
                st.markdown(f"- {pp}")
            st.markdown(f"**Recommended Tone:** {analysis.get('recommended_tone', 'N/A')}")
            st.markdown(f"**Best Angle:** {analysis.get('recommended_angle', 'N/A')}")
        if analysis.get("messaging_hooks"):
            st.markdown("**Messaging Hooks:**")
            for hook in analysis["messaging_hooks"]:
                st.markdown(f"- {hook}")

st.markdown("")  # spacer

# --- Input form (targeting options + generate button) ---
with st.form("prospect_form"):

    # ── Optional: Personalization Options ──
    with st.expander("Personalization Options  *(optional — increase targeting accuracy)*"):
        st.markdown("##### Targeting Parameters")
        col3, col4, col5 = st.columns(3)
        with col3:
            industry = st.selectbox("Industry", [
                "Auto-detect from website",
                "Manufacturing",
                "Wholesale & Distribution",
                "Retail & E-Commerce",
                "Software & Technology",
                "Professional Services",
                "Financial Services",
                "Healthcare & Life Sciences",
                "Food & Beverage",
                "Nonprofit",
                "Media & Publishing",
                "Energy & Utilities",
                "Construction & Real Estate",
                "Transportation & Logistics",
                "Education",
                "Other",
            ])
        with col4:
            company_size = st.selectbox("Company Size", [
                "Auto-detect",
                "Startup (1-50)",
                "Small Business (51-200)",
                "Mid-Market (201-1,000)",
                "Upper Mid-Market (1,001-5,000)",
                "Enterprise (5,000+)",
            ])
        with col5:
            prospect_role = st.selectbox("Prospect Role", [
                "Auto-detect from LinkedIn",
                "CFO / VP Finance",
                "Controller / Accounting Manager",
                "CIO / IT Director",
                "COO / VP Operations",
                "CEO / Founder / Owner",
                "Director of Supply Chain",
                "VP of Sales / Revenue Ops",
                "Procurement / Purchasing Manager",
            ])

        col6, col7, col8 = st.columns(3)
        with col6:
            current_system = st.selectbox("Current System", [
                "Unknown",
                "QuickBooks",
                "Sage (Intacct / 100 / 300)",
                "SAP Business One / ByDesign",
                "Microsoft Dynamics (GP / NAV / 365 BC)",
                "Acumatica",
                "Epicor",
                "Infor",
                "Spreadsheets / Manual Processes",
                "Custom / Legacy System",
                "Other",
            ])
        with col7:
            pain_point = st.selectbox("Primary Pain Point", [
                "Auto-detect",
                "Manual processes & data entry",
                "Lack of real-time financial visibility",
                "Scaling beyond current system",
                "Multi-entity / multi-currency complexity",
                "Disconnected systems (ERP, CRM, e-commerce)",
                "Compliance & audit readiness",
                "Inventory & supply chain management",
                "Revenue recognition challenges",
                "Slow month-end close",
                "Outgrowing QuickBooks",
            ])
        with col8:
            trigger_event = st.selectbox("Trigger Event", [
                "None",
                "Recent funding round",
                "New CFO / Finance hire",
                "Acquisition or merger",
                "IPO preparation",
                "Rapid headcount growth",
                "New product line / expansion",
                "Compliance deadline approaching",
                "Current vendor contract renewal",
                "Recent negative Glassdoor / press about ops",
            ])

        st.markdown("##### Tone & Sender")
        col9, col10 = st.columns(2)
        with col9:
            tone = st.selectbox("Email Tone", [
                "Conversational",
                "Professional / Formal",
                "Casual / Friendly",
                "Executive / Direct",
                "Consultative / Advisory",
            ])
        with col10:
            st.caption("Sender info appears in the email signature")

        col11, col12, col13, col14 = st.columns(4)
        with col11:
            sender_name = st.text_input("Your Name", placeholder="Matt Jacobs")
        with col12:
            sender_title = st.text_input("Your Title", placeholder="Account Executive")
        with col13:
            sender_company = st.text_input("Your Company", placeholder="NetSuite")
        with col14:
            sender_email = st.text_input("Your Email", placeholder="mjacobs@netsuite.com")

    submitted = st.form_submit_button("Generate Touch Plan", type="primary")

# --- Generation ---
if submitted:
    if not linkedin_url or not company_url:
        st.error("Please fill in both the LinkedIn URL and Company Website URL.")
    else:
        with st.spinner("Generating your personalized 6-email touch plan..."):
            try:
                # Build LinkedIn profile context if analysis exists
                profile_context = ""
                if "linkedin_analysis" in st.session_state:
                    profile_context = build_profile_context_block(st.session_state["linkedin_analysis"])

                result = generate_sequence(
                    linkedin_url=linkedin_url,
                    company_url=company_url,
                    api_key=api_key,
                    industry=industry,
                    company_size=company_size,
                    prospect_role=prospect_role,
                    current_system=current_system,
                    pain_point=pain_point,
                    trigger_event=trigger_event,
                    tone=tone,
                    sender_name=sender_name,
                    sender_title=sender_title,
                    sender_company=sender_company,
                    sender_email=sender_email,
                    linkedin_profile_context=profile_context,
                )
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
        for key in ["result", "linkedin_url", "company_url", "linkedin_analysis"]:
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
