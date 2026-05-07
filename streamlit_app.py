"""AutomatedOutreach - AI-Powered NetSuite Touch Plan Generator."""

import json
import os
import re
import time
from html.parser import HTMLParser

import anthropic
import requests
import streamlit as st

# ---------------------------------------------------------------------------
# Industry / Subindustry taxonomy (NetSuite-relevant verticals)
# ---------------------------------------------------------------------------

INDUSTRIES = {
    "Manufacturing": [
        "Discrete Manufacturing",
        "Process Manufacturing",
        "Contract Manufacturing",
        "Industrial Equipment & Machinery",
        "Automotive Parts & Accessories",
        "Electronics & High-Tech Manufacturing",
        "Plastics, Rubber & Packaging",
        "Aerospace & Defense",
        "Chemicals",
        "Other Manufacturing",
    ],
    "Wholesale & Distribution": [
        "General Wholesale",
        "Industrial & Building Materials",
        "Food & Beverage Distribution",
        "Electronics & Components Distribution",
        "Medical & Pharmaceutical Distribution",
        "Automotive Parts Distribution",
        "Janitorial & Facilities Supplies",
        "Apparel & Fashion Wholesale",
        "Other Wholesale & Distribution",
    ],
    "Retail & E-Commerce": [
        "Direct-to-Consumer (DTC)",
        "Omnichannel Retail",
        "Apparel & Fashion",
        "Health & Beauty",
        "Home Goods & Furniture",
        "Sporting Goods & Outdoor",
        "Electronics & Consumer Tech",
        "Subscription & Membership",
        "Marketplace Seller (Amazon, Shopify)",
        "Other Retail & E-Commerce",
    ],
    "Software & Technology": [
        "SaaS / Cloud Software",
        "IT Services & Consulting",
        "Managed Services Provider (MSP)",
        "Cybersecurity",
        "Hardware / IoT",
        "Fintech",
        "HealthTech / MedTech",
        "AdTech / MarTech",
        "AI / Machine Learning",
        "Other Software & Technology",
    ],
    "Professional Services": [
        "Consulting (Management / Strategy)",
        "Accounting & CPA Firms",
        "Legal Services",
        "Marketing & Advertising Agencies",
        "Architecture & Engineering",
        "Staffing & Recruiting",
        "IT Professional Services",
        "Research & Advisory",
        "Other Professional Services",
    ],
    "Financial Services": [
        "Banking & Lending",
        "Insurance",
        "Investment Management & PE/VC",
        "Payments & Processing",
        "Wealth Management",
        "Commercial Real Estate Finance",
        "Fintech (see also Software & Technology)",
        "Other Financial Services",
    ],
    "Healthcare & Life Sciences": [
        "Medical Devices & Equipment",
        "Pharmaceuticals",
        "Biotech & Life Sciences",
        "Healthcare Services & Clinics",
        "Health & Wellness Products",
        "Home Health & Senior Care",
        "Dental & Vision",
        "Other Healthcare & Life Sciences",
    ],
    "Food & Beverage": [
        "Food Manufacturing & CPG",
        "Beverage & Brewing",
        "Restaurants & Food Service",
        "Specialty & Organic Foods",
        "Agriculture & Farming",
        "Pet Food & Animal Nutrition",
        "Other Food & Beverage",
    ],
    "Nonprofit & Education": [
        "Nonprofit / NGO",
        "Higher Education",
        "K-12 Education",
        "EdTech",
        "Foundations & Grantmaking",
        "Other Nonprofit & Education",
    ],
    "Media & Publishing": [
        "Digital Media & Content",
        "Publishing & Print",
        "Advertising & Entertainment",
        "Gaming",
        "Sports & Events",
        "Other Media & Publishing",
    ],
    "Energy & Utilities": [
        "Oil & Gas",
        "Renewable Energy & Solar",
        "Utilities",
        "Mining & Natural Resources",
        "Environmental Services",
        "Other Energy & Utilities",
    ],
    "Construction & Real Estate": [
        "General Contracting",
        "Specialty Trade Contractors (HVAC, Electrical, Plumbing)",
        "Commercial Real Estate / Property Management",
        "Residential Construction & Development",
        "Building Materials & Supplies",
        "Other Construction & Real Estate",
    ],
    "Transportation & Logistics": [
        "Freight & Trucking",
        "Third-Party Logistics (3PL)",
        "Warehousing & Fulfillment",
        "Shipping & Maritime",
        "Aviation & Airlines",
        "Last-Mile Delivery",
        "Other Transportation & Logistics",
    ],
}

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


