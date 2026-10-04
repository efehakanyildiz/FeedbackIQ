"""
Deterministic follow-up question templates and field display mappings.
Only missing fields trigger follow-up questions.
"""

FIELD_DISPLAY_NAMES = {
    "hospital": "Hospital / Facility Name",
    "department": "Department / Clinic",
    "incident_date": "Incident Date",
    "approximate_time": "Approximate Time",
    "service_type": "Service or Procedure Type",
    "staff_role": "Staff Role / Title",
    "staff_name": "Staff Name",
    "billing_context": "Billing / Payment Context",
    "description_of_event": "Detailed Incident Description",
    "impact": "Operational Impact",
}

QUESTION_TEMPLATES = {
    "hospital": "Which hospital or facility did you visit?",
    "department": "Which department or unit did you receive service from?",
    "incident_date": "On which date did the incident occur?",
    "approximate_time": "Approximately what time did the incident occur?",
    "service_type": "Which service or examination were you receiving when this occurred?",
    "staff_role": "Do you remember the role of the staff member involved, such as doctor, nurse, or registration clerk?",
    "staff_name": "Do you happen to remember the name of the staff member involved?",
    "billing_context": "Could you provide more specific information regarding the billing or payment discrepancy?",
    "description_of_event": "Could you briefly describe exactly what happened in more detail?",
    "impact": "Could you describe how this incident impacted your care or schedule?",
}


def get_question_for_field(field_name: str) -> str:
    """Return standard deterministic question for missing field."""
    return QUESTION_TEMPLATES.get(
        field_name,
        f"Could you please provide more details regarding {FIELD_DISPLAY_NAMES.get(field_name, field_name)}?"
    )


def get_field_display_name(field_name: str) -> str:
    """Return clean human-readable name for a field."""
    return FIELD_DISPLAY_NAMES.get(field_name, field_name.replace("_", " ").title())
