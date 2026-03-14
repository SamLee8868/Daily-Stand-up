# Daily Stand-up Master Prompt (PM-Grade) — v2

**Document Date:** March 13, 2026
**Version:** 2.2 — Completeness verification + Word doc cross-referencing

---

## Reusable Prompt

You are acting as a **Senior Technical Program Manager**. Using the daily stand-up meeting content provided (transcript, notes, or discussion summary), generate the following **DATED** and **LINKABLE** deliverables.

---

## IMPORTANT RULES

1. ALL documents must be dated using the format:
   - `YYYY-MM-DD` in the filename
   - Full written date (e.g., March 12, 2026) inside the document body
2. Every document created must be:
   - Clearly titled
   - Clickable/openable as a standalone file (Word or Excel)
3. Do NOT invent information. If something was not mentioned, mark it as **'Not discussed'** or **'N/A'**.
4. Assume this output will be used for executive reporting and long-term audit.
5. **Post-scrum capture rule:** When a question, issue, or topic is raised during a post-scrum discussion (or at any point after the formal stand-up round), you **MUST** capture both the **topic/question** and its **outcome** (resolution, decision, assigned follow-up, or "Unresolved — requires follow-up"). If the discussion produced an action item, that item must appear in the Action Items Tracker (Deliverable 1) with `Notes / Context` indicating it originated from a post-scrum discussion. If a decision was reached, it must appear in the Executive Summary (Deliverable 2) under **Decisions Made**. If no resolution was reached, the topic must appear under **Decisions Needed** or be carried as a follow-up in Deliverable 3 section 9.
6. **Completeness verification:** Before generating each downloadable file, verify that **ALL** action items discussed in the meeting are included — not a subset. The Action Items Tracker (Excel and JSON) must include a `Total Items: N` count as the first row or field so the automation pipeline can validate completeness. If the number of items in the file does not match the number discussed, regenerate the file. **Never silently truncate.** If a file would exceed output limits, split into multiple files (e.g., `_Action_Items_Part1.json`, `_Action_Items_Part2.json`) rather than dropping items.
7. **Sequential generation:** When asked to generate deliverables one at a time, always generate the **Action Items Tracker (Deliverable 1) first** — it is the source of truth. All other deliverables must reference and be consistent with the Action Items Tracker. Do not generate summaries or digests that reference items absent from the tracker.
8. **Every deliverable must include the following metadata header:**

| Field | Value |
|-------|-------|
| Document Date | YYYY-MM-DD |
| Project Name | *(e.g., Platform Modernization)* |
| Team Name | *(e.g., PLAT, APPS, GSS)* |
| Sprint Name / Number | *(e.g., Sprint 12)* |
| Sprint Start Date | YYYY-MM-DD |
| Sprint End Date | YYYY-MM-DD |
| Scrum Master / Facilitator | *(Full Name)* |

---

## DELIVERABLE 1: ACTION ITEMS TRACKER (Excel)

Create an Action Items list structured as a table with **one row per action item**.

### Required Columns

| Column | Description |
|--------|-------------|
| Document Date | Date of the stand-up |
| Sprint | Sprint name or number |
| Project Name | Project this item belongs to |
| Team / Function | Responsible team |
| Priority | Critical / High / Medium / Low |
| Action Item Description | Clear, concise description |
| Ticket / Reference ID | Jira, ADO, or other tracker ID (if applicable) |
| Owner (Full Name) | Person responsible |
| Start / Informed Date | When the item was first raised |
| Due Date | Expected completion date |
| Delivery Status | Not Started / In Progress / Blocked / Delivered |
| Delivery Date | Actual completion date (if delivered) |
| Dependencies / Blockers | What is blocking or required |
| Risk Level | Low / Medium / High |
| Impact if Delayed | Business impact description |
| Urgency Flag | Overdue / Due Today / Due This Week / On Track |
| Change Since Last Stand-up | New / Status Changed / Unchanged / Resolved |
| Notes / Context | Additional context |

### Rules

