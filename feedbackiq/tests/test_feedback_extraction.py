"""
Integration test for the core end-to-end acceptance criteria scenario.
Tests extraction, initial evaluation, CSR follow-up enrichment, and re-evaluation.
"""

import pytest
from feedbackiq.database.db import init_db
from feedbackiq.database.repository import save_case, get_case, get_missing_fields_for_case
from feedbackiq.services.gemini_service import extract_feedback_info
from feedbackiq.services.completeness_service import evaluate_completeness
from feedbackiq.services.followup_service import process_case_reevaluation
from feedbackiq.models.schemas import CompletenessStatus, IssueType, FeedbackType


@pytest.fixture(autouse=True)
def setup_db(tmp_path, monkeypatch):
    """Point database to temporary directory for test isolation."""
    test_db = str(tmp_path / "test_feedbackiq.db")
    monkeypatch.setenv("FEEDBACKIQ_DB_PATH", test_db)
    init_db()


def test_core_end_to_end_scenario():
    """
    Test the exact Section 32 Acceptance Criteria:
    1. Feedback text: "I waited for a very long time yesterday and nobody explained the delay."
    2. Extract: complaint, Waiting Time, negative.
    3. Low completeness score, Follow-up Required.
    4. Save case to database.
    5. Missing fields identified.
    6. Customer service follow-up: adds Example Hospital, Cardiology, 14:00.
    7. Re-evaluate case.
    8. Completeness score increases substantially.
    9. Status becomes 'Ready for Workflow'.
    """
    feedback_text = "I waited for a very long time yesterday and nobody explained the delay."

    # 1. Extraction
    extracted, is_live, err = extract_feedback_info(feedback_text)
    assert extracted.feedback_type == FeedbackType.COMPLAINT
    assert extracted.issue_type == IssueType.WAITING_TIME
    assert extracted.sentiment.value in ["negative", "mixed"]
    assert extracted.hospital is None

    # 2. Rule evaluation
    result = evaluate_completeness(extracted)
    assert result.completeness_score < 60
    assert result.status == CompletenessStatus.FOLLOW_UP_REQUIRED
    assert "hospital" in result.critical_missing_fields

    # 3. Save case to DB
    case_dict = extracted.model_dump()
    case_dict["case_id"] = "FB-TEST-001"
    case_dict["source_channel"] = "Website"
    case_dict["original_feedback"] = feedback_text
    case_id = save_case(case_dict, result)
    assert case_id == "FB-TEST-001"

    # Verify missing fields in DB
    missing_db = get_missing_fields_for_case(case_id)
    field_names = [m["field_name"] for m in missing_db]
    assert "hospital" in field_names

    # 4. Customer Service collects missing details
    confirmed_data = {
        "hospital": "Example Hospital",
        "department": "Cardiology",
        "approximate_time": "14:00"
    }

    # 5. Re-evaluate case
    updated_case, updated_result, prev_score = process_case_reevaluation(
        case_id=case_id,
        confirmed_fields=confirmed_data,
        notes="Patient contacted by phone. Confirmed visit to Cardiology at 14:00.",
        contact_status="Information Collected"
    )

    # 6. Verify significant score improvement and final status
    assert updated_result.completeness_score > prev_score
    assert updated_result.completeness_score >= 85
    assert updated_result.is_complete is True
    assert updated_case["status"] == CompletenessStatus.READY_FOR_WORKFLOW.value
    assert updated_case["hospital"] == "Example Hospital"
    assert updated_case["department"] == "Cardiology"
    assert updated_case["approximate_time"] == "14:00"
