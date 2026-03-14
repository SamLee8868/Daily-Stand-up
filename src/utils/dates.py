"""
dates.py — Date, sprint, and business-day utilities.
"""

import json
from datetime import date, timedelta
from pathlib import Path
from typing import List, Optional

CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"


def load_sprints_config() -> dict:
    """Load sprint schedule from config/sprints.json."""
    config_path = CONFIG_DIR / "sprints.json"
    with open(config_path) as f:
        return json.load(f)


def get_current_sprint(today: date = None) -> Optional[dict]:
    """Return the sprint that contains the given date."""
    today = today or date.today()
    config = load_sprints_config()
    for sprint in config["sprints"]:
        start = date.fromisoformat(sprint["start_date"])
        end = date.fromisoformat(sprint["end_date"])
        if start <= today <= end:
            return sprint
    return None


def get_sprint_by_number(number: int) -> Optional[dict]:
    """Return sprint config by sprint number."""
    config = load_sprints_config()
    for sprint in config["sprints"]:
        if sprint["number"] == number:
            return sprint
    return None


def compute_urgency_flag(due_date_str: str, today: date = None) -> str:
    """Compute urgency flag based on due date relative to today.

    Returns: 'Overdue', 'Due Today', 'Due This Week', or 'On Track'.
    """
    today = today or date.today()
    try:
        due = date.fromisoformat(due_date_str)
    except (ValueError, TypeError):
        return ""

    if due < today:
        return "Overdue"
    elif due == today:
        return "Due Today"
    else:
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=4)
        if due <= week_end:
            return "Due This Week"
        return "On Track"


def get_business_days_in_range(start: date, end: date) -> List[date]:
    """Return all weekdays between start and end (inclusive)."""
    days = []
    current = start
    while current <= end:
        if current.weekday() < 5:
            days.append(current)
        current += timedelta(days=1)
    return days


def sprint_day_number(sprint_start: date, today: date = None) -> int:
    """Return which business day of the sprint today is (1-indexed)."""
    today = today or date.today()
    days = get_business_days_in_range(sprint_start, today)
    return len(days)
