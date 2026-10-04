"""
Synthetic seed data generator for FeedbackIQ.
Seeds 10+ realistic demo cases spanning varied channels, issue types, and quality states.
"""

from feedbackiq.database.db import init_db
from feedbackiq.database.repository import save_case, count_cases, add_follow_up_entry, update_case_after_reevaluation
from feedbackiq.models.schemas import (
    ExtractedFeedbackData,
    FeedbackType,
    IssueType,
    SentimentType,
    ContactStatus,
    SourceChannel,
)
from feedbackiq.services.completeness_service import evaluate_completeness


SEED_CASES = [
    {
        "case_id": "FB-2026-1001",
        "created_at": "2026-10-01 09:15:00",
        "source_channel": SourceChannel.QR_CODE.value,
        "original_feedback": "I waited almost an hour yesterday and nobody told me why.",
        "extracted": ExtractedFeedbackData(
            feedback_type=FeedbackType.COMPLAINT,
            issue_type=IssueType.WAITING_TIME,
            sentiment=SentimentType.NEGATIVE,
            hospital=None,
            department=None,
            incident_date="yesterday",
            approximate_time=None,
            service_type=None,
            description_of_event="Waited for almost an hour with zero communication regarding the delay.",
            extracted_summary="Patient experienced unexplained delay of nearly an hour.",
            extraction_confidence=0.86
        ),
        "contact_status": ContactStatus.NOT_CONTACTED.value
    },
    {
        "case_id": "FB-2026-1002",
        "created_at": "2026-10-01 11:30:00",
        "source_channel": SourceChannel.WEBSITE.value,
        "original_feedback": "I visited Example Hospital Cardiology on October 3 at around 14:00. I waited 45 minutes despite having an appointment.",
        "extracted": ExtractedFeedbackData(
            feedback_type=FeedbackType.COMPLAINT,
            issue_type=IssueType.WAITING_TIME,
            sentiment=SentimentType.NEGATIVE,
            hospital="Example Hospital",
            department="Cardiology",
            incident_date="October 3",
            approximate_time="14:00",
            service_type="Specialist Consultation",
            description_of_event="45-minute wait time exceeded despite confirmed appointment.",
            extracted_summary="Appointment delay of 45 minutes at Cardiology clinic.",
            extraction_confidence=0.96
        ),
        "contact_status": ContactStatus.COMPLETED.value
    },
    {
        "case_id": "FB-2026-1003",
        "created_at": "2026-10-02 14:10:00",
        "source_channel": SourceChannel.CALL_CENTER.value,
        "original_feedback": "The nurse in the pediatric department at Example Hospital was extremely kind and helpful.",
        "extracted": ExtractedFeedbackData(
            feedback_type=FeedbackType.APPRECIATION,
            issue_type=IssueType.APPRECIATION,
            sentiment=SentimentType.POSITIVE,
            hospital="Example Hospital",
            department="Pediatrics",
            incident_date=None,
            staff_role="Nurse",
            description_of_event="Nursing staff exhibited exceptional kindness and assistance.",
            extracted_summary="Commendation for pediatric nursing staff member.",
            extraction_confidence=0.94
        ),
        "contact_status": ContactStatus.COMPLETED.value
    },
    {
        "case_id": "FB-2026-1004",
        "created_at": "2026-10-02 16:45:00",
        "source_channel": SourceChannel.WEBSITE.value,
        "original_feedback": "I was charged twice for the same service yesterday.",
        "extracted": ExtractedFeedbackData(
            feedback_type=FeedbackType.COMPLAINT,
            issue_type=IssueType.BILLING_PAYMENT,
            sentiment=SentimentType.NEGATIVE,
            hospital=None,
            department=None,
            incident_date="yesterday",
            billing_context="Duplicate credit card debit for single procedure.",
            description_of_event="Patient noticed duplicate billing on bank statement.",
            extracted_summary="Duplicate charge reported without facility details.",
            extraction_confidence=0.88
        ),
        "contact_status": ContactStatus.CONTACT_ATTEMPTED.value
    },
    {
        "case_id": "FB-2026-1005",
        "created_at": "2026-10-03 08:20:00",
        "source_channel": SourceChannel.QR_CODE.value,
        "original_feedback": "The restroom near radiology at Example Hospital was not clean on October 2.",
        "extracted": ExtractedFeedbackData(
            feedback_type=FeedbackType.COMPLAINT,
            issue_type=IssueType.FACILITY_CLEANLINESS,
            sentiment=SentimentType.NEGATIVE,
            hospital="Example Hospital",
            department="Radiology",
            incident_date="October 2",
            description_of_event="Restroom facility adjacent to radiology wing was unsanitary.",
            extracted_summary="Housekeeping needed for restroom near Radiology.",
            extraction_confidence=0.92
        ),
        "contact_status": ContactStatus.COMPLETED.value
    },
    {
        "case_id": "FB-2026-1006",
        "created_at": "2026-10-03 10:05:00",
        "source_channel": SourceChannel.EMAIL.value,
        "original_feedback": "My appointment was cancelled but I was not informed.",
        "extracted": ExtractedFeedbackData(
            feedback_type=FeedbackType.COMPLAINT,
            issue_type=IssueType.APPOINTMENT,
            sentiment=SentimentType.NEGATIVE,
            hospital=None,
            department=None,
            incident_date=None,
            description_of_event="Appointment was cancelled without prior notification to patient.",
            extracted_summary="Unnotified appointment cancellation.",
            extraction_confidence=0.84
        ),
        "contact_status": ContactStatus.NOT_CONTACTED.value
    },
    {
        "case_id": "FB-2026-1007",
        "created_at": "2026-10-03 13:50:00",
        "source_channel": SourceChannel.SOCIAL_MEDIA.value,
        "original_feedback": "Registration staff member spoke rudely to me at Example Hospital yesterday morning.",
        "extracted": ExtractedFeedbackData(
            feedback_type=FeedbackType.COMPLAINT,
            issue_type=IssueType.STAFF_BEHAVIOR,
            sentiment=SentimentType.NEGATIVE,
            hospital="Example Hospital",
            department=None,
            incident_date="yesterday",
            approximate_time="morning",
            staff_role="Registration Clerk",
            description_of_event="Encountered discourteous communication at registration counter.",
            extracted_summary="Staff behavior complaint regarding registration desk.",
            extraction_confidence=0.90
        ),
        "contact_status": ContactStatus.CONTACT_ATTEMPTED.value
    },
    {
        "case_id": "FB-2026-1008",
        "created_at": "2026-10-04 09:10:00",
        "source_channel": SourceChannel.WEBSITE.value,
        "original_feedback": "I think the hospital should provide better parking guidance and clearer lane arrows.",
        "extracted": ExtractedFeedbackData(
            feedback_type=FeedbackType.SUGGESTION,
            issue_type=IssueType.PARKING_TRANSPORTATION,
            sentiment=SentimentType.NEUTRAL,
            hospital=None,
            description_of_event="Proposes enhanced visual wayfinding and lane signage in multi-story parking structure.",
            extracted_summary="Suggestion for clearer parking wayfinding signs.",
            extraction_confidence=0.91
        ),
        "contact_status": ContactStatus.NOT_CONTACTED.value
    },
    {
        "case_id": "FB-2026-1009",
        "created_at": "2026-10-04 14:40:00",
        "source_channel": SourceChannel.QR_CODE.value,
        "original_feedback": "I could not complete payment because the payment terminal repeatedly failed at the cashier.",
        "extracted": ExtractedFeedbackData(
            feedback_type=FeedbackType.COMPLAINT,
            issue_type=IssueType.TECHNICAL_ISSUE,
            sentiment=SentimentType.NEGATIVE,
            hospital=None,
            department="Cashier Desk",
            incident_date="today",
            billing_context="POS terminal hardware error / timeout.",
            description_of_event="Payment POS terminal connection timed out multiple times at cashier.",
            extracted_summary="POS payment terminal failure during patient checkout.",
            extraction_confidence=0.87
        ),
        "contact_status": ContactStatus.NO_RESPONSE.value
    },
    {
        "case_id": "FB-2026-1010",
        "created_at": "2026-10-04 17:00:00",
        "source_channel": SourceChannel.CALL_CENTER.value,
        "original_feedback": "Everything was excellent. Thank you to the cardiology team at Example Hospital for great care.",
        "extracted": ExtractedFeedbackData(
            feedback_type=FeedbackType.APPRECIATION,
            issue_type=IssueType.APPRECIATION,
            sentiment=SentimentType.POSITIVE,
            hospital="Example Hospital",
            department="Cardiology",
            description_of_event="Exemplary clinical care and professional attentiveness by Cardiology team.",
            extracted_summary="Positive commendation for entire cardiology department.",
            extraction_confidence=0.97
        ),
        "contact_status": ContactStatus.COMPLETED.value
    },
    {
        # Extra Case 11: A case that was previously incomplete, followed up, and now Ready for Workflow
        "case_id": "FB-2026-1011",
        "created_at": "2026-09-30 15:20:00",
        "source_channel": SourceChannel.CALL_CENTER.value,
        "original_feedback": "I had a delay with my blood test results last Tuesday.",
        "extracted": ExtractedFeedbackData(
            feedback_type=FeedbackType.COMPLAINT,
            issue_type=IssueType.WAITING_TIME,
            sentiment=SentimentType.NEGATIVE,
            hospital=None,
            department=None,
            incident_date="last Tuesday",
            service_type="Blood test",
            description_of_event="Phlebotomy test results took 6 hours instead of promised 2 hours.",
            extracted_summary="Laboratory turnaround delay for blood test.",
            extraction_confidence=0.85
        ),
        "contact_status": ContactStatus.INFO_COLLECTED.value,
        "reevaluation_data": {
            "hospital": "Example Hospital Central",
            "department": "Biochemistry Laboratory",
            "approximate_time": "10:30 AM"
        }
    }
]


