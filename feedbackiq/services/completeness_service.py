"""
Deterministic Python Rules Engine for Completeness Evaluation.
Evaluates structured feedback data against explicit business rules.
"""

from typing import Dict, Any, List, Tuple
from feedbackiq.models.schemas import (
    ExtractedFeedbackData,
    CompletenessResult,
    CompletenessStatus,
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
    Perform deterministic evaluation of structured feedback data.
    Does not use Gemini for scoring decisions.
    
    Args:
        data: Extracted feedback data from Gemini or mock.
        confirmed_overrides: Optional manually entered and verified values from CSR.
    
    Returns:
        CompletenessResult with score, status, missing fields, questions and explanation.
    """
    if confirmed_overrides is None:
        confirmed_overrides = {}

    # Merge data with manual overrides taking strict precedence
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
        max_group_weight = max(group_weights) if group_weights else 0
        sum_group_weight = sum(group_weights)
        
        present_in_group = [f for f in group if _is_value_present(merged_data.get(f))]
        for f in group:
            or_fields_evaluated.add(f)
            
        if present_in_group:
            # At least one field in OR group is satisfied
            # Award points for the group
            score += sum_group_weight
            for f in present_in_group:
                score_breakdown[f] = weights.get(f, 0)
                detected_fields[f] = merged_data[f]
        else:
            # Neither is present - add group representation to missing fields
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

    # Sort missing fields predictably
    sorted_missing = sorted(list(missing_fields_set))
    sorted_critical = sorted(list(critical_missing_set))

    # Build rich missing field items with questions
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

    # Determine status based on score AND critical missing fields
    if len(sorted_critical) == 0 and normalized_score >= THRESHOLD_COMPLETE:
        status = CompletenessStatus.COMPLETE
        is_complete = True
    elif len(sorted_critical) == 0 and normalized_score >= THRESHOLD_NEEDS_REVIEW:
        status = CompletenessStatus.NEEDS_REVIEW
        is_complete = False
    else:
        status = CompletenessStatus.FOLLOW_UP_REQUIRED
        is_complete = False

    # Determine follow-up priority (Customer Service Follow-up Priority, not medical)
    feedback_type = merged_data.get("feedback_type", "complaint")
    if normalized_score < 50 or (feedback_type == "complaint" and len(sorted_critical) >= 2):
        follow_up_priority = FollowUpPriority.HIGH
    elif feedback_type in ["appreciation", "suggestion"] and normalized_score >= 60:
        follow_up_priority = FollowUpPriority.LOW
    else:
        follow_up_priority = FollowUpPriority.MEDIUM

    # Build why_needed explanation
    if is_complete:
        why_explanation = "The feedback record contains all operational details (facility, unit, time context, and event description) required to investigate and resolve the case immediately."
    else:
        base_desc = rule_config.get("explanation", "Operational details are required for institutional investigation.")
        missing_names = [get_field_display_name(f) for f in sorted_missing]
        if missing_names:
            why_explanation = (
                f"{base_desc} Currently missing: {', '.join(missing_names)}. "
                "Contacting the patient to capture these specifics will ensure the unit team can investigate without delays."
            )
        else:
            why_explanation = base_desc

    return CompletenessResult(
        completeness_score=normalized_score,
        status=status,
        follow_up_priority=follow_up_priority,
        is_complete=is_complete,
        missing_fields=sorted_missing,
        critical_missing_fields=sorted_critical,
        missing_field_items=missing_items,
        detected_fields=detected_fields,
        why_needed_explanation=why_explanation,
        score_breakdown=score_breakdown,
    )
