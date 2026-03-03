import streamlit as st
import requests
from datetime import datetime
from utils.voice import render_mic_component, speak_text

BACKEND_URL = "http://localhost:8000"

SPEAKER_SVG = """<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor"
    stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
    <path d="M19.07 4.93a10 10 0 0 1 0 14.14"/>
    <path d="M15.54 8.46a5 5 0 0 1 0 7.07"/>
</svg>"""

ALERT_SVG = """<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
    stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <circle cx="12" cy="12" r="10"/>
    <line x1="12" y1="8" x2="12" y2="12"/>
    <line x1="12" y1="16" x2="12.01" y2="16"/>
</svg>"""


# ─────────────────────────────────────────────────────────────────────────────
# Auth
# ─────────────────────────────────────────────────────────────────────────────

def _get_headers() -> dict:
    jwt = st.session_state.get("jwt")
    if not jwt:
        raise Exception("User not authenticated")
    return {"Authorization": f"Bearer {jwt}"}


# ─────────────────────────────────────────────────────────────────────────────
# Backend calls — unchanged from your original
# ─────────────────────────────────────────────────────────────────────────────

def send_chat(message: str) -> dict:
    response = requests.post(
        f"{BACKEND_URL}/chat",
        json={"message": message},
        headers=_get_headers(),
        timeout=20,
    )
    response.raise_for_status()
    return response.json()


def submit_assessment(phq2: int, gad2: int):
    response = requests.post(
        f"{BACKEND_URL}/assessment",
        json={"phq2": phq2, "gad2": gad2},
        headers=_get_headers(),
        timeout=10,
    )
    response.raise_for_status()


def get_report() -> bytes:
    response = requests.get(
        f"{BACKEND_URL}/report",
        headers=_get_headers(),
        timeout=20,
    )
    response.raise_for_status()
    return response.content


def get_timeline() -> list:
    response = requests.get(
        f"{BACKEND_URL}/user/timeline",
        headers=_get_headers(),
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


# ─────────────────────────────────────────────────────────────────────────────
# UI helpers
# ─────────────────────────────────────────────────────────────────────────────

def _empty_state() -> None:
    st.markdown("""
    <div style="text-align:center; padding:4rem 0 2rem 0;">
        <div style="
            width:52px; height:52px;
            background:linear-gradient(135deg,#63b3ed,#4fd1c5);
            border-radius:16px;
            display:inline-flex; align-items:center; justify-content:center;
            margin-bottom:1.2rem;
            box-shadow: 0 8px 32px rgba(99,179,237,0.2);
        ">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#080c14"
                 stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06
                         a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78
                         1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
            </svg>
        </div>
        <div style="font-size:1.05rem; font-weight:600; color:#e8edf5; margin-bottom:0.5rem;
                    letter-spacing:-0.01em;">
            How are you feeling today?
        </div>
        <div style="font-size:0.82rem; color:#546070; line-height:1.9; max-width:320px; margin:0 auto;">
            This is your private space to share openly.<br>
            I'll listen, understand, and support you.
        </div>
        <div style="display:flex; justify-content:center; gap:1.5rem; margin-top:2rem;">
            <div style="font-size:0.73rem; color:#3a4555; display:flex; align-items:center; gap:6px;">
                <div style="width:6px;height:6px;border-radius:50%;background:#63b3ed;"></div>
                Emotion aware
            </div>
            <div style="font-size:0.73rem; color:#3a4555; display:flex; align-items:center; gap:6px;">
                <div style="width:6px;height:6px;border-radius:50%;background:#4fd1c5;"></div>
                Always private
            </div>
            <div style="font-size:0.73rem; color:#3a4555; display:flex; align-items:center; gap:6px;">
                <div style="width:6px;height:6px;border-radius:50%;background:#b794f4;"></div>
                CBT guided
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Mic — positioned inside the Streamlit chat input bar
# ─────────────────────────────────────────────────────────────────────────────

_MIC_OVERLAY_CSS = """
<style>
/* Push the chat textarea right so text doesn't overlap the mic icon */
[data-testid="stChatInput"] textarea {
    padding-right: 5.5rem !important;
}

/* Overlay the mic iframe over the right side of the input bar */
[data-testid="stBottom"] {
    position: relative !important;
}
[data-testid="stBottom"] > div {
    position: relative !important;
}
[data-testid="stBottom"] iframe {
    position: absolute !important;
    right: 54px !important;
    bottom: 13px !important;
    width: 36px !important;
    height: 36px !important;
    z-index: 200 !important;
    border: none !important;
    background: transparent !important;
    pointer-events: all !important;
}
</style>
"""


# ─────────────────────────────────────────────────────────────────────────────
# Main render
# ─────────────────────────────────────────────────────────────────────────────

def render_chat(voice_enabled: bool = False) -> None:

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "mhi_log" not in st.session_state:
        st.session_state.mhi_log = []

    # Empty state
    if not st.session_state.chat_history:
        _empty_state()

    # Chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Inject mic overlay CSS + component
    # The iframe is absolutely positioned by CSS to sit inside the input bar
    st.markdown(_MIC_OVERLAY_CSS, unsafe_allow_html=True)
    render_mic_component()

    user_input = st.chat_input("Share how you're feeling...")

    if not user_input:
        return

    # User message
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Assistant response
    with st.chat_message("assistant"):
        with st.spinner(""):
            try:
                data = send_chat(user_input)

                reply        = data.get("response", "")
                mhi          = data.get("mhi", 0)
                category     = data.get("category", "")
                crisis_score = data.get("crisis_score", 0)

                # Store MHI silently for the Dashboard
                if mhi:
                    st.session_state.mhi_log.append({
                        "timestamp": datetime.now().isoformat(),
                        "mhi":       mhi,
                        "category":  category,
                    })

                st.session_state.chat_history.append({"role": "assistant", "content": reply})
                st.markdown(reply)

                # Voice output
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

                # Crisis alert
                if crisis_score > 0.7:
                    st.markdown(f"""
                    <div class="crisis-alert" style="margin-top:12px;">
                        {ALERT_SVG}
                        <span>Immediate support is recommended. Please reach out to emergency
                        services, a crisis helpline, or a trusted person nearby.</span>
                    </div>
                    """, unsafe_allow_html=True)

            except Exception as e:
                err = str(e)
                if "not authenticated" in err.lower():
                    st.error("Session expired. Please log in again.")
                else:
                    st.error(f"Connection error: {err}")