def seed_database(force: bool = False) -> int:
    """Populate database with synthetic cases if empty or force=True."""
    init_db()
    current_count = count_cases()
    if current_count > 0 and not force:
        return current_count

    inserted = 0
    for item in SEED_CASES:
        ext = item["extracted"]
        result = evaluate_completeness(ext)
        case_dict = ext.model_dump()
        case_dict["case_id"] = item["case_id"]
        case_dict["created_at"] = item["created_at"]
        case_dict["source_channel"] = item["source_channel"]
        case_dict["original_feedback"] = item["original_feedback"]
        case_dict["contact_status"] = item["contact_status"]

        save_case(case_dict, result)
        inserted += 1

        # Simulate follow-up history and re-evaluation for case 1011
        if "reevaluation_data" in item:
            add_follow_up_entry(
                case_id=item["case_id"],
                contact_status=ContactStatus.INFO_COLLECTED.value,
                additional_information="Patient confirmed hospital was Example Hospital Central, Biochemistry Lab at 10:30 AM.",
                notes="Patient was reachable by phone; provided lab barcode."
            )
            # Re-evaluate
            overrides = item["reevaluation_data"]
            reeval_res = evaluate_completeness(ext, confirmed_overrides=overrides)
            update_case_after_reevaluation(
                case_id=item["case_id"],
                updated_fields=overrides,
                result=reeval_res,
                extracted_json=ext.model_dump_json()
            )

    return inserted


if __name__ == "__main__":
    count = seed_database(force=True)
    print(f"Successfully seeded {count} cases into FeedbackIQ database.")
