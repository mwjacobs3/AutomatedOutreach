# AutomatedOutreach — AI-Powered NetSuite Touch Plans

Generate hyper-personalized 6-email outreach sequences for NetSuite prospects using AI. Just provide a LinkedIn profile URL and a company website — the AI handles the rest.

## Live App

Deployed on **Streamlit Community Cloud**. No local setup required.

## How It Works

1. **Input** a prospect's LinkedIn profile URL and their company website URL
2. **AI generates** a tailored 6-email touch plan personalized to the prospect's role, company, and likely pain points
3. **Copy & paste** each email directly into your outreach tool

### The 6-Email Touch Plan

| # | Day | Strategy | Purpose |
|---|-----|----------|---------|
| 1 | 1   | Relevant Opener | Reference something specific about them, connect to a pain point |
| 2 | 3   | Value Drop | Share an industry-specific insight or stat |
| 3 | 7   | Pain Agitator | Call out a specific challenge and cost of inaction |
| 4 | 10  | Social Proof | Lead with results from a similar company |
| 5 | 14  | Breakup Tease | Acknowledge outreach, give an easy out |
| 6 | 21  | Final Value Add | Share useful content, leave the door open |

## Deploy to Streamlit Community Cloud

1. **Fork or push** this repo to your GitHub account
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub
3. Click **New app** → select this repo → set main file to `streamlit_app.py`
4. Under **Advanced settings → Secrets**, add:
   ```toml
   ANTHROPIC_API_KEY = "sk-ant-..."
   ```
5. Click **Deploy** — your app will be live in about a minute

### Optional: Supabase for History

To save generated touch plans and view history:

1. Create a free project at [supabase.com](https://supabase.com)
2. Run `supabase_schema.sql` in the Supabase SQL Editor to create the table
3. Add these to your Streamlit secrets:
   ```toml
   SUPABASE_URL = "https://your-project.supabase.co"
   SUPABASE_KEY = "your-anon-key"
   ```

## Local Development

```bash
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit secrets.toml with your Anthropic API key
streamlit run streamlit_app.py
```

## Project Structure

```
├── streamlit_app.py              # Main Streamlit app (cloud-ready)
├── requirements.txt              # Python dependencies
├── supabase_schema.sql           # Optional DB schema
├── .streamlit/
│   ├── config.toml               # Theme & server config
│   └── secrets.toml.example      # Secrets template
├── src/                          # Core logic (CLI mode)
│   ├── email_generator.py
│   ├── prospect.py
│   ├── cadence.py
│   └── gmail_drafter.py
├── main.py                       # CLI entrypoint (optional)
└── data/
    └── example_prospect.json
```
