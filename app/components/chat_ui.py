import streamlit as st
import requests
from datetime import datetime
from utils.voice import render_mic_component, speak_text, render_greeting, cancel_speech

BACKEND_URL = "http://localhost:8000"

SPEAKER_SVG = """<svg width="13" height="13" viewBox="0 0 24 24" fill="none"
    stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
    <path d="M19.07 4.93a10 10 0 0 1 0 14.14"/>
    <path d="M15.54 8.46a5 5 0 0 1 0 7.07"/>
</svg>"""

ALERT_SVG = """<svg width="14" height="14" viewBox="0 0 24 24" fill="none"
    stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <circle cx="12" cy="12" r="10"/>
    <line x1="12" y1="8" x2="12" y2="12"/>
    <line x1="12" y1="16" x2="12.01" y2="16"/>
</svg>"""

_MIC_OVERLAY_CSS = """
<style>
[data-testid="stChatInput"] textarea { padding-right: 5.5rem !important; }
[data-testid="stBottom"] { position: relative !important; }
[data-testid="stBottom"] > div { position: relative !important; }
[data-testid="stBottom"] iframe {
    position: absolute !important;
    right: 54px !important; bottom: 13px !important;
    width: 36px !important; height: 36px !important;
    z-index: 200 !important; border: none !important;
    background: transparent !important; pointer-events: all !important;
}
</style>
"""

# ── Auth ──────────────────────────────────────────────────────────────────────

def _get_headers() -> dict:
    jwt = st.session_state.get("jwt")
    if not jwt:
        raise Exception("User not authenticated")
    return {"Authorization": f"Bearer {jwt}"}


# ── Backend calls (unchanged) ─────────────────────────────────────────────────

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


# ── Empty state with greeting orb ────────────────────────────────────────────

def _empty_state(voice_enabled: bool) -> None:
    st.markdown("""
    <div style="text-align:center; padding:2.5rem 0 0.5rem 0;">
        <div style="font-size:1.05rem; font-weight:600; color:#e8edf5;
                    margin-bottom:0.5rem; letter-spacing:-0.01em;">
            How are you feeling today?
        </div>
        <div style="font-size:0.82rem; color:#546070; line-height:1.9;
                    max-width:320px; margin:0 auto 1.5rem auto;">
            This is your private space to share openly.<br>
            I'll listen, understand, and support you.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Render greeting orb — it auto-speaks when voice is enabled
    if voice_enabled:
        render_greeting("your Well-Being companion")
    else:
        # Silent orb (visual only, no auto-speak)
        st.markdown("""
        <div style="display:flex; justify-content:center; margin-bottom:1.5rem;">
            <div style="
                width:62px; height:62px; border-radius:50%;
                background: radial-gradient(circle at 38% 35%, #63b3ed 0%, #4fd1c5 55%, #7c3aed 100%);
                animation: idleOrb 3.5s ease-in-out infinite;
                box-shadow: 0 8px 32px rgba(99,179,237,0.2);
            "></div>
        </div>
        <style>
        @keyframes idleOrb {
            0%,100% { box-shadow:0 0 20px rgba(99,179,237,0.25); transform:scale(1);    }
            50%      { box-shadow:0 0 36px rgba(79,209,197,0.38); transform:scale(1.05); }
        }
        </style>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div style="display:flex; justify-content:center; gap:1.5rem; margin-top:0.5rem;">
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
    """, unsafe_allow_html=True)


# ── Main render ───────────────────────────────────────────────────────────────

def render_chat(voice_enabled: bool = False) -> None:

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "mhi_log" not in st.session_state:
        st.session_state.mhi_log = []

    # Show empty state with greeting orb on first load
    if not st.session_state.chat_history:
        _empty_state(voice_enabled)

    # Render chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Mic inside the input bar
    st.markdown(_MIC_OVERLAY_CSS, unsafe_allow_html=True)
    render_mic_component()

    user_input = st.chat_input("Share how you're feeling...")

    if not user_input:
        return

    # Stop any speaking before user sends new message
    cancel_speech()

    # Render user bubble
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Render assistant bubble
    with st.chat_message("assistant"):
        with st.spinner(""):
            try:
                data = send_chat(user_input)

                reply        = data.get("response", "")
                mhi          = data.get("mhi", 0)
                category     = data.get("category", "")
                crisis_score = data.get("crisis_score", 0)
                crisis_tier  = data.get("crisis_tier", "none")
                emotion_label = max(
                    data.get("emotion_scores", {"neutral": 1.0}),
                    key=data.get("emotion_scores", {"neutral": 1.0}).get,
                ) if data.get("emotion_scores") else "neutral"

                # Store MHI silently for Dashboard
                if mhi:
                    st.session_state.mhi_log.append({
                        "timestamp": datetime.now().isoformat(),
                        "mhi":       mhi,
                        "category":  category,
                    })

                st.session_state.chat_history.append({"role": "assistant", "content": reply})
                st.markdown(reply)

                # Voice output — emotion-aware + crisis-aware
                if voice_enabled and reply:
                    speak_text(reply, emotion_label=emotion_label, crisis_tier=crisis_tier)
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

                # Crisis alert banner — shown for passive tier and above
                if crisis_tier in ("active", "passive") or crisis_score > 0.60:
                    st.markdown(f"""
                    <div class="crisis-alert" style="margin-top:12px;">
                        {ALERT_SVG}
                        <span>If you're in distress, please reach out to a crisis helpline
                        or someone you trust. You don't have to face this alone.</span>
                    </div>
                    """, unsafe_allow_html=True)

            except Exception as e:
                err = str(e)
                if "not authenticated" in err.lower():
                    st.error("Session expired. Please log in again.")
                else:
                    st.error(f"Connection error: {err}")

   
  