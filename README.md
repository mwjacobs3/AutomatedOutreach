# AutomatedOutreach — AI-Powered NetSuite Email Sequences

Generate hyper-personalized 6-email outreach sequences for NetSuite prospects using AI.

## How It Works

1. **Input** prospect details — LinkedIn profile context, company info, contact details, and any known pain points
2. **AI generates** a 6-email sequence tailored to the prospect's specific situation, industry, and role
3. **Emails are saved** as a cadence file, and optionally created as Gmail drafts

### The 6-Email Sequence

| # | Day | Strategy | Purpose |
|---|-----|----------|---------|
| 1 | 1   | Relevant Opener | Reference something specific about them, connect to a pain point |
| 2 | 3   | Value Drop | Share an industry-specific insight or stat |
| 3 | 7   | Pain Agitator | Call out a specific challenge and cost of inaction |
| 4 | 10  | Social Proof | Lead with results from a similar company |
| 5 | 14  | Breakup Tease | Acknowledge outreach, give an easy out |
| 6 | 21  | Final Value Add | Share useful content, leave the door open |

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Configure your API key
cp .env.example .env
# Edit .env and add your Anthropic API key
```

## Usage

### Interactive Mode
```bash
python main.py
```
Walks you through entering prospect details step by step.

### From a JSON File
```bash
python main.py --from-file data/example_prospect.json
```
See `data/example_prospect.json` for the expected format.

### Save Individual Draft Files
```bash
python main.py --from-file prospect.json --drafts
```
Creates separate JSON files per email for easy review and editing.

### With Gmail Integration (via Claude Code)
When running inside Claude Code with Gmail MCP configured, you can ask Claude to:
1. Generate the sequence using this tool
2. Create Gmail drafts for each email in the sequence
3. Review and send them on the scheduled dates

## Project Structure

```
├── main.py                  # CLI entrypoint
├── src/
│   ├── prospect.py          # Prospect data model
│   ├── email_generator.py   # AI email generation (Claude API)
│   ├── cadence.py           # Sequence scheduling & persistence
│   └── gmail_drafter.py     # Gmail draft creation helpers
├── data/
│   ├── example_prospect.json  # Sample input
│   ├── cadences/              # Saved cadence files (gitignored)
│   └── drafts/                # Individual draft files (gitignored)
├── requirements.txt
└── .env.example
```

## Customization

- Edit the `SEQUENCE_STRATEGY` prompt in `src/email_generator.py` to adjust tone, style, or email structure
- Modify the cadence timing (days 1, 3, 7, 10, 14, 21) in the strategy prompt
- Add additional prospect fields in `src/prospect.py` for richer personalization
