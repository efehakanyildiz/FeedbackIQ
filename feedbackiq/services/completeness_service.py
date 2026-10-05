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
    
    Puanlama Kuralları:
    - Başlangıç Skoru: 100
    - Küçük Eksikler (Minor): Her biri -5 puan (örn: tahmini saat yoksa 100 - 5 = 95)
    - Büyük Eksikler (Major / Critical): Her biri -30 puan (örn: hastane yoksa -30, poliklinik yoksa -30)
    
    3 Kademeli Yönlendirme (Triage Rules):
    - Kademe 1 (Onaylandı): 0 eksik veri (missing_count == 0), skor = 100.
    - Kademe 2 (Yapay Zeka Asistanı): 1 ila 4 küçük eksik (veya 1 büyük eksik). AI Bot hastayı arar.
    - Kademe 3 (Müşteri Hizmetleri): 2 veya daha fazla büyük eksik (critical_count >= 2) veya skor < 50.
    """
    if confirmed_overrides is None:
        confirmed_overrides = {}

    merged_data: Dict[str, Any] = data.model_dump()
    for k, v in confirmed_overrides.items():
        if _is_value_present(v):
            merged_data[k] = v

    issue_type_key = merged_data.get("issue_type", "Other")
    rule_config = ISSUE_RULES_CONFIG.get(issue_type_key, ISSUE_RULES_CONFIG.get("Diğer", ISSUE_RULES_CONFIG["Other"]))

    critical_fields = list(rule_config.get("critical_fields", ["hospital", "description_of_event"]))
    minor_fields = list(rule_config.get("minor_fields", ["approximate_time", "incident_date"]))
    or_groups: List[Tuple[str, ...]] = rule_config.get("or_groups", [])

    missing_fields_set = set()
    critical_missing_set = set()
    minor_missing_set = set()
    detected_fields: Dict[str, Any] = {}
    score_breakdown: Dict[str, int] = {}

    # Track fields handled by OR groups (e.g. staff_role or staff_name)
    or_fields_evaluated = set()
    for group in or_groups:
        present_in_group = [f for f in group if _is_value_present(merged_data.get(f))]
        for f in group:
            or_fields_evaluated.add(f)

        if present_in_group:
            for f in present_in_group:
                detected_fields[f] = merged_data[f]
                score_breakdown[f] = 5
        else:
            primary_field = group[0]
            if primary_field in critical_fields:
                critical_missing_set.add(primary_field)
                missing_fields_set.add(primary_field)
                score_breakdown[primary_field] = 0
            else:
                minor_missing_set.add(primary_field)
                missing_fields_set.add(primary_field)
                score_breakdown[primary_field] = 0

    # Evaluate critical fields (Büyük Eksikler: Her biri -30 puan)
    for crit in critical_fields:
        if crit in or_fields_evaluated:
            continue
        val = merged_data.get(crit)
        if _is_value_present(val):
            detected_fields[crit] = val
            score_breakdown[crit] = 30
        else:
            critical_missing_set.add(crit)
            missing_fields_set.add(crit)
            score_breakdown[crit] = 0

    # Evaluate minor fields (Küçük Eksikler: Her biri -5 puan)
    for minor in minor_fields:
        if minor in or_fields_evaluated:
            continue
        val = merged_data.get(minor)
        if _is_value_present(val):
            detected_fields[minor] = val
            score_breakdown[minor] = 5
        else:
            minor_missing_set.add(minor)
            missing_fields_set.add(minor)
            score_breakdown[minor] = 0

    # Capture other present operational fields
    for extra_field in ["hospital", "department", "incident_date", "approximate_time", "service_type",
                        "staff_role", "staff_name", "billing_context", "description_of_event",
                        "feedback_type", "issue_type", "sentiment", "impact", "explicit_request", "extracted_summary"]:
        val = merged_data.get(extra_field)
        if _is_value_present(val) and extra_field not in detected_fields:
            detected_fields[extra_field] = val
            if extra_field not in score_breakdown:
                score_breakdown[extra_field] = 5

    # Net Puanlama Hesabı:
    # 100 - (Büyük Eksik Sayısı * 30) - (Küçük Eksik Sayısı * 5)
    calculated_score = 100 - (len(critical_missing_set) * 30) - (len(minor_missing_set) * 5)
    normalized_score = max(0, min(100, calculated_score))

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

    # 3-KADEMELİ TRIAGE YÖNLENDİRME MANTIĞI:

    # KADEME 3: Müşteri Hizmetleri Masası (CSR Escalation)
    # Koşul: 2 veya daha fazla büyük eksik varsa (critical_count >= 2) VEYA skor < 50
    if critical_count >= 2 or normalized_score < 50:
        triage_tier = TriageTier.TIER_3_CSR_ESCALATION
        status = CompletenessStatus.CSR_ESCALATION
        is_complete = False
        requires_ai_call = False
        requires_csr_escalation = True

        crit_names = [get_field_display_name(f) for f in sorted_critical]
        triage_reason = (
            f"Kritik operasyonel bilgi eksikliği ({critical_count} büyük eksik: {', '.join(crit_names) if crit_names else 'yetersiz veri'}). "
            "Temsilci incelemesi için Müşteri Hizmetleri Masasına sevk edildi."
        )
        follow_up_priority = FollowUpPriority.HIGH

    # KADEME 2: Yapay Zeka Asistanı (AI Sesli Arama Botu Planlandı)
    # Koşul: En az 1 eksik var (1-4 küçük eksik veya en fazla 1 büyük eksik).
    # Otonom Yapay Zeka Asistanı hastayı telefonla arayarak eksik detayları tamamlar.
    elif missing_count > 0:
        triage_tier = TriageTier.TIER_2_AI_CALL
        status = CompletenessStatus.AI_CALL_SCHEDULED
        is_complete = False
        requires_ai_call = True
        requires_csr_escalation = False

        missing_names = [get_field_display_name(f) for f in sorted_missing]
        triage_reason = (
            f"Tamamlanabilir operasyonel eksiklik ({', '.join(missing_names)}). "
            "Hedefli telefon teyidi için Yapay Zeka Sesli Arama Asistanına yönlendirildi."
        )
        follow_up_priority = FollowUpPriority.MEDIUM

    # KADEME 1: Onaylandı / Doğrudan İş Akışına Sevk (Yeterli Veri)
    # Koşul: Bütün operasyonel veriler eksiksiz (missing_count == 0), skor = 100.
    else:
        triage_tier = TriageTier.TIER_1_APPROVED
        status = CompletenessStatus.APPROVED
        is_complete = True
        requires_ai_call = False
        requires_csr_escalation = False
        normalized_score = 100
        triage_reason = "Tüm operasyonel veriler eksiksiz ve doğrulanmıştır. İlgili birim iş akışına onaylandı."
        follow_up_priority = FollowUpPriority.LOW

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
