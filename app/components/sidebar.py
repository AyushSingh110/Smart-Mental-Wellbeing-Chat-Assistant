import streamlit as st
from utils.api import submit_assessment


def render_sidebar() -> bool:

    with st.sidebar:
        st.markdown(f"""
        <div class="sidebar-brand">
            <div class="sidebar-brand-dot"></div>
            <div class="sidebar-brand-text">Well-Being AI</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="sidebar-section-label">Quick Assessment</div>', unsafe_allow_html=True)

        phq1 = st.slider("Little interest or pleasure", 0, 3, 0, help="PHQ-2 Item 1")
        phq2 = st.slider("Feeling down or hopeless", 0, 3, 0, help="PHQ-2 Item 2")
        gad1 = st.slider("Feeling nervous or anxious", 0, 3, 0, help="GAD-2 Item 1")
        gad2 = st.slider("Unable to stop worrying", 0, 3, 0, help="GAD-2 Item 2")

        if st.button("Submit Assessment", use_container_width=True):
            try:
                submit_assessment(phq1 + phq2, gad1 + gad2)
                st.success("Assessment recorded")
            except Exception:
                st.error("Backend unavailable")

        st.markdown('<div class="sidebar-section-label">Voice Assistant</div>', unsafe_allow_html=True)
        voice_enabled = st.toggle("Enable voice responses", value=True)

        st.markdown('<div class="sidebar-section-label">Wellness Score</div>', unsafe_allow_html=True)
        score = 75
        color = "#48bb78" if score >= 70 else "#ed8936" if score >= 40 else "#fc8181"
        st.markdown(f"""
        <div class="sidebar-score-card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                <span style="font-size:0.75rem; color:#a8b7cc;">Weekly Stability</span>
                <span style="font-size:0.9rem; font-weight:600; color:{color};">{score}%</span>
            </div>
            <div style="height:4px; background:rgba(255,255,255,0.06); border-radius:2px; overflow:hidden;">
                <div style="height:100%; width:{score}%; background:linear-gradient(90deg,#63b3ed,#4fd1c5); border-radius:2px;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="sidebar-disclaimer">
            This tool is not a substitute for professional mental health care.
            If you are in immediate danger or crisis, contact local emergency services.
        </div>
        """, unsafe_allow_html=True)

    return voice_enabled
