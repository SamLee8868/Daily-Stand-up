"""
teams.py — Microsoft Teams connector helpers.

Provides functions to load team configuration and resolve
webhook URLs for posting messages.
"""

import json
from pathlib import Path
from typing import Optional, List

CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"


def load_teams_config() -> List[dict]:
    """Load team definitions from config/teams.json."""
    config_path = CONFIG_DIR / "teams.json"
    with open(config_path) as f:
        return json.load(f)["teams"]


def get_team(team_id: str) -> Optional[dict]:
    """Look up a team by ID (e.g., 'APPS', 'GSS', 'PLAT')."""
    teams = load_teams_config()
    for team in teams:
        if team["id"] == team_id:
            return team
    return None


def get_webhook_url(team_id: str) -> str:
    """Get the Teams webhook URL for a given team."""
    team = get_team(team_id)
    if team:
        return team.get("teams_channel_webhook", "")
    return ""


def get_all_team_ids() -> List[str]:
    """Return all configured team IDs."""
    return [t["id"] for t in load_teams_config()]
