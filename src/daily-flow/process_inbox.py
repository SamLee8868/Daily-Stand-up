"""
process_inbox.py — Single-command entry point for processing Copilot stand-up files.

Scans an inbox folder for Copilot output, auto-detects team and date from
filenames, processes action items (JSON preferred, Excel fallback), applies
carry-forward and sprint enrichment, and generates a Teams digest.

Usage:
    python process_inbox.py --inbox /path/to/inbox
    python process_inbox.py --inbox /path/to/inbox --output-dir output/
"""

import argparse
import json
import shutil
import sys
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from urllib.parse import unquote

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.teams import load_teams_config
from utils.dates import get_current_sprint, sprint_day_number, get_business_days_in_range

from parse_standup import (
    load_copilot_json,
    parse_excel_action_items,
    extract_items_from_word_docs,
    cross_reference_items,
    load_previous_action_items,
    apply_carry_forward,
    apply_urgency_flags,
    enrich_with_sprint_info,
    sort_items,
    write_action_items_json,
)
from generate_digest import (
    categorize_items,
    render_digest,
    compute_health,
    write_digest,
)


def _build_meeting_name_map():
    """Build a mapping from meeting name variants to team IDs."""
    name_map = {}
    for team in load_teams_config():
        team_id = team["id"]
        for meeting_name in team.get("meeting_names", []):
            name_map[meeting_name.lower()] = team_id
        name_map[team["project_name"].lower()] = team_id
        name_map[team_id.lower()] = team_id
    return name_map


def _decode_filename(filename: str) -> str:
    """URL-decode a filename (handle %20 etc.)."""
    return unquote(filename)


def _extract_date_from_filename(filename: str) -> str:
    """Extract YYYY-MM-DD date from start of filename."""
    decoded = _decode_filename(filename)
    if len(decoded) >= 10:
        date_str = decoded[:10]
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return date_str
        except ValueError:
            pass
    return ""


def _extract_meeting_name(filename: str) -> str:
    """Extract meeting name from between date and deliverable type.

    Filenames follow: YYYY-MM-DD_<MeetingName>_<DeliverableType>.<ext>
    """
    decoded = _decode_filename(filename)
    if len(decoded) < 12:
        return ""

    without_date = decoded[11:]

    suffixes = [
        "_Action_Items.xlsx",
        "_Action_Items.json",
        "_Executive_Summary.docx",
        "_Daily_Standup_OnePager.docx",
        "_Teams_Digest.md",
        "_Daily_Standup_Recap.docx",
    ]

    for suffix in suffixes:
        if without_date.endswith(suffix):
            return without_date[:-len(suffix)]

    last_underscore = without_date.rfind("_")
    if last_underscore > 0:
        return without_date[:last_underscore]

    return without_date


def _resolve_team(meeting_name: str, name_map: dict) -> str:
    """Resolve a meeting name to a team ID using the config mapping."""
    lower = meeting_name.lower()
    if lower in name_map:
        return name_map[lower]

    for key, team_id in name_map.items():
        if key in lower or lower in key:
            return team_id

    return ""


def scan_inbox(inbox_dir: str) -> dict:
    """Scan inbox folder and group files by (date, team).

    Returns: dict of {(date_str, team_id): {file_type: Path}}
    """
    inbox = Path(inbox_dir)
    if not inbox.exists():
        print(f"Error: Inbox directory does not exist: {inbox_dir}")
        return {}

    name_map = _build_meeting_name_map()
    groups = defaultdict(dict)

    for f in sorted(inbox.iterdir()):
        if f.name.startswith("."):
            continue
        if not f.is_file():
            continue

        decoded_name = _decode_filename(f.name)
        date_str = _extract_date_from_filename(decoded_name)
        meeting_name = _extract_meeting_name(decoded_name)
        team_id = _resolve_team(meeting_name, name_map)

        if not date_str:
            print(f"  Skipping {f.name}: could not extract date")
            continue
        if not team_id:
            print(f"  Skipping {f.name}: could not resolve team from '{meeting_name}'")
            continue

        suffix = f.suffix.lower()
        key = (date_str, team_id)

        if suffix == ".json" and "action_items" in decoded_name.lower():
            groups[key]["json"] = f
        elif suffix == ".xlsx" and "action_items" in decoded_name.lower():
            groups[key]["xlsx"] = f
        elif suffix == ".docx" and "executive_summary" in decoded_name.lower():
            groups[key]["exec_summary"] = f
        elif suffix == ".docx" and ("onepager" in decoded_name.lower() or "one_pager" in decoded_name.lower()):
            groups[key]["one_pager"] = f
        elif suffix == ".docx" and "recap" in decoded_name.lower():
            groups[key]["recap"] = f
        elif suffix == ".md" and "teams_digest" in decoded_name.lower():
            groups[key]["copilot_digest"] = f
        else:
            groups[key][f"other_{f.name}"] = f

    return dict(groups)


