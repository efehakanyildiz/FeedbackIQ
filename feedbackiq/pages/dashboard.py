"""
Dashboard Page: Executive overview of patient feedback quality and 3-tier triage distribution:
- Tier 1: Approved / Ready for Workflow
- Tier 2: AI Voice Bot Follow-up
- Tier 3: Customer Service Escalation
"""

import streamlit as st
import pandas as pd
from feedbackiq.database.repository import get_kpis, get_analytics_data, get_cases
from feedbackiq.database.seed import seed_database
from feedbackiq.config.question_templates import get_field_display_name
from feedbackiq.utils.helpers import render_tier_badge, render_score_badge, render_priority_badge


def render_dashboard_page():
    # Clean enterprise header
    st.markdown('<div class="app-brand-badge">Quality Gate Overview</div>', unsafe_allow_html=True)
    st.title("Patient Feedback Quality Dashboard")
    st.markdown(
        "<p style='color:#64748b; margin-top:-8px; margin-bottom: 24px; font-size: 0.95rem;'>"
        "Automated data quality firewall routing incoming patient feedback across three operational tiers."
        "</p>",
        unsafe_allow_html=True
    )

    kpis = get_kpis()

    if kpis["total_cases"] == 0:
        st.info("No feedback records currently in the database. Initialize demo cases below.")
        if st.button("Load Synthetic Healthcare Records", type="primary"):
            seed_database(force=True)
            st.rerun()
        return

    # Top KPI Metrics Row
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Total Ingested</div>
            <div class="kpi-value">{kpis['total_cases']}</div>
            <div class="kpi-subtext">All intake channels</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Tier 1: Approved</div>
            <div class="kpi-value" style="color: #047857;">{kpis['tier_1_approved']}</div>
            <div class="kpi-subtext">Sufficient operational data</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Tier 2: AI Voice Call</div>
            <div class="kpi-value" style="color: #4338ca;">{kpis['tier_2_ai_call']}</div>
            <div class="kpi-subtext">Minor data gaps</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Tier 3: CSR Review</div>
            <div class="kpi-value" style="color: #b91c1c;">{kpis['tier_3_csr']}</div>
            <div class="kpi-subtext">Major critical gaps</div>
        </div>
        """, unsafe_allow_html=True)
    with c5:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Average Quality</div>
            <div class="kpi-value" style="color: #0f172a;">{kpis['avg_score']}<span style="font-size:0.9rem; color:#64748b;">/100</span></div>
            <div class="kpi-subtext">Deterministic score</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    analytics = get_analytics_data()

    # Two column layout: 3-Tier Distribution & Top Missing Fields
    left_col, right_col = st.columns([1, 1])

    with left_col:
        st.markdown("""
        <div class="iq-card">
            <div class="iq-card-title">Three-Tier Triage Distribution</div>
        """, unsafe_allow_html=True)

        tier_data = analytics["tier_dist"]
        total_count = kpis["total_cases"] or 1

        tier_colors = {
            "Approved": "#10b981",
            "AI Call Scheduled": "#6366f1",
            "Customer Service Review": "#f43f5e"
        }

        for row in tier_data:
            t_name = row["triage_tier"]
            cnt = row["count"]
            pct = int(round((cnt / total_count) * 100))
            bar_color = tier_colors.get(t_name, "#94a3b8")

            st.markdown(f"""
            <div style="margin-bottom: 12px;">
                <div style="display:flex; justify-content:space-between; font-size:0.83rem; font-weight:600; margin-bottom:4px;">
                    <span style="color:#1e293b;">{t_name}</span>
                    <span style="color:#64748b;">{cnt} records ({pct}%)</span>
                </div>
                <div style="background:#e2e8f0; border-radius:3px; height:7px; overflow:hidden;">
                    <div style="background:{bar_color}; width:{pct}%; height:100%;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    with right_col:
        st.markdown("""
        <div class="iq-card">
            <div class="iq-card-title">Top Missing Operational Fields</div>
        """, unsafe_allow_html=True)

        top_missing = analytics["top_missing"]
        if top_missing:
            for item in top_missing[:5]:
                field_key = item["field_name"]
                cnt = item["count"]
                d_name = get_field_display_name(field_key)
                st.markdown(f"""
                <div style="display:flex; justify-content:space-between; align-items:center; padding:7px 0; border-bottom:1px solid #f8fafc; font-size:0.85rem;">
                    <span style="font-weight:500; color:#334155;">{d_name}</span>
                    <span style="background:#f1f5f9; color:#475569; font-weight:700; padding:1px 8px; border-radius:4px; font-size:0.75rem;">
                        {cnt} cases
                    </span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.write("No active missing fields.")

        st.markdown("</div>", unsafe_allow_html=True)

    # Recent Records Table
    st.markdown("""
    <div class="iq-card">
        <div class="iq-card-title">Recent Feedback Ingestion Log</div>
    """, unsafe_allow_html=True)

    recent_cases = get_cases(sort_by="date_desc")[:8]
    if recent_cases:
        table_rows = []
        for c in recent_cases:
            table_rows.append({
                "Case ID": c["case_id"],
                "Timestamp": c["created_at"],
                "Channel": c["source_channel"],
                "Category": c["issue_type"],
                "Quality Score": f"{c['completeness_score']}/100",
                "Triage Tier": c.get("triage_tier", "Customer Service Review"),
                "Contact Status": c["contact_status"]
            })
        df = pd.DataFrame(table_rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)
