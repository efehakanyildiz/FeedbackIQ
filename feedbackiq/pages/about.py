"""
About & Architecture Page: Explains system purpose, business problem, architectural design,
why this is NOT a chatbot, and the separation between Generative AI and deterministic rules.
"""

import streamlit as st


def render_about_page():
    st.markdown('<div class="app-brand-badge">Enterprise System Architecture</div>', unsafe_allow_html=True)
    st.title("About FeedbackIQ & Architecture")
    st.markdown(
        "<p style='color:#64748b; margin-top:-10px; margin-bottom: 25px;'>"
        "An AI-powered data quality layer and triage gate for healthcare patient experience operations."
        "</p>",
        unsafe_allow_html=True
    )

    # Core Differentiation Callout: Why NOT a Chatbot
    st.markdown("""
    <div class="iq-card" style="border-left: 5px solid #2563eb;">
        <div class="iq-card-title" style="color:#1d4ed8; font-size:1.05rem;">
            <span>🛡️</span> Fundamental Design Principle: Why This Is NOT a Chatbot
        </div>
        <p style="color:#334155; font-size:0.92rem; line-height:1.6;">
            Most AI implementations attempt to place an interactive chatbot in front of frustrated patients. 
            <strong>FeedbackIQ takes the opposite architectural approach:</strong>
        </p>
        <ul style="color:#334155; font-size:0.9rem; line-height:1.6;">
            <li><strong>Zero Conversational Noise:</strong> The patient submits feedback normally through any existing channel (web forms, SMS, QR codes, surveys, or call centers).</li>
            <li><strong>Silent Backend Intelligence:</strong> Google Gemini operates purely in the backend as a high-precision, low-temperature information extraction engine.</li>
            <li><strong>Deterministic Quality Enforcement:</strong> Gemini is <em>never</em> allowed to decide if a case is complete or calculate scores. Business rules are strictly executed in predictable, testable Python code.</li>
            <li><strong>Human-in-the-Loop Triage:</strong> Incomplete records are diverted to a dedicated Customer Service Queue, equipping representatives with exact targeted questions before unit escalation.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    # Business Problem & Solution
    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown("""
        <div class="iq-card">
            <div class="iq-card-title">
                <span>⚠️</span> The Operational Problem
            </div>
            <p style="font-size:0.88rem; color:#475569; line-height:1.55;">
                Patients often submit vague complaints such as: <em>"I waited for an hour yesterday and nobody helped me."</em><br/><br/>
                When such incomplete records enter hospital ticketing systems, departmental managers:
            </p>
            <ul style="font-size:0.85rem; color:#64748b; line-height:1.5;">
                <li>Cannot identify which branch, clinic, or counter is responsible.</li>
                <li>Route tickets back and forth between units, delaying investigation.</li>
                <li>Reach out to patients blindly without knowing what specific facts to ask.</li>
                <li>Create noisy, low-quality compliance logs.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown("""
        <div class="iq-card">
            <div class="iq-card-title">
                <span>🎯</span> The FeedbackIQ Solution
            </div>
            <p style="font-size:0.88rem; color:#475569; line-height:1.55;">
                FeedbackIQ acts as an <strong>intelligent data quality firewall</strong> positioned before the hospital's operational case management workflow:
            </p>
            <ul style="font-size:0.85rem; color:#64748b; line-height:1.5;">
                <li>Extracts structured fields (Hospital, Unit, Date, Time, Staff, Billing Context).</li>
                <li>Applies issue-specific completeness rules and computes a 0–100 quality score.</li>
                <li>Generates deterministic questions for only the missing critical variables.</li>
                <li>Enables CSRs to collect missing data, re-evaluate, and dispatch cleanly.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    # Workflow Diagram
    st.markdown("""
    <div class="iq-card">
        <div class="iq-card-title">
            <span>🔄</span> End-to-End System Workflow
        </div>
    """, unsafe_allow_html=True)

    st.code("""
  Patient Feedback (Unstructured Text)
                 │
                 ▼
  Google Gemini API (Strict Extraction, Low Temp)
                 │
                 ▼
  Validated JSON (Pydantic Schema Validation)
                 │
                 ▼
  Python Rules Engine (Deterministic Weights & Critical Fields)
                 │
                 ▼
         Completeness Score (0-100)
                 │
        ┌────────┴───────────────────────────┐
        ▼                                    ▼
[Score >= 85 & No Critical Gaps]    [Critical Fields Missing]
        │                                    │
        ▼                                    ▼
 Ready for Existing Workflow         Customer Service Queue
 (Escalate to Clinic/Unit)                   │
                                             ▼
                                     CSR Contacts Patient
                                             │
                                             ▼
                                     Context Re-evaluation
                                             │
                                             ▼
                                     Ready for Workflow
    """, language="text")

    st.markdown("</div>", unsafe_allow_html=True)

    # Technology Stack & Data Privacy
    tc1, tc2 = st.columns([1, 1])
    with tc1:
        st.markdown("""
        <div class="iq-card">
            <div class="iq-card-title">
                <span>⚙️</span> Enterprise Technology Stack
            </div>
            <ul style="font-size:0.85rem; color:#334155; line-height:1.6;">
                <li><strong>Backend Engine:</strong> Python 3.9+ & SQLite with WAL mode.</li>
                <li><strong>AI Extraction:</strong> Google Gemini 2.0/1.5 Flash via official Google GenAI SDK.</li>
                <li><strong>Schema Validation:</strong> Pydantic v2 (Strict typing, no loose coercion).</li>
                <li><strong>Rules Engine:</strong> Pure deterministic Python (Zero LLM drift).</li>
                <li><strong>User Interface:</strong> Streamlit with custom enterprise SaaS theme.</li>
                <li><strong>Reliability Fallback:</strong> Deterministic Demo Mode for zero-quota environments.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with tc2:
        st.markdown("""
        <div class="iq-card">
            <div class="iq-card-title">
                <span>🔒</span> Privacy & Compliance Guardrails
            </div>
            <ul style="font-size:0.85rem; color:#334155; line-height:1.6;">
                <li><strong>Non-Clinical Scope:</strong> FeedbackIQ evaluates purely administrative and operational variables. It does NOT make clinical diagnoses or medical decisions.</li>
                <li><strong>Synthetic Demo Data:</strong> No real patient health records (PHI), Turkish National IDs (TCKN), or private phone numbers are stored.</li>
                <li><strong>No Model Training:</strong> Prompt data is not retained for model training.</li>
                <li><strong>Auditable History:</strong> Every re-evaluation and CSR contact attempt is stamped and logged in SQLite.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
