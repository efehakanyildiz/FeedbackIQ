"""
Deterministic Python Rules Engine for Completeness Evaluation and 3-Tier Triage:
1. Tier 1: Sufficient Data -> Approved / Ready for Workflow
2. Tier 2: Minor Missing Data -> Automated AI Voice Call Scheduled
3. Tier 3: Major Missing Data -> Human Customer Service Escalation
"""

from typing import Dict, Any, List, Tuple
from feedbackiq.models.schemas import (
    ExtractedFeedbackData,
    CompletenessResult,
    CompletenessStatus,
    TriageTier,
    FollowUpPriority,
    MissingFieldItem,
)
from feedbackiq.config.completeness_rules import (
    ISSUE_RULES_CONFIG,
    THRESHOLD_COMPLETE,
    THRESHOLD_NEEDS_REVIEW,
)
from feedbackiq.config.question_templates import (
    get_question_for_field,
    get_field_display_name,
)


def _is_value_present(val: Any) -> bool:
    """Check if an extracted field value is non-empty and non-null."""
    if val is None:
        return False
    if isinstance(val, str):
        cleaned = val.strip().lower()
        if not cleaned or cleaned in ["null", "none", "unknown", "n/a", "not detected", "not mentioned"]:
            return False
        return True
    if isinstance(val, list):
        return len(val) > 0
    return bool(val)


