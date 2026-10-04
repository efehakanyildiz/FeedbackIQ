"""
UI helper utilities and enterprise CSS styling for FeedbackIQ.
Implements a clean, modern, typography-driven B2B interface without casual emojis.
"""

import streamlit as st


def apply_enterprise_theme():
    """Inject polished enterprise SaaS CSS styles without playful emojis."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        color: #0f172a;
        background-color: #f8fafc;
    }

    /* Container Spacing */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2.5rem;
        max-width: 1220px;
    }

    /* Header Brand Pill */
    .app-brand-badge {
        display: inline-flex;
        align-items: center;
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 4px;
        padding: 3px 9px;
        font-size: 0.72rem;
        font-weight: 700;
        color: #475569;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 0.4rem;
    }

    /* Modern Flat Card */
    .iq-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1.25rem 1.4rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
    }

    .iq-card-title {
        font-size: 0.92rem;
        font-weight: 600;
        color: #0f172a;
        letter-spacing: -0.01em;
        margin-bottom: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        font-size: 0.8rem;
        color: #64748b;
    }

    /* KPI Metric Cards */
    .kpi-container {
        display: flex;
        gap: 1rem;
        margin-bottom: 1.25rem;
        flex-wrap: wrap;
    }

    .kpi-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        flex: 1;
        min-width: 170px;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02);
    }

    .kpi-label {
        font-size: 0.72rem;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 0.35rem;
    }

    .kpi-value {
        font-size: 1.85rem;
        font-weight: 700;
        color: #0f172a;
        letter-spacing: -0.02em;
        line-height: 1.15;
    }

    .kpi-subtext {
        font-size: 0.74rem;
        color: #94a3b8;
        margin-top: 0.25rem;
    }

    /* Minimalist Pill Badges */
    .tier-badge {
        display: inline-flex;
        align-items: center;
        padding: 3px 9px;
        border-radius: 4px;
        font-size: 0.73rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        line-height: 1.2;
    }

    /* Tier 1: Approved */
    .tier-approved {
        background-color: #ecfdf5;
        color: #065f46;
        border: 1px solid #a7f3d0;
    }

    /* Tier 2: AI Voice Call */
    .tier-ai-call {
        background-color: #eef2ff;
        color: #4338ca;
        border: 1px solid #c7d2fe;
    }

    /* Tier 3: CSR Escalation */
    .tier-csr-escalation {
        background-color: #fff1f2;
        color: #9f1239;
        border: 1px solid #fecdd3;
    }

    .tier-resolved {
        background-color: #f0fdf4;
        color: #15803d;
        border: 1px solid #bbf7d0;
    }

    .priority-badge {
        display: inline-flex;
        align-items: center;
        padding: 2px 7px;
        border-radius: 4px;
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }

    .priority-high {
        background: #fee2e2;
        color: #991b1b;
    }

    .priority-medium {
        background: #fef3c7;
        color: #92400e;
    }

    .priority-low {
        background: #f1f5f9;
        color: #475569;
    }

    /* Notice Panels */
    .notice-box {
        border-radius: 6px;
        padding: 0.9rem 1.1rem;
        font-size: 0.86rem;
        line-height: 1.5;
        margin-bottom: 1rem;
    }

    .notice-info {
        background: #f8fafc;
        border-left: 3px solid #6366f1;
        color: #334155;
    }

    .notice-success {
        background: #f0fdf4;
        border-left: 3px solid #10b981;
        color: #064e3b;
    }

    .notice-warning {
        background: #fffbeb;
        border-left: 3px solid #f59e0b;
        color: #78350f;
    }

    .notice-urgent {
        background: #fff1f2;
        border-left: 3px solid #e11d48;
        color: #881337;
    }

    /* Clean Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }

    header[data-testid="stHeader"] {
        background: transparent;
    }

    /* Clean Streamlit form inputs */
    div[data-baseweb="select"] {
        border-radius: 6px;
    }

    button[kind="primary"] {
        border-radius: 6px !important;
        font-weight: 600 !important;
        letter-spacing: 0.02em !important;
    }
    </style>
    """, unsafe_allow_html=True)


def render_tier_badge(tier_or_status: str) -> str:
    """Return minimalist HTML pill badge for the 3 triage tiers."""
    s = str(tier_or_status).strip().lower()
    if "approved" in s or "complete" in s or "resolved" in s:
        cls = "tier-approved"
        label = "Tier 1 — Approved"
    elif "ai call" in s or "ai voice" in s:
        cls = "tier-ai-call"
        label = "Tier 2 — AI Voice Follow-up"
    else:
        cls = "tier-csr-escalation"
        label = "Tier 3 — Customer Service Review"
    return f'<span class="tier-badge {cls}">{label}</span>'


def render_score_badge(score: int) -> str:
    """Return clean minimalist score indicator."""
    if score >= 80:
        color = "#047857"
        bg = "#ecfdf5"
        border = "#a7f3d0"
    elif score >= 50:
        color = "#4338ca"
        bg = "#eef2ff"
        border = "#c7d2fe"
    else:
        color = "#b91c1c"
        bg = "#fff1f2"
        border = "#fecdd3"
    return f'<span style="background:{bg}; color:{color}; border:1px solid {border}; font-weight:700; padding:2px 8px; border-radius:4px; font-size:0.8rem; letter-spacing:0.02em;">{score}/100</span>'


def render_priority_badge(priority: str) -> str:
    """Return clean priority badge."""
    p = str(priority).strip().lower()
    if p == "high":
        cls = "priority-high"
    elif p == "medium":
        cls = "priority-medium"
    else:
        cls = "priority-low"
    return f'<span class="priority-badge {cls}">{priority.upper()} PRIORITY</span>'
