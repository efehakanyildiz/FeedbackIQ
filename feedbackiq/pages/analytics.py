"""
Analytics Page: Aggregated insights into feedback data quality, intake channels,
follow-up resolution efficiency, and operational bottlenecks.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from feedbackiq.database.repository import get_analytics_data, get_kpis


def render_analytics_page():
    st.markdown('<div class="app-brand-badge">Operational Intelligence</div>', unsafe_allow_html=True)
    st.title("Feedback Quality Analytics")
    st.markdown(
        "<p style='color:#64748b; margin-top:-10px; margin-bottom: 25px;'>"
        "Auditing intake channels and measuring follow-up data enrichment across hospital operations."
        "</p>",
        unsafe_allow_html=True
    )

    kpis = get_kpis()
    analytics = get_analytics_data()

    if kpis["total_cases"] == 0:
        st.info("No feedback records available to analyze.")
        return

    # Top Metric Tiles
    total = kpis["total_cases"]
    followup_req = kpis["followup_required"]
    recovered = analytics["recovered_count"]
    pct_followup = int(round((followup_req / total) * 100)) if total else 0
    pct_recovered = int(round((recovered / max(1, followup_req + recovered)) * 100))

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Avg Quality Score</div>
            <div class="kpi-value" style="color:#2563eb;">{kpis['avg_score']}</div>
            <div class="kpi-subtext">Overall completeness</div>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Follow-up Rate</div>
            <div class="kpi-value" style="color:#dc2626;">{pct_followup}%</div>
            <div class="kpi-subtext">Arrived incomplete</div>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">CSR Recovery Rate</div>
            <div class="kpi-value" style="color:#059669;">{pct_recovered}%</div>
            <div class="kpi-subtext">Completed after outreach</div>
        </div>
        """, unsafe_allow_html=True)
    with m4:
        top_missing_name = analytics["top_missing"][0]["field_name"].replace("_", " ").title() if analytics["top_missing"] else "None"
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Primary Missing Field</div>
            <div class="kpi-value" style="color:#d97706; font-size:1.45rem;">{top_missing_name}</div>
            <div class="kpi-subtext">Highest friction item</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

    # Core Value Prop Insight Box (Section 20 Idea)
    st.markdown("""
    <div class="notice-box notice-info" style="border-left: 4px solid #6366f1; background:#f5f3ff;">
        <strong style="color:#4338ca; font-size:0.95rem;">💡 Strategic Channel Insight:</strong><br/>
        Feedback collected via <strong>QR Codes</strong> has a significantly lower average completeness score (~61/100) compared to <strong>Call Center</strong> records (~89/100).
        Because patients scanning QR codes on mobile devices submit terse descriptions without specifying hospital branches or clinic names, 
        <strong>FeedbackIQ intercepts these records</strong> before they pollute department workflows and equips CSRs with immediate follow-up prompts.
    </div>
    """, unsafe_allow_html=True)

    # Channel Quality Section
    st.markdown("""
    <div class="iq-card">
        <div class="iq-card-title">
            <span>📡</span> Feedback Collection Quality by Intake Channel
        </div>
    """, unsafe_allow_html=True)

    ch_data = analytics["channel_quality"]
    if ch_data:
        df_ch = pd.DataFrame(ch_data)
        fig_ch = px.bar(
            df_ch,
            x="source_channel",
            y="avg_score",
            color="avg_score",
            color_continuous_scale=["#f87171", "#fbbf24", "#34d399"],
            labels={"source_channel": "Intake Channel", "avg_score": "Avg Completeness Score (0-100)"},
            title="Channel Quality Benchmarking",
            text="avg_score"
        )
        fig_ch.update_layout(
            template="plotly_white",
            margin=dict(l=20, r=20, t=40, b=20),
            coloraxis_showscale=False,
            height=320
        )
        fig_ch.update_traces(textposition='outside')
        st.plotly_chart(fig_ch, use_container_width=True)

        # Small summary table
        st.dataframe(df_ch, use_container_width=True, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # Two column: Issue breakdown & Missing Fields
    c1, c2 = st.columns([1, 1])

    with c1:
        st.markdown("""
        <div class="iq-card">
            <div class="iq-card-title">
                <span>📂</span> Feedback Volume by Issue Category
            </div>
        """, unsafe_allow_html=True)

        issues = analytics["issue_breakdown"]
        if issues:
            df_issues = pd.DataFrame(issues)
            fig_iss = px.pie(
                df_issues,
                names="issue_type",
                values="count",
                hole=0.45,
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            fig_iss.update_layout(
                template="plotly_white",
                margin=dict(l=10, r=10, t=10, b=10),
                height=300
            )
            st.plotly_chart(fig_iss, use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown("""
        <div class="iq-card">
            <div class="iq-card-title">
                <span>📉</span> Missing Field Frequencies
            </div>
        """, unsafe_allow_html=True)

        top_m = analytics["top_missing"]
        if top_m:
            df_m = pd.DataFrame(top_m)
            df_m["field_label"] = df_m["field_name"].apply(lambda x: x.replace("_", " ").title())
            fig_m = px.bar(
                df_m,
                x="count",
                y="field_label",
                orientation="h",
                color_discrete_sequence=["#3b82f6"]
            )
            fig_m.update_layout(
                template="plotly_white",
                margin=dict(l=20, r=20, t=10, b=20),
                height=300,
                yaxis=dict(autorange="reversed")
            )
            st.plotly_chart(fig_m, use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)
