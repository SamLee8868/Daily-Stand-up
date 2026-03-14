**Daily Stand-up Digest — {{ project_name }} — {{ date }}**
{{ sprint_info }}

{% if categories.overdue %}
**OVERDUE ({{ categories.overdue | length }})**
{% for item in categories.overdue %}
- {{ item["Action Item Description"] }} — Owner: {{ item["Owner (Full Name)"] }} — Was due: {{ item["Due Date"] }}
{% endfor %}

{% endif %}
{% if categories.due_today %}
**DUE TODAY ({{ categories.due_today | length }})**
{% for item in categories.due_today %}
- {{ item["Action Item Description"] }} — Owner: {{ item["Owner (Full Name)"] }}
{% endfor %}

{% endif %}
{% if categories.due_this_week %}
**DUE THIS WEEK ({{ categories.due_this_week | length }})**
{% for item in categories.due_this_week %}
- {{ item["Action Item Description"] }} — Owner: {{ item["Owner (Full Name)"] }} — Due: {{ item["Due Date"] }}
{% endfor %}

{% endif %}
{% if categories.blocked %}
**BLOCKED ({{ categories.blocked | length }})**
{% for item in categories.blocked %}
- {{ item["Action Item Description"] }} — Owner: {{ item["Owner (Full Name)"] }} — Blocker: {{ item.get("Dependencies / Blockers", "N/A") }}
{% endfor %}

{% endif %}
{% if categories.completed_yesterday %}
**COMPLETED YESTERDAY ({{ categories.completed_yesterday | length }})**
{% for item in categories.completed_yesterday %}
- {{ item["Action Item Description"] }} — Owner: {{ item["Owner (Full Name)"] }}
{% endfor %}

{% endif %}
{% if categories.new_items %}
**NEW ITEMS ({{ categories.new_items | length }})**
{% for item in categories.new_items %}
- {{ item["Action Item Description"] }} — Owner: {{ item["Owner (Full Name)"] }} — Priority: {{ item["Priority"] }} — Due: {{ item.get("Due Date", "TBD") }}
{% endfor %}

{% endif %}
