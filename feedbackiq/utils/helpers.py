"""
UI helper utilities and enterprise CSS injection for FeedbackIQ.
Provides a clean, modern B2B SaaS appearance.
"""

import streamlit as st


def apply_enterprise_theme():
    """Inject polished enterprise SaaS CSS styles."""
    st.markdown("""
    <style>
    /* Global Font & Spacing */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        color: #1e293b;
    }

    /* Main Container Padding */
    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 2.5rem;
        max-width: 1200px;
    }

    /* Top App Header Banner */
    .app-brand-badge {
        display: inline-flex;
        align-items: center;
        background: #f1f5f9;
        border: 1px solid #cbd5e1;
        border-radius: 6px;
        padding: 4px 10px;
        font-size: 0.75rem;
        font-weight: 600;
        color: #475569;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }

    /* Clean Card Container */
    .iq-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 1.25rem;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.04), 0 1px 2px -1px rgba(0, 0, 0, 0.02);
    }

    .iq-card-title {
        font-size: 0.95rem;
        font-weight: 600;
        color: #0f172a;
        margin-bottom: 0.75rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    /* KPI Metric Cards */
    .kpi-container {
        display: flex;
        gap: 1rem;
        margin-bottom: 1.5rem;
        flex-wrap: wrap;
    }

    .kpi-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1rem 1.25rem;
        flex: 1;
        min-width: 180px;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
    }

    .kpi-label {
        font-size: 0.78rem;
        font-weight: 500;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.03em;
        margin-bottom: 0.35rem;
    }

    .kpi-value {
        font-size: 1.85rem;
        font-weight: 700;
        color: #0f172a;
        line-height: 1.2;
    }

    .kpi-subtext {
        font-size: 0.75rem;
        color: #94a3b8;
        margin-top: 0.25rem;
    }

    /* Status Badges */
    .status-badge {
        display: inline-flex;
        align-items: center;
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        line-height: 1;
    }

    .status-complete {
        background-color: #ecfdf5;
        color: #065f46;
        border: 1px solid #a7f3d0;
    }

    .status-ready {
        background-color: #eff6ff;
        color: #1e40af;
        border: 1px solid #bfdbfe;
    }

    .status-review {
        background-color: #fffbeb;
        color: #92400e;
        border: 1px solid #fde68a;
    }

    .status-followup {
        background-color: #fef2f2;
        color: #991b1b;
        border: 1px solid #fecaca;
    }

    .priority-high {
        background-color: #fee2e2;
        color: #b91c1c;
        border: 1px solid #fca5a5;
    }

    .priority-medium {
        background-color: #fef3c7;
        color: #b45309;
        border: 1px solid #fcd34d;
    }

    .priority-low {
        background-color: #f1f5f9;
        color: #475569;
        border: 1px solid #cbd5e1;
    }

    /* Alert / Notice Boxes */
    .notice-box {
        border-radius: 8px;
        padding: 0.9rem 1.1rem;
        font-size: 0.85rem;
        line-height: 1.45;
        margin-bottom: 1rem;
    }

    .notice-info {
        background: #f8fafc;
        border-left: 4px solid #3b82f6;
        color: #334155;
    }

    .notice-warning {
        background: #fffbeb;
        border-left: 4px solid #f59e0b;
        color: #78350f;
    }

    .notice-success {
        background: #f0fdf4;
        border-left: 4px solid #10b981;
        color: #064e3b;
    }

    /* Subtle Table Header */
    thead tr th {
        background-color: #f8fafc !important;
        color: #475569 !important;
        font-weight: 600 !important;
        font-size: 0.8rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.04em !important;
    }

    /* Clean Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #f8fafc;
        border-right: 1px solid #e2e8f0;
    }

    /* Hide Streamlit default top decoration line */
    header[data-testid="stHeader"] {
        background: transparent;
    }
    </style>
    """, unsafe_allow_html=True)


def render_status_pill(status: str) -> str:
    """Return HTML string for color-coded status badge."""
    s = str(status).strip()
    if s in ["Complete", "Completed"]:
        cls = "status-complete"
    elif s in ["Ready for Workflow", "Ready for Existing Feedback Workflow"]:
        cls = "status-ready"
    elif s in ["Needs Review"]:
        cls = "status-review"
    else:
        cls = "status-followup"
    return f'<span class="status-badge {cls}">{s}</span>'


def render_priority_pill(priority: str) -> str:
    """Return HTML string for follow-up priority badge."""
    p = str(priority).strip().lower()
    if p == "high":
        cls = "priority-high"
    elif p == "medium":
        cls = "priority-medium"
    else:
        cls = "priority-low"
    return f'<span class="status-badge {cls}">{priority.title()} Priority</span>'


def render_score_badge(score: int) -> str:
    """Return colored score indicator."""
    if score >= 85:
        color = "#059669"
        bg = "#ecfdf5"
    elif score >= 60:
        color = "#d97706"
        bg = "#fffbeb"
    else:
        color = "#dc2626"
        bg = "#fef2f2"
    return f'<span style="background:{bg}; color:{color}; font-weight:700; padding:2px 8px; border-radius:6px; font-size:0.85rem;">{score}/100</span>'
