"""
Customer Service Review Queue (Tier 3): Dedicated triage workspace for high-complexity,
severely incomplete feedback records requiring human representative investigation.
"""

import streamlit as st
import pandas as pd
from feedbackiq.database.repository import get_cases
from feedbackiq.models.schemas import IssueType, ContactStatus, TriageTier
from feedbackiq.utils.helpers import render_tier_badge, render_score_badge, render_priority_badge


def render_followup_queue_page():
    st.markdown('<div class="app-brand-badge">Human Representative Workspace</div>', unsafe_allow_html=True)
    st.title("Customer Service Review Queue (Tier 3)")
    st.markdown(
        "<p style='color:#64748b; margin-top:-8px; margin-bottom: 24px; font-size:0.95rem;'>"
        "Records with multiple critical missing parameters escalated to human Customer Service Representatives for comprehensive patient outreach."
        "</p>",
        unsafe_allow_html=True
    )

    # Filter Bar
    st.markdown("<div class='iq-card' style='padding: 0.9rem 1.2rem 0.4rem 1.2rem;'>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1.2])

    with col1:
        tier_filter = st.selectbox(
            "Triage Tier",
            ["Customer Service Review", "All Incomplete Tiers"],
            index=0
        )
    with col2:
        issue_options = ["All Categories"] + [i.value for i in IssueType]
        issue_filter = st.selectbox("Issue Category", issue_options, index=0)
    with col3:
        contact_options = ["All Contact States"] + [c.value for c in ContactStatus]
        contact_filter = st.selectbox("Contact Status", contact_options, index=0)
    with col4:
        score_range = st.slider("Completeness Score Range", 0, 80, (0, 80))

    st.markdown("</div>", unsafe_allow_html=True)

    # Fetch matching cases
    selected_tier = TriageTier.TIER_3_CSR_ESCALATION.value if tier_filter == "Customer Service Review" else None
    queue_cases = get_cases(
        tier_filter=selected_tier,
        issue_type_filter=issue_filter if issue_filter != "All Categories" else None,
        contact_status_filter=contact_filter if contact_filter != "All Contact States" else None,
        score_min=score_range[0],
        score_max=score_range[1],
        sort_by="score_asc"
    )

    # Filter out cases that are already Approved or Resolved
    unresolved_cases = [c for c in queue_cases if c["status"] not in ["Approved", "Resolved / Ready for Workflow"]]

    st.markdown(f"""
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
        <span style="font-weight:600; font-size:0.9rem; color:#334155;">
            {len(unresolved_cases)} Escalated Cases Requiring Human Contact
        </span>
        <span style="font-size:0.78rem; color:#64748b;">
            Ordering: <strong>Lowest Completeness Score First</strong>
        </span>
    </div>
    """, unsafe_allow_html=True)

    if not unresolved_cases:
        st.success("All escalated cases have been reviewed and resolved.")
        return

    # Render each case in a modern enterprise list card
    for case in unresolved_cases:
        case_id = case["case_id"]
        score = case["completeness_score"]
        priority = case["follow_up_priority"]
        missing_count = case.get("missing_fields_count", 0)
        feedback_preview = case["original_feedback"]
        if len(feedback_preview) > 130:
            feedback_preview = feedback_preview[:130] + "..."

        with st.container():
            st.markdown(f"""
            <div class="iq-card" style="margin-bottom: 12px; padding: 1.1rem 1.3rem;">
                <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:6px;">
                    <div>
                        <span style="font-size:1.05rem; font-weight:700; color:#0f172a; margin-right:8px;">{case_id}</span>
                        <span style="font-size:0.8rem; color:#64748b; margin-right:8px;">{case['created_at']}</span>
                        <span style="background:#f1f5f9; color:#475569; padding:2px 7px; border-radius:3px; font-size:0.72rem; font-weight:600;">
                            Channel: {case['source_channel']}
                        </span>
                    </div>
                    <div style="display:flex; align-items:center; gap:8px;">
                        {render_score_badge(score)}
                        {render_tier_badge(case.get('triage_tier', 'Customer Service Review'))}
                        {render_priority_badge(priority)}
                    </div>
                </div>
                <div style="font-size:0.88rem; color:#334155; margin-bottom:8px; font-style:italic; background:#f8fafc; padding:8px 12px; border-radius:4px; border-left:3px solid #cbd5e1;">
                    "{feedback_preview}"
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center; font-size:0.8rem; color:#64748b;">
                    <div>
                        <strong>Category:</strong> {case['issue_type']} &bull;
                        <strong>Missing Fields:</strong> <span style="color:#b91c1c; font-weight:700;">{missing_count}</span> &bull;
                        <strong>Outreach Status:</strong> {case['contact_status']}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            btn_col1, btn_col2 = st.columns([1.5, 4])
            with btn_col1:
                if st.button(f"Investigate Case", key=f"csr_{case_id}", type="secondary", use_container_width=True):
                    st.session_state["selected_case_id"] = case_id
                    st.session_state["current_page"] = "Case Details"
                    st.rerun()