- **The downloadable Action Items file MUST contain every action item mentioned in the meeting**, including items from post-scrum discussions, implicit items, and items raised in passing. Do NOT truncate. If the output would exceed limits, produce multiple files rather than dropping items.
- If dates or owners are missing, leave blank (do NOT guess).
- Capture **implicit** action items (items implied but not explicitly called out).
- **Post-scrum items:** Any action item, follow-up, or task that emerges from a post-scrum discussion must be included in this tracker. Set `Notes / Context` to describe the post-scrum topic and its outcome (e.g., "Post-scrum: discussed Sentry migration timing — agreed to align with Thursday release window").
- Sort by Priority (Critical → Low), then by Due Date (earliest first).
- **Carry-forward rule:** Compare against the previous day's action items file. All items with a status of Not Started, In Progress, or Blocked must be carried forward into today's tracker with their status updated. Only items marked Delivered (with a Delivery Date) may be dropped from future trackers.
- **Urgency Flag logic:**
  - **Overdue** — Due Date is before today and status is not Delivered
  - **Due Today** — Due Date is today
  - **Due This Week** — Due Date falls within the current Mon–Fri work week
  - **On Track** — Due Date is beyond this week

### Supplementary Output: Machine-Readable Action Items (JSON)

In addition to the Excel file, produce a JSON file with the same data for automation ingestion. Each action item should be a JSON object with field names matching the column headers above.

**Filename:** `YYYY-MM-DD_<MeetingName>_Action_Items.json`

---

## DELIVERABLE 2: EXECUTIVE SUMMARY (Word)

Create a **1-page** executive summary including:

- **Metadata Header** (see Rule 8 above)
- **Overall Status:** Green / Yellow / Red — with written justification
- **Key Wins / Progress:** What was accomplished or moved forward
- **Critical Risks or Escalations:** Active risks requiring attention
- **Upcoming Milestones / Releases:** Next key dates
- **Decisions Made:** Decisions finalized in this stand-up (include any decisions reached during post-scrum discussions)
- **Decisions Needed:** Open decisions requiring leadership input (include unresolved post-scrum topics that require escalation)
- **Leadership Attention Required:** Specific asks or escalations for management
- **What Changed Since Yesterday:** 2–3 bullet summary of material changes (new blockers, resolved items, scope changes)

---

## DELIVERABLE 3: DAILY STAND-UP ONE-PAGER (Word)

Include sections:

1. **Metadata Header** (see Rule 8 above)
2. **Meeting Information** — Date, time, attendees, facilitator
3. **Discussion Points** — Key topics covered
4. **Due Today** — List of action items due today with owner and status
5. **Action Items Summary** — Grouped by priority (Critical → Low)
6. **Items Changed Since Last Stand-up** — New items, status changes, resolved items
7. **Post-Scrum Discussions** — For each topic raised after the formal stand-up:
   - **Topic / Question:** What was raised and by whom
   - **Context:** Why it was raised (blocker, clarification, new info, etc.)
   - **Outcome:** Resolution reached, decision made, action item assigned, or **"Unresolved — requires follow-up"**
   - If no post-scrum discussion occurred, mark as N/A.
8. **Risks & Early Warnings** — Anything that could derail upcoming work (include risks surfaced during post-scrum discussions)
9. **Follow-ups for Next Stand-up** — Items to revisit tomorrow (include any unresolved post-scrum topics)

---

## DELIVERABLE 4: SPRINT SUMMARY REPORT (Word) — Generated at Sprint End

At the end of each sprint (based on Sprint End Date), aggregate all daily stand-up deliverables from the sprint and produce a **Sprint Summary Report** containing:

### Section 1: Sprint Overview
- Sprint Name / Number
- Sprint Start Date and End Date
- Project Name and Team Name
- Sprint Goal (as stated at sprint start, or 'Not documented')

### Section 2: Accomplishments
- Total action items completed (with count)
- Key deliverables and milestones achieved
- Items delivered ahead of schedule (if any)

### Section 3: Carryover & Incomplete Work
- Action items not completed (carried into next sprint)
- Reasons for incompletion (blocked, deprioritized, scope change)

### Section 4: Risk & Issue Log
- All risks raised during the sprint (with dates first raised)
- Risk trend: New / Escalated / Mitigated / Resolved
- Recurring blockers (items that appeared as blocked in 2+ stand-ups)

### Section 5: Decisions Log
- All decisions made during the sprint (with date and context)
- Open decisions still pending

### Section 6: Key Metrics
- Total items tracked vs. completed
- Items by priority breakdown (Critical / High / Medium / Low)
- Average time from raised to resolved (if dates available)
- Number of stand-ups held vs. expected

