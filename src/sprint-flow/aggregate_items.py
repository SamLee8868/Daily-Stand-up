"""
aggregate_items.py — Collect all daily action item JSONs for a sprint period.

Reads every action items JSON file between the sprint start and end dates,
deduplicates by keeping the latest version of each item, and produces a
combined dataset with computed metrics for sprint summary generation.
"""

import argparse
import json
import sys
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.dates import get_sprint_by_number, get_business_days_in_range


def find_action_item_files(
    base_dir: str,
    team: str,
    start_date: date,
    end_date: date,
) -> List[Path]:
    """Find all action item JSON files for a team within a date range."""
    base = Path(base_dir)
    if not base.exists():
        return []

    files = []
    current = start_date
    while current <= end_date:
        pattern = f"{current.isoformat()}_{team}_Action_Items.json"
        candidate = base / pattern
        if candidate.exists():
            files.append(candidate)
        current += timedelta(days=1)
    return sorted(files)


def load_daily_snapshots(files: List[Path]) -> List[Tuple[str, List[dict]]]:
    """Load each daily file as a (date_str, items) tuple."""
    snapshots = []
    for f in files:
        date_str = f.name[:10]
        with open(f) as fh:
            items = json.load(fh)
        snapshots.append((date_str, items))
    return snapshots


def merge_to_latest(snapshots: List[Tuple[str, List[dict]]]) -> List[dict]:
    """Merge all daily snapshots, keeping the latest version of each item.

    Items are keyed by (description, owner). The most recent daily snapshot's
    version of each item wins, preserving the full history of status changes.
    """
    latest = {}
    for date_str, items in snapshots:
        for item in items:
            key = (
                item.get("Action Item Description", "").strip().lower(),
                item.get("Owner (Full Name)", "").strip().lower(),
            )
            item["_last_seen"] = date_str
            latest[key] = item

    return list(latest.values())


def track_status_history(snapshots: List[Tuple[str, List[dict]]]) -> Dict[str, List[dict]]:
    """Build a per-item status history across the sprint.

    Returns a dict keyed by (description||owner) with a list of
    {date, status} entries showing how the item evolved.
    """
    history = defaultdict(list)

    for date_str, items in snapshots:
        for item in items:
            key = f"{item.get('Action Item Description', '').strip().lower()}||{item.get('Owner (Full Name)', '').strip().lower()}"
            history[key].append({
                "date": date_str,
                "status": item.get("Delivery Status", ""),
                "priority": item.get("Priority", ""),
            })

    return dict(history)


def find_recurring_blockers(history: Dict[str, List[dict]]) -> List[dict]:
    """Identify items that were blocked on 2+ separate days."""
    blockers = []
    for key, entries in history.items():
        blocked_days = [e for e in entries if e["status"] == "Blocked"]
        if len(blocked_days) >= 2:
            parts = key.split("||")
            blockers.append({
                "description": parts[0] if parts else key,
                "owner": parts[1] if len(parts) > 1 else "",
                "blocked_days": len(blocked_days),
                "first_blocked": blocked_days[0]["date"],
                "last_blocked": blocked_days[-1]["date"],
            })
    return blockers


def compute_sprint_metrics(
    items: List[dict],
    history: Dict[str, List[dict]],
    expected_standups: int,
    actual_standups: int,
) -> dict:
    """Compute comprehensive sprint metrics from aggregated items."""
    metrics = {
        "total_tracked": len(items),
        "total_completed": 0,
        "by_priority": {"Critical": 0, "High": 0, "Medium": 0, "Low": 0},
        "by_status": {"Not Started": 0, "In Progress": 0, "Blocked": 0, "Delivered": 0},
        "recurring_blockers": find_recurring_blockers(history),
        "standups_held": actual_standups,
        "standups_expected": expected_standups,
        "resolution_times": [],
    }

    for item in items:
        priority = item.get("Priority", "")
        status = item.get("Delivery Status", "")

        if priority in metrics["by_priority"]:
            metrics["by_priority"][priority] += 1
        if status in metrics["by_status"]:
            metrics["by_status"][status] += 1
        if status == "Delivered":
            metrics["total_completed"] += 1

        start = item.get("Start / Informed Date", "")
        delivered = item.get("Delivery Date", "")
        if start and delivered:
            try:
                days = (date.fromisoformat(delivered) - date.fromisoformat(start)).days
                if days >= 0:
                    metrics["resolution_times"].append(days)
            except ValueError:
                pass

    if metrics["resolution_times"]:
        metrics["avg_resolution_days"] = round(
            sum(metrics["resolution_times"]) / len(metrics["resolution_times"]), 1
        )
    else:
        metrics["avg_resolution_days"] = None

    return metrics


def main():
    parser = argparse.ArgumentParser(
        description="Aggregate sprint action items for summary generation."
    )
    parser.add_argument("--sprint", required=True, type=int, help="Sprint number")
    parser.add_argument("--team", required=True, help="Team ID (APPS, GSS, PLAT)")
    parser.add_argument("--data-dir", default="output/", help="Directory containing daily JSON files")
    parser.add_argument("--output-dir", default="output/", help="Output directory")
    args = parser.parse_args()

    sprint = get_sprint_by_number(args.sprint)
    if not sprint:
        print(f"Error: Sprint {args.sprint} not found in config/sprints.json")
        return

    start = date.fromisoformat(sprint["start_date"])
    end = date.fromisoformat(sprint["end_date"])

    files = find_action_item_files(args.data_dir, args.team, start, end)
    print(f"Found {len(files)} action item files for Sprint {args.sprint}")

    if not files:
        print("No files found. Nothing to aggregate.")
        return

    snapshots = load_daily_snapshots(files)
    items = merge_to_latest(snapshots)
    history = track_status_history(snapshots)

    expected_standups = len(get_business_days_in_range(start, end))
    metrics = compute_sprint_metrics(items, history, expected_standups, len(files))

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    aggregate_path = output_dir / f"Sprint_{args.sprint}_{args.team}_Aggregate.json"
    with open(aggregate_path, "w") as f:
        json.dump({
            "sprint": sprint,
            "team": args.team,
            "items": items,
            "history": history,
            "metrics": metrics,
        }, f, indent=2, default=str)

    print(f"Wrote aggregate data to {aggregate_path}")
    print(f"  Items: {metrics['total_tracked']}, Completed: {metrics['total_completed']}, "
          f"Blocked: {metrics['by_status']['Blocked']}")
    if metrics["avg_resolution_days"] is not None:
        print(f"  Avg resolution: {metrics['avg_resolution_days']} days")
    if metrics["recurring_blockers"]:
        print(f"  Recurring blockers: {len(metrics['recurring_blockers'])}")


if __name__ == "__main__":
    main()
