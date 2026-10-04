"""
New Feedback Page: Form to enter or select example feedback, run AI extraction,
execute deterministic 3-tier triage rules, and display the quality evaluation.
"""

import streamlit as st
from feedbackiq.models.schemas import SourceChannel, TriageTier
from feedbackiq.services.gemini_service import extract_feedback_info
from feedbackiq.services.completeness_service import evaluate_completeness
from feedbackiq.database.repository import save_case
from feedbackiq.utils.helpers import render_tier_badge, render_score_badge, render_priority_badge


SAMPLE_SCENARIOS = {
    "Scenario A: Sufficient Data (Tier 1 Approved)": {
        "text": "I visited Merkez Sağlık Hastanesi cardiology department on October 3 around 14:00. Registration took almost 45 minutes even though I had an appointment.",
        "channel": SourceChannel.WEBSITE.value,
        "hospital": "Merkez Sağlık Hastanesi",
        "date": "October 3"
    },
    "Scenario B: Minor Gap (Tier 2 AI Voice Call)": {
        "text": "I visited Example Hospital yesterday and had to wait for almost an hour in the waiting room with no explanation.",
        "channel": SourceChannel.QR_CODE.value,
        "hospital": "Example Hospital",
        "date": "yesterday"
    },
    "Scenario C: Major Gaps (Tier 3 CSR Review)": {
        "text": "I was charged twice for the same service yesterday and nobody answered my email. I am very dissatisfied.",
        "channel": SourceChannel.EMAIL.value,
        "hospital": "",
        "date": "yesterday"
    }
}


