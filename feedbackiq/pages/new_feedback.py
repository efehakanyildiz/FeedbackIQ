"""
New Feedback Page: Form to enter or select example feedback, run AI information extraction,
execute deterministic completeness rules, and display the quality evaluation.
"""

import streamlit as st
from feedbackiq.models.schemas import (
    SourceChannel,
    CompletenessStatus,
)
from feedbackiq.services.gemini_service import extract_feedback_info
from feedbackiq.services.completeness_service import evaluate_completeness
from feedbackiq.database.repository import save_case
from feedbackiq.utils.helpers import render_status_pill, render_priority_pill


SAMPLE_EXAMPLES = {
    "Example 1 (Incomplete Delay Complaint)": {
        "text": "I waited for almost an hour yesterday. Nobody informed us about the delay and I was very disappointed.",
        "channel": SourceChannel.WEBSITE.value,
        "hospital": "",
        "date": ""
    },
    "Example 2 (Complete Specialist Complaint)": {
        "text": "I visited Medicana Example Hospital cardiology department on October 3 around 14:00. Registration took almost 45 minutes even though I had an appointment.",
        "channel": SourceChannel.WEBSITE.value,
        "hospital": "Medicana Example Hospital",
        "date": "October 3"
    },
    "Example 3 (Commendation / Appreciation)": {
        "text": "The nurse in the oncology ward was extremely helpful and explained every medication step very clearly.",
        "channel": SourceChannel.CALL_CENTER.value,
        "hospital": "Example Hospital",
        "date": ""
    },
    "Example 4 (Missing Billing Context)": {
        "text": "I was charged twice for the same service yesterday and need a refund immediately.",
        "channel": SourceChannel.EMAIL.value,
        "hospital": "",
        "date": "yesterday"
    }
}


