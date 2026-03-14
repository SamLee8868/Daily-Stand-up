# ShowRunner — Architecture

## Overview

ShowRunner automates the pipeline from daily stand-up meetings to actionable intelligence:
daily digests, action item tracking, and bi-weekly executive sprint reports.

## System Components

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Copilot / AI    │────▶│  parse_standup    │────▶│  Action Items   │
│  Stand-up Output │     │  (Excel/Word ▶ JSON) │  │  JSON + Excel   │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                           │
                              ┌─────────────────────────────┤
                              │                             │
                              ▼                             ▼
                   ┌──────────────────┐          ┌──────────────────┐
                   │  generate_digest  │          │  SharePoint      │
                   │  (JSON ▶ Teams msg)│         │  Document Library│
                   └────────┬─────────┘          └──────────────────┘
                            │
                            ▼
                   ┌──────────────────┐
                   │  post_to_teams    │
                   │  (Webhook/Graph)  │
                   └────────┬─────────┘
                            │
                            ▼
                   ┌──────────────────┐
                   │  MS Teams Channel │
                   │  (Daily Digest)   │
                   └──────────────────┘


Sprint End:
                   ┌──────────────────┐     ┌──────────────────┐
                   │  aggregate_items  │────▶│  generate_summary│
                   │  (All sprint JSONs)│    │  (Executive Rpt) │
                   └──────────────────┘     └────────┬─────────┘
                                                      │
                                            ┌─────────┴─────────┐
                                            ▼                   ▼
                                   ┌──────────────┐   ┌──────────────┐
                                   │  Teams Post   │   │  SharePoint   │
                                   └──────────────┘   └──────────────┘
```

## Daily Flow

1. **Input:** Copilot generates stand-up deliverables (Excel tracker, Word summary)
2. **Parse:** `parse_standup.py` reads Excel/Word, extracts action items, applies carry-forward logic
3. **Enrich:** Urgency flags computed, change-since-yesterday tracked
4. **Output:** Action Items JSON written to SharePoint
5. **Digest:** `generate_digest.py` categorizes items and renders the Teams message
6. **Notify:** `post_to_teams.py` sends the digest to the configured channel

**Trigger:** Scheduled daily at 7:00 AM (configurable in `config/settings.json`)

## Sprint-End Flow

1. **Aggregate:** `aggregate_items.py` collects all daily JSON files for the sprint period
2. **Metrics:** Completion rates, priority breakdown, recurring blockers calculated
3. **Report:** `generate_summary.py` renders the executive summary from a Jinja2 template
4. **Distribute:** Posted to Teams and saved to SharePoint

**Trigger:** Sprint end date (from `config/sprints.json`) or manual invocation

## Integration Points

| System | Method | Purpose |
|--------|--------|---------|
| Microsoft Teams | Incoming Webhook or Graph API | Post daily digests and sprint summaries |
| SharePoint | Graph API (MSAL client credentials) | Store and retrieve deliverables |
| Copilot / Azure OpenAI | Prompt-based | Generate stand-up deliverables from transcripts |

## Authentication

- **Teams Webhook:** No auth — URL acts as the credential (store in `.env`, never in Git)
- **Graph API (SharePoint):** Azure AD app registration with client credentials flow
  - Requires `Sites.ReadWrite.All` permission
  - Tenant ID, Client ID, Client Secret stored in `.env`

## Data Storage

| Data | Location | Format |
|------|----------|--------|
| Prompts, code, config | GitLab (`showrunner` repo) | Markdown, Python, JSON |
| Daily deliverables | SharePoint document library | JSON, Excel, Word |
| Secrets | `.env` file (local) or Azure Key Vault (production) | Environment variables |

## Configuration

All runtime configuration lives in `config/`:

- `teams.json` — Team definitions, members, webhook URLs
- `sprints.json` — Sprint schedule with start/end dates
- `settings.json` — Notification times, storage preferences
