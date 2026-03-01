GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bg-primary:     #0f1117;
    --bg-secondary:   #161b27;
    --bg-card:        #1a2035;
    --bg-input:       #1e2640;
    --border:         rgba(255,255,255,0.07);
    --border-hover:   rgba(99,179,237,0.3);
    --text-primary:   #e8edf5;
    --text-secondary: #8b9ab0;
    --text-muted:     #546070;
    --accent:         #63b3ed;
    --accent-soft:    rgba(99,179,237,0.12);
    --accent-teal:    #4fd1c5;
    --accent-purple:  #b794f4;
    --user-bubble:    #1e3a5f;
    --assistant-bubble: #1a2035;
    --success:  #48bb78;
    --warning:  #ed8936;
    --danger:   #fc8181;
    --shadow-sm: 0 1px 3px rgba(0,0,0,0.3);
    --shadow-md: 0 4px 16px rgba(0,0,0,0.4);
    --font-main: 'Sora', -apple-system, sans-serif;
    --font-mono: 'JetBrains Mono', monospace;
}

html, body, .stApp {
    background-color: var(--bg-primary) !important;
    font-family: var(--font-main) !important;
    color: var(--text-primary) !important;
}
.stApp { background: var(--bg-primary) !important; }
.main .block-container {
    padding: 1.5rem 2rem 5rem 2rem !important;
    max-width: 900px !important;
}

::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: var(--bg-secondary) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stCaption { color: var(--text-secondary) !important; font-size: 0.82rem !important; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: var(--text-primary) !important; font-weight: 500 !important; }
[data-testid="stSidebar"] .stSlider > div > div > div { background: var(--accent) !important; }

/* ── Buttons ── */
.stButton > button {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    color: var(--text-primary) !important;
    border-radius: 8px !important;
    font-family: var(--font-main) !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    padding: 0.4rem 1rem !important;
    transition: all 0.18s ease !important;
}
.stButton > button:hover {
    border-color: var(--accent) !important;
    color: var(--accent) !important;
    background: var(--accent-soft) !important;
    box-shadow: 0 0 12px rgba(99,179,237,0.15) !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid var(--border) !important;
    gap: 0 !important;
    padding: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border: none !important;
    color: var(--text-muted) !important;
    font-family: var(--font-main) !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    padding: 0.6rem 1.2rem !important;
    border-radius: 0 !important;
    border-bottom: 2px solid transparent !important;
    margin-bottom: -1px !important;
    transition: all 0.18s ease !important;
}
.stTabs [data-baseweb="tab"]:hover { color: var(--text-primary) !important; }
.stTabs [aria-selected="true"] {
    color: var(--accent) !important;
    border-bottom-color: var(--accent) !important;
    background: transparent !important;
}
.stTabs [data-baseweb="tab-panel"] {
    padding: 1.5rem 0 0 0 !important;
    background: transparent !important;
}

/* ── Progress ── */
.stProgress > div > div { background: linear-gradient(90deg, var(--accent), var(--accent-teal)) !important; }
.stProgress > div { background: var(--bg-card) !important; }

/* ── Toggle ── */
.stToggle { color: var(--text-primary) !important; }

/* ── Metrics ── */
[data-testid="stMetric"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    padding: 1rem 1.2rem !important;
}
[data-testid="stMetricLabel"] { color: var(--text-secondary) !important; font-size: 0.75rem !important; }
[data-testid="stMetricValue"] { color: var(--text-primary) !important; font-size: 1.5rem !important; }

/* ── Chat messages ── */
[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    padding: 0.25rem 0 !important;
}
[data-testid="stChatMessageContent"] {
    background: var(--assistant-bubble) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    padding: 1rem 1.2rem !important;
    font-size: 0.9rem !important;
    line-height: 1.65 !important;
    color: var(--text-primary) !important;
    box-shadow: var(--shadow-sm) !important;
}

/* ── Chat input wrapper — position:relative so mic can be absolutely placed ── */
[data-testid="stBottom"] {
    background: var(--bg-primary) !important;
    padding-bottom: 1rem !important;
}
[data-testid="stChatInput"] {
    background: var(--bg-input) !important;
    border: 1px solid var(--border) !important;
    border-radius: 24px !important;
    box-shadow: var(--shadow-md) !important;
    transition: border-color 0.2s ease !important;
    position: relative !important;
}
[data-testid="stChatInput"]:focus-within {
    border-color: var(--border-hover) !important;
    box-shadow: 0 0 0 3px rgba(99,179,237,0.08), var(--shadow-md) !important;
}
[data-testid="stChatInput"] textarea {
    background: transparent !important;
    color: var(--text-primary) !important;
    font-family: var(--font-main) !important;
    font-size: 0.9rem !important;
    padding-right: 5rem !important; /* space for mic icon */
}
[data-testid="stChatInput"] textarea::placeholder { color: var(--text-muted) !important; }