def save_to_supabase(client, prospect_name, company, result):
    """Persist a generated sequence to the Supabase 'sequences' table."""
    client.table("sequences").insert({
        "prospect_name": result.get("prospect_name", prospect_name),
        "company_name": result.get("company", company),
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
# Company website research
# ---------------------------------------------------------------------------


class _TextExtractor(HTMLParser):
    """Lightweight HTML-to-text extractor using the stdlib."""

    _SKIP_TAGS = {"script", "style", "noscript", "svg", "head"}

    def __init__(self):
        super().__init__()
        self._pieces: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in self._SKIP_TAGS:
            self._skip_depth += 1

    def handle_endtag(self, tag):
        if tag in self._SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data):
        if self._skip_depth == 0:
            self._pieces.append(data)

    def get_text(self) -> str:
        raw = " ".join(self._pieces)
        return re.sub(r"\s+", " ", raw).strip()


def scrape_company_page(url: str, timeout: int = 10) -> str:
    """Fetch a company URL and return extracted text (max ~6 000 chars)."""
    try:
        resp = requests.get(
            url,
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0 (compatible; AutomatedOutreach/1.0)"},
        )
        resp.raise_for_status()
    except Exception:
        return ""

    extractor = _TextExtractor()
    extractor.feed(resp.text)
    text = extractor.get_text()
    return text[:6000]


def summarize_company(client: anthropic.Anthropic, company_name: str, page_text: str) -> str:
    """Use Claude to distill raw website text into a concise company profile."""
    if not page_text or len(page_text) < 50:
        return ""

    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=400,
        messages=[{
            "role": "user",
            "content": f"""Summarize this company's website text into a short research brief for a salesperson.
Include: what the company does, products/services, target market, approximate size if mentioned, any recent news or initiatives, and technology/tools they mention.
Be specific and factual. Only include what's actually on the page. 3-5 bullet points max.

Company: {company_name}
Website text:
{page_text}""",
        }],
    )
    return msg.content[0].text.strip()


# ---------------------------------------------------------------------------
# Email generation
# ---------------------------------------------------------------------------

SEQUENCE_STRATEGY = """You are a real salesperson who writes like a human being, not a copywriter or AI.

Your job is to write a 6-email outreach sequence for a NetSuite prospect. These emails need to sound like they were typed quickly by a busy sales rep who genuinely wants to help, not crafted by a marketing team.

WRITING STYLE:
- Short sentences. Fragments are fine.
- No em dashes. Use commas, periods, or just start a new sentence.
- Never start with "I hope this finds you well" or "I wanted to reach out" or "I came across your profile"
- Don't use words like "streamline", "leverage", "synergy", "optimize", "drive efficiency", "empower", or "transform"
- Don't use phrases like "in today's fast-paced", "are you struggling with", "what if I told you", or "imagine a world where"
- Write the way you'd text a coworker, but professional
- Vary sentence length. Mix short punchy lines with slightly longer ones.
- Use "you" and "your" more than "we" and "our"
- Sound curious, not pushy
- No exclamation marks in subject lines
- Subject lines should be lowercase, 3-6 words, look like a real person wrote them

INDUSTRY EXPERTISE:
When given an industry and subindustry, you MUST write like someone who actually knows that specific vertical. This means:
- Use the terminology people in that industry actually use (not generic business speak)
- Reference real challenges, metrics, and processes specific to that subindustry
- Mention the types of systems, workflows, and pain points that are unique to their world
- Name specific scenarios that a person in their role at that type of company would instantly recognize
- If they're in food manufacturing, talk about lot traceability and FSMA compliance, not "operational efficiency"
- If they're in wholesale distribution, talk about pick/pack/ship accuracy and vendor chargebacks, not "improving processes"
- If they're in SaaS, talk about ASC 606, deferred revenue, and cohort metrics, not "financial visibility"
- The more specific you are to their actual day-to-day, the more real the email sounds

EMAIL SEQUENCE:

Email 1, "Relevant Opener" (Day 1)
- Mention something specific to their role and industry
- Connect it to a real problem NetSuite solves for companies like theirs
- End with a question
- 3-4 sentences

Email 2, "Value Drop" (Day 3)
- Share a stat, benchmark, or quick story relevant to their specific subindustry
- No selling, just be helpful and knowledgeable about their world
- 3-4 sentences

Email 3, "Pain Agitator" (Day 7)
- Name a specific industry problem using their language
- Talk about what it actually costs them (time, money, headaches, compliance risk)
- Mention how NetSuite helps without being a brochure
- 4-5 sentences

Email 4, "Social Proof" (Day 10)
- Lead with a result from a similar company in their industry
- Use specific numbers and industry-relevant metrics
- Ask if they'd want to see how it could work for them
- 3-4 sentences

Email 5, "Breakup Tease" (Day 14)
- Keep it short
- Acknowledge you've emailed a few times
- Make it easy to say no
- 2-3 sentences

Email 6, "Final Value Add" (Day 21)
- Share something genuinely useful for their industry (a report, benchmark, checklist)
- Zero pressure
- Leave the door open
- 2-3 sentences

CRITICAL RULES:
- NO em dashes anywhere. Not in emails, not in subject lines. Use periods or commas instead.
- Every email must read like a different person could have written it. Don't repeat structures.
- Use their first name once, naturally. Don't force it.
- Each email stands alone. The prospect may not have read the others.
- Include sender signature info if provided.
- If industry and subindustry are provided, EVERY email must contain at least one reference specific to that vertical. Generic emails are a failure.
"""


