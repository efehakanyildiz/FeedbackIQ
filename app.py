"""
FeedbackIQ — AI-Powered Patient Feedback Quality & Follow-up System
Main application entry point.
"""

import os
import streamlit as st
from dotenv import load_dotenv

# Initialize environment
load_dotenv()

# Page configuration - Must be first Streamlit command
st.set_page_config(
    page_title="FeedbackIQ — Patient Feedback Quality & Follow-up System",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom enterprise theme
from feedbackiq.utils.helpers import apply_enterprise_theme
apply_enterprise_theme()

# Ensure database is initialized and seeded
from feedbackiq.database.seed import seed_database
seed_database(force=False)

# Import page modules
from feedbackiq.pages.dashboard import render_dashboard_page
from feedbackiq.pages.new_feedback import render_new_feedback_page
from feedbackiq.pages.followup_queue import render_followup_queue_page
from feedbackiq.pages.case_details import render_case_details_page
from feedbackiq.pages.analytics import render_analytics_page
from feedbackiq.pages.about import render_about_page

# Session state initialization for navigation
PAGES = [
    "Dashboard",
    "New Feedback",
    "Follow-up Queue",
    "Case Details",
    "Analytics",
    "About / Architecture"
]

if "current_page" not in st.session_state:
    st.session_state["current_page"] = "Dashboard"

# ----------------- SIDEBAR -----------------
with st.sidebar:
    st.markdown("""
    <div style="padding: 10px 0 15px 0;">
        <div style="display:flex; align-items:center; gap:8px;">
            <span style="font-size:1.6rem;">🏥</span>
            <div>
                <div style="font-size:1.25rem; font-weight:800; color:#0f172a; letter-spacing:-0.02em;">FeedbackIQ</div>
                <div style="font-size:0.75rem; color:#64748b; font-weight:600; text-transform:uppercase;">Quality & Triage Engine</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Role Context Badge
    st.markdown("""
    <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:8px; padding:10px; margin-bottom:15px;">
        <div style="font-size:0.72rem; color:#64748b; font-weight:600; text-transform:uppercase;">Operational Role Simulation</div>
        <div style="display:flex; gap:6px; margin-top:5px;">
            <span style="background:#eff6ff; color:#1d4ed8; font-size:0.75rem; font-weight:600; padding:2px 8px; border-radius:4px;">Analyst</span>
            <span style="background:#f0fdf4; color:#15803d; font-size:0.75rem; font-weight:600; padding:2px 8px; border-radius:4px;">CSR Representative</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Navigation Menu
    nav_icons = {
        "Dashboard": "📊",
        "New Feedback": "📝",
        "Follow-up Queue": "📥",
        "Case Details": "🔍",
        "Analytics": "📈",
        "About / Architecture": "ℹ️"
    }

    selected_page = st.radio(
        "Navigation",
        PAGES,
        index=PAGES.index(st.session_state["current_page"]) if st.session_state["current_page"] in PAGES else 0,
        format_func=lambda p: f"{nav_icons.get(p, '•')}  {p}",
        label_visibility="collapsed"
    )

    if selected_page != st.session_state["current_page"]:
        st.session_state["current_page"] = selected_page
        st.rerun()

    st.markdown("<hr style='margin:20px 0; border:none; border-top:1px solid #e2e8f0;' />", unsafe_allow_html=True)

    # Gemini Engine Status Indicator
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    demo_mode = os.environ.get("DEMO_MODE", "true").lower() in ["true", "1", "yes"]

    if api_key and api_key != "your_gemini_api_key_here":
        st.markdown("""
        <div style="display:flex; align-items:center; gap:6px; font-size:0.8rem; color:#059669; font-weight:600;">
            <span style="height:8px; width:8px; background:#10b981; border-radius:50%; display:inline-block;"></span>
            Gemini Flash Engine Active
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="display:flex; align-items:center; gap:6px; font-size:0.8rem; color:#d97706; font-weight:600;">
            <span style="height:8px; width:8px; background:#f59e0b; border-radius:50%; display:inline-block;"></span>
            Demo Mode Active (Zero-Quota Safe)
        </div>
        """, unsafe_allow_html=True)

    # Optional Live Key Configuration
    with st.expander("⚙️ Engine Configuration", expanded=False):
        new_key = st.text_input(
            "Gemini API Key",
            value=api_key if api_key != "your_gemini_api_key_here" else "",
            type="password",
            placeholder="AIzaSy..."
        )
        model_choice = st.selectbox(
            "Model Name",
            ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"],
            index=0
        )
        if st.button("Save API Configuration"):
            os.environ["GEMINI_API_KEY"] = new_key
            os.environ["GEMINI_MODEL"] = model_choice
            st.success("Config updated!")
            st.rerun()

    # Footer note
    st.markdown("""
    <div style="font-size:0.75rem; color:#94a3b8; margin-top:20px; text-align:center;">
        FeedbackIQ v1.0.0 &bull; Enterprise POC<br/>
        Hospital Quality Assurance Layer
    </div>
    """, unsafe_allow_html=True)


# ----------------- PAGE ROUTING -----------------
current = st.session_state["current_page"]

if current == "Dashboard":
    render_dashboard_page()
elif current == "New Feedback":
    render_new_feedback_page()
elif current == "Follow-up Queue":
    render_followup_queue_page()
elif current == "Case Details":
    render_case_details_page()
elif current == "Analytics":
    render_analytics_page()
elif current == "About / Architecture":
    render_about_page()
