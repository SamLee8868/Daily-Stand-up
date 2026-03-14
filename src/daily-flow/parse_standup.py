"""
parse_standup.py — Parse Copilot stand-up output into structured action items.

Reads Copilot-generated stand-up documents (Excel or Word) and produces
a normalized JSON file of action items with carry-forward logic applied.

Handles varying Excel schemas by mapping known column name variants to
the canonical ShowRunner action item schema.
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional

import openpyxl

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.dates import get_current_sprint, compute_urgency_flag

COLUMN_ALIASES = {
    "Action Item Description": [
        "action item", "action item description", "action", "title",
        "task", "description", "item",
    ],
    "Priority": [
        "priority", "severity", "p",
    ],
    "Owner (Full Name)": [
        "owner", "owner (full name)", "assigned to", "assignee",
    ],
    "Team / Function": [
        "team", "team / function", "function", "group",
    ],
    "Due Date": [
        "due date", "due", "target date", "deadline",
    ],
    "Start / Informed Date": [
        "start / informed date", "start date", "created date",
        "informed date", "date", "document date", "created",
    ],
    "Delivery Status": [
        "delivery status", "status", "state",
    ],
    "Delivery Date": [
        "delivery date", "completed date", "done date",
    ],
    "Ticket / Reference ID": [
        "ticket / reference id", "ticket", "reference", "id",
        "jira", "ado", "ticket id",
    ],
    "Dependencies / Blockers": [
        "dependencies / blockers", "dependencies", "blockers",
        "blocked by", "blocking",
    ],
    "Risk Level": [
        "risk level", "risk",
    ],
    "Impact if Delayed": [
        "impact if delayed", "impact", "business impact",
    ],
    "Notes / Context": [
        "notes / context", "notes", "context", "comments",
        "source", "details",
    ],
}

PRIORITY_NORMALIZE = {
    "critical": "Critical",
    "critical / high": "Critical",
    "p0": "Critical",
    "high": "High",
    "p1": "High",
    "medium": "Medium",
    "p2": "Medium",
    "low": "Low",
    "p3": "Low",
}

STATUS_NORMALIZE = {
    "not started": "Not Started",
    "open": "Not Started",
    "new": "Not Started",
    "in progress": "In Progress",
    "in-progress": "In Progress",
    "active": "In Progress",
    "blocked": "Blocked",
    "delivered": "Delivered",
    "done": "Delivered",
    "closed": "Delivered",
    "complete": "Delivered",
    "completed": "Delivered",
    "resolved": "Delivered",
}


def _resolve_column_map(headers: List[str]) -> Dict[str, int]:
    """Map canonical field names to column indices based on header text.

    Handles the inconsistent column names Copilot produces by matching
    against known aliases for each canonical field.
    """
    col_map = {}
    used_indices = set()

    for canonical, aliases in COLUMN_ALIASES.items():
        for idx, header in enumerate(headers):
            if idx in used_indices or header is None:
                continue
            normalized = str(header).strip().lower()
            if normalized in aliases:
                col_map[canonical] = idx
                used_indices.add(idx)
                break

    return col_map


def _normalize_priority(raw: Optional[str]) -> str:
    if not raw:
        return ""
    return PRIORITY_NORMALIZE.get(str(raw).strip().lower(), str(raw).strip())


def _normalize_status(raw: Optional[str]) -> str:
    if not raw:
        return "Not Started"
    return STATUS_NORMALIZE.get(str(raw).strip().lower(), str(raw).strip())


def _normalize_date(raw) -> str:
    """Convert various date formats to ISO YYYY-MM-DD string."""
    if raw is None:
        return ""
    if isinstance(raw, datetime):
        return raw.date().isoformat()
    if isinstance(raw, date):
        return raw.isoformat()
    raw_str = str(raw).strip()
    if not raw_str or raw_str.upper() in ("TBD", "N/A", "NONE", ""):
        return ""
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%B %d, %Y", "%b %d, %Y", "%m-%d-%Y"):
        try:
            return datetime.strptime(raw_str, fmt).date().isoformat()
        except ValueError:
            continue
    return raw_str


def parse_excel_action_items(filepath: str) -> List[dict]:
    """Extract action items from a Copilot-generated Excel tracker.

    Handles varying column layouts by resolving header names against
    known aliases, then normalizing each row to the canonical schema.
    """
    wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
    ws = wb.active

    rows = list(ws.iter_rows(values_only=True))
    wb.close()

    if not rows:
        return []

    headers = [str(h).strip() if h else None for h in rows[0]]
    col_map = _resolve_column_map(headers)

    if "Action Item Description" not in col_map:
        raise ValueError(
            f"Could not find an action item column in headers: {headers}. "
            f"Expected one of: {COLUMN_ALIASES['Action Item Description']}"
        )

    items = []
    for row in rows[1:]:
        def _get(field: str):
            idx = col_map.get(field)
            if idx is None or idx >= len(row):
                return None
            return row[idx]

        description = _get("Action Item Description")
        if not description or str(description).strip() == "":
            continue

        item = {
            "Document Date": _normalize_date(_get("Start / Informed Date")),
            "Sprint": "",
            "Project Name": "",
            "Team / Function": str(_get("Team / Function") or ""),
            "Priority": _normalize_priority(_get("Priority")),
            "Action Item Description": str(description).strip(),
            "Ticket / Reference ID": str(_get("Ticket / Reference ID") or ""),
            "Owner (Full Name)": str(_get("Owner (Full Name)") or ""),
            "Start / Informed Date": _normalize_date(_get("Start / Informed Date")),
            "Due Date": _normalize_date(_get("Due Date")),
            "Delivery Status": _normalize_status(_get("Delivery Status")),
            "Delivery Date": _normalize_date(_get("Delivery Date")),
            "Dependencies / Blockers": str(_get("Dependencies / Blockers") or ""),
            "Risk Level": str(_get("Risk Level") or ""),
            "Impact if Delayed": str(_get("Impact if Delayed") or ""),
            "Urgency Flag": "",
            "Change Since Last Stand-up": "",
            "Notes / Context": str(_get("Notes / Context") or ""),
        }

        if item["Owner (Full Name)"] in ("None", ""):
            item["Owner (Full Name)"] = ""
        if item["Delivery Status"] in ("None", ""):
            item["Delivery Status"] = "Not Started"

        items.append(item)

    return items


def load_copilot_json(filepath: str) -> List[dict]:
    """Load action items directly from a Copilot-generated JSON file.

    Copilot's JSON already matches the ShowRunner schema when using the v2
    prompt. This function normalizes N/A and escaped values to clean strings.
    """
    with open(filepath) as f:
        raw_items = json.load(f)

    NA_VALUES = {"N/A", "N\\/A", "n/a", "None", "none", ""}

    items = []
    for raw in raw_items:
        item = {}
        for key, val in raw.items():
            clean_key = key.replace("\\/", "/")
            if isinstance(val, str):
                clean_val = val.replace("\\/", "/")
                if clean_val in NA_VALUES:
                    clean_val = ""
                item[clean_key] = clean_val
            else:
                item[clean_key] = val if val is not None else ""
        items.append(item)

    return items


def _extract_owner_from_line(line: str) -> str:
    """Try to extract an owner name from common patterns in Word doc text."""
    patterns = [
        r'[Oo]wner:\s*(.+?)(?:\s*[—–\-|]|$)',
        r'[Aa]ssigned\s+to:\s*(.+?)(?:\s*[—–\-|]|$)',
        r'[—–]\s*([A-Z][a-z]+ [A-Z][a-z]+)\s*(?:[—–\-|]|$)',
        r'\(([A-Z][a-z]+ [A-Z][a-z]+)\)\s*$',
    ]
    for pattern in patterns:
        match = re.search(pattern, line)
        if match:
            name = match.group(1).strip().rstrip(".,;:")
            if 2 <= len(name.split()) <= 4 and not any(
                kw in name.lower() for kw in ("status", "priority", "date", "sprint", "n/a")
            ):
                return name
    return ""


def _extract_status_from_line(line: str) -> str:
    """Try to extract a delivery status from text."""
    lower = line.lower()
    for raw, normalized in STATUS_NORMALIZE.items():
        if raw in lower:
            return normalized
    return "Not Started"


def parse_word_standup(filepath: str) -> dict:
    """Extract structured sections from a Copilot-generated Word document.

    Uses macOS textutil to convert .docx to plain text, then parses
    the content into sections based on known heading patterns. Extracts
    action items, post-scrum discussion topics with outcomes, risks,
    and follow-ups.
    """
    result = subprocess.run(
        ["textutil", "-convert", "txt", "-stdout", filepath],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"textutil failed: {result.stderr}")

    text = result.stdout
    sections = {
        "metadata": {},
        "discussion_points": [],
        "action_items": [],
        "post_scrum_topics": [],
        "risks": [],
        "followups": [],
        "source_file": filepath,
    }

    SECTION_MARKERS = {
        "action_items": [
            "action item", "action items summary", "action items tracker",
        ],
        "post_scrum": [
            "post-scrum", "post scrum", "parking lot",
        ],
        "risks": [
            "risk", "early warning", "dependencies / risk",
        ],
        "followups": [
            "follow-up", "follow up", "next stand-up", "follow-ups for next",
        ],
        "discussion": [
            "discussion point", "key topics", "discussion summary",
        ],
        "decisions": [
            "decisions made", "decisions needed",
        ],
    }

    current_section = None
    current_priority = "Medium"
    current_post_scrum_topic = None

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        lower = line.lower()

        if "date:" in lower and not sections["metadata"].get("date"):
            date_match = re.search(r'(\w+ \d{1,2}, \d{4})', line)
            if date_match:
                sections["metadata"]["date"] = _normalize_date(date_match.group(1))

        if "sprint" in lower and (":" in line) and not sections["metadata"].get("sprint"):
            sprint_match = re.search(r'[Ss]print[:\s]+(.+?)(?:\s*[|]|$)', line)
            if sprint_match:
                sections["metadata"]["sprint"] = sprint_match.group(1).strip()

        detected_section = None
        for section_name, markers in SECTION_MARKERS.items():
            if any(lower.startswith(m) or lower == m for m in markers):
                detected_section = section_name
                break

        if detected_section:
            if current_post_scrum_topic and current_section == "post_scrum":
                sections["post_scrum_topics"].append(current_post_scrum_topic)
                current_post_scrum_topic = None
            current_section = detected_section
            current_priority = "Medium"
            continue

        if line.startswith("---") or line.startswith("==="):
            continue

        if current_section == "action_items":
            if lower in ("critical", "high", "medium", "low"):
                current_priority = lower.capitalize()
                continue

            cleaned = line.lstrip("•-–*123456789.) ").strip()
            if not cleaned:
                continue

            owner = _extract_owner_from_line(cleaned)
            status = _extract_status_from_line(cleaned)

            desc = cleaned
            if owner:
                desc = re.sub(
                    r'\s*[—–\-]\s*' + re.escape(owner) + r'\s*', ' ', desc
                ).strip()
                desc = re.sub(
                    r'\s*[Oo]wner:\s*' + re.escape(owner) + r'\s*', ' ', desc
                ).strip()
                desc = re.sub(r'\(' + re.escape(owner) + r'\)\s*', '', desc).strip()

            desc = desc.rstrip("—–- ").strip()

            if len(desc) < 5:
                continue

            sections["action_items"].append({
                "Document Date": sections["metadata"].get("date", ""),
                "Sprint": sections["metadata"].get("sprint", ""),
                "Project Name": "",
                "Team / Function": "",
                "Priority": current_priority,
                "Action Item Description": desc,
                "Ticket / Reference ID": "",
                "Owner (Full Name)": owner,
                "Start / Informed Date": sections["metadata"].get("date", ""),
                "Due Date": "",
                "Delivery Status": status,
                "Delivery Date": "",
                "Dependencies / Blockers": "",
                "Risk Level": "",
                "Impact if Delayed": "",
                "Urgency Flag": "",
                "Change Since Last Stand-up": "",
                "Notes / Context": f"Extracted from {Path(filepath).name}",
            })

        elif current_section == "post_scrum":
            cleaned = line.lstrip("•-–*123456789.) ").strip()
            if not cleaned:
                continue

            if any(cleaned.lower().startswith(k) for k in ("topic", "question")):
                if current_post_scrum_topic:
                    sections["post_scrum_topics"].append(current_post_scrum_topic)
                current_post_scrum_topic = {
                    "topic": re.sub(r'^[Tt]opic\s*/?\s*[Qq]uestion:\s*', '', cleaned).strip(),
                    "context": "",
                    "outcome": "",
                }
            elif current_post_scrum_topic:
                if cleaned.lower().startswith("context"):
                    current_post_scrum_topic["context"] = re.sub(
                        r'^[Cc]ontext:\s*', '', cleaned
                    ).strip()
                elif cleaned.lower().startswith("outcome"):
                    current_post_scrum_topic["outcome"] = re.sub(
                        r'^[Oo]utcome:\s*', '', cleaned
                    ).strip()
                else:
                    if not current_post_scrum_topic["topic"]:
                        current_post_scrum_topic["topic"] = cleaned
                    elif not current_post_scrum_topic["outcome"]:
                        current_post_scrum_topic["outcome"] = cleaned
            else:
                current_post_scrum_topic = {
                    "topic": cleaned,
                    "context": "",
                    "outcome": "",
                }

        elif current_section == "risks":
            cleaned = line.lstrip("•-–*123456789.) ").strip()
            if cleaned:
                sections["risks"].append(cleaned)

        elif current_section == "followups":
            cleaned = line.lstrip("•-–*123456789.) ").strip()
            if cleaned:
                sections["followups"].append(cleaned)

    if current_post_scrum_topic and current_section == "post_scrum":
        sections["post_scrum_topics"].append(current_post_scrum_topic)

    return sections


def extract_items_from_word_docs(doc_paths: List[str]) -> List[dict]:
    """Extract action items from multiple Word documents and merge them.

    Parses each document using parse_word_standup() and combines the
    action items into a single deduplicated list.
    """
    all_items = []
    seen_descriptions = set()

    for path in doc_paths:
        try:
            parsed = parse_word_standup(path)
        except (RuntimeError, OSError) as e:
            print(f"  Warning: could not parse {Path(path).name}: {e}")
            continue

        for item in parsed.get("action_items", []):
            desc_key = item.get("Action Item Description", "").strip().lower()
            if desc_key and desc_key not in seen_descriptions:
                seen_descriptions.add(desc_key)
                all_items.append(item)

        for topic in parsed.get("post_scrum_topics", []):
            if not topic.get("topic"):
                continue
            outcome = topic.get("outcome", "")
            context = topic.get("context", "")
            notes = f"Post-scrum: {topic['topic']}"
            if context:
                notes += f" — Context: {context}"
            if outcome:
                notes += f" — Outcome: {outcome}"
            else:
                notes += " — Outcome: Unresolved"

            desc_key = topic["topic"].strip().lower()
            if desc_key not in seen_descriptions:
                seen_descriptions.add(desc_key)
                all_items.append({
                    "Document Date": parsed.get("metadata", {}).get("date", ""),
                    "Sprint": parsed.get("metadata", {}).get("sprint", ""),
                    "Project Name": "",
                    "Team / Function": "",
                    "Priority": "Medium",
                    "Action Item Description": topic["topic"],
                    "Ticket / Reference ID": "",
                    "Owner (Full Name)": "",
                    "Start / Informed Date": parsed.get("metadata", {}).get("date", ""),
                    "Due Date": "",
                    "Delivery Status": "Not Started",
                    "Delivery Date": "",
                    "Dependencies / Blockers": "",
                    "Risk Level": "",
                    "Impact if Delayed": "",
                    "Urgency Flag": "",
                    "Change Since Last Stand-up": "New",
                    "Notes / Context": notes,
                })

    return all_items


def _token_overlap_ratio(a: str, b: str) -> float:
    """Compute a simple token overlap similarity between two strings.

    Returns the Jaccard-like ratio: |intersection| / |smaller set|.
    Uses the smaller set as denominator so a short phrase that fully
    appears in a longer description scores 1.0.
    """
    tokens_a = set(re.findall(r'\w+', a.lower()))
    tokens_b = set(re.findall(r'\w+', b.lower()))
    if not tokens_a or not tokens_b:
        return 0.0
    overlap = len(tokens_a & tokens_b)
    return overlap / min(len(tokens_a), len(tokens_b))


def cross_reference_items(
    primary_items: List[dict],
    supplementary_items: List[dict],
    similarity_threshold: float = 0.6,
) -> List[dict]:
    """Recover action items from Word docs that were truncated in JSON/Excel.

    Compares supplementary items (from One-Pager / Executive Summary) against
    primary items (from JSON/Excel) using fuzzy token overlap. Any supplementary
    item that doesn't closely match an existing primary item is added to the
    result with a note indicating it was recovered.
    """
    if not supplementary_items:
        return primary_items

    primary_descriptions = [
        item.get("Action Item Description", "").strip().lower()
        for item in primary_items
    ]

    recovered = []
    for supp_item in supplementary_items:
        supp_desc = supp_item.get("Action Item Description", "").strip()
        if not supp_desc:
            continue

        best_score = 0.0
        for primary_desc in primary_descriptions:
            score = _token_overlap_ratio(supp_desc, primary_desc)
            best_score = max(best_score, score)

        if best_score < similarity_threshold:
            existing_notes = supp_item.get("Notes / Context", "")
            recovery_note = "Recovered from Word doc — not in JSON/Excel export"
            if existing_notes:
                supp_item["Notes / Context"] = f"{existing_notes}; {recovery_note}"
            else:
                supp_item["Notes / Context"] = recovery_note
            recovered.append(supp_item)

    if recovered:
        print(f"  Cross-reference: recovered {len(recovered)} additional item(s) from Word docs")

    return primary_items + recovered


def load_previous_action_items(output_dir: str, team: str, current_date: date) -> List[dict]:
    """Load the most recent prior day's action items JSON for carry-forward.

    Scans the output directory for JSON files matching the team, sorted by date,
    and returns the most recent one before current_date.
    """
    out = Path(output_dir)
    if not out.exists():
        return []

    candidates = []
    for f in out.glob(f"*_{team}_Action_Items.json"):
        date_str = f.name[:10]
        try:
            file_date = date.fromisoformat(date_str)
            if file_date < current_date:
                candidates.append((file_date, f))
        except ValueError:
            continue

    if not candidates:
        return []

    candidates.sort(reverse=True)
    latest = candidates[0][1]
    with open(latest) as fh:
        return json.load(fh)


def apply_carry_forward(
    today_items: List[dict],
    previous_items: List[dict],
) -> List[dict]:
    """Merge today's items with carried-forward items from yesterday.

    - Items with status Not Started / In Progress / Blocked carry forward.
    - Items marked Delivered (with Delivery Date) are dropped.
    - The 'Change Since Last Stand-up' field is set based on comparison.
    """
    if not previous_items:
        for item in today_items:
            item["Change Since Last Stand-up"] = "New"
        return today_items

    def _item_key(item: dict) -> str:
        desc = item.get("Action Item Description", "").strip().lower()
        owner = item.get("Owner (Full Name)", "").strip().lower()
        return f"{desc}||{owner}"

    prev_lookup = {}
    for item in previous_items:
        key = _item_key(item)
        prev_lookup[key] = item

    today_lookup = set()
    for item in today_items:
        key = _item_key(item)
        today_lookup.add(key)

        if key in prev_lookup:
            prev = prev_lookup[key]
            if item.get("Delivery Status") != prev.get("Delivery Status"):
                item["Change Since Last Stand-up"] = "Status Changed"
            else:
                item["Change Since Last Stand-up"] = "Unchanged"

            if not item.get("Start / Informed Date") and prev.get("Start / Informed Date"):
                item["Start / Informed Date"] = prev["Start / Informed Date"]
        else:
            item["Change Since Last Stand-up"] = "New"

    carried = []
    for key, prev_item in prev_lookup.items():
        if key not in today_lookup:
            status = prev_item.get("Delivery Status", "")
            if status in ("Not Started", "In Progress", "Blocked"):
                prev_item["Change Since Last Stand-up"] = "Unchanged"
                carried.append(prev_item)

    return today_items + carried


def apply_urgency_flags(items: List[dict], today: date) -> List[dict]:
    """Compute and set the Urgency Flag for each action item."""
    for item in items:
        due = item.get("Due Date")
        status = item.get("Delivery Status", "")
        if due and status != "Delivered":
            item["Urgency Flag"] = compute_urgency_flag(due, today)
        elif status == "Delivered":
            item["Urgency Flag"] = ""
    return items


def enrich_with_sprint_info(items: List[dict], team: str, standup_date: date) -> List[dict]:
    """Fill in Sprint and Project Name from config."""
    from utils.teams import get_team

    sprint = get_current_sprint(standup_date)
    team_config = get_team(team)

    sprint_name = sprint["name"] if sprint else ""
    project_name = team_config["project_name"] if team_config else f"MP {team}"

    for item in items:
        if not item.get("Sprint"):
            item["Sprint"] = sprint_name
        if not item.get("Project Name"):
            item["Project Name"] = project_name
        if not item.get("Team / Function"):
            item["Team / Function"] = team

    return items


def sort_items(items: List[dict]) -> List[dict]:
    """Sort by Priority (Critical > High > Medium > Low), then Due Date."""
    priority_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3, "": 4}

    def sort_key(item):
        p = priority_order.get(item.get("Priority", ""), 4)
        d = item.get("Due Date", "") or "9999-99-99"
        return (p, d)

    return sorted(items, key=sort_key)


def write_action_items_json(items: List[dict], output_path: str) -> None:
    """Write action items to a JSON file for automation ingestion."""
    with open(output_path, "w") as f:
        json.dump(items, f, indent=2, default=str)


def main():
    parser = argparse.ArgumentParser(
        description="Parse Copilot stand-up output into structured action items."
    )
    parser.add_argument("--input", required=True, help="Path to Copilot output file (.xlsx or .docx)")
    parser.add_argument("--team", required=True, help="Team ID (APPS, GSS, PLAT)")
    parser.add_argument("--date", default=str(date.today()), help="Stand-up date (YYYY-MM-DD)")
    parser.add_argument("--output-dir", default="output/", help="Output directory for JSON")
    args = parser.parse_args()

    standup_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    input_path = Path(args.input)

    print(f"Parsing {input_path.name} for team {args.team} on {args.date}...")

    if input_path.suffix == ".json":
        items = load_copilot_json(str(input_path))
    elif input_path.suffix == ".xlsx":
        items = parse_excel_action_items(str(input_path))
    elif input_path.suffix == ".docx":
        doc = parse_word_standup(str(input_path))
        items = doc.get("action_items", [])
    else:
        raise ValueError(f"Unsupported file type: {input_path.suffix}")

    print(f"  Parsed {len(items)} action items from input")

    previous = load_previous_action_items(args.output_dir, args.team, standup_date)
    if previous:
        print(f"  Loaded {len(previous)} previous items for carry-forward")

    items = apply_carry_forward(items, previous)
    items = enrich_with_sprint_info(items, args.team, standup_date)
    items = apply_urgency_flags(items, standup_date)
    items = sort_items(items)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{args.date}_{args.team}_Action_Items.json"
    write_action_items_json(items, str(output_file))
    print(f"  Wrote {len(items)} action items to {output_file}")


if __name__ == "__main__":
    main()