def evaluate_completeness(
    data: ExtractedFeedbackData,
    confirmed_overrides: Dict[str, Any] = None
) -> CompletenessResult:
    """
    Perform deterministic evaluation and 3-tier classification.
    
    Triage Rules:
    - Tier 1 (Approved): Score >= 80 and no critical fields missing.
    - Tier 2 (AI Voice Call): Score >= 50 and <= 2 missing fields (minor operational gaps).
    - Tier 3 (CSR Escalation): Score < 50 or multiple critical fields missing.
    """
    if confirmed_overrides is None:
        confirmed_overrides = {}

    merged_data: Dict[str, Any] = data.model_dump()
    for k, v in confirmed_overrides.items():
        if _is_value_present(v):
            merged_data[k] = v

    issue_type_key = merged_data.get("issue_type", "Other")
    rule_config = ISSUE_RULES_CONFIG.get(issue_type_key, ISSUE_RULES_CONFIG["Other"])

    weights = rule_config.get("weights", {})
    critical_fields = list(rule_config.get("critical_fields", []))
    or_groups: List[Tuple[str, ...]] = rule_config.get("or_groups", [])

    score = 0
    score_breakdown: Dict[str, int] = {}
    missing_fields_set = set()
    critical_missing_set = set()
    detected_fields: Dict[str, Any] = {}

    # Track fields handled by OR groups
    or_fields_evaluated = set()
    for group in or_groups:
        group_weights = [weights.get(f, 0) for f in group]
        sum_group_weight = sum(group_weights)
        present_in_group = [f for f in group if _is_value_present(merged_data.get(f))]
        for f in group:
            or_fields_evaluated.add(f)

        if present_in_group:
            score += sum_group_weight
            for f in present_in_group:
                score_breakdown[f] = weights.get(f, 0)
                detected_fields[f] = merged_data[f]
        else:
            primary_field = group[0]
            missing_fields_set.add(primary_field)
            for f in group:
                score_breakdown[f] = 0

    # Evaluate individual weights for fields not in OR groups
    for field_name, weight in weights.items():
        if field_name in or_fields_evaluated:
            continue
        val = merged_data.get(field_name)
        if _is_value_present(val):
            score += weight
            score_breakdown[field_name] = weight
            detected_fields[field_name] = val
        else:
            score_breakdown[field_name] = 0
            missing_fields_set.add(field_name)

    # Capture contextual fields not part of score weights
    for extra_field in ["feedback_type", "issue_type", "sentiment", "impact", "explicit_request", "extracted_summary"]:
        val = merged_data.get(extra_field)
        if _is_value_present(val):
            detected_fields[extra_field] = val

    # Check critical fields
    for crit in critical_fields:
        if not _is_value_present(merged_data.get(crit)):
            critical_missing_set.add(crit)
            missing_fields_set.add(crit)

    # Normalize score to max 100
    total_possible_weights = sum(weights.values())
    if total_possible_weights > 0:
        normalized_score = min(100, int(round((score / total_possible_weights) * 100)))
    else:
        normalized_score = 50

    sorted_missing = sorted(list(missing_fields_set))
    sorted_critical = sorted(list(critical_missing_set))
    missing_count = len(sorted_missing)
    critical_count = len(sorted_critical)

    # Build missing field items with questions
    missing_items: List[MissingFieldItem] = []
    for f in sorted_missing:
        is_crit = f in sorted_critical
        missing_items.append(
            MissingFieldItem(
                field_name=f,
                display_name=get_field_display_name(f),
                is_critical=is_crit,
                suggested_question=get_question_for_field(f),
                resolved=False
            )
        )

    # 3-Tier Triage Classification Logic
    is_hospital_missing = "hospital" in sorted_missing

    if missing_count == 0 or (critical_count == 0 and normalized_score >= 95):
        # Kademe 1: Yeterli Veri -> Onaylandı / Doğrudan İş Akışına Sevk
        triage_tier = TriageTier.TIER_1_APPROVED
        status = CompletenessStatus.APPROVED
        is_complete = True
        requires_ai_call = False
        requires_csr_escalation = False
        triage_reason = "Yeterli operasyonel veri mevcut. Doğrudan ilgili birim iş akışına onaylandı."
        follow_up_priority = FollowUpPriority.LOW

    elif not is_hospital_missing and normalized_score >= 50 and missing_count <= 2 and critical_count <= 1:
        # Kademe 2: Küçük Eksiklik (Hastane biliniyor, 1-2 küçük detay eksik) -> AI Sesli Arama Botu
        triage_tier = TriageTier.TIER_2_AI_CALL
        status = CompletenessStatus.AI_CALL_SCHEDULED
        is_complete = False
        requires_ai_call = True
        requires_csr_escalation = False
        missing_names = [get_field_display_name(f) for f in sorted_missing]
        triage_reason = (
            f"Küçük operasyonel eksiklik ({', '.join(missing_names)}). "
            "Hedefli telefon teyidi için otonom Yapay Zeka Sesli Arama Botuna yönlendirildi."
        )
        follow_up_priority = FollowUpPriority.MEDIUM

    else:
        # Kademe 3: Kritik Eksik Veri (Hastane belirsiz veya birden çok eksik) -> Müşteri Hizmetleri İncelemesi
        triage_tier = TriageTier.TIER_3_CSR_ESCALATION
        status = CompletenessStatus.CSR_ESCALATION
        is_complete = False
        requires_ai_call = False
        requires_csr_escalation = True
        missing_names = [get_field_display_name(f) for f in sorted_missing]
        triage_reason = (
            f"Kritik bilgi eksikliği ({', '.join(missing_names) if missing_names else 'yetersiz operasyonel veri'}). "
            "Temsilci incelemesi için Müşteri Hizmetleri Masasına sevk edildi."
        )
        follow_up_priority = FollowUpPriority.HIGH

    # Build why_needed explanation in Turkish
    base_desc = rule_config.get("explanation", "Kurumsal inceleme için operasyonel ayrıntılar gereklidir.")
    if is_complete:
        why_explanation = "Geri bildirim kaydı, ilgili poliklinik veya birimin derhal inceleme başlatması için gereken tüm operasyonel ayrıntıları eksiksiz içermektedir."
    else:
        missing_names = [get_field_display_name(f) for f in sorted_missing]
        why_explanation = f"{base_desc} Şu an eksik olan parametreler: {', '.join(missing_names)}. {triage_reason}"

    return CompletenessResult(
        completeness_score=normalized_score,
        triage_tier=triage_tier,
        status=status,
        triage_reason=triage_reason,
        follow_up_priority=follow_up_priority,
        is_complete=is_complete,
        requires_ai_call=requires_ai_call,
        requires_csr_escalation=requires_csr_escalation,
        missing_fields=sorted_missing,
        critical_missing_fields=sorted_critical,
        missing_field_items=missing_items,
        detected_fields=detected_fields,
        why_needed_explanation=why_explanation,
        score_breakdown=score_breakdown,
    )
