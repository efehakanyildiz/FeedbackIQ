"""
Customer Service Follow-up Queue: Displays incomplete patient feedback cases requiring outreach,
ordered by lowest completeness score by default, with rich filters and quick-action navigation.
"""

import streamlit as st
import pandas as pd
from feedbackiq.database.repository import get_cases
from feedbackiq.models.schemas import IssueType, ContactStatus
from feedbackiq.utils.helpers import render_status_pill, render_priority_pill, render_score_badge


def render_followup_queue_page():
    st.markdown('<div class="app-brand-badge">CSR Outreach Workspace</div>', unsafe_allow_html=True)
    st.title("Customer Service Follow-up Queue")
    st.markdown(
        "<p style='color:#64748b; margin-top:-10px; margin-bottom: 20px;'>"
        "Active queue of incomplete feedback records requiring patient contact to gather essential investigation details."
        "</p>",
        unsafe_allow_html=True
    )

    # Filter Bar
    st.markdown("<div class='iq-card' style='padding: 1rem 1.25rem 0.5rem 1.25rem;'>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1.2])

    with col1:
        status_filter = st.selectbox(
            "Status",
            ["All", "Follow-up Required", "Needs Review"],
            index=0
        )
    with col2:
        issue_options = ["All"] + [i.value for i in IssueType]
        issue_filter = st.selectbox("Issue Category", issue_options, index=0)
    with col3:
        contact_options = ["All"] + [c.value for c in ContactStatus]
        contact_filter = st.selectbox("Contact Status", contact_options, index=0)
    with col4:
        score_range = st.slider("Completeness Score Range", 0, 84, (0, 84))

    st.markdown("</div>", unsafe_allow_html=True)

    # Fetch matching cases (restricted to Follow-up Required or Needs Review)
    all_incomplete = get_cases(
        status_filter=status_filter if status_filter != "All" else None,
        issue_type_filter=issue_filter if issue_filter != "All" else None,
        contact_status_filter=contact_filter if contact_filter != "All" else None,
        score_min=score_range[0],
        score_max=score_range[1],
        sort_by="score_asc"
    )

    # If status filter was 'All', make sure we only include Follow-up Required and Needs Review in this queue
    queue_cases = [c for c in all_incomplete if c["status"] in ["Follow-up Required", "Needs Review"]]

    st.markdown(f"""
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
        <span style="font-weight:600; font-size:0.95rem; color:#334155;">
            {len(queue_cases)} Incomplete Cases Awaiting Follow-up
        </span>
        <span style="font-size:0.8rem; color:#64748b;">
            Sorted by: <strong>Lowest Completeness Score First</strong>
        </span>
    </div>
    """, unsafe_allow_html=True)

    if not queue_cases:
        st.success("🎉 All feedback records in the queue have been fully resolved and completed!")
        return

    # Render each case in a modern enterprise list card
    for case in queue_cases:
        case_id = case["case_id"]
        score = case["completeness_score"]
        priority = case["follow_up_priority"]
        missing_count = case.get("missing_fields_count", 0)
        feedback_preview = case["original_feedback"]
        if len(feedback_preview) > 130:
            feedback_preview = feedback_preview[:130] + "..."

        with st.container():
            st.markdown(f"""
            <div class="iq-card" style="margin-bottom: 12px; padding: 1rem 1.25rem;">
                <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:6px;">
                    <div>
                        <span style="font-size:1.05rem; font-weight:700; color:#0f172a; margin-right:8px;">{case_id}</span>
                        <span style="font-size:0.8rem; color:#64748b; margin-right:10px;">{case['created_at']}</span>
                        <span style="background:#f1f5f9; color:#475569; padding:2px 8px; border-radius:4px; font-size:0.75rem; font-weight:600;">
                            Channel: {case['source_channel']}
                        </span>
                    </div>
                    <div style="display:flex; align-items:center; gap:8px;">
                        {render_score_badge(score)}
                        {render_priority_pill(priority)}
                        {render_status_pill(case['status'])}
                    </div>
                </div>
                <div style="font-size:0.9rem; color:#334155; margin-bottom:8px; font-style:italic; background:#f8fafc; padding:8px 12px; border-radius:6px; border-left:3px solid #cbd5e1;">
                    "{feedback_preview}"
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center; font-size:0.8rem; color:#64748b;">
                    <div>
                        <strong style="color:#475569;">Issue:</strong> {case['issue_type']} &bull;
                        <strong style="color:#dc2626;">Missing Fields:</strong> {missing_count} &bull;
                        <strong style="color:#475569;">Contact Status:</strong> {case['contact_status']}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            btn_col1, btn_col2 = st.columns([1, 6])
            with btn_col1:
                if st.button(f"Open Case {case_id}", key=f"open_{case_id}", type="secondary", use_container_width=True):
                    st.session_state["selected_case_id"] = case_id
                    st.session_state["current_page"] = "Case Details"
                    st.rerun()
