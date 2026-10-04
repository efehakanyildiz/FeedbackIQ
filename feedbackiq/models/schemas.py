"""
Data models and Pydantic schemas for FeedbackIQ.
Implements 3-tier intelligent triage:
- Tier 1: Sufficient Data -> Approved / Ready for Workflow
- Tier 2: Minor Missing Data -> AI Voice Bot Follow-up
- Tier 3: Major Missing Data -> Customer Service Escalation
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class FeedbackType(str, Enum):
    COMPLAINT = "complaint"
    SUGGESTION = "suggestion"
    APPRECIATION = "appreciation"
    OTHER = "other"


class IssueType(str, Enum):
    WAITING_TIME = "Waiting Time"
    STAFF_BEHAVIOR = "Staff Behavior"
    APPOINTMENT = "Appointment"
    REGISTRATION = "Registration"
    BILLING_PAYMENT = "Billing / Payment"
    MEDICAL_SERVICE_PROCESS = "Medical Service Process"
    COMMUNICATION = "Communication"
    FACILITY_CLEANLINESS = "Facility / Cleanliness"
    TECHNICAL_ISSUE = "Technical Issue"
    FOOD_CATERING = "Food / Catering"
    PARKING_TRANSPORTATION = "Parking / Transportation"
    APPRECIATION = "Appreciation"
    GENERAL_SUGGESTION = "General Suggestion"
    OTHER = "Other"


class SentimentType(str, Enum):
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    POSITIVE = "positive"
    MIXED = "mixed"


class TriageTier(str, Enum):
    TIER_1_APPROVED = "Approved"
    TIER_2_AI_CALL = "AI Call Scheduled"
    TIER_3_CSR_ESCALATION = "Customer Service Review"


class CompletenessStatus(str, Enum):
    APPROVED = "Approved"
    AI_CALL_SCHEDULED = "AI Call Scheduled"
    CSR_ESCALATION = "Customer Service Review"
    RESOLVED = "Resolved / Ready for Workflow"


class FollowUpPriority(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class ContactStatus(str, Enum):
    NOT_CONTACTED = "Not Contacted"
    AI_CALL_PENDING = "AI Call Pending"
    AI_CALL_COMPLETED = "AI Call Completed"
    CSR_CONTACT_ATTEMPTED = "CSR Contact Attempted"
    INFO_COLLECTED = "Information Collected"
    COMPLETED = "Completed"


class SourceChannel(str, Enum):
    WEBSITE = "Website"
    CALL_CENTER = "Call Center"
    QR_CODE = "QR Code"
    EMAIL = "Email"
    SOCIAL_MEDIA = "Social Media"
    OTHER = "Other"


class ExtractedFeedbackData(BaseModel):
    """Structured data extracted from unstructured patient feedback text."""
    feedback_type: FeedbackType = Field(
        default=FeedbackType.OTHER,
        description="Type of feedback: complaint, suggestion, appreciation, other"
    )
    issue_type: IssueType = Field(
        default=IssueType.OTHER,
        description="Controlled operational issue category"
    )
    sentiment: SentimentType = Field(
        default=SentimentType.NEUTRAL,
        description="Sentiment expressed by the patient"
    )
    hospital: Optional[str] = Field(
        default=None,
        description="Name of the specific hospital branch visited. Null if not mentioned."
    )
    department: Optional[str] = Field(
        default=None,
        description="Clinical or administrative department. Null if not mentioned."
    )
    incident_date: Optional[str] = Field(
        default=None,
        description="Date of the incident. Null if not mentioned."
    )
    approximate_time: Optional[str] = Field(
        default=None,
        description="Time or time of day of incident. Null if not mentioned."
    )
    service_type: Optional[str] = Field(
        default=None,
        description="Specific service or exam. Null if not mentioned."
    )
    staff_role: Optional[str] = Field(
        default=None,
        description="Role of staff involved. Null if not mentioned."
    )
    staff_name: Optional[str] = Field(
        default=None,
        description="Name of staff member. Null if not mentioned."
    )
    billing_context: Optional[str] = Field(
        default=None,
        description="Details regarding billing or payment. Null if not mentioned."
    )
    description_of_event: Optional[str] = Field(
        default=None,
        description="Concise description of the specific operational incident."
    )
    impact: Optional[str] = Field(
        default=None,
        description="Impact on the patient."
    )
    explicit_request: Optional[str] = Field(
        default=None,
        description="Any explicit request or demand made by the patient."
    )
    mentioned_entities: List[str] = Field(
        default_factory=list,
        description="Key entities detected in the text"
    )
    extracted_summary: str = Field(
        default="",
        description="One-sentence objective summary of the feedback."
    )
    extraction_confidence: float = Field(
        default=0.85,
        ge=0.0,
        le=1.0,
        description="Confidence score for information extraction."
    )


class MissingFieldItem(BaseModel):
    field_name: str
    display_name: str
    is_critical: bool
    suggested_question: str
    resolved: bool = False


class CompletenessResult(BaseModel):
    """Result of deterministic rule-based completeness evaluation & 3-tier triage."""
    completeness_score: int = Field(ge=0, le=100)
    triage_tier: TriageTier
    status: CompletenessStatus
    triage_reason: str
    follow_up_priority: FollowUpPriority
    is_complete: bool
    requires_ai_call: bool
    requires_csr_escalation: bool
    missing_fields: List[str]
    critical_missing_fields: List[str]
    missing_field_items: List[MissingFieldItem]
    detected_fields: Dict[str, Any]
    why_needed_explanation: str
    score_breakdown: Dict[str, int]


class FeedbackCaseRecord(BaseModel):
    """Full database record model for a feedback case."""
    case_id: str
    created_at: str
    source_channel: str
    original_feedback: str
    feedback_type: str
    issue_type: str
    sentiment: str
    hospital: Optional[str] = None
    department: Optional[str] = None
    incident_date: Optional[str] = None
    approximate_time: Optional[str] = None
    service_type: Optional[str] = None
    staff_role: Optional[str] = None
    staff_name: Optional[str] = None
    billing_context: Optional[str] = None
    description_of_event: Optional[str] = None
    impact: Optional[str] = None
    explicit_request: Optional[str] = None
    extracted_summary: str = ""
    extraction_confidence: float = 0.85
    completeness_score: int = 0
    triage_tier: str = TriageTier.TIER_3_CSR_ESCALATION.value
    status: str = CompletenessStatus.CSR_ESCALATION.value
    follow_up_priority: str = FollowUpPriority.MEDIUM.value
    contact_status: str = ContactStatus.NOT_CONTACTED.value
    ai_call_transcript: Optional[str] = None
    updated_at: str = ""
