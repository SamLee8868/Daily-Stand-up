"""
generate_summary.py — Produce a sprint executive summary report.

Reads the aggregated sprint data and renders a markdown executive report
suitable for leadership consumption.
"""

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.dates import get_sprint_by_number
from utils.teams import get_team


def load_aggregate(filepath: str) -> dict:
    """Load the aggregated sprint data (items + metrics + history)."""
    with open(filepath) as f:
        return json.load(f)


def classify_items(items: List[dict]) -> dict:
    """Split items into accomplishments, carryover, and in-progress."""
    accomplishments = []
    carryover = []
    in_progress = []

    for item in items:
        status = item.get("Delivery Status", "")
        if status == "Delivered":
            accomplishments.append(item)
        elif status in ("Not Started", "Blocked"):
            carryover.append(item)
        elif status == "In Progress":
            in_progress.append(item)

    return {
        "accomplishments": accomplishments,
        "carryover": carryover,
        "in_progress": in_progress,
    }


def compute_health(metrics: dict) -> str:
    """Determine overall sprint health."""
    total = metrics.get("total_tracked", 0)
    completed = metrics.get("total_completed", 0)
    blocked = metrics.get("by_status", {}).get("Blocked", 0)
    recurring = len(metrics.get("recurring_blockers", []))

    if total == 0:
        return "Green"

    completion_rate = completed / total if total else 0

    if blocked >= 3 or recurring >= 2 or completion_rate < 0.3:
        return "Red"
    elif blocked >= 1 or recurring >= 1 or completion_rate < 0.6:
        return "Yellow"
    return "Green"


def render_summary(
    sprint: dict,
    team_name: str,
    project_name: str,
    metrics: dict,
    classified: dict,
    recurring_blockers: List[dict],
    health: str,
) -> str:
    """Render the sprint summary report as markdown."""
    lines = []

    lines.append("# Sprint Summary Report")
    lines.append("")
    lines.append("| Field | Value |")
    lines.append("|-------|-------|")
    lines.append(f"| Document Date | {date.today().isoformat()} |")
    lines.append(f"| Project Name | {project_name} |")
    lines.append(f"| Team Name | {team_name} |")
    lines.append(f"| Sprint Number | {sprint.get('number', '')} |")
    lines.append(f"| Sprint Start Date | {sprint.get('start_date', '')} |")
    lines.append(f"| Sprint End Date | {sprint.get('end_date', '')} |")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Section 1: Sprint Overview")
    lines.append("")
    lines.append(f"- **Sprint:** {sprint.get('name', '')}")
    lines.append(f"- **Dates:** {sprint.get('start_date', '')} to {sprint.get('end_date', '')}")
    lines.append(f"- **Team:** {team_name}")
    lines.append(f"- **Sprint Goal:** {sprint.get('goal', 'Not documented')}")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Section 2: Accomplishments")
    lines.append("")
    completed = metrics.get("total_completed", 0)
    total = metrics.get("total_tracked", 0)
    lines.append(f"**Total items completed:** {completed} of {total}")
    lines.append("")
    for item in classified["accomplishments"]:
        desc = item.get("Action Item Description", "")
        owner = item.get("Owner (Full Name)", "")
        delivered = item.get("Delivery Date", "N/A")
        lines.append(f"- {desc} — Owner: {owner} — Delivered: {delivered}")
    if not classified["accomplishments"]:
        lines.append("- No items marked as delivered in this sprint")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Section 3: Carryover & Incomplete Work")
    lines.append("")
    for item in classified["carryover"]:
        desc = item.get("Action Item Description", "")
        owner = item.get("Owner (Full Name)", "")
        status = item.get("Delivery Status", "")
        blocker = item.get("Dependencies / Blockers", "N/A")
        lines.append(f"- {desc} — Owner: {owner} — Status: {status} — Reason: {blocker}")
    if not classified["carryover"]:
        lines.append("- No carryover items")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Section 4: Risk & Issue Log")
    lines.append("")
    if recurring_blockers:
        for b in recurring_blockers:
            lines.append(
                f"- {b['description']} — Owner: {b['owner']} — "
                f"Blocked on {b['blocked_days']} days "
                f"({b['first_blocked']} to {b['last_blocked']})"
            )
    else:
        lines.append("- No recurring blockers identified")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Section 5: Key Metrics")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Total Items Tracked | {total} |")
    lines.append(f"| Total Completed | {completed} |")
    bp = metrics.get("by_priority", {})
    lines.append(f"| Critical | {bp.get('Critical', 0)} |")
    lines.append(f"| High | {bp.get('High', 0)} |")
    lines.append(f"| Medium | {bp.get('Medium', 0)} |")
    lines.append(f"| Low | {bp.get('Low', 0)} |")
    standups = metrics.get("standups_held", "?")
    expected = metrics.get("standups_expected", "?")
    lines.append(f"| Stand-ups Held / Expected | {standups} / {expected} |")
    avg = metrics.get("avg_resolution_days")
    lines.append(f"| Avg Resolution Time | {avg if avg is not None else 'N/A'} days |")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Section 6: Executive Takeaways")
    lines.append("")
    lines.append(f"- **Overall Sprint Health:** {health}")
    completion_pct = round((completed / total * 100) if total else 0)
    lines.append(f"- Completion rate: {completion_pct}% ({completed}/{total})")
    blocked_count = metrics.get("by_status", {}).get("Blocked", 0)
    if blocked_count:
        lines.append(f"- {blocked_count} item(s) currently blocked — requires attention")
    if recurring_blockers:
        lines.append(f"- {len(recurring_blockers)} recurring blocker(s) identified across the sprint")
    if classified["carryover"]:
        lines.append(f"- {len(classified['carryover'])} item(s) carrying over to next sprint")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Section 7: Next Sprint Preview")
    lines.append("")
    lines.append(f"- Known carryover items: {len(classified['carryover'])}")
    lines.append("- Anticipated risks: Review recurring blockers above")
    lines.append("- Key dates: TBD")
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Generate sprint executive summary report."
    )
    parser.add_argument("--aggregate", required=True, help="Path to aggregate JSON file")
    parser.add_argument("--sprint", required=True, type=int, help="Sprint number")
    parser.add_argument("--team", required=True, help="Team ID")
    parser.add_argument("--output-dir", default="output/", help="Output directory")
    args = parser.parse_args()

    data = load_aggregate(args.aggregate)
    items = data["items"]
    metrics = data["metrics"]
    history = data.get("history", {})

    sprint = data.get("sprint") or get_sprint_by_number(args.sprint) or {
        "number": args.sprint,
        "name": f"Sprint {args.sprint}",
        "start_date": "",
        "end_date": "",
        "goal": "",
    }

    team_config = get_team(args.team)
    team_name = team_config["name"] if team_config else args.team
    project_name = team_config["project_name"] if team_config else f"MP {args.team}"

    classified = classify_items(items)
    recurring_blockers = metrics.get("recurring_blockers", [])
    health = compute_health(metrics)

    content = render_summary(
        sprint, team_name, project_name,
        metrics, classified, recurring_blockers, health,
    )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{date.today().isoformat()}_{args.team}_Sprint_{args.sprint}_Summary.md"
    with open(output_file, "w") as f:
        f.write(content)

    print(f"Wrote sprint summary to {output_file}")
    print(f"  Health: {health}, Completed: {metrics['total_completed']}/{metrics['total_tracked']}")


if __name__ == "__main__":
    main()
