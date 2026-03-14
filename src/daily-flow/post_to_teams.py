"""
post_to_teams.py — Post the daily digest message to a Microsoft Teams channel.

Supports two methods:
1. Teams Incoming Webhook (simple, no auth beyond the URL)
2. Microsoft Graph API (requires Azure AD app registration)
"""

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path

import requests
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.teams import get_team, get_webhook_url

load_dotenv()


def load_digest(filepath: str) -> str:
    """Read the digest message content from a file."""
    with open(filepath) as f:
        return f.read()


def build_adaptive_card(message: str, title: str = "ShowRunner Daily Digest") -> dict:
    """Build a Teams Adaptive Card payload from a markdown message.

    Splits the message into sections for better visual rendering.
    """
    body_blocks = []

    body_blocks.append({
        "type": "TextBlock",
        "text": title,
        "weight": "Bolder",
        "size": "Medium",
        "wrap": True,
    })

    sections = message.split("\n\n")
    for section in sections:
        if not section.strip():
            continue
        body_blocks.append({
            "type": "TextBlock",
            "text": section.strip(),
            "wrap": True,
            "spacing": "Medium",
        })

    return {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "type": "AdaptiveCard",
                    "version": "1.4",
                    "body": body_blocks,
                },
            }
        ],
    }


def post_via_webhook(webhook_url: str, message: str, title: str = "") -> bool:
    """Post a message to Teams using an Incoming Webhook connector."""
    if not webhook_url:
        print("Error: No webhook URL provided.")
        return False

    payload = build_adaptive_card(message, title or "ShowRunner Daily Digest")

    try:
        response = requests.post(
            webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
    except requests.RequestException as e:
        print(f"Error posting to Teams: {e}")
        return False

    if response.status_code in (200, 202):
        print("Message posted to Teams successfully.")
        return True
    else:
        print(f"Failed to post to Teams: {response.status_code} — {response.text}")
        return False


def post_via_graph_api(team_id: str, channel_id: str, message: str, access_token: str) -> bool:
    """Post a message to Teams using Microsoft Graph API.

    Requires an Azure AD app with ChannelMessage.Send permission.
    """
    url = f"https://graph.microsoft.com/v1.0/teams/{team_id}/channels/{channel_id}/messages"

    payload = {
        "body": {
            "contentType": "html",
            "content": message.replace("\n", "<br/>"),
        }
    }

    try:
        response = requests.post(
            url,
            json=payload,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            timeout=30,
        )
    except requests.RequestException as e:
        print(f"Error posting via Graph API: {e}")
        return False

    if response.status_code == 201:
        print("Message posted to Teams via Graph API.")
        return True
    else:
        print(f"Graph API error: {response.status_code} — {response.text}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Post daily digest to Microsoft Teams."
    )
    parser.add_argument("--digest", required=True, help="Path to digest .md file")
    parser.add_argument("--team", required=True, help="Team ID (APPS, GSS, PLAT)")
    parser.add_argument("--method", choices=["webhook", "graph"], default="webhook")
    parser.add_argument("--dry-run", action="store_true", help="Print message without posting")
    args = parser.parse_args()

    message = load_digest(args.digest)

    if args.dry_run:
        print("=== DRY RUN — Would post the following to Teams ===")
        print(message)
        print("=== END DRY RUN ===")
        return

    team_config = get_team(args.team)
    title = f"ShowRunner — {team_config['project_name']}" if team_config else "ShowRunner Daily Digest"

    if args.method == "webhook":
        webhook_url = get_webhook_url(args.team)
        if not webhook_url:
            env_url = os.getenv("TEAMS_WEBHOOK_URL", "")
            if env_url:
                webhook_url = env_url
            else:
                print(f"Error: No webhook URL configured for team {args.team}.")
                print("  Set it in config/teams.json or TEAMS_WEBHOOK_URL env var.")
                return
        post_via_webhook(webhook_url, message, title)
    else:
        print("Graph API posting requires AZURE_* env vars and a configured app registration.")
        print("See docs/setup-guide.md for configuration instructions.")


if __name__ == "__main__":
    main()