def generate_sequence(
    api_key: str,
    prospect_name: str,
    prospect_role: str,
    company_name: str,
    industry: str = "",
    subindustry: str = "",
    company_url: str = "",
    pain_point: str = "",
    tone: str = "Conversational",
    sender_name: str = "",
    sender_title: str = "",
    sender_company: str = "",
    sender_email: str = "",
    company_research: str = "",
) -> dict:
    """Generate a 6-email personalized touch plan."""
    client = anthropic.Anthropic(api_key=api_key)

    context_lines = [
        f"- Prospect name: {prospect_name}",
        f"- Role: {prospect_role}",
        f"- Company: {company_name}",
    ]
    if industry:
        context_lines.append(f"- Industry: {industry}")
    if subindustry:
        context_lines.append(f"- Subindustry: {subindustry}")
    if company_url:
        context_lines.append(f"- Company website: {company_url}")
    if pain_point:
        context_lines.append(f"- Primary pain point: {pain_point}")

    context_block = "\n".join(context_lines)

    research_block = ""
    if company_research:
        research_block = f"""

COMPANY RESEARCH (from their website — use these real details in your emails):
{company_research}

IMPORTANT: Weave specific details from the research above into the emails naturally. Reference their actual products, services, markets, or initiatives instead of making generic guesses. This is what makes the emails feel like you actually did your homework."""

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
        sender_block = "\n\nSENDER SIGNATURE (use in every email):\n" + "\n".join(sig_parts)

    user_prompt = f"""Write a 6-email NetSuite outreach sequence for this prospect.

PROSPECT:
{context_block}
{tone_instruction}{sender_block}{research_block}

Make every email feel like it was written by a real person who knows their industry inside and out. Use terminology and references that someone in their specific subindustry would immediately recognize. No em dashes anywhere. No generic business language.

Return your response as a JSON object with this exact structure:
{{
  "prospect_name": "{prospect_name}",
  "company": "{company_name}",
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

    max_retries = 3
    for attempt in range(max_retries):
        try:
            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system=SEQUENCE_STRATEGY,
                messages=[{"role": "user", "content": user_prompt}],
            )
            break
        except anthropic.APIStatusError as e:
            if e.status_code == 529 and attempt < max_retries - 1:
                time.sleep(2 ** (attempt + 1))
                continue
            raise

    response_text = message.content[0].text.strip()

    if response_text.startswith("```"):
        response_text = response_text.split("\n", 1)[1]
        response_text = response_text.rsplit("```", 1)[0].strip()

    return json.loads(response_text)


# ---------------------------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="AutomatedOutreach",
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
        margin-bottom: 0.5rem;
        border-left: 4px solid #2563eb;
    }
    .email-header {
        display: flex;
        gap: 0.5rem;
        margin-bottom: 0.75rem;
        flex-wrap: wrap;
        align-items: center;
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
        line-height: 1.7;
        color: #333;
        font-size: 0.95rem;
    }
    div.stButton > button[kind="primary"] {
        background-color: #2563eb;
        width: 100%;
    }
    .result-header {
        padding: 0.5rem 0;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.title("AutomatedOutreach")
st.caption("AI-powered personalized NetSuite outreach sequences. Fill in the prospect details and get a 6-email touch plan in seconds.")

# --- API key handling ---
api_key = st.secrets.get("ANTHROPIC_API_KEY", os.environ.get("ANTHROPIC_API_KEY", ""))
if not api_key:
    st.error("Anthropic API key not configured. Please add it to Streamlit secrets.")
    st.stop()

# --- Supabase client ---
sb = get_supabase_client()

# --- Collapse form when results are showing ---
_has_result = "result" in st.session_state
_form_container = st.expander("New Touch Plan", expanded=not _has_result) if _has_result else st.container()

with _form_container:
    # Industry selection (outside form so subindustry updates dynamically)
    st.markdown("##### Industry & Targeting")
    col_ind1, col_ind2, col_ind3 = st.columns(3)
    with col_ind1:
        industry_list = list(INDUSTRIES.keys())
        industry = st.selectbox("Industry *", industry_list)
    with col_ind2:
        subindustry_options = INDUSTRIES.get(industry, [])
        subindustry = st.selectbox("Subindustry", subindustry_options)
    with col_ind3:
        pain_point = st.selectbox("Pain Point", [
            "General (auto-detect based on role and industry)",
            "Outgrowing QuickBooks or entry-level accounting software",
            "Manual processes and too much data entry",
            "No real-time visibility into financials",
            "Disconnected systems (ERP, CRM, e-commerce not talking)",
            "Slow month-end close taking weeks instead of days",
            "Multi-entity or multi-currency headaches",
            "Inventory and supply chain visibility gaps",
            "Revenue recognition compliance concerns",
            "Scaling the business but systems can't keep up",
            "Preparing for audit, IPO, or investor scrutiny",
            "Compliance and regulatory requirements",
            "Order management complexity",
        ])

    # Input form
    with st.form("prospect_form"):
        st.markdown("##### Prospect")
        col1, col2, col3 = st.columns(3)
        with col1:
            prospect_name = st.text_input(
                "Prospect Name *",
                placeholder="Jane Doe",
            )
        with col2:
            company_name = st.text_input(
                "Company *",
                placeholder="Acme Corp",
            )
        with col3:
            company_url = st.text_input(
                "Company Website",
                placeholder="https://acmecorp.com",
            )

        col4, col5 = st.columns(2)
        with col4:
            prospect_role = st.selectbox("Role *", [
                "CFO / VP Finance",
                "Controller / Accounting Manager",
                "CIO / IT Director",
                "COO / VP Operations",
                "CEO / Founder / Owner",
                "Director of Supply Chain",
                "VP of Sales / Revenue Ops",
                "Procurement / Purchasing Manager",
                "Other",
            ])
        with col5:
            tone = st.selectbox("Email Tone", [
                "Conversational",
                "Professional / Formal",
                "Casual / Friendly",
                "Executive / Direct",
                "Consultative / Advisory",
            ])

        with st.expander("Sender Info (optional)"):
            col9, col10, col11, col12 = st.columns(4)
            with col9:
                sender_name = st.text_input("Your Name", placeholder="Matt Jacobs")
            with col10:
                sender_title = st.text_input("Your Title", placeholder="Account Executive")
            with col11:
                sender_company = st.text_input("Your Company", placeholder="NetSuite")
            with col12:
                sender_email = st.text_input("Your Email", placeholder="mjacobs@netsuite.com")

        submitted = st.form_submit_button("Generate Touch Plan", type="primary")

# --- Generation ---
if submitted:
    if not prospect_name or not company_name:
        st.error("Please fill in the prospect name and company.")
    else:
        try:
            pain = pain_point if pain_point != "General (auto-detect based on role and industry)" else ""

            # Step 1: Research company website if URL provided
            company_research = ""
            if company_url:
                with st.spinner("Researching company website..."):
                    page_text = scrape_company_page(company_url)
                    if page_text:
                        client = anthropic.Anthropic(api_key=api_key)
                        company_research = summarize_company(client, company_name, page_text)

            # Step 2: Generate the email sequence
            with st.spinner("Generating your 6-email touch plan..."):
                result = generate_sequence(
                    api_key=api_key,
                    prospect_name=prospect_name,
                    prospect_role=prospect_role,
                    company_name=company_name,
                    industry=industry,
                    subindustry=subindustry,
                    company_url=company_url,
                    pain_point=pain,
                    tone=tone,
                    sender_name=sender_name,
                    sender_title=sender_title,
                    sender_company=sender_company,
                    sender_email=sender_email,
                    company_research=company_research,
                )
                st.session_state["result"] = result

            # Save to Supabase if available
            if sb:
                try:
                    save_to_supabase(sb, prospect_name, company_name, result)
                except Exception:
                    pass

        except json.JSONDecodeError:
            st.error("Failed to parse the AI response. Please try again.")
        except anthropic.APIError as e:
            st.error(f"API error: {e.message}")
        except Exception as e:
            st.error(f"Something went wrong: {e}")

# --- Display results ---
if "result" in st.session_state:
    result = st.session_state["result"]
    prospect = result.get("prospect_name", "Prospect")
    company = result.get("company", "Company")

    st.markdown("---")
    st.subheader(f"Touch Plan for {prospect} at {company}")

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

        with st.expander("Copy to clipboard"):
            st.caption("Subject")
            st.code(subject, language=None)
            st.caption("Body")
            st.code(body, language=None)

    st.markdown("---")
    if st.button("Clear & Start Over"):
        st.session_state.pop("result", None)
        st.rerun()

# --- Sidebar: History (Supabase only) ---
if sb:
    with st.sidebar:
        st.markdown("### Recent Touch Plans")
        try:
            history = load_history(sb)
            if history:
                for row in history:
                    label = f"{row.get('prospect_name', 'Unknown')} at {row.get('company_name', '')}"
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
