"""
Case Details Page: In-depth triage workspace for Customer Service Representatives.
Allows reviewing detected vs missing operational data, viewing suggested questions,
entering collected patient responses, and triggering context-enriched re-evaluation.
"""

import streamlit as st
import pandas as pd
from feedbackiq.database.repository import (
    get_case,
    get_cases,
    get_missing_fields_for_case,
    get_follow_up_entries,
)
from feedbackiq.services.followup_service import process_case_reevaluation
from feedbackiq.config.question_templates import get_field_display_name, get_question_for_field
from feedbackiq.models.schemas import ContactStatus
from feedbackiq.utils.helpers import render_tier_badge, render_score_badge, render_priority_badge


def render_case_details_page():
    st.markdown('<div class="app-brand-badge">Investigation Workspace</div>', unsafe_allow_html=True)
    st.title("Case Investigation & Resolution")

    # Case Selector
    all_cases = get_cases(sort_by="score_asc")
    if not all_cases:
        st.warning("No cases available in the system.")
        return

    case_ids = [c["case_id"] for c in all_cases]
    default_case_id = st.session_state.get("selected_case_id", case_ids[0])
    if default_case_id not in case_ids:
        default_case_id = case_ids[0]

    selected_case_id = st.selectbox(
        "Select Feedback Case",
        case_ids,
        index=case_ids.index(default_case_id),
        format_func=lambda cid: f"{cid} — {next(c['issue_type'] for c in all_cases if c['case_id'] == cid)} ({next(c['completeness_score'] for c in all_cases if c['case_id'] == cid)}/100, Tier: {next(c.get('triage_tier', 'CSR Review') for c in all_cases if c['case_id'] == cid)})"
    )

    st.session_state["selected_case_id"] = selected_case_id
    case = get_case(selected_case_id)
    if not case:
        st.error("Case record not found.")
        return

    # Check for recent re-evaluation confirmation
    reeval_info = st.session_state.get(f"reeval_done_{selected_case_id}")
    if reeval_info:
        st.markdown(f"""
        <div class="notice-box notice-success" style="padding:1.1rem; margin-bottom:1.2rem;">
            <div style="font-size:1.05rem; font-weight:700; color:#065f46; margin-bottom:4px;">
                Record Verified & Ready for Operational Dispatch
            </div>
            <div style="font-size:0.88rem; color:#064e3b; margin-bottom:6px;">
                Completeness score improved from <strong>{reeval_info['prev_score']}</strong> to <strong style="color:#047857;">{reeval_info['new_score']} / 100</strong>.
                All required operational variables have been confirmed.
            </div>
            <div style="background:#ffffff; border:1px solid #a7f3d0; border-radius:4px; padding:6px 10px; font-size:0.8rem; font-weight:700; color:#047857; display:inline-block;">
                Ready for Normal Case Management Workflow
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Top Case Status Bar
    score = case["completeness_score"]
    st.markdown(f"""
    <div class="iq-card" style="margin-bottom:1.2rem;">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
            <div>
                <span style="font-size:1.3rem; font-weight:800; color:#0f172a; margin-right:12px;">Case {case['case_id']}</span>
                <span style="color:#64748b; font-size:0.82rem;">Ingested on {case['created_at']} via {case['source_channel']}</span>
            </div>
            <div style="display:flex; align-items:center; gap:8px;">
                {render_score_badge(score)}
                {render_tier_badge(case.get('triage_tier', 'Customer Service Review'))}
                {render_priority_badge(case['follow_up_priority'])}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Original Feedback Display
    st.markdown("""
    <div class="iq-card">
        <div class="iq-card-title">Original Patient Narrative</div>
    """, unsafe_allow_html=True)
    st.markdown(f"""
    <div style="background:#f8fafc; border-left:3px solid #2563eb; padding:0.9rem 1.1rem; border-radius:4px; font-size:0.92rem; color:#1e293b; line-height:1.5;">
        "{case['original_feedback']}"
    </div>
    <div style="margin-top:8px; font-size:0.78rem; color:#64748b;">
        <strong>Summary:</strong> {case['extracted_summary'] or 'N/A'} &bull; 
        <strong>Sentiment:</strong> {case['sentiment'].title()} &bull; 
        <strong>Category:</strong> {case['issue_type']}
    </div>
    </div>
    """, unsafe_allow_html=True)

    # Two column: Detected Info vs Missing & Suggested Questions
    c1, c2 = st.columns([1, 1])

    with c1:
        st.markdown("""
        <div class="iq-card">
            <div class="iq-card-title">Known Operational Parameters</div>
        """, unsafe_allow_html=True)

        fields_to_show = [
            ("Hospital", case["hospital"]),
            ("Department", case["department"]),
            ("Incident Date", case["incident_date"]),
            ("Approximate Time", case["approximate_time"]),
            ("Service / Procedure", case["service_type"]),
            ("Staff Role", case["staff_role"]),
            ("Staff Name", case["staff_name"]),
            ("Billing Context", case["billing_context"]),
            ("Event Description", case["description_of_event"]),
        ]

        for label, val in fields_to_show:
            val_html = f"<strong style='color:#0f172a;'>{val}</strong>" if val else "<span style='color:#94a3b8; font-style:italic;'>Not specified</span>"
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; padding:5px 0; border-bottom:1px solid #f8fafc; font-size:0.83rem;">
                <span style="color:#64748b;">{label}</span>
                <span style="text-align:right; max-width:65%;">{val_html}</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown("""
        <div class="iq-card">
            <div class="iq-card-title">Missing Parameters & Outreach Prompts</div>
        """, unsafe_allow_html=True)

        missing_fields = get_missing_fields_for_case(selected_case_id)
        if missing_fields:
            for item in missing_fields:
                f_name = item["field_name"]
                d_name = get_field_display_name(f_name)
                question = get_question_for_field(f_name)
                crit_tag = "<span style='background:#fee2e2; color:#991b1b; font-size:0.68rem; font-weight:700; padding:1px 5px; border-radius:3px;'>CRITICAL</span>" if item["is_critical"] else "<span style='background:#f1f5f9; color:#475569; font-size:0.68rem; font-weight:600; padding:1px 5px; border-radius:3px;'>MINOR</span>"

                st.markdown(f"""
                <div style="margin-bottom:8px; padding-bottom:6px; border-bottom:1px solid #f8fafc; font-size:0.83rem;">
                    <div><strong style="color:#334155;">{d_name}</strong> {crit_tag}</div>
                    <div style="color:#4338ca; margin-top:2px;">Prompt: "{question}"</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="color:#047857; font-weight:600; font-size:0.86rem; padding:10px 0;">
                All operational requirements met. Ready for dispatch.
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # Customer Service Action & Re-evaluation Form
    st.markdown("""
    <div class="iq-card" style="border: 1px solid #cbd5e1;">
        <div class="iq-card-title" style="color:#1e293b;">
            Customer Service Investigation & Re-evaluation
        </div>
        <p style="font-size:0.83rem; color:#475569; margin-top:-6px; margin-bottom:12px;">
            Log contact outreach and input confirmed patient responses. Confirmed values strictly take precedence over initial inferences.
        </p>
    """, unsafe_allow_html=True)

    act_col1, act_col2 = st.columns([1, 2])
    with act_col1:
        contact_options = [c.value for c in ContactStatus]
        curr_contact_idx = contact_options.index(case["contact_status"]) if case["contact_status"] in contact_options else 0
        new_contact_status = st.selectbox("Update Outreach Status", contact_options, index=curr_contact_idx)
    with act_col2:
        csr_notes = st.text_input("Representative Outreach Notes", placeholder="e.g. Telephoned patient; confirmed cardiology appointment delay.")

    st.markdown("<p style='font-size:0.8rem; font-weight:700; color:#334155; text-transform:uppercase; letter-spacing:0.04em; margin-top:8px;'>Input Confirmed Operational Details:</p>", unsafe_allow_html=True)

    inp_c1, inp_c2, inp_c3 = st.columns(3)
    with inp_c1:
        confirmed_hospital = st.text_input("Hospital", value=case["hospital"] or "", placeholder="e.g. Example Hospital Central")
        confirmed_dept = st.text_input("Department / Unit", value=case["department"] or "", placeholder="e.g. Cardiology")
    with inp_c2:
        confirmed_date = st.text_input("Incident Date", value=case["incident_date"] or "", placeholder="e.g. 2026-10-03")
        confirmed_time = st.text_input("Approximate Time", value=case["approximate_time"] or "", placeholder="e.g. 14:00")
    with inp_c3:
        confirmed_service = st.text_input("Service / Exam", value=case["service_type"] or "", placeholder="e.g. Specialist Consult, MRI")
        confirmed_staff = st.text_input("Staff Role / Name", value=f"{case['staff_role'] or ''} {case['staff_name'] or ''}".strip(), placeholder="e.g. Nurse Jane")

    reeval_clicked = st.button("Re-evaluate Case Completeness", type="primary", use_container_width=False)

    if reeval_clicked:
        with st.spinner("Re-evaluating case with confirmed parameters..."):
            confirmed_dict = {}
            if confirmed_hospital.strip():
                confirmed_dict["hospital"] = confirmed_hospital.strip()
            if confirmed_dept.strip():
                confirmed_dict["department"] = confirmed_dept.strip()
            if confirmed_date.strip():
                confirmed_dict["incident_date"] = confirmed_date.strip()
            if confirmed_time.strip():
                confirmed_dict["approximate_time"] = confirmed_time.strip()
            if confirmed_service.strip():
                confirmed_dict["service_type"] = confirmed_service.strip()
            if confirmed_staff.strip():
                confirmed_dict["staff_role"] = confirmed_staff.strip()

            updated_case, result, prev_score = process_case_reevaluation(
                case_id=selected_case_id,
                confirmed_fields=confirmed_dict,
                notes=csr_notes or "Re-evaluation triggered via Case Details.",
                contact_status=new_contact_status
            )

            st.session_state[f"reeval_done_{selected_case_id}"] = {
                "prev_score": prev_score,
                "new_score": result.completeness_score,
                "is_complete": result.is_complete,
                "status": result.status.value
            }
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    # Outreach Log
    st.markdown("""
    <div class="iq-card">
        <div class="iq-card-title">Outreach History & Audit Trail</div>
    """, unsafe_allow_html=True)

    history_entries = get_follow_up_entries(selected_case_id)
    if history_entries:
        hist_rows = []
        for h in history_entries:
            hist_rows.append({
                "Timestamp": h["created_at"],
                "Contact Status": h["contact_status"],
                "Details Collected": h["additional_information"] or "-",
                "Notes": h["notes"] or "-"
            })
        df_hist = pd.DataFrame(hist_rows)
        st.dataframe(df_hist, use_container_width=True, hide_index=True)
    else:
        st.write("No outreach logs recorded.")

    st.markdown("</div>", unsafe_allow_html=True)
