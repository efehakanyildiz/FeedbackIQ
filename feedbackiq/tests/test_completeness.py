"""
Unit tests for FeedbackIQ completeness rules and scoring logic.
"""

import pytest
from feedbackiq.models.schemas import (
    ExtractedFeedbackData,
    FeedbackType,
    IssueType,
    SentimentType,
    CompletenessStatus,
    FollowUpPriority,
)
from feedbackiq.services.completeness_service import evaluate_completeness


def test_missing_hospital_lowers_score_and_triggers_followup():
    """Verify that omitting hospital lowers score and sets status to Follow-up Required."""
    data = ExtractedFeedbackData(
        feedback_type=FeedbackType.COMPLAINT,
        issue_type=IssueType.WAITING_TIME,
        sentiment=SentimentType.NEGATIVE,
        hospital=None,  # Missing critical field
        department="Cardiology",
        incident_date="yesterday",
        approximate_time="14:00",
        description_of_event="Waited for 45 minutes past appointment time.",
        extraction_confidence=0.85
    )
    result = evaluate_completeness(data)

    assert not result.is_complete
    assert "hospital" in result.missing_fields
    assert "hospital" in result.critical_missing_fields
    assert result.status == CompletenessStatus.FOLLOW_UP_REQUIRED
    assert result.completeness_score < 85


def test_complete_waiting_time_reaches_complete_status():
    """Verify that a fully populated waiting time complaint is marked Complete."""
    data = ExtractedFeedbackData(
        feedback_type=FeedbackType.COMPLAINT,
        issue_type=IssueType.WAITING_TIME,
        sentiment=SentimentType.NEGATIVE,
        hospital="Medicana Atakoy Hospital",
        department="Cardiology",
        incident_date="2026-10-03",
        approximate_time="14:00",
        service_type="Outpatient consult",
        description_of_event="Waited 45 minutes despite confirmed appointment and no queue announcement was made.",
        extraction_confidence=0.95
    )
    result = evaluate_completeness(data)

    assert result.is_complete
    assert result.status == CompletenessStatus.COMPLETE
    assert result.completeness_score >= 85
    assert len(result.critical_missing_fields) == 0


def test_appreciation_has_lighter_requirements():
    """Verify that appreciation feedback can be marked Complete with lighter requirements."""
    data = ExtractedFeedbackData(
        feedback_type=FeedbackType.APPRECIATION,
        issue_type=IssueType.APPRECIATION,
        sentiment=SentimentType.POSITIVE,
        hospital="Medicana Kadikoy",
        department=None,
        description_of_event="The oncology nursing staff was wonderfully supportive throughout my mother's infusion.",
        extraction_confidence=0.9
    )
    result = evaluate_completeness(data)

    # Appreciation with hospital and description should not be stuck in Follow-up Required
    assert "hospital" not in result.critical_missing_fields
    assert result.completeness_score >= 60


def test_adding_followup_information_increases_score():
    """Verify that CSR follow-up overrides increase score and change status from Follow-up Required to Complete."""
    initial_data = ExtractedFeedbackData(
        feedback_type=FeedbackType.COMPLAINT,
        issue_type=IssueType.WAITING_TIME,
        sentiment=SentimentType.NEGATIVE,
        hospital=None,
        department=None,
        incident_date="yesterday",
        approximate_time=None,
        description_of_event="Waited for a very long time and nobody explained the delay.",
        extraction_confidence=0.75
    )
    initial_res = evaluate_completeness(initial_data)
    assert initial_res.status == CompletenessStatus.FOLLOW_UP_REQUIRED
    assert initial_res.completeness_score < 60

    # CSR contacts patient and collects missing fields
    csr_collected = {
        "hospital": "Medicana Camlica Hospital",
        "department": "Cardiology",
        "approximate_time": "14:30",
        "service_type": "Echo Doppler"
    }
    updated_res = evaluate_completeness(initial_data, confirmed_overrides=csr_collected)

    assert updated_res.completeness_score > initial_res.completeness_score
    assert updated_res.completeness_score >= 85
    assert updated_res.status == CompletenessStatus.COMPLETE
    assert "hospital" not in updated_res.missing_fields


def test_manually_confirmed_values_take_precedence():
    """Verify that CSR confirmed overrides strictly override AI data."""
    data = ExtractedFeedbackData(
        feedback_type=FeedbackType.COMPLAINT,
        issue_type=IssueType.STAFF_BEHAVIOR,
        sentiment=SentimentType.NEGATIVE,
        hospital="Wrong Hospital AI Guess",
        department="Pediatrics",
        incident_date="2026-10-02",
        description_of_event="Staff member was dismissive at desk.",
        staff_role="Receptionist",
        extraction_confidence=0.6
    )
    overrides = {
        "hospital": "Confirmed Central Hospital",
        "staff_name": "Nurse Sarah"
    }
    res = evaluate_completeness(data, confirmed_overrides=overrides)
    assert res.detected_fields["hospital"] == "Confirmed Central Hospital"


def test_question_generator_asks_only_about_missing_fields():
    """Verify suggested questions are generated strictly for missing fields."""
    data = ExtractedFeedbackData(
        feedback_type=FeedbackType.COMPLAINT,
        issue_type=IssueType.BILLING_PAYMENT,
        sentiment=SentimentType.NEGATIVE,
        hospital="Medicana Bahcelievler",
        incident_date="2026-10-01",
        billing_context=None,  # Missing
        description_of_event="Charged twice for lab test.",
        extraction_confidence=0.88
    )
    res = evaluate_completeness(data)

    question_fields = [item.field_name for item in res.missing_field_items]
    assert "billing_context" in question_fields
    assert "hospital" not in question_fields
    assert "incident_date" not in question_fields


def test_no_duplicate_missing_fields():
    """Verify missing fields list contains unique entries."""
    data = ExtractedFeedbackData(
        feedback_type=FeedbackType.COMPLAINT,
        issue_type=IssueType.WAITING_TIME,
        sentiment=SentimentType.NEGATIVE,
        hospital=None,
        description_of_event="Waited forever."
    )
    res = evaluate_completeness(data)
    assert len(res.missing_fields) == len(set(res.missing_fields))
