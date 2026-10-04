"""
Gemini Information Extraction Service.
Extracts structured operational data from patient feedback with strict schema validation.
Includes deterministic Demo Mode fallback for offline or zero-quota portfolio demonstration.
"""

import os
import json
import re
from typing import Optional, Dict, Any, Tuple
from dotenv import load_dotenv

from feedbackiq.models.schemas import (
    ExtractedFeedbackData,
    FeedbackType,
    IssueType,
    SentimentType,
)

load_dotenv()

SYSTEM_INSTRUCTION = """You are an information extraction system for hospital service feedback.
Your job is NOT to answer the patient.
Your job is NOT to provide medical advice.
Your job is NOT to resolve the complaint.

Extract ONLY operational information explicitly stated or strongly supported by the feedback.
Never invent hospitals, departments, dates, times, staff members, or medical details.
If a field is not present or unknown, return null.

You must classify issue_type strictly from this controlled list:
- "Waiting Time"
- "Staff Behavior"
- "Appointment"
- "Registration"
- "Billing / Payment"
- "Medical Service Process"
- "Communication"
- "Facility / Cleanliness"
- "Technical Issue"
- "Food / Catering"
- "Parking / Transportation"
- "Appreciation"
- "General Suggestion"
- "Other"

Return clean structured data adhering to the schema.
"""


def _heuristic_mock_extraction(text: str, context: Optional[str] = None) -> ExtractedFeedbackData:
    """
    Deterministic rule-based mock extractor for portfolio demonstration.
    Activated when DEMO_MODE=true or no GEMINI_API_KEY is configured.
    """
    lower = text.lower()
    full_text = f"{text} {context or ''}".lower()

    # Determine feedback type
    if any(w in lower for w in ["thank", "helpful", "great", "excellent", "kind", "appreciation", "good job", "teşekkür"]):
        feedback_type = FeedbackType.APPRECIATION
        sentiment = SentimentType.POSITIVE
    elif any(w in lower for w in ["suggest", "should provide", "recommend", "better if", "could you add"]):
        feedback_type = FeedbackType.SUGGESTION
        sentiment = SentimentType.NEUTRAL
    else:
        feedback_type = FeedbackType.COMPLAINT
        sentiment = SentimentType.NEGATIVE

    # Determine issue type
    if any(w in full_text for w in ["wait", "delay", "late", "hour", "minutes", "slow"]):
        issue_type = IssueType.WAITING_TIME
    elif any(w in full_text for w in ["rude", "behavior", "attitude", "disrespectful", "shouted", "dismissive"]):
        issue_type = IssueType.STAFF_BEHAVIOR
    elif any(w in full_text for w in ["charged", "bill", "invoice", "refund", "payment", "cost", "price", "fee"]):
        issue_type = IssueType.BILLING_PAYMENT
    elif any(w in full_text for w in ["appointment", "booking", "schedule", "reschedule", "cancelled"]):
        issue_type = IssueType.APPOINTMENT
    elif any(w in full_text for w in ["registration", "intake", "counter", "desk clerk"]):
        issue_type = IssueType.REGISTRATION
    elif any(w in full_text for w in ["clean", "restroom", "dirty", "trash", "toilet", "hygiene"]):
        issue_type = IssueType.FACILITY_CLEANLINESS
    elif any(w in full_text for w in ["terminal", "pos", "kiosk", "system", "app", "website", "wifi", "portal"]):
        issue_type = IssueType.TECHNICAL_ISSUE
    elif any(w in full_text for w in ["park", "parking", "car", "valet", "garage"]):
        issue_type = IssueType.PARKING_TRANSPORTATION
    elif any(w in full_text for w in ["food", "meal", "cafeteria", "lunch", "dinner"]):
        issue_type = IssueType.FOOD_CATERING
    elif feedback_type == FeedbackType.APPRECIATION:
        issue_type = IssueType.APPRECIATION
    elif feedback_type == FeedbackType.SUGGESTION:
        issue_type = IssueType.GENERAL_SUGGESTION
    else:
        issue_type = IssueType.OTHER

    # Detect Hospital
    hospital = None
    hosp_match = re.search(r"([A-Z][a-zA-Z0-9\s]+Hospital[a-zA-Z0-9\s]*)", text + " " + (context or ""))
    if hosp_match:
        hospital = hosp_match.group(1).strip()
    elif "example hospital" in full_text:
        hospital = "Example Hospital"
    elif "merkez" in full_text:
        hospital = "Merkez Sağlık Hastanesi"

    # Detect Department
    department = None
    departments = [
        "Cardiology", "Pediatrics", "Radiology", "Emergency", "Orthopedics",
        "Neurology", "Oncology", "Biochemistry", "General Surgery", "Internal Medicine", "Cashier Desk"
    ]
    for dept in departments:
        if dept.lower() in full_text:
            department = dept
            break

    # Detect Date
    incident_date = None
    if "yesterday" in full_text:
        incident_date = "yesterday"
    elif "today" in full_text:
        incident_date = "today"
    else:
        date_match = re.search(r"(october\s+\d+|[0-9]{4}-[0-9]{2}-[0-9]{2}|last\s+\w+)", full_text)
        if date_match:
            incident_date = date_match.group(1).title()

    # Detect Time
    approximate_time = None
    time_match = re.search(r"(\b\d{1,2}:\d{2}\b|\b\d{1,2}\s*(?:am|pm)\b|morning|afternoon|evening)", full_text)
    if time_match:
        approximate_time = time_match.group(1)

    # Detect Staff Role / Name
    staff_role = None
    for role in ["Nurse", "Doctor", "Physician", "Registration Clerk", "Security", "Technician", "Surgeon"]:
        if role.lower() in full_text:
            staff_role = role
            break

    # Billing context
    billing_context = None
    if issue_type == IssueType.BILLING_PAYMENT or "charged twice" in full_text:
        billing_context = "Duplicate or disputed charge for healthcare service"
    elif issue_type == IssueType.TECHNICAL_ISSUE and "payment terminal" in full_text:
        billing_context = "Payment terminal POS error at checkout"

    # Summary
    summary = text[:120] + "..." if len(text) > 120 else text

    return ExtractedFeedbackData(
        feedback_type=feedback_type,
        issue_type=issue_type,
        sentiment=sentiment,
        hospital=hospital,
        department=department,
        incident_date=incident_date,
        approximate_time=approximate_time,
        service_type=None,
        staff_role=staff_role,
        staff_name=None,
        billing_context=billing_context,
        description_of_event=text.strip(),
        impact=None,
        explicit_request=None,
        mentioned_entities=[e for e in [hospital, department, staff_role] if e],
        extracted_summary=summary,
        extraction_confidence=0.89
    )


