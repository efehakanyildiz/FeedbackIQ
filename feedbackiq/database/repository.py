"""
Database repository providing CRUD and query operations for FeedbackIQ.
"""

import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from feedbackiq.database.db import db_session
from feedbackiq.models.schemas import CompletenessResult, CompletenessStatus, ContactStatus


def _now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def generate_case_id() -> str:
    """Generate a clean human-readable sequential or timestamped case ID."""
    with db_session() as conn:
        cursor = conn.execute("SELECT COUNT(*) as cnt FROM feedback_cases;")
        cnt = cursor.fetchone()["cnt"]
        return f"FB-{datetime.now().year}-{1001 + cnt}"


def save_case(case_dict: Dict[str, Any], result: CompletenessResult) -> str:
    """Insert a newly analyzed feedback case along with missing fields and history."""
    case_id = case_dict.get("case_id") or generate_case_id()
    now_str = _now_iso()

    with db_session() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO feedback_cases (
                case_id, created_at, source_channel, original_feedback,
                feedback_type, issue_type, sentiment, hospital, department,
                incident_date, approximate_time, service_type, staff_role,
                staff_name, billing_context, description_of_event, impact,
                explicit_request, extracted_summary, extraction_confidence,
                completeness_score, status, follow_up_priority, contact_status, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            case_id,
            case_dict.get("created_at", now_str),
            case_dict.get("source_channel", "Website"),
            case_dict.get("original_feedback", ""),
            case_dict.get("feedback_type", "complaint"),
            case_dict.get("issue_type", "Other"),
            case_dict.get("sentiment", "negative"),
            case_dict.get("hospital"),
            case_dict.get("department"),
            case_dict.get("incident_date"),
            case_dict.get("approximate_time"),
            case_dict.get("service_type"),
            case_dict.get("staff_role"),
            case_dict.get("staff_name"),
            case_dict.get("billing_context"),
            case_dict.get("description_of_event"),
            case_dict.get("impact"),
            case_dict.get("explicit_request"),
            case_dict.get("extracted_summary", ""),
            case_dict.get("extraction_confidence", 0.8),
            result.completeness_score,
            result.status.value,
            result.follow_up_priority.value,
            case_dict.get("contact_status", ContactStatus.NOT_CONTACTED.value),
            now_str
        ))

        # Insert missing fields
        for item in result.missing_field_items:
            conn.execute("""
                INSERT INTO missing_fields (case_id, field_name, is_critical, resolved)
                VALUES (?, ?, ?, ?)
            """, (case_id, item.field_name, 1 if item.is_critical else 0, 0))

        # Insert initial analysis history
        conn.execute("""
            INSERT INTO analysis_history (case_id, created_at, completeness_score, status, extracted_json)
            VALUES (?, ?, ?, ?, ?)
        """, (case_id, now_str, result.completeness_score, result.status.value, json.dumps(case_dict)))

    return case_id