def render_new_feedback_page():
    st.markdown('<div class="app-brand-badge">Intake & Triage Classification</div>', unsafe_allow_html=True)
    st.title("Analyze Patient Feedback")
    st.markdown(
        "<p style='color:#64748b; margin-top:-8px; margin-bottom: 20px; font-size:0.95rem;'>"
        "Enter raw patient feedback to extract operational variables and determine automated triage routing."
        "</p>",
        unsafe_allow_html=True
    )

    # Clean scenario buttons
    st.markdown("<p style='font-size:0.8rem; font-weight:700; color:#475569; text-transform:uppercase; letter-spacing:0.04em; margin-bottom:8px;'>Load Test Scenarios:</p>", unsafe_allow_html=True)
    cols = st.columns(len(SAMPLE_SCENARIOS))
    for i, (name, data) in enumerate(SAMPLE_SCENARIOS.items()):
        with cols[i]:
            short_title = name.split(":")[0].strip() + ": " + name.split("(")[1].replace(")", "")
            if st.button(short_title, key=f"scen_{i}", use_container_width=True):
                st.session_state["feedback_input"] = data["text"]
                st.session_state["channel_input"] = data["channel"]
                st.session_state["hosp_hint"] = data["hospital"]
                st.session_state["date_hint"] = data["date"]
                st.rerun()

    # Form inputs
    current_text = st.session_state.get("feedback_input", "")
    current_channel = st.session_state.get("channel_input", SourceChannel.WEBSITE.value)
    current_hosp = st.session_state.get("hosp_hint", "")
    current_date = st.session_state.get("date_hint", "")

    feedback_text = st.text_area(
        "Patient Feedback Text",
        value=current_text,
        height=120,
        placeholder="Enter unstructured patient feedback narrative..."
    )

    st.markdown("<p style='font-size:0.8rem; font-weight:700; color:#475569; text-transform:uppercase; letter-spacing:0.04em; margin-top:10px;'>Intake Channel & Operational Context:</p>", unsafe_allow_html=True)
    fcol1, fcol2, fcol3 = st.columns(3)
    with fcol1:
        channel_options = [c.value for c in SourceChannel]
        channel_index = channel_options.index(current_channel) if current_channel in channel_options else 0
        selected_channel = st.selectbox("Source Channel", channel_options, index=channel_index)
    with fcol2:
        hospital_hint = st.text_input("Known Hospital (if available)", value=current_hosp, placeholder="e.g. Example Hospital")
    with fcol3:
        date_hint = st.text_input("Known Date (if available)", value=current_date, placeholder="e.g. 2026-10-03 or yesterday")

    analyze_clicked = st.button("Run Operational Analysis", type="primary", use_container_width=False)

    if analyze_clicked:
        if not feedback_text.strip():
            st.error("Feedback text cannot be empty.")
            return

        with st.spinner("Analyzing operational variables and calculating triage tier..."):
            context_parts = []
            if hospital_hint.strip():
                context_parts.append(f"Hospital: {hospital_hint.strip()}")
            if date_hint.strip():
                context_parts.append(f"Incident Date: {date_hint.strip()}")
            context_str = ", ".join(context_parts) if context_parts else None

            # 1. Extraction
            extracted, is_live, warning = extract_feedback_info(feedback_text, context_hint=context_str)

            # 2. Rule evaluation
            confirmed_inputs = {}
            if hospital_hint.strip():
                confirmed_inputs["hospital"] = hospital_hint.strip()
            if date_hint.strip():
                confirmed_inputs["incident_date"] = date_hint.strip()

            result = evaluate_completeness(extracted, confirmed_overrides=confirmed_inputs)

            # 3. Save to database
            case_dict = extracted.model_dump()
            case_dict["source_channel"] = selected_channel
            case_dict["original_feedback"] = feedback_text
            for k, v in confirmed_inputs.items():
                case_dict[k] = v

            case_id = save_case(case_dict, result)

            st.session_state["last_analysis"] = {
                "case_id": case_id,
                "extracted": extracted,
                "result": result,
                "is_live": is_live,
                "warning": warning,
                "channel": selected_channel
            }

    # Analysis Results Display
    if "last_analysis" in st.session_state:
        res_data = st.session_state["last_analysis"]
        result = res_data["result"]
        extracted = res_data["extracted"]
        case_id = res_data["case_id"]

        st.markdown("<hr style='margin: 25px 0 20px 0; border: none; border-top: 1px solid #e2e8f0;' />", unsafe_allow_html=True)

        # Triage Outcome Banner
        tier = result.triage_tier
        if tier == TriageTier.TIER_1_APPROVED:
            banner_class = "notice-success"
            tier_title = "Tier 1: Approved / Ready for Operational Dispatch"
            tier_instruction = "Sufficient operational data is present. This case requires no customer service outreach and is ready for department resolution."
        elif tier == TriageTier.TIER_2_AI_CALL:
            banner_class = "notice-info"
            tier_title = "Tier 2: AI Voice Bot Follow-up Scheduled"
            tier_instruction = "Minor operational gaps detected. This case is queued for an automated AI Voice Agent telephone call to confirm missing details."
        else:
            banner_class = "notice-urgent"
            tier_title = "Tier 3: Customer Service Review Escalation"
            tier_instruction = "Major critical variables are missing. This case has been escalated to a human Customer Service Representative for manual investigation."

        st.markdown(f"""
        <div class="notice-box {banner_class}">
            <div style="font-weight:700; font-size:0.95rem; margin-bottom:4px;">{tier_title}</div>
            <div>{tier_instruction}</div>
        </div>
        """, unsafe_allow_html=True)

        # Quality Score Card
        score = result.completeness_score
        st.markdown(f"""
        <div class="iq-card">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
                <div>
                    <div style="font-size:0.75rem; font-weight:700; text-transform:uppercase; color:#64748b; letter-spacing:0.06em;">
                        Evaluation Result &bull; Record {case_id}
                    </div>
                    <div style="display:flex; align-items:baseline; gap:12px; margin-top:5px;">
                        <span style="font-size:2.2rem; font-weight:800; color:#0f172a;">{score}</span>
                        <span style="font-size:1rem; color:#94a3b8; font-weight:600;">/ 100</span>
                        {render_tier_badge(result.triage_tier.value)}
                        {render_priority_badge(result.follow_up_priority.value)}
                    </div>
                </div>
                <div style="min-width:240px; flex:1; max-width:360px;">
                    <div style="display:flex; justify-content:space-between; font-size:0.75rem; color:#64748b; margin-bottom:5px;">
                        <span>Completeness Score</span>
                        <span>{score}%</span>
                    </div>
                    <div style="background:#e2e8f0; border-radius:3px; height:8px; overflow:hidden;">
                        <div style="background:#2563eb; width:{score}%; height:100%;"></div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Metadata cards
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(f"""
            <div class="iq-card" style="padding:0.9rem;">
                <div class="kpi-label">Feedback Category</div>
                <div style="font-weight:600; font-size:0.95rem; color:#1e293b;">{extracted.issue_type.value}</div>
            </div>
            """, unsafe_allow_html=True)
        with m2:
            st.markdown(f"""
            <div class="iq-card" style="padding:0.9rem;">
                <div class="kpi-label">Feedback Type</div>
                <div style="font-weight:600; font-size:0.95rem; color:#1e293b;">{extracted.feedback_type.value.title()}</div>
            </div>
            """, unsafe_allow_html=True)
        with m3:
            st.markdown(f"""
            <div class="iq-card" style="padding:0.9rem;">
                <div class="kpi-label">Sentiment</div>
                <div style="font-weight:600; font-size:0.95rem; color:#1e293b;">{extracted.sentiment.value.title()}</div>
            </div>
            """, unsafe_allow_html=True)
        with m4:
            conf_pct = int(extracted.extraction_confidence * 100)
            st.markdown(f"""
            <div class="iq-card" style="padding:0.9rem;">
                <div class="kpi-label">Extraction Confidence</div>
                <div style="font-weight:600; font-size:0.95rem; color:#2563eb;">{conf_pct}%</div>
            </div>
            """, unsafe_allow_html=True)

        # Detected vs Missing Columns
        d1, d2 = st.columns([1, 1])
        with d1:
            st.markdown("""
            <div class="iq-card">
                <div class="iq-card-title">Detected Operational Parameters</div>
            """, unsafe_allow_html=True)
            detected_items = [
                ("Hospital", extracted.hospital),
                ("Department", extracted.department),
                ("Incident Date", extracted.incident_date),
                ("Approximate Time", extracted.approximate_time),
                ("Service / Procedure", extracted.service_type),
                ("Staff Role / Name", f"{extracted.staff_role or ''} {extracted.staff_name or ''}".strip() or None),
                ("Billing Context", extracted.billing_context),
                ("Description", extracted.description_of_event)
            ]
            for label, val in detected_items:
                val_disp = val if val else "<span style='color:#94a3b8; font-style:italic;'>Not specified</span>"
                st.markdown(f"""
                <div style="display:flex; justify-content:space-between; padding:5px 0; border-bottom:1px solid #f8fafc; font-size:0.84rem;">
                    <span style="color:#64748b;">{label}</span>
                    <span style="font-weight:600; color:#0f172a; text-align:right; max-width:60%;">{val_disp}</span>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with d2:
            st.markdown("""
            <div class="iq-card">
                <div class="iq-card-title">Missing Information & Questions</div>
            """, unsafe_allow_html=True)
            if result.missing_field_items:
                for item in result.missing_field_items:
                    tag = "<span style='background:#fee2e2; color:#991b1b; font-size:0.68rem; font-weight:700; padding:1px 5px; border-radius:3px;'>CRITICAL</span>" if item.is_critical else "<span style='background:#f1f5f9; color:#475569; font-size:0.68rem; font-weight:600; padding:1px 5px; border-radius:3px;'>MINOR</span>"
                    st.markdown(f"""
                    <div style="margin-bottom:8px; padding-bottom:6px; border-bottom:1px solid #f8fafc; font-size:0.84rem;">
                        <div><strong style="color:#334155;">{item.display_name}</strong> {tag}</div>
                        <div style="color:#4338ca; font-size:0.8rem; margin-top:2px;">Prompt: "{item.suggested_question}"</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("<div style='color:#047857; font-weight:600; font-size:0.86rem; padding:10px 0;'>All required operational variables detected.</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # Queue routing action
        if tier == TriageTier.TIER_2_AI_CALL:
            if st.button("Open in AI Voice Call Queue", type="primary"):
                st.session_state["selected_case_id"] = case_id
                st.session_state["current_page"] = "AI Voice Queue"
                st.rerun()
        elif tier == TriageTier.TIER_3_CSR_ESCALATION:
            if st.button("Open in Customer Service Queue", type="primary"):
                st.session_state["selected_case_id"] = case_id
                st.session_state["current_page"] = "Customer Service Queue"
                st.rerun()
