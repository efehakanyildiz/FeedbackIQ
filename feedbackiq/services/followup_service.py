"""
Follow-up and Case Re-evaluation Service.
Handles customer service follow-up workflows and context-enriched re-evaluation.
"""

from typing import Dict, Any, Tuple
from feedbackiq.database.repository import (
    get_case,
    update_case_after_reevaluation,
    add_follow_up_entry,
)
from feedbackiq.models.schemas import CompletenessResult, ExtractedFeedbackData
from feedbackiq.services.completeness_service import evaluate_completeness
from feedbackiq.services.gemini_service import extract_feedback_info


def process_case_reevaluation(
    case_id: str,
    confirmed_fields: Dict[str, Any],
    notes: str = "",
    contact_status: str = "Information Collected"
) -> Tuple[Dict[str, Any], CompletenessResult, int]:
    """
    Re-evaluate an incomplete feedback case using original feedback + confirmed CSR data.
    
    Returns:
        (updated_case_dict, completeness_result, previous_score)
    """
    case = get_case(case_id)
    if not case:
        raise ValueError(f"Case with ID {case_id} not found.")

    previous_score = case.get("completeness_score", 0)
    original_text = case.get("original_feedback", "")

    # Construct clean human-readable summary of confirmed follow-up information
    confirmed_summary_parts = []
    for k, v in confirmed_fields.items():
        if v and str(v).strip():
            confirmed_summary_parts.append(f"{k.replace('_', ' ').title()}: {v}")
    confirmed_text = ", ".join(confirmed_summary_parts)

    # Log follow-up entry in database
    add_follow_up_entry(
        case_id=case_id,
        contact_status=contact_status,
        additional_information=confirmed_text,
        notes=notes
    )

    # Run extraction with enriched context
    re_extracted, is_live, err = extract_feedback_info(original_text, context_hint=confirmed_text)

    # Evaluate completeness with confirmed manual fields taking strict precedence
    result = evaluate_completeness(re_extracted, confirmed_overrides=confirmed_fields)

    # Persist updated case details
    merged_updates = re_extracted.model_dump()
    for k, v in confirmed_fields.items():
        if v and str(v).strip():
            merged_updates[k] = v

    update_case_after_reevaluation(
        case_id=case_id,
        updated_fields=merged_updates,
        result=result,
        extracted_json=re_extracted.model_dump_json()
    )

    updated_case = get_case(case_id)
    return updated_case, result, previous_score
