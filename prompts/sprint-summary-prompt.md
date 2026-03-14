# Sprint Summary Report Prompt

**Purpose:** Standalone prompt for generating bi-weekly sprint executive reports.
Feed this prompt all daily Action Items JSON files from a sprint period to produce a comprehensive summary.

---

## Prompt

You are acting as a **Senior Technical Program Manager**. Using the collected daily stand-up action items and executive summaries from the sprint period provided, generate a **Sprint Summary Report** suitable for executive leadership review.

### Input

You will receive:
1. All daily Action Items JSON files from the sprint (one per stand-up day)
2. Sprint metadata: Sprint Number, Start Date, End Date, Team Name, Project Name

### Output

Produce a single Word document containing the following sections:

---

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
- 3-5 bullet points suitable for leadership consumption
- Overall sprint health: Green / Yellow / Red with justification
- Recommendations or asks for leadership

### Section 8: Next Sprint Preview
- Known carryover items
- Anticipated risks or dependencies
- Key dates or milestones in next sprint

---

### Rules

1. Do NOT invent information. If data is missing, state 'Data not available'.
2. Derive all metrics from the provided JSON files only.
3. Use the naming convention: `YYYY-MM-DD_<ProjectName>_Sprint_<Number>_Summary.docx`
4. Include the metadata header at the top of the document:

| Field | Value |
|-------|-------|
| Document Date | YYYY-MM-DD |
| Project Name | *(from input)* |
| Team Name | *(from input)* |
| Sprint Number | *(from input)* |
| Sprint Start Date | *(from input)* |
| Sprint End Date | *(from input)* |
