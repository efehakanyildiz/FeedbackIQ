"""
AI Voice Follow-up Service.
Handles automated AI phone outreach for cases in Tier 2 (minor missing operational data).
Simulates an enterprise AI voice assistant calling the patient, conducting a natural spoken inquiry,
extracting the missing fields, and auto-promoting the case to Approved.
"""

from datetime import datetime
from typing import Dict, Any, Tuple
from feedbackiq.database.repository import (
    get_case,
    update_case_after_reevaluation,
    add_follow_up_entry,
)
from feedbackiq.models.schemas import (
    CompletenessResult,
    ContactStatus,
    CompletenessStatus,
)
from feedbackiq.services.completeness_service import evaluate_completeness
from feedbackiq.services.gemini_service import extract_feedback_info
from feedbackiq.config.question_templates import get_question_for_field, get_field_display_name


def simulate_ai_voice_call(
    case_id: str,
    patient_responses: Dict[str, Any] = None
) -> Tuple[Dict[str, Any], CompletenessResult, str]:
    """
    Simulate an automated AI Voice Agent telephone call to the patient.
    Generates realistic dialogue transcript and resolves missing fields.
    """
    case = get_case(case_id)
    if not case:
        raise ValueError(f"Case {case_id} not found.")

    hospital = case.get("hospital") or "Example Hospital"
    issue_type = case.get("issue_type") or "service delay"

    # Default simulated responses if not manually supplied
    if not patient_responses:
        patient_responses = {}
        if not case.get("approximate_time"):
            patient_responses["approximate_time"] = "14:15"
        if not case.get("department"):
            patient_responses["department"] = "Cardiology Clinic"
        if not case.get("hospital"):
            patient_responses["hospital"] = "Merkez Sağlık Hastanesi"
        if not case.get("service_type"):
            patient_responses["service_type"] = "Specialist Consultation"

    # Construct clean dialogue transcript in Turkish
    transcript_lines = [
        f"YAPAY ZEKA ASİSTANI: Merhaba, {hospital} Hasta Deneyimi Merkezi'nden arıyorum. Son geri bildiriminiz hakkında birim yöneticimizin detaylı inceleme yapabilmesi adına eksik kalan birkaç operasyonel bilgiyi teyit etmek için aradım. Çok kısa vaktiniz var mı?",
        "HASTA: Evet, dinliyorum, buyrun.",
    ]

    for field_key, answer_val in patient_responses.items():
        q_text = get_question_for_field(field_key)
        transcript_lines.append(f"YAPAY ZEKA ASİSTANI: {q_text}")
        transcript_lines.append(f"HASTA: {answer_val} idi.")

    transcript_lines.append(
        "YAPAY ZEKA ASİSTANI: Çok teşekkür ederiz, gerekli bilgileri sisteme kaydettim. İlgili birim yöneticimiz incelemeyi ivedilikle başlatacaktır. Sağlıklı ve iyi günler dileriz!"
    )
    transcript_text = "\n".join(transcript_lines)

    # Re-evaluate with confirmed responses (reuse extracted_json if available)
    extracted_json = case.get("extracted_json")
    if extracted_json:
        try:
            from feedbackiq.models.schemas import ExtractedFeedbackData
            re_extracted = ExtractedFeedbackData.model_validate_json(extracted_json)
        except Exception:
            re_extracted, is_live, err = extract_feedback_info(case.get("original_feedback", ""))
    else:
        original_text = case.get("original_feedback", "")
        re_extracted, is_live, err = extract_feedback_info(original_text)

    # Evaluate completeness with overrides
    result = evaluate_completeness(re_extracted, confirmed_overrides=patient_responses)

    # Persist follow-up entry in Turkish
    collected_summary = ", ".join([f"{get_field_display_name(k)}: {v}" for k, v in patient_responses.items()])
    add_follow_up_entry(
        case_id=case_id,
        contact_status=ContactStatus.AI_CALL_COMPLETED.value,
        additional_information=f"Yapay Zeka Sesli Arama Tamamlandı. Alınan Bilgiler: {collected_summary}",
        notes="Otonom sesli arama süresi: 1 dk 14 sn. Konuşma dökümü kaydedildi."
    )

    # Update case with new data and transcript
    update_data = {**patient_responses, "ai_call_transcript": transcript_text}
    update_case_after_reevaluation(
        case_id=case_id,
        updated_fields=update_data,
        result=result,
        extracted_json=re_extracted.model_dump_json()
    )

    updated_case = get_case(case_id)
    return updated_case, result, transcript_text
