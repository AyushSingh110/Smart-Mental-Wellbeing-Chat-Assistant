GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bg-primary:     #0b1220;
    --bg-secondary:   #0f1a2c;
    --bg-card:        #121f35;
    --bg-input:       #17243b;
    --border:         rgba(255,255,255,0.10);
    --border-hover:   rgba(99,179,237,0.3);
    --text-primary:   #eaf1fb;
    --text-secondary: #a8b7cc;
    --text-muted:     #7a8ca4;
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
    scroll-behavior: smooth;
}
.stApp { background: var(--bg-primary) !important; }
.main .block-container {
    padding: 1.5rem 2rem 4rem 2rem !important;
    max-width: 1080px !important;
    animation: app-fade-in 260ms ease-out;
}

@keyframes app-fade-in {
    from { opacity: 0; transform: translateY(6px); }
    to { opacity: 1; transform: translateY(0); }
}

[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(circle at 14% -10%, rgba(99, 179, 237, 0.17), transparent 34%),
        radial-gradient(circle at 88% 0%, rgba(79, 209, 197, 0.12), transparent 30%),
        var(--bg-primary) !important;
}

::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background:
        linear-gradient(180deg, rgba(15, 26, 44, 0.97), rgba(12, 21, 36, 0.98)) !important;
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
    background: linear-gradient(180deg, rgba(20, 35, 58, 0.96), rgba(15, 26, 44, 0.96)) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    color: var(--text-primary) !important;
    border-radius: 10px !important;
    font-family: var(--font-main) !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    padding: 0.48rem 1rem !important;
    transition: all 0.18s ease !important;
}
.stButton > button:hover {
    border-color: var(--accent) !important;
    color: var(--accent) !important;
    background: linear-gradient(180deg, rgba(32, 50, 78, 0.96), rgba(24, 41, 67, 0.96)) !important;
    box-shadow: 0 0 12px rgba(99,179,237,0.15) !important;
}
.stButton > button:focus-visible {
    outline: none !important;
    box-shadow: 0 0 0 3px rgba(99,179,237,0.22) !important;
    border-color: rgba(99,179,237,0.5) !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(10, 18, 31, 0.65) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    gap: 0 !important;
    padding: 4px !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border: none !important;
    color: var(--text-muted) !important;
    font-family: var(--font-main) !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    padding: 0.58rem 1rem !important;
    border-radius: 8px !important;
    border-bottom: none !important;
    margin-bottom: 0 !important;
    transition: all 0.18s ease !important;
}
.stTabs [data-baseweb="tab"]:hover { color: var(--text-primary) !important; }
.stTabs [aria-selected="true"] {
    color: #d7ebff !important;
    border: 1px solid rgba(99,179,237,0.45) !important;
    background: rgba(99,179,237,0.16) !important;
    box-shadow: inset 0 0 0 1px rgba(255,255,255,0.05) !important;
}
.stTabs [data-baseweb="tab-panel"] {
    padding: 1.5rem 0 0 0 !important;
    background: transparent !important;
    animation: app-fade-in 220ms ease-out;
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
    justify-content: space-between;
    padding: 1.15rem 1.2rem;
    border: 1px solid var(--border);
    border-radius: 14px;
    margin-bottom: 1rem;
    background:
        linear-gradient(130deg, rgba(17, 31, 53, 0.96), rgba(13, 24, 42, 0.96));
    box-shadow: var(--shadow-md);
    transition: border-color 0.2s ease, transform 0.2s ease;
}
.app-header:hover { border-color: var(--border-hover); }
.app-header-main { display: flex; align-items: center; gap: 12px; }
.app-header-icon {
    width: 36px; height: 36px;
    background: linear-gradient(135deg, var(--accent), var(--accent-teal));
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
}
.app-header-title { font-size: 1.05rem; font-weight: 600; color: var(--text-primary); letter-spacing: -0.01em; }
.app-header-sub { font-size: 0.75rem; color: var(--text-secondary); margin-top: 1px; }
.app-header-chip {
    padding: 0.38rem 0.72rem;
    border-radius: 999px;
    border: 1px solid rgba(79,209,197,0.32);
    background: rgba(79,209,197,0.10);
    color: var(--accent-teal);
    font-size: 0.66rem;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    font-weight: 600;
}

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
    transition: border-color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
    margin-top: 0.5rem;
}
.tool-card:hover {
    border-color: var(--border-hover);
    transform: translateY(-1px);
    box-shadow: 0 10px 28px rgba(3, 8, 20, 0.35);
}
.tool-card h4 { font-size: 0.9rem; font-weight: 600; color: var(--accent); margin: 0 0 6px 0; }
.tool-card p  { font-size: 0.82rem; color: var(--text-secondary); margin: 0; line-height: 1.55; }

.tool-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin: 0.2rem 0 0.8rem;
}
.tool-title {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--text-muted);
    font-weight: 600;
}
.tool-hint {
    font-size: 0.72rem;
    color: var(--text-secondary);
}

.sidebar-score-card {
    background: linear-gradient(180deg, rgba(21, 35, 58, 0.96), rgba(17, 28, 46, 0.96));
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 14px 16px;
    margin-bottom: 8px;
}
.sidebar-disclaimer {
    margin-top: 2rem;
    padding-top: 1.2rem;
    border-top: 1px solid var(--border);
    font-size: 0.72rem;
    color: var(--text-muted);
    line-height: 1.65;
}

@media (max-width: 900px) {
    .main .block-container {
        padding: 1rem 1rem 3rem 1rem !important;
    }
    .app-header {
        flex-direction: column;
        align-items: flex-start;
        gap: 10px;
    }
    .tool-head {
        flex-direction: column;
        align-items: flex-start;
        gap: 4px;
    }
    .stTabs [data-baseweb="tab-list"] {
        overflow-x: auto !important;
        scrollbar-width: thin;
    }
    .stTabs [data-baseweb="tab"] {
        white-space: nowrap;
    }
}

@media (prefers-reduced-motion: reduce) {
    * {
        animation: none !important;
        transition: none !important;
        scroll-behavior: auto !important;
    }
}

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
