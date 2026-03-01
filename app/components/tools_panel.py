import streamlit as st


_TOOLS = {
    "breathing": {
        "label": "Breathing Exercise",
        "icon": """<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#63b3ed" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22a10 10 0 1 1 0-20 10 10 0 0 1 0 20z"/><path d="M12 8v4l3 3"/></svg>""",
        "title": "4-7-8 Breathing",
        "body": "Inhale for 4 seconds · Hold for 7 seconds · Exhale for 8 seconds. Repeat 4 cycles to activate your parasympathetic nervous system.",
    },
    "grounding": {
        "label": "Grounding 5-4-3-2-1",
        "icon": """<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#4fd1c5" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>""",
        "title": "Grounding Technique",
        "body": "5 things you see · 4 you can touch · 3 you hear · 2 you smell · 1 you taste. Anchors you to the present moment.",
    },
    "reframe": {
        "label": "Cognitive Reframe",
        "icon": """<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#b794f4" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="16"/><line x1="8" y1="12" x2="16" y2="12"/></svg>""",
        "title": "Cognitive Reframe",
        "body": "Identify the automatic thought · Examine the evidence · Consider alternative explanations · Generate a balanced response.",
    },
}


def render_tools():
    st.markdown("""
    <div style="margin: 2rem 0 1rem 0;">
        <div style="font-size:0.68rem; font-weight:600; text-transform:uppercase; letter-spacing:0.08em; color:#546070; margin-bottom:0.8rem;">Self-Help Tools</div>
    </div>
    """, unsafe_allow_html=True)

    if "active_tool" not in st.session_state:
        st.session_state.active_tool = None

    cols = st.columns(3)
    tool_keys = list(_TOOLS.keys())

    for i, col in enumerate(cols):
        key = tool_keys[i]
        tool = _TOOLS[key]
        with col:
            if st.button(tool["label"], key=f"tool_{key}", use_container_width=True):
                st.session_state.active_tool = key if st.session_state.active_tool != key else None

    if st.session_state.active_tool:
        tool = _TOOLS[st.session_state.active_tool]
        st.markdown(f"""
        <div class="tool-card" style="margin-top:0.75rem;">
            <div style="display:flex; align-items:center; gap:8px; margin-bottom:8px;">
                {tool["icon"]}
                <h4 style="margin:0;">{tool["title"]}</h4>
            </div>
            <p>{tool["body"]}</p>
        </div>
        """, unsafe_allow_html=True)
