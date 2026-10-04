"""
Dashboard Page: High-level overview of feedback quality metrics, completeness distribution,
top missing operational fields, and recent cases.
"""

import streamlit as st
import pandas as pd
from feedbackiq.database.repository import get_kpis, get_analytics_data, get_cases
from feedbackiq.database.seed import seed_database
from feedbackiq.config.question_templates import get_field_display_name
from feedbackiq.utils.helpers import render_status_pill, render_score_badge


def render_dashboard_page():
    # Header
    st.markdown('<div class="app-brand-badge">Quality Firewall Overview</div>', unsafe_allow_html=True)
    st.title("Patient Feedback Quality Dashboard")
    st.markdown(
        "<p style='color:#64748b; margin-top:-10px; margin-bottom: 25px;'>"
        "Monitoring feedback records for operational completeness before dispatching to hospital departments."
        "</p>",
        unsafe_allow_html=True
    )

    kpis = get_kpis()

    if kpis["total_cases"] == 0:
        st.info("The database has no feedback records yet. Click below to load synthetic demo records.")
        if st.button("Load 10+ Synthetic Demo Cases", type="primary"):
            seed_database(force=True)
            st.rerun()
        return

    # KPI Metrics Row
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Total Feedback</div>
            <div class="kpi-value">{kpis['total_cases']}</div>
            <div class="kpi-subtext">All intake channels</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Complete Cases</div>
            <div class="kpi-value" style="color: #059669;">{kpis['complete_cases']}</div>
            <div class="kpi-subtext">Ready for workflow</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Follow-up Required</div>
            <div class="kpi-value" style="color: #dc2626;">{kpis['followup_required']}</div>
            <div class="kpi-subtext">Missing critical data</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Avg Quality Score</div>
            <div class="kpi-value" style="color: #2563eb;">{kpis['avg_score']}<span style="font-size:1rem; color:#64748b;">/100</span></div>
            <div class="kpi-subtext">Deterministic quality</div>
        </div>
        """, unsafe_allow_html=True)
    with col5:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Open Follow-ups</div>
            <div class="kpi-value" style="color: #d97706;">{kpis['open_followups']}</div>
            <div class="kpi-subtext">In CSR triage queue</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    analytics = get_analytics_data()

    # Two column layout: Completeness Distribution & Top Missing Fields
    left_col, right_col = st.columns([1, 1])

    with left_col:
        st.markdown("""
        <div class="iq-card">
            <div class="iq-card-title">
                <span>📊</span> Completeness Status Distribution
            </div>
        """, unsafe_allow_html=True)

        dist_data = analytics["status_dist"]
        total_count = kpis["total_cases"] or 1

        for row in dist_data:
            st_name = row["status"]
            cnt = row["count"]
            pct = int(round((cnt / total_count) * 100))
            
            bar_color = "#10b981" if st_name in ["Complete", "Ready for Workflow"] else "#f59e0b" if st_name == "Needs Review" else "#ef4444"
            st.markdown(f"""
            <div style="margin-bottom: 12px;">
                <div style="display:flex; justify-content:space-between; font-size:0.85rem; font-weight:500; margin-bottom:4px;">
                    <span>{st_name}</span>
                    <span style="color:#64748b;">{cnt} cases ({pct}%)</span>
                </div>
                <div style="background:#e2e8f0; border-radius:4px; height:8px; overflow:hidden;">
                    <div style="background:{bar_color}; width:{pct}%; height:100%;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    with right_col:
        st.markdown("""
        <div class="iq-card">
            <div class="iq-card-title">
                <span>🔍</span> Top Missing Operational Information
            </div>
        """, unsafe_allow_html=True)

        top_missing = analytics["top_missing"]
        if top_missing:
            for item in top_missing[:5]:
                field_key = item["field_name"]
                cnt = item["count"]
                d_name = get_field_display_name(field_key)
                st.markdown(f"""
                <div style="display:flex; justify-content:space-between; align-items:center; padding:8px 0; border-bottom:1px solid #f1f5f9; font-size:0.88rem;">
                    <span style="font-weight:500; color:#334155;">{d_name}</span>
                    <span style="background:#f1f5f9; color:#475569; font-weight:600; padding:2px 10px; border-radius:12px; font-size:0.8rem;">
                        {cnt} cases
                    </span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.write("No missing field records currently active.")

        st.markdown("</div>", unsafe_allow_html=True)

    # Recent Feedback Cases Table
    st.markdown("""
    <div class="iq-card">
        <div class="iq-card-title">
            <span>📋</span> Recent Feedback Cases
        </div>
    """, unsafe_allow_html=True)

    recent_cases = get_cases(sort_by="date_desc")[:8]
    if recent_cases:
        table_rows = []
        for c in recent_cases:
            table_rows.append({
                "Case ID": c["case_id"],
                "Created At": c["created_at"],
                "Channel": c["source_channel"],
                "Issue Type": c["issue_type"],
                "Score": f"{c['completeness_score']}/100",
                "Status": c["status"],
                "Contact": c["contact_status"]
            })
        df = pd.DataFrame(table_rows)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.write("No recent cases found.")

    st.markdown("</div>", unsafe_allow_html=True)