def extract_feedback_info(
    feedback_text: str,
    context_hint: Optional[str] = None
) -> Tuple[ExtractedFeedbackData, bool, Optional[str]]:
    """
    Extract structured feedback data using Gemini API or fallback to Demo Mode.
    
    Returns:
        (ExtractedFeedbackData, is_live_gemini: bool, warning_or_error: Optional[str])
    """
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    demo_mode_env = os.environ.get("DEMO_MODE", "true").lower() in ["true", "1", "yes"]
    model_name = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash").strip() or "gemini-2.0-flash"

    # If no valid API key or explicitly configured Demo Mode
    if not api_key or api_key in ["your_gemini_api_key_here", ""]:
        mock_data = _heuristic_mock_extraction(feedback_text, context_hint)
        return mock_data, False, "Demo Mode active (no Gemini API key detected). Running deterministic extraction."

    if demo_mode_env and os.environ.get("FORCE_GEMINI", "").lower() not in ["true", "1"]:
        # When demo mode is on but API key exists, still try live API if desired, or allow override
        pass

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        prompt = f"PATIENT FEEDBACK TEXT:\n\"\"\"{feedback_text}\"\"\"\n"
        if context_hint:
            prompt += f"\nCONFIRMED / ADDITIONAL OPERATIONAL CONTEXT:\n\"\"\"{context_hint}\"\"\"\n"

        prompt += "\nExtract structured JSON adhering strictly to the schema. Do not invent details."

        candidate_models = [model_name, "gemini-3.7-flash", "gemini-3.5-flash", "gemini-3.8-flash"]
        seen_models = set()
        models_to_try = [m for m in candidate_models if not (m in seen_models or seen_models.add(m))]

        last_err = None
        for m in models_to_try:
            try:
                response = client.models.generate_content(
                    model=m,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                        temperature=0.1,
                        response_mime_type="application/json",
                        response_schema=ExtractedFeedbackData,
                    )
                )

                raw_json = response.text
                parsed = ExtractedFeedbackData.model_validate_json(raw_json)
                return parsed, True, None
            except Exception as candidate_err:
                last_err = candidate_err
                continue

        raise last_err or Exception("All candidate models failed.")

    except Exception as e:
        error_msg = f"Gemini API request failed ({type(e).__name__}: {str(e)[:120]}). Falling back to deterministic analysis."
        fallback_data = _heuristic_mock_extraction(feedback_text, context_hint)
        fallback_data.extraction_confidence = 0.75
        return fallback_data, False, error_msg