def get_case(case_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve single case record by case_id."""
    with db_session() as conn:
        cursor = conn.execute("SELECT * FROM feedback_cases WHERE case_id = ?", (case_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return dict(row)


def get_cases(
    status_filter: Optional[str] = None,
    issue_type_filter: Optional[str] = None,
    score_min: Optional[int] = None,
    score_max: Optional[int] = None,
    contact_status_filter: Optional[str] = None,
    sort_by: str = "score_asc"
) -> List[Dict[str, Any]]:
    """Retrieve list of cases with optional filtering and ordering."""
    query = """
        SELECT c.*, 
               (SELECT COUNT(*) FROM missing_fields m WHERE m.case_id = c.case_id AND m.resolved = 0) as missing_fields_count
        FROM feedback_cases c
        WHERE 1=1
    """
    params = []

    if status_filter and status_filter != "All":
        query += " AND c.status = ?"
        params.append(status_filter)

    if issue_type_filter and issue_type_filter != "All":
        query += " AND c.issue_type = ?"
        params.append(issue_type_filter)

    if contact_status_filter and contact_status_filter != "All":
        query += " AND c.contact_status = ?"
        params.append(contact_status_filter)

    if score_min is not None:
        query += " AND c.completeness_score >= ?"
        params.append(score_min)

    if score_max is not None:
        query += " AND c.completeness_score <= ?"
        params.append(score_max)

    if sort_by == "score_asc":
        query += " ORDER BY c.completeness_score ASC, c.id DESC"
    elif sort_by == "score_desc":
        query += " ORDER BY c.completeness_score DESC, c.id DESC"
    elif sort_by == "date_desc":
        query += " ORDER BY c.created_at DESC"
    else:
        query += " ORDER BY c.id DESC"

    with db_session() as conn:
        cursor = conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]


def get_missing_fields_for_case(case_id: str) -> List[Dict[str, Any]]:
    """Get active missing fields for a specific case."""
    with db_session() as conn:
        cursor = conn.execute("""
            SELECT * FROM missing_fields WHERE case_id = ? ORDER BY is_critical DESC, id ASC
        """, (case_id,))
        return [dict(row) for row in cursor.fetchall()]


def get_follow_up_entries(case_id: str) -> List[Dict[str, Any]]:
    """Get CSR contact & follow-up logs for a case."""
    with db_session() as conn:
        cursor = conn.execute("""
            SELECT * FROM follow_up_entries WHERE case_id = ? ORDER BY created_at DESC
        """, (case_id,))
        return [dict(row) for row in cursor.fetchall()]


def add_follow_up_entry(
    case_id: str,
    contact_status: str,
    additional_information: str,
    notes: str
) -> None:
    """Log an interaction attempt or collected information from customer service."""
    now_str = _now_iso()
    with db_session() as conn:
        conn.execute("""
            INSERT INTO follow_up_entries (case_id, created_at, contact_status, additional_information, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (case_id, now_str, contact_status, additional_information, notes))

        conn.execute("""
            UPDATE feedback_cases 
            SET contact_status = ?, updated_at = ?
            WHERE case_id = ?
        """, (contact_status, now_str, case_id))


def update_case_after_reevaluation(
    case_id: str,
    updated_fields: Dict[str, Any],
    result: CompletenessResult,
    extracted_json: str
) -> None:
    """Update case with re-evaluated fields, new completeness score, and history entry."""
    now_str = _now_iso()
    
    # If complete after follow up, mark status as READY_FOR_WORKFLOW
    new_status = CompletenessStatus.READY_FOR_WORKFLOW.value if result.is_complete else result.status.value

    with db_session() as conn:
        conn.execute("""
            UPDATE feedback_cases
            SET hospital = COALESCE(?, hospital),
                department = COALESCE(?, department),
                incident_date = COALESCE(?, incident_date),
                approximate_time = COALESCE(?, approximate_time),
                service_type = COALESCE(?, service_type),
                staff_role = COALESCE(?, staff_role),
                staff_name = COALESCE(?, staff_name),
                billing_context = COALESCE(?, billing_context),
                description_of_event = COALESCE(?, description_of_event),
                impact = COALESCE(?, impact),
                completeness_score = ?,
                status = ?,
                follow_up_priority = ?,
                updated_at = ?
            WHERE case_id = ?
        """, (
            updated_fields.get("hospital"),
            updated_fields.get("department"),
            updated_fields.get("incident_date"),
            updated_fields.get("approximate_time"),
            updated_fields.get("service_type"),
            updated_fields.get("staff_role"),
            updated_fields.get("staff_name"),
            updated_fields.get("billing_context"),
            updated_fields.get("description_of_event"),
            updated_fields.get("impact"),
            result.completeness_score,
            new_status,
            result.follow_up_priority.value,
            now_str,
            case_id
        ))

        # Clear and re-populate missing fields
        conn.execute("DELETE FROM missing_fields WHERE case_id = ?", (case_id,))
        for item in result.missing_field_items:
            conn.execute("""
                INSERT INTO missing_fields (case_id, field_name, is_critical, resolved)
                VALUES (?, ?, ?, ?)
            """, (case_id, item.field_name, 1 if item.is_critical else 0, 0))

        # Record analysis history
        conn.execute("""
            INSERT INTO analysis_history (case_id, created_at, completeness_score, status, extracted_json)
            VALUES (?, ?, ?, ?, ?)
        """, (case_id, now_str, result.completeness_score, new_status, extracted_json))


def get_kpis() -> Dict[str, Any]:
    """Calculate dashboard summary KPIs."""
    with db_session() as conn:
        total = conn.execute("SELECT COUNT(*) as c FROM feedback_cases;").fetchone()["c"]
        if total == 0:
            return {
                "total_cases": 0,
                "complete_cases": 0,
                "followup_required": 0,
                "avg_score": 0,
                "open_followups": 0
            }

        complete = conn.execute("""
            SELECT COUNT(*) as c FROM feedback_cases 
            WHERE status IN ('Complete', 'Ready for Workflow')
        """).fetchone()["c"]

        followup = conn.execute("""
            SELECT COUNT(*) as c FROM feedback_cases 
            WHERE status = 'Follow-up Required'
        """).fetchone()["c"]

        avg_score = conn.execute("SELECT AVG(completeness_score) as avg_s FROM feedback_cases;").fetchone()["avg_s"]
        
        open_followups = conn.execute("""
            SELECT COUNT(*) as c FROM feedback_cases 
            WHERE status IN ('Follow-up Required', 'Needs Review') 
            AND contact_status NOT IN ('Completed', 'Information Collected')
        """).fetchone()["c"]

        return {
            "total_cases": total,
            "complete_cases": complete,
            "followup_required": followup,
            "avg_score": round(avg_score or 0, 1),
            "open_followups": open_followups
        }


def get_analytics_data() -> Dict[str, Any]:
    """Provide structured analytics data for dashboard and analytics page."""
    with db_session() as conn:
        # Status distribution
        status_rows = conn.execute("""
            SELECT status, COUNT(*) as count 
            FROM feedback_cases 
            GROUP BY status
        """).fetchall()

        # Channel quality (score by channel)
        channel_rows = conn.execute("""
            SELECT source_channel, 
                   COUNT(*) as total_cases, 
                   ROUND(AVG(completeness_score), 1) as avg_score,
                   SUM(CASE WHEN status IN ('Complete', 'Ready for Workflow') THEN 1 ELSE 0 END) as complete_count
            FROM feedback_cases
            GROUP BY source_channel
            ORDER BY avg_score DESC
        """).fetchall()

        # Top missing fields
        missing_rows = conn.execute("""
            SELECT field_name, COUNT(*) as count
            FROM missing_fields
            WHERE resolved = 0
            GROUP BY field_name
            ORDER BY count DESC
            LIMIT 10
        """).fetchall()

        # Feedback by Issue Type
        issue_rows = conn.execute("""
            SELECT issue_type, 
                   COUNT(*) as count, 
                   ROUND(AVG(completeness_score), 1) as avg_score
            FROM feedback_cases
            GROUP BY issue_type
            ORDER BY count DESC
        """).fetchall()

        # Re-evaluation recovery rate
        recovered = conn.execute("""
            SELECT COUNT(*) as c FROM feedback_cases
            WHERE status = 'Ready for Workflow'
        """).fetchone()["c"]

        return {
            "status_dist": [dict(r) for r in status_rows],
            "channel_quality": [dict(r) for r in channel_rows],
            "top_missing": [dict(r) for r in missing_rows],
            "issue_breakdown": [dict(r) for r in issue_rows],
            "recovered_count": recovered
        }


def count_cases() -> int:
    with db_session() as conn:
        return conn.execute("SELECT COUNT(*) as c FROM feedback_cases;").fetchone()["c"]
