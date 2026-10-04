"""
About & Architecture Page: Explains system purpose, business problem, architectural design,
the 3-tier triage model, and the separation between Generative AI and deterministic rules.
"""

import streamlit as st


def render_about_page():
    st.markdown('<div class="app-brand-badge">System Architecture & Governance</div>', unsafe_allow_html=True)
    st.title("About FeedbackIQ & Architecture")
    st.markdown(
        "<p style='color:#64748b; margin-top:-8px; margin-bottom: 24px; font-size:0.95rem;'>"
        "An AI-powered data quality layer and 3-tier operational triage gate for healthcare patient experience management."
        "</p>",
        unsafe_allow_html=True
    )

    # Core Differentiation Callout
    st.markdown("""
    <div class="iq-card" style="border-left: 3px solid #2563eb;">
        <div class="iq-card-title" style="color:#1d4ed8; font-size:0.95rem;">
            Architectural Philosophy: Silent Intelligence vs. Conversational Chatbots
        </div>
        <p style="color:#334155; font-size:0.9rem; line-height:1.6;">
            Most implementations attempt to force an interactive chatbot onto frustrated patients. 
            <strong>FeedbackIQ takes an enterprise data-pipeline approach:</strong>
        </p>
        <ul style="color:#334155; font-size:0.88rem; line-height:1.6;">
            <li><strong>Frictionless Patient Ingestion:</strong> Patients submit feedback normally through web forms, QR codes, SMS, or surveys without conversational friction.</li>
            <li><strong>Silent Backend Intelligence:</strong> Google Gemini operates purely in the backend as a low-temperature information extraction engine.</li>
            <li><strong>Predictable Business Governance:</strong> Triage decisions and completeness scores are computed by deterministic Python rules—never by subjective LLM outputs.</li>
            <li><strong>100% Free & Open Architecture:</strong> Runs completely free via Google AI Studio's free tier, local SQLite storage, and a deterministic offline fallback mode.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    # 3-Tier Classification Model Explained
    st.markdown("""
    <div class="iq-card">
        <div class="iq-card-title">Three-Tier Triage Framework</div>
    """, unsafe_allow_html=True)

    t1, t2, t3 = st.columns(3)
    with t1:
        st.markdown("""
        <div style="background:#f0fdf4; border:1px solid #bbf7d0; border-radius:6px; padding:1rem; height:100%;">
            <div style="font-weight:700; color:#15803d; font-size:0.88rem; margin-bottom:6px;">TIER 1: APPROVED</div>
            <div style="font-size:0.8rem; color:#166534; line-height:1.5;">
                <strong>Condition:</strong> Feedback contains sufficient operational context (Hospital, Unit, Event details, Score &ge; 80).<br/><br/>
                <strong>Action:</strong> Immediately approved and routed directly to clinic managers and departmental ticketing.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with t2:
        st.markdown("""
        <div style="background:#eef2ff; border:1px solid #c7d2fe; border-radius:6px; padding:1rem; height:100%;">
            <div style="font-weight:700; color:#4338ca; font-size:0.88rem; margin-bottom:6px;">TIER 2: AI VOICE BOT CALL</div>
            <div style="font-size:0.8rem; color:#3730a3; line-height:1.5;">
                <strong>Condition:</strong> Feedback has minor operational gaps (e.g., missing exact time or clinic unit, Score 50–79).<br/><br/>
                <strong>Action:</strong> Dispatched to an automated AI Voice Agent to conduct a brief spoken telephone inquiry, saving staff hours.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with t3:
        st.markdown("""
        <div style="background:#fff1f2; border:1px solid #fecdd3; border-radius:6px; padding:1rem; height:100%;">
            <div style="font-weight:700; color:#9f1239; font-size:0.88rem; margin-bottom:6px;">TIER 3: CSR ESCALATION</div>
            <div style="font-size:0.8rem; color:#881337; line-height:1.5;">
                <strong>Condition:</strong> Multiple critical parameters are missing or dispute is complex (Score &lt; 50).<br/><br/>
                <strong>Action:</strong> Escalated to human Customer Service Representatives for comprehensive patient outreach.
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # Workflow Diagram
    st.markdown("""
    <div class="iq-card">
        <div class="iq-card-title">System Workflow Diagram</div>
    """, unsafe_allow_html=True)

    st.code("""
  Patient Feedback (Unstructured Text)
                 │
                 ▼
  Google Gemini API (Strict Extraction, Temp=0.1)
                 │
                 ▼
  Pydantic Validation (ExtractedFeedbackData)
                 │
                 ▼
  Deterministic Rules Engine (config/completeness_rules.py)
                 │
                 ▼
        3-Tier Triage Engine
                 │
       ┌─────────┼────────────────────────┐
       ▼         ▼                        ▼
[Tier 1]      [Tier 2]                 [Tier 3]
Sufficient    Minor Gap                Major Critical Gaps
       │         │                        │
       ▼         ▼                        ▼
  APPROVED    AI VOICE CALL            CUSTOMER SERVICE
Direct Route  Automated Call           Representative Outreach
to Clinic     Captures Missing Fields  Investigates & Re-evaluates
                 │                        │
                 └───────────┬────────────┘
                             │
                             ▼
                    Resolved / Ready
    """, language="text")

    st.markdown("</div>", unsafe_allow_html=True)
