import streamlit as st

from components.login import render_login
from components.sidebar import render_sidebar
from components.chat_ui  import render_chat        # voice-only, interrupt, multilingual
from components.tools_panel     import render_tools
from components.dashboard import render_dashboard   # equal cards, live MHI
from styles import GLOBAL_CSS

st.set_page_config(
    page_title="Well-Being AI",
    page_icon="\U0001FAE7",   # 🫧
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Auth gate ─────────────────────────────────────────────────────────────────
if "jwt" not in st.session_state:
    render_login()
    st.stop()

# ── Main app ──────────────────────────────────────────────────────────────────
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "mhi_log" not in st.session_state:
    st.session_state.mhi_log = []

voice_enabled = render_sidebar()

st.markdown("""
<div class="app-header">
    <div class="app-header-icon">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white"
             stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06
                     a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78
                     1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
        </svg>
    </div>
    <div>
        <div class="app-header-title">Smart Mental Well-Being Assistant</div>
        <div class="app-header-sub">Emotion Detection · Mental Health Index · CBT Support</div>
    </div>
</div>
""", unsafe_allow_html=True)

mhi_count = len(st.session_state.mhi_log)
dashboard_label = f"Dashboard ({mhi_count})" if mhi_count else "Dashboard"

tab_chat, tab_dashboard, tab_tools = st.tabs([
    "Chat",
    dashboard_label,
    "Self-Help Tools",
])

with tab_chat:
    render_chat(voice_enabled=voice_enabled)

with tab_dashboard:
    render_dashboard()

with tab_tools:
    render_tools()