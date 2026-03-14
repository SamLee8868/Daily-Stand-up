"""
generate_digest.py — Build a Teams-ready daily digest from action items JSON.

Reads the day's action items JSON and produces a formatted markdown message
suitable for posting to a Microsoft Teams channel.
"""

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.dates import get_current_sprint, sprint_day_number, get_business_days_in_range
from utils.teams import get_team

TEMPLATE_DIR = Path(__file__).resolve().parent.parent.parent / "templates"


def load_action_items(json_path: str) -> List[dict]:
    """Load action items from a JSON file."""
    with open(json_path) as f:
        return json.load(f)


def categorize_items(items: List[dict]) -> Dict[str, List[dict]]:
    """Group action items by urgency category for the digest.

    An item can appear in multiple categories (e.g., blocked AND overdue).
    """
    categories = {
        "overdue": [],
        "due_today": [],
        "due_this_week": [],
        "blocked": [],
        "completed_yesterday": [],
        "new_items": [],
    }

    for item in items:
        flag = item.get("Urgency Flag", "")
        status = item.get("Delivery Status", "")
        change = item.get("Change Since Last Stand-up", "")

        if status == "Delivered" and change in ("Resolved", "Status Changed"):
            categories["completed_yesterday"].append(item)
            continue

        if status == "Blocked":
            categories["blocked"].append(item)

        if flag == "Overdue":
            categories["overdue"].append(item)
        elif flag == "Due Today":
            categories["due_today"].append(item)
        elif flag == "Due This Week":
            categories["due_this_week"].append(item)

        if change == "New":
            categories["new_items"].append(item)

    return categories


def render_digest(
    categories: Dict[str, List[dict]],
    project_name: str,
    sprint_info: str,
    digest_date: str,
    overall_health: str = "",
) -> str:
    """Render the Teams digest as a formatted string.

    Uses direct string building for reliability — no Jinja2 dependency
    needed for a single message format.
    """
    lines = []
    lines.append(f"**Daily Stand-up Digest — {project_name} — {digest_date}**")
    lines.append(sprint_info)
    lines.append("")

    def _section(emoji: str, title: str, items: List[dict], show_fields: List[str]):
        if not items:
            return
        lines.append(f"{emoji} **{title} ({len(items)})**")
        for item in items:
            parts = [item.get("Action Item Description", "???")]
            for field, label in show_fields:
                val = item.get(field, "")
                if val:
                    parts.append(f"{label}: {val}")
            lines.append(f"- {' — '.join(parts)}")
        lines.append("")

    _section(
        "OVERDUE", "OVERDUE", categories["overdue"],
        [("Owner (Full Name)", "Owner"), ("Due Date", "Was due")],
    )
    _section(
        "DUE TODAY", "DUE TODAY", categories["due_today"],
        [("Owner (Full Name)", "Owner")],
    )
    _section(
        "DUE THIS WEEK", "DUE THIS WEEK", categories["due_this_week"],
        [("Owner (Full Name)", "Owner"), ("Due Date", "Due")],
    )
    _section(
        "BLOCKED", "BLOCKED", categories["blocked"],
        [("Owner (Full Name)", "Owner"), ("Dependencies / Blockers", "Blocker")],
    )
    _section(
        "COMPLETED", "COMPLETED YESTERDAY", categories["completed_yesterday"],
        [("Owner (Full Name)", "Owner")],
    )
    _section(
        "NEW", "NEW ITEMS", categories["new_items"],
        [("Owner (Full Name)", "Owner"), ("Priority", "Priority"), ("Due Date", "Due")],
    )

    if overall_health:
        lines.append(f"**Sprint Health:** {overall_health}")

    return "\n".join(lines)


def compute_health(categories: Dict[str, List[dict]]) -> str:
    """Rough sprint health based on overdue/blocked counts."""
    overdue = len(categories["overdue"])
    blocked = len(categories["blocked"])

    if overdue >= 3 or blocked >= 3:
        return "Red"
    elif overdue >= 1 or blocked >= 1:
        return "Yellow"
    return "Green"


def write_digest(content: str, output_path: str) -> None:
    """Write the digest message to a file."""
    with open(output_path, "w") as f:
        f.write(content)


def main():
    parser = argparse.ArgumentParser(
        description="Generate Teams daily digest from action items JSON."
    )
    parser.add_argument("--input", required=True, help="Path to action items JSON")
    parser.add_argument("--team", required=True, help="Team ID (APPS, GSS, PLAT)")
    parser.add_argument("--date", default=str(date.today()), help="Digest date (YYYY-MM-DD)")
    parser.add_argument("--output-dir", default="output/", help="Output directory")
    args = parser.parse_args()

    digest_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    items = load_action_items(args.input)
    categories = categorize_items(items)

    team_config = get_team(args.team)
    project_name = team_config["project_name"] if team_config else f"MP {args.team}"

    sprint = get_current_sprint(digest_date)
    if sprint:
        start = date.fromisoformat(sprint["start_date"])
        end = date.fromisoformat(sprint["end_date"])
        total_days = len(get_business_days_in_range(start, end))
        current_day = sprint_day_number(start, digest_date)
        sprint_info = f"Sprint: {sprint['name']} | Day {current_day} of {total_days}"
    else:
        sprint_info = "Sprint: Not in active sprint"

    health = compute_health(categories)

    content = render_digest(categories, project_name, sprint_info, args.date, health)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{args.date}_{args.team}_Teams_Digest.md"
    write_digest(content, str(output_file))

    print(f"Wrote digest to {output_file}")
    print(f"  Overdue: {len(categories['overdue'])}, Due Today: {len(categories['due_today'])}, "
          f"Blocked: {len(categories['blocked'])}, New: {len(categories['new_items'])}")
    print(f"  Sprint Health: {health}")


if __name__ == "__main__":
    main()