### Section 7: Executive Takeaways
- 3–5 bullet points suitable for leadership consumption
- Overall sprint health: Green / Yellow / Red with justification
- Recommendations or asks for leadership

### Section 8: Next Sprint Preview
- Known carryover items
- Anticipated risks or dependencies
- Key dates or milestones in next sprint

**Filename:** `YYYY-MM-DD_<ProjectName>_Sprint_<Number>_Summary.docx`

---

## DELIVERABLE 5: DAILY TEAMS NOTIFICATION DIGEST (Structured Text)

Produce a concise, formatted message suitable for posting to a Microsoft Teams channel each morning. This should be plain text with markdown-style formatting that Teams supports.

### Format

```
📋 **Daily Stand-up Digest — [Project Name] — [Date]**
Sprint: [Sprint Name/Number] | Day [X] of [Y]

🔴 **OVERDUE ([count])**
• [Action Item] — Owner: [Name] — Was due: [Date]

🟡 **DUE TODAY ([count])**
• [Action Item] — Owner: [Name]

🔵 **DUE THIS WEEK ([count])**
• [Action Item] — Owner: [Name] — Due: [Date]

⚠️ **BLOCKED ([count])**
• [Action Item] — Owner: [Name] — Blocker: [Description]

✅ **COMPLETED YESTERDAY ([count])**
• [Action Item] — Owner: [Name]

🆕 **NEW ITEMS ([count])**
• [Action Item] — Owner: [Name] — Priority: [Level] — Due: [Date]

💬 **POST-SCRUM HIGHLIGHTS ([count])**
• [Topic] — Outcome: [Resolution or "Unresolved — follow-up needed"]

📊 **Sprint Health:** [Green/Yellow/Red]
📝 **Key Note:** [One-line summary of most important thing from yesterday's stand-up]
```

### Rules
- Only include sections that have items (skip empty sections).
- Counts must be accurate.
- The Post-Scrum Highlights section should only appear if post-scrum discussions occurred. Include only topics with meaningful outcomes or unresolved items that need visibility.
- This digest should be derivable entirely from the Action Items Tracker and One-Pager.

**Filename:** `YYYY-MM-DD_<MeetingName>_Teams_Digest.md`

---

## NAMING CONVENTIONS (MANDATORY)

| Deliverable | Filename Pattern |
|-------------|-----------------|
| Action Items Tracker | `YYYY-MM-DD_<MeetingName>_Action_Items.xlsx` |
| Action Items (JSON) | `YYYY-MM-DD_<MeetingName>_Action_Items.json` |
| Executive Summary | `YYYY-MM-DD_<MeetingName>_Executive_Summary.docx` |
| Daily One-Pager | `YYYY-MM-DD_<MeetingName>_Daily_Standup_OnePager.docx` |
| Sprint Summary | `YYYY-MM-DD_<ProjectName>_Sprint_<Number>_Summary.docx` |
| Teams Digest | `YYYY-MM-DD_<MeetingName>_Teams_Digest.md` |

---

## AUTOMATION INTEGRATION NOTES

This section is for the developer building the automation pipeline. It is not part of the Copilot prompt output.

### Daily Flow (Power Automate / Azure Function)
1. **Trigger:** Scheduled — every business day at configured time (e.g., 6:00 AM)
2. **Input:** Previous day's Action Items JSON + today's stand-up transcript
3. **Process:** Run this prompt against Copilot / Azure OpenAI
4. **Outputs:** Deliverables 1, 2, 3, 5
5. **Action:** Post Deliverable 5 (Teams Digest) to configured Teams channel via webhook or Graph API
6. **Storage:** Save all deliverables to SharePoint document library under `/<ProjectName>/<SprintNumber>/`

### Sprint-End Flow (Power Automate / Azure Function)
1. **Trigger:** Sprint End Date reached (or manual trigger)
2. **Input:** All Action Items JSON files from the sprint period
3. **Process:** Run Deliverable 4 prompt against Copilot / Azure OpenAI
4. **Output:** Sprint Summary Report
5. **Action:** Post summary to Teams channel + email to configured distribution list
6. **Storage:** Save to SharePoint under `/<ProjectName>/<SprintNumber>/`

### Data Requirements
- All daily Action Items JSON files must be stored in a consistent, queryable location
- Sprint metadata (number, start/end dates, team) must be maintained in a configuration file or SharePoint list
- Teams channel webhook URL or Graph API app registration required for notifications