def render_new_feedback_page():
    st.markdown('<div class="app-brand-badge">Intake & Quality Gate</div>', unsafe_allow_html=True)
    st.title("Analyze Patient Feedback")
    st.markdown(
        "<p style='color:#64748b; margin-top:-10px; margin-bottom: 20px;'>"
        "Enter raw patient feedback to extract operational variables and validate investigative completeness."
        "</p>",
        unsafe_allow_html=True
    )

    # Example Selector Buttons
    st.markdown("<p style='font-size:0.85rem; font-weight:600; color:#475569; margin-bottom:8px;'>Load Pre-configured Demo Scenarios:</p>", unsafe_allow_html=True)
    cols = st.columns(len(SAMPLE_EXAMPLES))
    for i, (name, data) in enumerate(SAMPLE_EXAMPLES.items()):
        with cols[i]:
            if st.button(name.split("(")[0].strip(), key=f"ex_btn_{i}", use_container_width=True):
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
        "Enter patient feedback",
        value=current_text,
        height=130,
        placeholder="e.g., I waited for a very long time yesterday and nobody explained the delay..."
    )

    st.markdown("<p style='font-size:0.85rem; font-weight:600; color:#475569; margin-top:10px;'>Optional Contextual Channels & Prior Hints:</p>", unsafe_allow_html=True)
    fcol1, fcol2, fcol3 = st.columns(3)
    with fcol1:
        channel_options = [c.value for c in SourceChannel]
        channel_index = channel_options.index(current_channel) if current_channel in channel_options else 0
        selected_channel = st.selectbox("Source Channel", channel_options, index=channel_index)
    with fcol2:
        hospital_hint = st.text_input("Known Hospital (if available)", value=current_hosp, placeholder="e.g. Example Hospital")
    with fcol3:
        date_hint = st.text_input("Known Date (if available)", value=current_date, placeholder="e.g. 2026-10-03 or yesterday")

    analyze_clicked = st.button("🔍 Analyze Feedback", type="primary", use_container_width=False)

    if analyze_clicked:
        if not feedback_text.strip():
            st.error("Please provide feedback text to analyze.")
            return

        with st.spinner("Extracting operational variables & running completeness rules..."):
            # Prepare context hint if provided in fields
            context_parts = []
            if hospital_hint.strip():
                context_parts.append(f"Hospital: {hospital_hint.strip()}")
            if date_hint.strip():
                context_parts.append(f"Incident Date: {date_hint.strip()}")
            context_str = ", ".join(context_parts) if context_parts else None

            # 1. Gemini information extraction
            extracted, is_live, warning = extract_feedback_info(feedback_text, context_hint=context_str)

            # 2. Rule-based completeness validation
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

    # Display Analysis Result
    if "last_analysis" in st.session_state:
        res_data = st.session_state["last_analysis"]
        result = res_data["result"]
        extracted = res_data["extracted"]
        case_id = res_data["case_id"]

        st.markdown("<hr style='margin: 25px 0 20px 0; border: none; border-top: 1px solid #e2e8f0;' />", unsafe_allow_html=True)

        if res_data["warning"]:
            st.markdown(f"""
            <div class="notice-box notice-warning">
                ℹ️ <strong>System Notification:</strong> {res_data['warning']}
            </div>
            """, unsafe_allow_html=True)

        # Main Quality Score Card
        score = result.completeness_score
        score_color = "#059669" if score >= 85 else "#d97706" if score >= 60 else "#dc2626"
        score_bg = "#ecfdf5" if score >= 85 else "#fffbeb" if score >= 60 else "#fef2f2"

        st.markdown(f"""
        <div class="iq-card" style="border-left: 5px solid {score_color};">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
                <div>
                    <div style="font-size:0.8rem; font-weight:600; text-transform:uppercase; color:#64748b; letter-spacing:0.04em;">
                        Feedback Quality Score &bull; Case {case_id}
                    </div>
                    <div style="display:flex; align-items:baseline; gap:12px; margin-top:4px;">
                        <span style="font-size:2.4rem; font-weight:800; color:{score_color};">{score}</span>
                        <span style="font-size:1.1rem; color:#94a3b8; font-weight:600;">/ 100</span>
                        {render_status_pill(result.status.value)}
                        {render_priority_pill(result.follow_up_priority.value)}
                    </div>
                </div>
                <div style="min-width:240px; flex:1; max-width:380px;">
                    <div style="font-size:0.8rem; color:#64748b; margin-bottom:5px; text-align:right;">
                        Completeness Threshold: <strong>85+</strong> Complete
                    </div>
                    <div style="background:#e2e8f0; border-radius:6px; height:12px; overflow:hidden;">
                        <div style="background:{score_color}; width:{score}%; height:100%; transition: width 0.4s ease;"></div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 4 Metadata Chips
        mcol1, mcol2, mcol3, mcol4 = st.columns(4)
        with mcol1:
            st.markdown(f"""
            <div class="iq-card" style="padding:1rem;">
                <div class="kpi-label">Feedback Type</div>
                <div style="font-weight:600; font-size:1.05rem; color:#1e293b;">{extracted.feedback_type.value.title()}</div>
            </div>
            """, unsafe_allow_html=True)
        with mcol2:
            st.markdown(f"""
            <div class="iq-card" style="padding:1rem;">
                <div class="kpi-label">Issue Category</div>
                <div style="font-weight:600; font-size:1.05rem; color:#1e293b;">{extracted.issue_type.value}</div>
            </div>
            """, unsafe_allow_html=True)
        with mcol3:
            st.markdown(f"""
            <div class="iq-card" style="padding:1rem;">
                <div class="kpi-label">Sentiment</div>
                <div style="font-weight:600; font-size:1.05rem; color:#1e293b;">{extracted.sentiment.value.title()}</div>
            </div>
            """, unsafe_allow_html=True)
        with mcol4:
            conf_pct = int(extracted.extraction_confidence * 100)
            st.markdown(f"""
            <div class="iq-card" style="padding:1rem;">
                <div class="kpi-label">AI Extraction Confidence</div>
                <div style="font-weight:600; font-size:1.05rem; color:#2563eb;">{conf_pct}%</div>
            </div>
            """, unsafe_allow_html=True)

        # 2 Column: Detected vs Missing Information
        dcol1, dcol2 = st.columns([1, 1])

        with dcol1:
            st.markdown("""
            <div class="iq-card">
                <div class="iq-card-title">
                    <span>✅</span> Information Detected
                </div>
            """, unsafe_allow_html=True)

            detected_fields = [
                ("Hospital", extracted.hospital),
                ("Department", extracted.department),
                ("Incident Date", extracted.incident_date),
                ("Approximate Time", extracted.approximate_time),
                ("Service / Procedure", extracted.service_type),
                ("Staff Role / Name", f"{extracted.staff_role or ''} {extracted.staff_name or ''}".strip() or None),
                ("Billing Context", extracted.billing_context),
                ("Event Description", extracted.description_of_event)
            ]

            for label, val in detected_fields:
                val_display = val if val else "<span style='color:#94a3b8; font-style:italic;'>Not detected</span>"
                st.markdown(f"""
                <div style="display:flex; justify-content:space-between; padding:6px 0; border-bottom:1px solid #f8fafc; font-size:0.86rem;">
                    <span style="font-weight:500; color:#475569;">{label}</span>
                    <span style="font-weight:600; color:#0f172a; text-align:right; max-width:60%;">{val_display}</span>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

        with dcol2:
            st.markdown("""
            <div class="iq-card">
                <div class="iq-card-title">
                    <span>⚠️</span> Missing Information
                </div>
            """, unsafe_allow_html=True)

            if result.missing_field_items:
                for item in result.missing_field_items:
                    crit_badge = "<span style='background:#fee2e2; color:#b91c1c; font-weight:700; font-size:0.7rem; padding:1px 6px; border-radius:4px; margin-left:6px;'>CRITICAL</span>" if item.is_critical else "<span style='background:#f1f5f9; color:#64748b; font-size:0.7rem; padding:1px 6px; border-radius:4px; margin-left:6px;'>CONTEXTUAL</span>"
                    st.markdown(f"""
                    <div style="padding:8px 0; border-bottom:1px solid #f8fafc; font-size:0.86rem;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-weight:600; color:#334155;">{item.display_name} {crit_badge}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="color:#059669; font-weight:500; font-size:0.9rem; padding:10px 0;">
                    No operational fields are missing. Record has sufficient context.
                </div>
                """, unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

        # Why Follow-up is Needed Explanation
        st.markdown(f"""
        <div class="notice-box notice-info">
            <strong>📋 Why Follow-up Is Needed:</strong><br/>
            {result.why_needed_explanation}
        </div>
        """, unsafe_allow_html=True)

        # Suggested Questions Card
        if result.missing_field_items:
            st.markdown("""
            <div class="iq-card">
                <div class="iq-card-title">
                    <span>💬</span> Suggested Follow-up Questions (For Customer Service)
                </div>
            """, unsafe_allow_html=True)

            for i, item in enumerate(result.missing_field_items, 1):
                st.markdown(f"""
                <div style="margin-bottom:8px; font-size:0.88rem;">
                    <span style="color:#2563eb; font-weight:700;">Q{i}:</span>
                    <span style="font-weight:500; color:#1e293b;">"{item.suggested_question}"</span>
                    <span style="color:#64748b; font-size:0.78rem;">({item.display_name})</span>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

        # Next Step CTA Button
        if result.status == CompletenessStatus.FOLLOW_UP_REQUIRED:
            if st.button("➡️ Proceed to Customer Service Follow-up Queue", type="primary"):
                st.session_state["selected_case_id"] = case_id
                st.session_state["current_page"] = "Follow-up Queue"
                st.rerun()
        else:
            st.success("Case successfully evaluated. Ready for standard feedback workflow.")
