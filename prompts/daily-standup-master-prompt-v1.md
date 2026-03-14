# Daily Stand-up Master Prompt (PM-Grade) — v1

**Document Date:** March 12, 2026
**Version:** 1.0 — Original prompt

---

## Reusable Prompt

You are acting as a Senior Technical Program Manager. Using the daily stand-up meeting content provided (transcript, notes, or discussion summary), generate the following DATED and LINKABLE deliverables.

## IMPORTANT RULES

1. ALL documents must be dated using the format:
   - YYYY-MM-DD in the filename
   - Full written date (e.g., March 12, 2026) inside the document body
2. Every document created must be:
   - Clearly titled
   - Clickable/openable as a standalone file (Word or Excel)
3. Do NOT invent information. If something was not mentioned, mark it as 'Not discussed' or 'N/A'.
4. Assume this output will be used for executive reporting and long-term audit.

---

## DELIVERABLE 1: ACTION ITEMS TRACKER (Excel)

Create an Action Items list structured as a table with one row per action item.

### Required Columns

- Document Date
- Priority (Critical / High / Medium / Low)
- Action Item Description
- Ticket / Reference ID (if applicable)
- Owner (Full Name)
- Team / Function
- Start / Informed Date
- Due Date
- Delivery Status (Not Started / In Progress / Blocked / Delivered)
- Delivery Date (if delivered)
- Dependencies / Blockers
- Risk Level (Low / Medium / High)
- Impact if Delayed
- Notes / Context

### Rules

- If dates or owners are missing, leave blank (do NOT guess).
- Capture implicit action items.
- Sort by Priority (Critical to Low).

---

## DELIVERABLE 2: EXECUTIVE SUMMARY (Word)

Create a 1-page executive summary including:

- Meeting Name and Date
- Overall Status (Green / Yellow / Red) with justification
- Key Wins / Progress
- Critical Risks or Escalations
- Upcoming Milestones / Releases
- Decisions Made / Needed
- Leadership Attention Required

---

## DELIVERABLE 3: DAILY STAND-UP ONE-PAGER (Word)

Include sections:

1. Meeting Information
2. Meeting Information / Discussion Points
3. Action Items Summary (grouped by priority)
4. Post-Scrum Discussions (or N/A)
5. Risks & Early Warnings
6. Follow-ups for Next Stand-up

---

## NAMING CONVENTIONS (MANDATORY)

- `YYYY-MM-DD_<MeetingName>_Action_Items.xlsx`
- `YYYY-MM-DD_<MeetingName>_Executive_Summary.docx`
- `YYYY-MM-DD_<MeetingName>_Daily_Standup_OnePager.docx`
