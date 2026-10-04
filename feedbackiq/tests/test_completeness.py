"""
Unit tests for FeedbackIQ completeness rules and 3-tier triage logic:
- Tier 1: Sufficient data -> Approved
- Tier 2: Minor missing data -> AI Voice Bot Call
- Tier 3: Major missing data -> CSR Escalation
"""

import pytest
from feedbackiq.models.schemas import (
    ExtractedFeedbackData,
    FeedbackType,
    IssueType,
    SentimentType,
    CompletenessStatus,
    TriageTier,
    FollowUpPriority,
)
from feedbackiq.services.completeness_service import evaluate_completeness


def test_sufficient_data_reaches_tier_1_approved():
    """Verify that a fully populated waiting time complaint reaches Tier 1 Approved."""
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

    assert result.is_complete is True
    assert result.status == CompletenessStatus.APPROVED
    assert result.triage_tier == TriageTier.TIER_1_APPROVED
    assert result.completeness_score >= 80
    assert len(result.critical_missing_fields) == 0


def test_minor_gap_reaches_tier_2_ai_call():
    """Verify that a complaint with only minor missing data is routed to Tier 2 AI Call."""
    data = ExtractedFeedbackData(
        feedback_type=FeedbackType.COMPLAINT,
        issue_type=IssueType.WAITING_TIME,
        sentiment=SentimentType.NEGATIVE,
        hospital="Medicana Atakoy Hospital",
        department="Cardiology",
        incident_date="yesterday",
        approximate_time=None,  # Only time is missing (minor gap)
        description_of_event="Waited for a long time past my appointment yesterday.",
        extraction_confidence=0.88
    )
    result = evaluate_completeness(data)

    assert result.is_complete is False
    assert result.triage_tier == TriageTier.TIER_2_AI_CALL
    assert result.status == CompletenessStatus.AI_CALL_SCHEDULED
    assert result.requires_ai_call is True
    assert "approximate_time" in result.missing_fields


def test_major_gap_reaches_tier_3_csr_escalation():
    """Verify that missing hospital and multiple critical fields escalates to Tier 3 CSR."""
    data = ExtractedFeedbackData(
        feedback_type=FeedbackType.COMPLAINT,
        issue_type=IssueType.BILLING_PAYMENT,
        sentiment=SentimentType.NEGATIVE,
        hospital=None,  # Missing critical hospital
        department=None,
        incident_date="yesterday",
        billing_context=None,  # Missing critical context
        description_of_event="I was charged twice.",
        extraction_confidence=0.75
    )
    result = evaluate_completeness(data)

    assert result.is_complete is False
    assert result.triage_tier == TriageTier.TIER_3_CSR_ESCALATION
    assert result.status == CompletenessStatus.CSR_ESCALATION
    assert result.requires_csr_escalation is True
    assert "hospital" in result.critical_missing_fields


def test_appreciation_has_lighter_requirements():
    """Verify that appreciation feedback can be marked Approved with lighter requirements."""
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

    assert "hospital" not in result.critical_missing_fields
    assert result.completeness_score >= 60


def test_adding_followup_information_increases_score_and_resolves():
    """Verify that follow-up overrides increase score and change status to Approved."""
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
    assert initial_res.triage_tier == TriageTier.TIER_3_CSR_ESCALATION

    # Collected details
    collected = {
        "hospital": "Medicana Camlica Hospital",
        "department": "Cardiology",
        "approximate_time": "14:30",
        "service_type": "Echo Doppler"
    }
    updated_res = evaluate_completeness(initial_data, confirmed_overrides=collected)

    assert updated_res.completeness_score > initial_res.completeness_score
    assert updated_res.completeness_score >= 80
    assert updated_res.triage_tier == TriageTier.TIER_1_APPROVED


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
        billing_context=None,
        description_of_event="Charged twice for lab test.",
        extraction_confidence=0.88
    )
    res = evaluate_completeness(data)

    question_fields = [item.field_name for item in res.missing_field_items]
    assert "billing_context" in question_fields
    assert "hospital" not in question_fields


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
