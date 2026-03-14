# ShowRunner — Setup Guide

## Prerequisites

- Python 3.10 or later
- Git
- Microsoft 365 account with Teams and SharePoint access
- (For Graph API) Azure AD app registration with `Sites.ReadWrite.All`

## Step 1: Clone and Install

```bash
git clone https://github.com/SamLee8868/Daily-Stand-up.git
cd showrunner

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Step 2: Configure Environment

Copy the example environment file and fill in your values:

```bash
cp .env.example .env
```

Edit `.env`:

| Variable | Description | Where to get it |
|----------|-------------|-----------------|
| `TEAMS_WEBHOOK_URL` | Incoming Webhook URL for your Teams channel | Teams > Channel > Connectors > Incoming Webhook |
| `AZURE_TENANT_ID` | Your Azure AD tenant ID | Azure Portal > Azure Active Directory > Overview |
| `AZURE_CLIENT_ID` | App registration client ID | Azure Portal > App Registrations |
| `AZURE_CLIENT_SECRET` | App registration secret | Azure Portal > App Registrations > Certificates & Secrets |
| `SHAREPOINT_SITE_URL` | Your SharePoint site URL | SharePoint site settings |
| `SHAREPOINT_DOCUMENT_LIBRARY` | Document library name (default: `ShowRunner`) | SharePoint site |

## Step 3: Configure Teams and Sprints

### Teams (`config/teams.json`)

Update the team definitions with your actual members and webhook URLs:

```json
{
  "id": "GSS",
  "name": "Guest Services",
  "teams_channel_webhook": "https://your-webhook-url-here"
}
```

### Sprints (`config/sprints.json`)

Add your sprint schedule:

```json
{
  "number": 12,
  "name": "Sprint 12 — Release 2.45",
  "start_date": "2026-03-03",
  "end_date": "2026-03-14",
  "teams": ["APPS", "GSS", "PLAT"]
}
```

### Settings (`config/settings.json`)

Adjust notification timing and storage preferences as needed.

## Step 4: Create a Teams Incoming Webhook

1. Open Microsoft Teams
2. Navigate to the channel where you want ShowRunner digests
3. Click the channel name > **Manage Channel** (or **Connectors**)
4. Find **Incoming Webhook** and click **Configure**
5. Name it "ShowRunner" and optionally upload an icon
6. Copy the webhook URL and paste it into your `.env` file

## Step 5: Run the Daily Flow Manually

Test the pipeline end-to-end:

```bash
# Parse a stand-up Excel file
python src/daily-flow/parse_standup.py \
  --input path/to/standup.xlsx \
  --team GSS \
  --date 2026-03-12

# Generate the Teams digest
python src/daily-flow/generate_digest.py \
  --input output/2026-03-12_GSS_Action_Items.json \
  --team GSS \
  --date 2026-03-12

# Post to Teams
python src/daily-flow/post_to_teams.py \
  --digest output/2026-03-12_GSS_Teams_Digest.md \
  --team GSS
```

## Step 6: Run the Sprint Summary

```bash
# Aggregate all daily files for the sprint
python src/sprint-flow/aggregate_items.py \
  --sprint 12 \
  --team GSS \
  --data-dir output/

# Generate the executive summary
python src/sprint-flow/generate_summary.py \
  --aggregate output/Sprint_12_GSS_Aggregate.json \
  --sprint 12 \
  --team GSS
```

## Step 7: Automate with Power Automate (Future)

Once the manual flow works end-to-end:

1. **Daily trigger:** Create a Power Automate flow that runs at 7:00 AM on weekdays
2. **Input:** Pull the latest Copilot stand-up output from SharePoint
3. **Process:** Call the Python scripts (via Azure Function or HTTP trigger)
4. **Output:** Post digest to Teams, save deliverables to SharePoint

See [architecture.md](architecture.md) for the full automation design.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Ensure virtual environment is activated: `source venv/bin/activate` |
| Teams post returns 400 | Verify webhook URL is correct and the connector is still active |
| SharePoint upload fails | Check Azure AD app has `Sites.ReadWrite.All` permission and admin consent |
| Sprint not found | Add the sprint to `config/sprints.json` |
