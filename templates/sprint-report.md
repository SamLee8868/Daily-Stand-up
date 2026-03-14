# Sprint Summary Report

| Field | Value |
|-------|-------|
| Document Date | {{ date or "YYYY-MM-DD" }} |
| Project Name | {{ sprint.get("name", "") }} |
| Team Name | {{ team_name }} |
| Sprint Number | {{ sprint.get("number", "") }} |
| Sprint Start Date | {{ sprint.get("start_date", "") }} |
| Sprint End Date | {{ sprint.get("end_date", "") }} |

---

## Section 1: Sprint Overview

- **Sprint:** {{ sprint.get("name", "") }}
- **Dates:** {{ sprint.get("start_date", "") }} to {{ sprint.get("end_date", "") }}
- **Team:** {{ team_name }}
- **Sprint Goal:** {{ sprint.get("goal", "Not documented") }}

---

## Section 2: Accomplishments

**Total items completed:** {{ metrics.get("total_completed", 0) }} of {{ metrics.get("total_tracked", 0) }}

{% for item in accomplishments %}
- {{ item.get("Action Item Description", "") }} — Owner: {{ item.get("Owner (Full Name)", "") }} — Delivered: {{ item.get("Delivery Date", "N/A") }}
{% endfor %}
{% if not accomplishments %}
- No items marked as delivered in this sprint
{% endif %}

---

## Section 3: Carryover & Incomplete Work

{% for item in carryover %}
- {{ item.get("Action Item Description", "") }} — Owner: {{ item.get("Owner (Full Name)", "") }} — Status: {{ item.get("Delivery Status", "") }} — Reason: {{ item.get("Dependencies / Blockers", "N/A") }}
{% endfor %}
{% if not carryover %}
- No carryover items
{% endif %}

---

## Section 4: Risk & Issue Log

{% for risk in risks %}
- {{ risk.get("description", "") }} — Trend: {{ risk.get("trend", "") }} — First Raised: {{ risk.get("date_raised", "") }}
{% endfor %}
{% if not risks %}
- No risks tracked in this sprint
{% endif %}

---

## Section 5: Decisions Log

{% for decision in decisions %}
- {{ decision.get("description", "") }} — Date: {{ decision.get("date", "") }}
{% endfor %}
{% if not decisions %}
- No decisions logged
{% endif %}

---

## Section 6: Key Metrics

| Metric | Value |
|--------|-------|
| Total Items Tracked | {{ metrics.get("total_tracked", 0) }} |
| Total Completed | {{ metrics.get("total_completed", 0) }} |
| Critical | {{ metrics.get("by_priority", {}).get("Critical", 0) }} |
| High | {{ metrics.get("by_priority", {}).get("High", 0) }} |
| Medium | {{ metrics.get("by_priority", {}).get("Medium", 0) }} |
| Low | {{ metrics.get("by_priority", {}).get("Low", 0) }} |

---

## Section 7: Executive Takeaways

*To be completed by ShowRunner or PM review.*

- Overall Sprint Health: **TBD**
- Key takeaway 1
- Key takeaway 2
- Key takeaway 3

---

## Section 8: Next Sprint Preview

- Known carryover items: {{ carryover | length }}
- Anticipated risks: TBD
- Key dates: TBD