def process_group(
    date_str: str,
    team_id: str,
    files: dict,
    output_dir: str,
) -> bool:
    """Process a single (date, team) group of Copilot files."""
    standup_date = datetime.strptime(date_str, "%Y-%m-%d").date()

    print(f"\nProcessing {team_id} — {date_str}")
    print(f"  Files: {', '.join(f.name for f in files.values())}")

    if "json" in files:
        print(f"  Using JSON directly: {files['json'].name}")
        items = load_copilot_json(str(files["json"]))
    elif "xlsx" in files:
        print(f"  Parsing Excel: {files['xlsx'].name}")
        items = parse_excel_action_items(str(files["xlsx"]))
    else:
        print(f"  Warning: No action items file (JSON or Excel) found. Skipping.")
        return False

    print(f"  Loaded {len(items)} action items from structured file")

    word_doc_paths = []
    for key in ("one_pager", "exec_summary", "recap"):
        if key in files:
            word_doc_paths.append(str(files[key]))

    if word_doc_paths:
        print(f"  Cross-referencing against {len(word_doc_paths)} Word doc(s)...")
        supplementary = extract_items_from_word_docs(word_doc_paths)
        if supplementary:
            print(f"  Found {len(supplementary)} item(s) in Word docs")
            items = cross_reference_items(items, supplementary)
            print(f"  Total after cross-reference: {len(items)} item(s)")
        else:
            print(f"  No additional items found in Word docs")

    previous = load_previous_action_items(output_dir, team_id, standup_date)
    if previous:
        print(f"  Loaded {len(previous)} previous items for carry-forward")

    items = apply_carry_forward(items, previous)
    items = enrich_with_sprint_info(items, team_id, standup_date)
    items = apply_urgency_flags(items, standup_date)
    items = sort_items(items)

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    json_path = out / f"{date_str}_{team_id}_Action_Items.json"
    write_action_items_json(items, str(json_path))
    print(f"  Wrote {len(items)} enriched action items to {json_path.name}")

    categories = categorize_items(items)

    from utils.teams import get_team
    team_config = get_team(team_id)
    project_name = team_config["project_name"] if team_config else f"MP {team_id}"

    sprint = get_current_sprint(standup_date)
    if sprint:
        start = date.fromisoformat(sprint["start_date"])
        end_d = date.fromisoformat(sprint["end_date"])
        total_days = len(get_business_days_in_range(start, end_d))
        current_day = sprint_day_number(start, standup_date)
        sprint_info = f"Sprint: {sprint['name']} | Day {current_day} of {total_days}"
    else:
        sprint_info = "Sprint: Not in active sprint"

    health = compute_health(categories)
    digest_content = render_digest(categories, project_name, sprint_info, date_str, health)

    digest_path = out / f"{date_str}_{team_id}_Teams_Digest.md"
    write_digest(digest_content, str(digest_path))
    print(f"  Wrote digest to {digest_path.name}")
    print(f"  Sprint Health: {health}")

    archive_dir = out / team_id
    archive_dir.mkdir(parents=True, exist_ok=True)
    for file_type, file_path in files.items():
        dest = archive_dir / _decode_filename(file_path.name)
        if not dest.exists():
            shutil.copy2(str(file_path), str(dest))

    counts = {k: len(v) for k, v in categories.items() if v}
    if counts:
        print(f"  Digest breakdown: {counts}")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Process Copilot stand-up files from an inbox folder."
    )
    parser.add_argument(
        "--inbox",
        required=True,
        help="Path to inbox folder containing Copilot output files",
    )
    parser.add_argument(
        "--output-dir",
        default="output/",
        help="Output directory for processed files",
    )
    args = parser.parse_args()

    print(f"Scanning inbox: {args.inbox}")
    groups = scan_inbox(args.inbox)

    if not groups:
        print("No processable files found in inbox.")
        return

    print(f"Found {len(groups)} stand-up(s) to process:")
    for (date_str, team_id), files in sorted(groups.items()):
        print(f"  {date_str} / {team_id}: {len(files)} file(s)")

    success_count = 0
    for (date_str, team_id), files in sorted(groups.items()):
        if process_group(date_str, team_id, files, args.output_dir):
            success_count += 1

    print(f"\nDone. Processed {success_count}/{len(groups)} stand-up(s).")


if __name__ == "__main__":
    main()
