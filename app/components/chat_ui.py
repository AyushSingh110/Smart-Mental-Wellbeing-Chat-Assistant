import streamlit as st
from utils.api import send_chat      
from utils.voice import speak_text, render_mic_component

SPEAKER_SVG = """<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/></svg>"""
ALERT_SVG   = """<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>"""


def render_chat(user_id: str, voice_enabled: bool) -> None:
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # mhi_log stores dicts: {timestamp, mhi, category} for the dashboard
    if "mhi_log" not in st.session_state:
        st.session_state.mhi_log = []

    if not st.session_state.chat_history:
        st.markdown("""
        <div style="text-align:center; padding:3.5rem 0 2rem 0;">
            <div style="font-size:0.88rem; color:#546070; line-height:1.8;">
                Share how you're feeling today.<br>I'm here to listen and support you.
            </div>
        </div>
        """, unsafe_allow_html=True)

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # ── Input area with mic overlaid inside the chat input ────────────────────
    # We use a relative wrapper div and position the iframe absolutely
    # so it sits visually inside the right side of the chat input bar.
    st.markdown("""
    <style>
    /* Pull the mic iframe into the chat input bar */
    [data-testid="stBottom"] > div { position: relative !important; }
    [data-testid="stBottom"] iframe {
        position: absolute !important;
        right: 52px !important;
        bottom: 14px !important;
        width: 36px !important;
        height: 36px !important;
        z-index: 100 !important;
        border: none !important;
        background: transparent !important;
        pointer-events: all !important;
    }
    </style>
    """, unsafe_allow_html=True)

    render_mic_component()
    user_input = st.chat_input("Share how you're feeling...")

    # ── Handle submission ──────────────────────────────────────────────────────
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner(""):
                try:
                    data        = send_chat(user_id, user_input)
                    reply       = data.get("response", "")
                    mhi         = data.get("mhi", 0)
                    category    = data.get("category", "")
                    crisis_flag = data.get("crisis_score", 0) > 0.7

                    # Store MHI silently — never shown in chat
                    if mhi:
                        from datetime import datetime
                        st.session_state.mhi_log.append({
                            "timestamp": datetime.now().isoformat(),
                            "mhi": mhi,
                            "category": category,
                        })

                    st.session_state.chat_history.append({"role": "assistant", "content": reply})
                    st.markdown(reply)

                    if voice_enabled and reply:
                        speak_text(reply)
                        st.markdown(f"""
                        <div class="speaking-indicator">
                            {SPEAKER_SVG}
                            <span>Speaking</span>
                            <div class="speak-bars">
                                <div class="speak-bar"></div><div class="speak-bar"></div>
                                <div class="speak-bar"></div><div class="speak-bar"></div>
                                <div class="speak-bar"></div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                    if crisis_flag:
                        st.markdown(f"""
                        <div class="crisis-alert" style="margin-top:12px;">
                            {ALERT_SVG}
                            <span>Immediate support is recommended. Please reach out to emergency services, a crisis helpline, or a trusted person nearby.</span>
                        </div>
                        """, unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"Connection error: {e}")
