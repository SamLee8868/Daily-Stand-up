# Executive Summary

| Field | Value |
|-------|-------|
| Document Date | {{ date }} |
| Project Name | {{ project_name }} |
| Team Name | {{ team_name }} |
| Sprint | {{ sprint.name }} |
| Sprint Dates | {{ sprint.start_date }} to {{ sprint.end_date }} |
| Facilitator | {{ facilitator }} |

---

## Overall Status: {{ overall_status }}

{{ status_justification }}

---

## Key Wins / Progress

{% for win in wins %}
- {{ win }}
{% endfor %}
{% if not wins %}
- N/A
{% endif %}

---

## Critical Risks or Escalations

{% for risk in risks %}
- {{ risk }}
{% endfor %}
{% if not risks %}
- None reported
{% endif %}

---

## Upcoming Milestones / Releases

{% for milestone in milestones %}
- {{ milestone }}
{% endfor %}
{% if not milestones %}
- N/A
{% endif %}

---

## Decisions Made

{% for decision in decisions_made %}
- {{ decision }}
{% endfor %}
{% if not decisions_made %}
- None
{% endif %}

## Decisions Needed

{% for decision in decisions_needed %}
- {{ decision }}
{% endfor %}
{% if not decisions_needed %}
- None
{% endif %}

---

## Leadership Attention Required

{% for item in leadership_attention %}
- {{ item }}
{% endfor %}
{% if not leadership_attention %}
- No escalations at this time
{% endif %}

---

## What Changed Since Yesterday

{% for change in changes %}
- {{ change }}
{% endfor %}
{% if not changes %}
- No material changes
{% endif %}
