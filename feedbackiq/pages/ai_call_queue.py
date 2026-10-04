"""
AI Voice Follow-up Queue: Dedicated operational workspace for Tier 2 cases.
Handles automated telephone outreach for patient records missing minor operational parameters,
allowing interactive simulation of voice inquiries and instant case resolution.
"""

import streamlit as st
import pandas as pd
from feedbackiq.database.repository import get_cases, get_case, get_missing_fields_for_case
from feedbackiq.services.ai_call_service import simulate_ai_voice_call
from feedbackiq.utils.helpers import render_tier_badge, render_score_badge, render_priority_badge
from feedbackiq.models.schemas import TriageTier, ContactStatus


def render_ai_call_queue_page():
    st.markdown('<div class="app-brand-badge">Automated Telephony Dispatch</div>', unsafe_allow_html=True)
    st.title("AI Voice Follow-up Queue (Tier 2)")
    st.markdown(
        "<p style='color:#64748b; margin-top:-8px; margin-bottom: 24px; font-size:0.95rem;'>"
        "Records with minor operational gaps routed to autonomous AI voice agents to conduct telephone verification without human staff overhead."
        "</p>",
        unsafe_allow_html=True
    )

    # Fetch Tier 2 cases
    ai_cases = get_cases(tier_filter=TriageTier.TIER_2_AI_CALL.value, sort_by="score_asc")

    st.markdown(f"""
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
        <span style="font-weight:600; font-size:0.9rem; color:#334155;">
            {len(ai_cases)} Cases Queued for Automated Phone Outreach
        </span>
        <span style="font-size:0.78rem; color:#64748b;">
            Resolution Method: <strong>Interactive Spoken Telephone Inquiry</strong>
        </span>
    </div>
    """, unsafe_allow_html=True)

    if not ai_cases:
        st.success("No pending cases in the AI Voice Queue. All minor gaps have been verified.")
        return

    # Render each case in a modern card
    for case in ai_cases:
        case_id = case["case_id"]
        score = case["completeness_score"]
        priority = case["follow_up_priority"]
        preview = case["original_feedback"]
        if len(preview) > 130:
            preview = preview[:130] + "..."

        missing_fields = get_missing_fields_for_case(case_id)
        missing_names = [m["field_name"].replace("_", " ").title() for m in missing_fields]

        with st.container():
            st.markdown(f"""
            <div class="iq-card" style="margin-bottom: 12px; padding: 1.1rem 1.3rem;">
                <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:6px;">
                    <div>
                        <span style="font-size:1.05rem; font-weight:700; color:#0f172a; margin-right:8px;">{case_id}</span>
                        <span style="font-size:0.8rem; color:#64748b; margin-right:8px;">{case['created_at']}</span>
                        <span style="background:#f1f5f9; color:#475569; padding:2px 7px; border-radius:3px; font-size:0.72rem; font-weight:600;">
                            Channel: {case['source_channel']}
                        </span>
                    </div>
                    <div style="display:flex; align-items:center; gap:8px;">
                        {render_score_badge(score)}
                        {render_tier_badge(case.get('triage_tier', 'AI Call Scheduled'))}
                    </div>
                </div>
                <div style="font-size:0.88rem; color:#334155; margin-bottom:8px; font-style:italic; background:#f8fafc; padding:8px 12px; border-radius:4px; border-left:3px solid #cbd5e1;">
                    "{preview}"
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center; font-size:0.8rem; color:#64748b;">
                    <div>
                        <strong>Target Gaps:</strong> <span style="color:#4338ca; font-weight:600;">{', '.join(missing_names) if missing_names else 'Minor time/location confirmation'}</span> &bull;
                        <strong>Status:</strong> {case['contact_status']}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            btn_col1, btn_col2 = st.columns([1.5, 4])
            with btn_col1:
                if st.button(f"Simulate AI Voice Call", key=f"call_{case_id}", type="primary", use_container_width=True):
                    with st.spinner("Connecting simulated AI Voice Agent..."):
                        updated_case, result, transcript = simulate_ai_voice_call(case_id)
                        st.session_state[f"ai_call_done_{case_id}"] = {
                            "transcript": transcript,
                            "new_score": result.completeness_score,
                            "status": result.status.value
                        }
                        st.rerun()

            # If call was recently executed, show transcript
            call_res = st.session_state.get(f"ai_call_done_{case_id}")
            if call_res or case.get("ai_call_transcript"):
                transcript_text = call_res["transcript"] if call_res else case.get("ai_call_transcript")
                st.markdown(f"""
                <div class="notice-box notice-success" style="margin-top:10px;">
                    <div style="font-weight:700; margin-bottom:4px;">Telephone Verification Completed</div>
                    <div style="font-size:0.82rem; margin-bottom:8px;">
                        Patient confirmed missing parameters. Score updated to <strong>{case['completeness_score']}/100</strong> &bull; Status: <strong>{case['status']}</strong>
                    </div>
                    <pre style="background:#ffffff; border:1px solid #d1fae5; border-radius:4px; padding:10px; font-size:0.78rem; color:#065f46; white-space:pre-wrap; font-family:monospace;">{transcript_text}</pre>
                </div>
                """, unsafe_allow_html=True)