/* ── Mic overlay inside chat input ── */
/* The iframe component sits absolutely over the chat input right side */
.mic-overlay-wrapper {
    position: relative;
    width: 100%;
}
.mic-overlay-wrapper iframe {
    position: absolute !important;
    right: 52px !important;   /* left of Streamlit's send button */
    bottom: 6px !important;
    width: 36px !important;
    height: 36px !important;
    border: none !important;
    background: transparent !important;
    z-index: 999 !important;
    pointer-events: all !important;
}

/* ── Spinner ── */
.stSpinner > div { border-top-color: var(--accent) !important; }

hr { border-color: var(--border) !important; margin: 1.5rem 0 !important; }

/* ── App header ── */
.app-header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 1.2rem 0 1.5rem 0;
    border-bottom: 1px solid var(--border);
    margin-bottom: 0;
}
.app-header-icon {
    width: 36px; height: 36px;
    background: linear-gradient(135deg, var(--accent), var(--accent-teal));
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
}
.app-header-title { font-size: 1.05rem; font-weight: 600; color: var(--text-primary); letter-spacing: -0.01em; }
.app-header-sub { font-size: 0.75rem; color: var(--text-muted); margin-top: 1px; }

/* ── Speaking indicator ── */
@keyframes speak-pulse {
    0%, 100% { opacity: 0.4; transform: scaleY(0.6); }
    50%       { opacity: 1;   transform: scaleY(1);   }
}
.speaking-indicator {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 4px 10px;
    background: rgba(79,209,197,0.1);
    border: 1px solid rgba(79,209,197,0.2);
    border-radius: 20px;
    font-size: 0.75rem;
    color: var(--accent-teal);
    margin-top: 6px;
}
.speak-bars { display: flex; align-items: center; gap: 2px; height: 14px; }
.speak-bar {
    width: 2px; background: var(--accent-teal); border-radius: 1px;
    animation: speak-pulse 0.6s ease-in-out infinite;
}
.speak-bar:nth-child(1) { height: 8px;  animation-delay: 0s;   }
.speak-bar:nth-child(2) { height: 14px; animation-delay: 0.1s; }
.speak-bar:nth-child(3) { height: 10px; animation-delay: 0.2s; }
.speak-bar:nth-child(4) { height: 14px; animation-delay: 0.3s; }
.speak-bar:nth-child(5) { height: 6px;  animation-delay: 0.4s; }

/* ── Category badge ── */
.category-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 500;
    background: rgba(183,148,244,0.12);
    border: 1px solid rgba(183,148,244,0.25);
    color: var(--accent-purple);
    margin-top: 6px;
}

/* ── Crisis alert ── */
.crisis-alert {
    background: rgba(252,129,129,0.08);
    border: 1px solid rgba(252,129,129,0.3);
    border-radius: 12px;
    padding: 12px 16px;
    font-size: 0.85rem;
    color: var(--danger);
    display: flex;
    align-items: flex-start;
    gap: 10px;
}

/* ── MHI container ── */
.mhi-container {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 0.5rem;
}

/* ── Tool card ── */
.tool-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.2rem;
    transition: border-color 0.2s ease;
    margin-top: 0.5rem;
}
.tool-card:hover { border-color: var(--border-hover); }
.tool-card h4 { font-size: 0.9rem; font-weight: 600; color: var(--accent); margin: 0 0 6px 0; }
.tool-card p  { font-size: 0.82rem; color: var(--text-secondary); margin: 0; line-height: 1.55; }

/* ── Sidebar brand ── */
.sidebar-brand {
    display: flex; align-items: center; gap: 10px;
    padding: 0.5rem 0 1.2rem 0;
    border-bottom: 1px solid var(--border);
    margin-bottom: 1.2rem;
}
.sidebar-brand-dot {
    width: 28px; height: 28px;
    background: linear-gradient(135deg, var(--accent), var(--accent-teal));
    border-radius: 8px;
}
.sidebar-brand-text { font-size: 0.9rem; font-weight: 600; color: var(--text-primary); }
.sidebar-section-label {
    font-size: 0.68rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--text-muted);
    margin: 1.2rem 0 0.6rem 0;
}

/* ── Dashboard stat card ── */
.stat-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
}
.stat-card .label {
    font-size: 0.68rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.08em;
    color: var(--text-muted); margin-bottom: 6px;
}
.stat-card .value { font-size: 1.8rem; font-weight: 600; line-height: 1; }

/* Hide Streamlit chrome */
#MainMenu, footer, header { visibility: hidden !important; }
.stDeployButton { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
</style>
"""
