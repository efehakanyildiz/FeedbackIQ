"""
FeedbackIQ — AI-Powered Patient Feedback Quality & Follow-up System
Main application entry point with 3-tier operational triage.
"""

import os
import streamlit as st
from dotenv import load_dotenv

# Initialize environment
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="FeedbackIQ — Patient Feedback Quality & Triage System",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom enterprise theme (no emojis)
from feedbackiq.utils.helpers import apply_enterprise_theme
apply_enterprise_theme()

# Ensure database is initialized and seeded
from feedbackiq.database.seed import seed_database
seed_database(force=False)

# Import page modules
from feedbackiq.pages.dashboard import render_dashboard_page
from feedbackiq.pages.new_feedback import render_new_feedback_page
from feedbackiq.pages.ai_call_queue import render_ai_call_queue_page
from feedbackiq.pages.followup_queue import render_followup_queue_page
from feedbackiq.pages.case_details import render_case_details_page
from feedbackiq.pages.analytics import render_analytics_page
from feedbackiq.pages.about import render_about_page

# Navigation configuration
PAGES = [
    "Overview",
    "Intake & Analysis",
    "AI Voice Queue",
    "Customer Service Queue",
    "Case Details",
    "Analytics",
    "Architecture"
]

if "current_page" not in st.session_state:
    st.session_state["current_page"] = "Overview"

# ----------------- SIDEBAR -----------------
with st.sidebar:
    st.markdown("""
    <div style="padding: 12px 0 16px 0; border-bottom: 1px solid #e2e8f0; margin-bottom: 16px;">
        <div style="font-size:1.15rem; font-weight:800; color:#0f172a; letter-spacing:-0.03em;">FeedbackIQ</div>
        <div style="font-size:0.7rem; color:#64748b; font-weight:700; text-transform:uppercase; letter-spacing:0.06em; margin-top:2px;">
            Patient Experience Quality Firewall
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 3-Tier Legend Pill
    st.markdown("""
    <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:6px; padding:10px; margin-bottom:16px;">
        <div style="font-size:0.7rem; color:#64748b; font-weight:700; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:6px;">
            Triage Architecture
        </div>
        <div style="display:flex; flex-direction:column; gap:4px; font-size:0.72rem; font-weight:600;">
            <span style="color:#047857;">Tier 1: Approved (Sufficient Data)</span>
            <span style="color:#4338ca;">Tier 2: AI Voice Bot Call (Minor Gap)</span>
            <span style="color:#b91c1c;">Tier 3: CSR Review (Major Gaps)</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Navigation Menu without emojis
    selected_page = st.radio(
        "Navigation",
        PAGES,
        index=PAGES.index(st.session_state["current_page"]) if st.session_state["current_page"] in PAGES else 0,
        label_visibility="collapsed"
    )

    if selected_page != st.session_state["current_page"]:
        st.session_state["current_page"] = selected_page
        st.rerun()

    st.markdown("<hr style='margin:20px 0; border:none; border-top:1px solid #e2e8f0;' />", unsafe_allow_html=True)

    # Engine Status
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    demo_mode = os.environ.get("DEMO_MODE", "true").lower() in ["true", "1", "yes"]

    if api_key and api_key != "your_gemini_api_key_here" and not demo_mode:
        st.markdown("""
        <div style="font-size:0.75rem; color:#047857; font-weight:700; text-transform:uppercase; letter-spacing:0.04em;">
            [Active] Gemini Flash Free Tier
        </div>
        <div style="font-size:0.7rem; color:#64748b; margin-top:2px;">Connected & Verified &bull; $0 Cost</div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="font-size:0.75rem; color:#d97706; font-weight:700; text-transform:uppercase; letter-spacing:0.04em;">
            [Active] Offline Demo Mode
        </div>
        <div style="font-size:0.7rem; color:#64748b; margin-top:2px;">Deterministic &bull; Zero API Dependency</div>
        """, unsafe_allow_html=True)

    # Configuration Expander
    with st.expander("Engine Configuration", expanded=False):
        new_key = st.text_input(
            "API Key",
            value=api_key if api_key != "your_gemini_api_key_here" else "",
            type="password",
            placeholder="AQ... or AIzaSy..."
        )
        model_choice = st.selectbox(
            "Model Selection",
            ["gemini-3.7-flash", "gemini-3.5-flash", "gemini-2.0-flash"],
            index=0
        )
        toggle_demo = st.checkbox("Force Offline Demo Mode", value=demo_mode)
        if st.button("Save Settings", use_container_width=True):
            os.environ["GEMINI_API_KEY"] = new_key
            os.environ["GEMINI_MODEL"] = model_choice
            os.environ["DEMO_MODE"] = "true" if toggle_demo else "false"
            st.success("Configuration updated.")
            st.rerun()

    # Footer
    st.markdown("""
    <div style="font-size:0.72rem; color:#94a3b8; margin-top:24px; text-align:center;">
        FeedbackIQ POC &bull; 100% Free Architecture<br/>
        Hospital Quality Assurance
    </div>
    """, unsafe_allow_html=True)


# ----------------- PAGE ROUTING -----------------
current = st.session_state["current_page"]

if current == "Overview":
    render_dashboard_page()
elif current == "Intake & Analysis":
    render_new_feedback_page()
elif current == "AI Voice Queue":
    render_ai_call_queue_page()
elif current == "Customer Service Queue":
    render_followup_queue_page()
elif current == "Case Details":
    render_case_details_page()
elif current == "Analytics":
    render_analytics_page()
elif current == "Architecture":
    render_about_page()
