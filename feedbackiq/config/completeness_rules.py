"""
Configurable completeness rules and scoring weights per Issue Type.
Deterministic business logic independent of Gemini API.
"""

from typing import Dict, Any, List

# Completeness threshold definitions
THRESHOLD_COMPLETE = 85
THRESHOLD_NEEDS_REVIEW = 60

# Scoring configurations per Issue Type
# Each rule config defines:
# - weights: numeric weights for each detected field (must total 100)
# - critical_fields: fields that MUST be present for workflow readiness
# - or_groups: list of tuples where at least one field must be populated
# - why_needed_template: explanation template for CSR
ISSUE_RULES_CONFIG: Dict[str, Dict[str, Any]] = {
    "Waiting Time": {
        "weights": {
            "hospital": 25,
            "department": 20,
            "service_type": 10,
            "incident_date": 15,
            "approximate_time": 10,
            "description_of_event": 20,
        },
        "critical_fields": ["hospital", "incident_date", "description_of_event"],
        "or_groups": [
            ("department", "service_type"),
        ],
        "time_sensitive": True,
        "explanation": "Waiting-time complaints require the hospital, clinic/department, date, and approximate time to cross-reference with queue logs."
    },
    "Staff Behavior": {
        "weights": {
            "hospital": 25,
            "department": 15,
            "service_type": 10,
            "incident_date": 15,
            "staff_role": 15,
            "staff_name": 5,
            "description_of_event": 15,
        },
        "critical_fields": ["hospital", "incident_date", "description_of_event"],
        "or_groups": [
            ("department", "service_type"),
            ("staff_role", "staff_name"),
        ],
        "time_sensitive": False,
        "explanation": "Staff conduct complaints require the hospital branch, department, and staff role/identity so unit managers can conduct a targeted inquiry."
    },
    "Billing / Payment": {
        "weights": {
            "hospital": 25,
            "incident_date": 15,
            "billing_context": 25,
            "service_type": 15,
            "description_of_event": 20,
        },
        "critical_fields": ["hospital", "billing_context", "description_of_event"],
        "or_groups": [],
        "time_sensitive": False,
        "explanation": "Billing issues require the specific hospital, transaction context (e.g., invoice, receipt, POS terminal), and incident date for financial reconciliation."
    },
    "Appointment": {
        "weights": {
            "hospital": 25,
            "department": 20,
            "service_type": 15,
            "incident_date": 20,
            "description_of_event": 20,
        },
        "critical_fields": ["hospital", "incident_date", "description_of_event"],
        "or_groups": [
            ("department", "service_type"),
        ],
        "time_sensitive": False,
        "explanation": "Appointment discrepancies require the hospital, relevant specialty/doctor, and scheduled date to audit HIS booking logs."
    },
    "Registration": {
        "weights": {
            "hospital": 25,
            "incident_date": 20,
            "department": 15,
            "service_type": 15,
            "description_of_event": 25,
        },
        "critical_fields": ["hospital", "incident_date", "description_of_event"],
        "or_groups": [
            ("department", "service_type"),
        ],
        "time_sensitive": False,
        "explanation": "Registration issues require the hospital location and date to review counter desk operations and intake logs."
    },
    "Facility / Cleanliness": {
        "weights": {
            "hospital": 30,
            "department": 20,
            "service_type": 10,
            "incident_date": 15,
            "description_of_event": 25,
        },
        "critical_fields": ["hospital", "description_of_event"],
        "or_groups": [
            ("department", "service_type"),
        ],
        "time_sensitive": False,
        "explanation": "Facility and hygiene reports need the exact hospital and specific location/floor/unit for housekeeping dispatch."
    },
    "Medical Service Process": {
        "weights": {
            "hospital": 25,
            "department": 20,
            "service_type": 15,
            "incident_date": 15,
            "staff_role": 10,
            "description_of_event": 15,
        },
        "critical_fields": ["hospital", "incident_date", "description_of_event"],
        "or_groups": [
            ("department", "service_type"),
        ],
        "time_sensitive": False,
        "explanation": "Clinical process feedback requires hospital, department, and procedure details for quality review."
    },
    "Communication": {
        "weights": {
            "hospital": 25,
            "department": 20,
            "service_type": 15,
            "incident_date": 15,
            "description_of_event": 25,
        },
        "critical_fields": ["hospital", "description_of_event"],
        "or_groups": [
            ("department", "service_type"),
        ],
        "time_sensitive": False,
        "explanation": "Communication gaps require hospital and clinic context to clarify patient instructions and follow-up messaging."
    },
    "Technical Issue": {
        "weights": {
            "hospital": 20,
            "department": 15,
            "service_type": 15,
            "incident_date": 20,
            "description_of_event": 30,
        },
        "critical_fields": ["description_of_event"],
        "or_groups": [],
        "time_sensitive": False,
        "explanation": "Technical defects require a clear description of the failing system (portal, kiosk, payment terminal) and approximate date."
    },
    "Food / Catering": {
        "weights": {
            "hospital": 30,
            "department": 20,
            "incident_date": 20,
            "description_of_event": 30,
        },
        "critical_fields": ["hospital", "description_of_event"],
        "or_groups": [],
        "time_sensitive": False,
        "explanation": "Catering feedback requires hospital and department/ward location to audit meal distribution."
    },
    "Parking / Transportation": {
        "weights": {
            "hospital": 40,
            "incident_date": 20,
            "description_of_event": 40,
        },
        "critical_fields": ["hospital", "description_of_event"],
        "or_groups": [],
        "time_sensitive": False,
        "explanation": "Parking feedback requires the specific hospital campus and description of the parking area."
    },
    "Appreciation": {
        "weights": {
            "hospital": 25,
            "department": 25,
            "staff_role": 15,
            "staff_name": 15,
            "description_of_event": 20,
        },
        "critical_fields": ["description_of_event"],
        "or_groups": [
            ("hospital", "department"),
        ],
        "time_sensitive": False,
        "explanation": "Appreciation records have lighter requirements; knowing either the hospital or department is sufficient to route commendations."
    },
    "General Suggestion": {
        "weights": {
            "hospital": 20,
            "department": 20,
            "description_of_event": 40,
            "service_type": 20,
        },
        "critical_fields": ["description_of_event"],
        "or_groups": [],
        "time_sensitive": False,
        "explanation": "General suggestions require actionable operational descriptions to assess institutional feasibility."
    },
    "Other": {
        "weights": {
            "hospital": 25,
            "department": 20,
            "incident_date": 20,
            "description_of_event": 35,
        },
        "critical_fields": ["description_of_event"],
        "or_groups": [],
        "time_sensitive": False,
        "explanation": "Uncategorized feedback requires sufficient descriptive detail and context for preliminary administrative review."
    }
}
