import streamlit as st
import requests

BACKEND_URL = "http://localhost:8000"

# ── Supported languages for selection ─────────────────────────────────────────
LANGUAGES = [
    {"code": "en", "name": "English",    "native": "English",    "icon": "\U0001F1EC\U0001F1E7"},
    {"code": "hi", "name": "Hindi",      "native": "\u0939\u093f\u0928\u094d\u0926\u0940",       "icon": "\U0001F1EE\U0001F1F3"},
    {"code": "bn", "name": "Bengali",    "native": "\u09ac\u09be\u0982\u09b2\u09be",       "icon": "\U0001F1E7\U0001F1E9"},
    {"code": "ta", "name": "Tamil",      "native": "\u0ba4\u0bae\u0bbf\u0bb4\u0bcd",       "icon": "\U0001F1EE\U0001F1F3"},
    {"code": "te", "name": "Telugu",     "native": "\u0c24\u0c46\u0c32\u0c41\u0c17\u0c41",       "icon": "\U0001F1EE\U0001F1F3"},
    {"code": "mr", "name": "Marathi",    "native": "\u092e\u0930\u093e\u0920\u0940",        "icon": "\U0001F1EE\U0001F1F3"},
    {"code": "gu", "name": "Gujarati",   "native": "\u0a97\u0ac1\u0a9c\u0ab0\u0abe\u0aa4\u0ac0",     "icon": "\U0001F1EE\U0001F1F3"},
    {"code": "pa", "name": "Punjabi",    "native": "\u0a2a\u0a70\u0a1c\u0a3e\u0a2c\u0a40",      "icon": "\U0001F1EE\U0001F1F3"},
    {"code": "kn", "name": "Kannada",    "native": "\u0c95\u0ca8\u0ccd\u0ca8\u0ca1",       "icon": "\U0001F1EE\U0001F1F3"},
    {"code": "ml", "name": "Malayalam",  "native": "\u0d2e\u0d32\u0d2f\u0d3e\u0d33\u0d02",      "icon": "\U0001F1EE\U0001F1F3"},
    {"code": "ur", "name": "Urdu",       "native": "\u0627\u0631\u062f\u0648",         "icon": "\U0001F1F5\U0001F1F0"},
    {"code": "or", "name": "Odia",       "native": "\u0b13\u0b21\u0b3c\u0b3f\u0b06",         "icon": "\U0001F1EE\U0001F1F3"},
    {"code": "as", "name": "Assamese",   "native": "\u0985\u09b8\u09ae\u09c0\u09af\u09bc\u09be",      "icon": "\U0001F1EE\U0001F1F3"},
    {"code": "ne", "name": "Nepali",     "native": "\u0928\u0947\u092a\u093e\u0932\u0940",       "icon": "\U0001F1F3\U0001F1F5"},
]

LOGIN_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700&display=swap');

html, body, .stApp {
    background: #060b14 !important;
    font-family: 'Sora', -apple-system, sans-serif !important;
    scroll-behavior: smooth;
}

#MainMenu, footer, header,
[data-testid="stDecoration"],
[data-testid="stToolbar"],
.stDeployButton { display: none !important; }

.main .block-container {
    padding-top: 0 !important;
    padding-bottom: 0 !important;
    max-width: 100% !important;
    animation: authFadeIn 350ms ease-out;
}

@keyframes authFadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes floatGlow {
    0%, 100% { transform: translate(0, 0) scale(1); opacity: 0.08; }
    33% { transform: translate(12px, -18px) scale(1.05); opacity: 0.12; }
    66% { transform: translate(-8px, 10px) scale(0.96); opacity: 0.06; }
}

@keyframes shimmer {
    0% { background-position: -200% center; }
    100% { background-position: 200% center; }
}

/* Left panel */
.left-panel {
    min-height: 100vh;
    padding: 3.5rem 2.8rem;
    background: linear-gradient(160deg, #0a1628 0%, #0d1e38 50%, #081425 100%);
    border-right: 1px solid rgba(99,179,237,0.06);
    display: flex;
    flex-direction: column;
    justify-content: center;
    position: relative;
    overflow: hidden;
}

.left-panel::before {
    content: '';
    position: absolute;
    top: -120px; left: -120px;
    width: 400px; height: 400px;
    background: radial-gradient(circle, rgba(99,179,237,0.06) 0%, transparent 65%);
    border-radius: 50%;
    pointer-events: none;
    animation: floatGlow 12s ease-in-out infinite;
}

.left-panel::after {
    content: '';
    position: absolute;
    bottom: -80px; right: -80px;
    width: 300px; height: 300px;
    background: radial-gradient(circle, rgba(79,209,197,0.05) 0%, transparent 65%);
    border-radius: 50%;
    pointer-events: none;
    animation: floatGlow 15s ease-in-out infinite reverse;
}

.brand-logo {
    width: 58px; height: 58px;
    background: linear-gradient(135deg, #63b3ed 0%, #4fd1c5 100%);
    border-radius: 18px;
    display: inline-flex;
    align-items: center; justify-content: center;
    margin-bottom: 2rem;
    box-shadow: 0 10px 40px rgba(99,179,237,0.25), 0 0 0 1px rgba(99,179,237,0.1);
    position: relative;
    z-index: 1;
}

.brand-title {
    font-size: 2rem;
    font-weight: 700;
    background: linear-gradient(135deg, #e8edf5 0%, #a8d0f0 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.03em;
    line-height: 1.15;
    margin-bottom: 0.6rem;
    position: relative;
    z-index: 1;
}

.brand-desc {
    font-size: 0.84rem;
    color: #546a82;
    line-height: 1.85;
    max-width: 310px;
    margin-bottom: 2.6rem;
    position: relative;
    z-index: 1;
}

.feature-row {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 1rem;
    position: relative;
    z-index: 1;
}

.feature-icon {
    width: 34px; height: 34px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.72rem;
    flex-shrink: 0;
    border: 1px solid;
}

.feature-label {
    font-size: 0.80rem;
    color: #8b9ab0;
    line-height: 1.3;
}

.feature-label strong {
    color: #c0cfe0;
    font-weight: 500;
}

/* Trust badges */
.trust-row {
    display: flex;
    gap: 18px;
    margin-top: 2.2rem;
    position: relative;
    z-index: 1;
}
.trust-badge {
    display: flex;
    align-items: center;
    gap: 5px;
    font-size: 0.66rem;
    color: #546a82;
    letter-spacing: 0.02em;
}
.trust-dot {
    width: 5px;
    height: 5px;
    border-radius: 50%;
    background: #48bb78;
    box-shadow: 0 0 6px rgba(72,187,120,0.4);
}

/* Right panel */
.main .block-container > div[data-testid="stHorizontalBlock"] > div:nth-child(2) {
    display: flex;
    align-items: center;
    min-height: 100vh;
    padding: 0 2.5rem;
}

.main .block-container > div[data-testid="stHorizontalBlock"] > div:nth-child(2) > div[data-testid="stVerticalBlock"] {
    max-width: 440px;
    width: 100%;
    margin: 0 auto;
    padding: 2rem 1.6rem;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 20px;
    background: linear-gradient(180deg, rgba(12, 20, 35, 0.95), rgba(8, 14, 26, 0.95));
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(255,255,255,0.03);
    backdrop-filter: blur(12px);
}

.form-heading {
    font-size: 1.6rem;
    font-weight: 600;
    background: linear-gradient(135deg, #e8edf5, #b8d0e8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.02em;
    margin-bottom: 0.2rem;
}

.form-sub {
    font-size: 0.78rem;
    color: #546a82;
    margin-bottom: 1.8rem;
}

.field-label {
    font-size: 0.68rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #546a82;
    margin-bottom: 0.3rem;
    margin-top: 1rem;
    display: block;
}

.auth-footer {
    text-align: center;
    font-size: 0.74rem;
    color: #3a4555;
    margin-top: 1.2rem;
}

.auth-footer a { color: #63b3ed; text-decoration: none; }

.divider-line {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.06), transparent);
    margin: 1.8rem 0 1rem 0;
}

.legal-note {
    text-align: center;
    font-size: 0.68rem;
    color: #2a3545;
    line-height: 1.8;
}

/* Streamlit input overrides */
.stTextInput > label { display: none !important; }

.stTextInput > div > div > input {
    background: rgba(10, 18, 32, 0.8) !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 12px !important;
    color: #e8edf5 !important;
    font-family: 'Sora', sans-serif !important;
    font-size: 0.86rem !important;
    padding: 0.75rem 1rem !important;
    height: 48px !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}

.stTextInput > div > div > input:focus {
    border-color: rgba(99,179,237,0.4) !important;
    box-shadow: 0 0 0 3px rgba(99,179,237,0.08) !important;
    outline: none !important;
}

.stTextInput > div > div > input::placeholder { color: #2e3d50 !important; }

/* Primary button */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #63b3ed, #4fd1c5) !important;
    border: none !important;
    border-radius: 12px !important;
    color: #060b14 !important;
    font-family: 'Sora', sans-serif !important;
    font-size: 0.86rem !important;
    font-weight: 600 !important;
    height: 48px !important;
    letter-spacing: 0.01em !important;
    box-shadow: 0 4px 24px rgba(99,179,237,0.22) !important;
    transition: opacity 0.18s, box-shadow 0.18s, transform 0.15s !important;
}
.stButton > button[kind="primary"]:hover {
    opacity: 0.9 !important;
    box-shadow: 0 6px 32px rgba(99,179,237,0.35) !important;
    transform: translateY(-1px) !important;
}

/* Secondary button */
.stButton > button[kind="secondary"] {
    background: transparent !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 12px !important;
    color: #546a82 !important;
    font-family: 'Sora', sans-serif !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    height: 44px !important;
    transition: border-color 0.18s, color 0.18s !important;
}
.stButton > button[kind="secondary"]:hover {
    border-color: rgba(99,179,237,0.25) !important;
    color: #63b3ed !important;
}

/* Alert */
[data-testid="stAlert"] {
    border-radius: 10px !important;
    font-size: 0.80rem !important;
    font-family: 'Sora', sans-serif !important;
    margin-top: 0.8rem !important;
}

@media (max-width: 1080px) {
    .left-panel { padding: 2.5rem 2rem; }
    .brand-title { font-size: 1.7rem; }
}

@media (max-width: 760px) {
    .left-panel {
        min-height: auto;
        padding: 2rem 1.2rem;
        border-right: none;
        border-bottom: 1px solid rgba(99,179,237,0.06);
    }
    .main .block-container > div[data-testid="stHorizontalBlock"] > div:nth-child(2) {
        min-height: auto;
        padding: 1.2rem 0.8rem 1.6rem;
    }
    .main .block-container > div[data-testid="stHorizontalBlock"] > div:nth-child(2) > div[data-testid="stVerticalBlock"] {
        max-width: 100%;
        padding: 1.2rem;
    }
}

@media (prefers-reduced-motion: reduce) {
    * {
        animation: none !important;
        transition: none !important;
    }
}
</style>
"""

# ── Language selection page CSS ───────────────────────────────────────────────
LANG_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700&display=swap');

html, body, .stApp {
    background: #060b14 !important;
    font-family: 'Sora', -apple-system, sans-serif !important;
}

#MainMenu, footer, header,
[data-testid="stDecoration"],
[data-testid="stToolbar"],
.stDeployButton { display: none !important; }

.main .block-container {
    padding-top: 0 !important;
    max-width: 720px !important;
    animation: langFadeIn 400ms ease-out;
}

@keyframes langFadeIn {
    from { opacity: 0; transform: translateY(12px); }
    to { opacity: 1; transform: translateY(0); }
}

/* Language card buttons */
.stButton > button {
    background: linear-gradient(180deg, rgba(14, 24, 42, 0.95), rgba(10, 18, 32, 0.95)) !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: 14px !important;
    color: #c0cfe0 !important;
    font-family: 'Sora', sans-serif !important;
    font-size: 0.84rem !important;
    font-weight: 500 !important;
    padding: 1rem 0.5rem !important;
    min-height: 68px !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 2px 12px rgba(0,0,0,0.15) !important;
}
.stButton > button:hover {
    border-color: rgba(99,179,237,0.35) !important;
    color: #e8edf5 !important;
    background: linear-gradient(180deg, rgba(20, 35, 58, 0.95), rgba(14, 24, 42, 0.95)) !important;
    box-shadow: 0 4px 20px rgba(99,179,237,0.12) !important;
    transform: translateY(-2px) !important;
}
</style>
"""


def render_login() -> None:
    st.markdown(LOGIN_CSS, unsafe_allow_html=True)

    if "auth_tab" not in st.session_state:
        st.session_state.auth_tab = "login"

    left, right = st.columns([1, 1], gap="small")

    # ── Left decorative panel ─────────────────────────────────────────────────
    with left:
        st.markdown("""
        <div class="left-panel">
            <div class="brand-logo">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none"
                     stroke="#060b14" stroke-width="2.2"
                     stroke-linecap="round" stroke-linejoin="round">
                    <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67
                             l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78
                             l1.06 1.06L12 21.23l7.78-7.78
                             1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
                </svg>
            </div>
            <div class="brand-title">Smart Mental<br>Well-Being AI</div>
            <div class="brand-desc">
                A calm, private space to express yourself,
                track your mental health, and receive
                compassionate AI-powered support.
            </div>
            <div class="feature-row">
                <div class="feature-icon" style="background:rgba(99,179,237,0.08);border-color:rgba(99,179,237,0.18);color:#63b3ed;">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/></svg>
                </div>
                <span class="feature-label"><strong>Emotion Detection</strong><br>Real-time mood analysis from your voice</span>
            </div>
            <div class="feature-row">
                <div class="feature-icon" style="background:rgba(79,209,197,0.08);border-color:rgba(79,209,197,0.18);color:#4fd1c5;">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
                </div>
                <span class="feature-label"><strong>MHI Tracking</strong><br>Mental Health Index updated every turn</span>
            </div>
            <div class="feature-row">
                <div class="feature-icon" style="background:rgba(183,148,244,0.08);border-color:rgba(183,148,244,0.18);color:#b794f4;">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                </div>
                <span class="feature-label"><strong>CBT Conversations</strong><br>Evidence-based therapeutic guidance</span>
            </div>
            <div class="feature-row">
                <div class="feature-icon" style="background:rgba(104,211,145,0.08);border-color:rgba(104,211,145,0.18);color:#68d391;">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                </div>
                <span class="feature-label"><strong>14+ Languages</strong><br>Speak in your native Indian language</span>
            </div>
            <div class="trust-row">
                <div class="trust-badge"><div class="trust-dot"></div>End-to-end encrypted</div>
                <div class="trust-badge"><div class="trust-dot"></div>HIPAA aware</div>
                <div class="trust-badge"><div class="trust-dot"></div>No data sharing</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Right form panel ──────────────────────────────────────────────────────
    with right:
        if st.session_state.auth_tab == "login":
            st.markdown("""
            <div class="form-heading">Welcome back</div>
            <div class="form-sub">Sign in to continue your wellness journey</div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="form-heading">Create your account</div>
            <div class="form-sub">Free, private, and always available for you</div>
            """, unsafe_allow_html=True)

        tc1, tc2 = st.columns(2, gap="small")
        with tc1:
            if st.button("Sign In", key="tab_login", use_container_width=True,
                         type="primary" if st.session_state.auth_tab == "login" else "secondary"):
                st.session_state.auth_tab = "login"
                st.rerun()
        with tc2:
            if st.button("Create Account", key="tab_register", use_container_width=True,
                         type="primary" if st.session_state.auth_tab == "register" else "secondary"):
                st.session_state.auth_tab = "register"
                st.rerun()

        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

        # ── Login ─────────────────────────────────────────────────────────────
        if st.session_state.auth_tab == "login":
            st.markdown('<span class="field-label">Email address</span>', unsafe_allow_html=True)
            email = st.text_input("e", placeholder="you@example.com",
                                  key="li_email", label_visibility="collapsed")

            st.markdown('<span class="field-label">Password</span>', unsafe_allow_html=True)
            password = st.text_input("p", type="password", placeholder="Enter your password",
                                     key="li_pw", label_visibility="collapsed")

            st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

            if st.button("Sign In", key="do_login", use_container_width=True, type="primary"):
                if not email or not password:
                    st.error("Please enter your email and password.")
                else:
                    with st.spinner(""):
                        try:
                            res = requests.post(
                                f"{BACKEND_URL}/auth/login",
                                json={"email": email, "password": password},
                                timeout=10,
                            )
                            res.raise_for_status()
                            st.session_state.jwt = res.json()["access_token"]
                            st.rerun()
                        except requests.exceptions.HTTPError as e:
                            code = e.response.status_code if e.response is not None else 0
                            if code in (401, 403):
                                st.error("Invalid email or password.")
                            elif code == 404:
                                st.error("No account found with this email.")
                            else:
                                st.error("Something went wrong. Please try again.")
                        except Exception:
                            st.error("Could not reach the server.")

            st.markdown("""
            <div class="auth-footer" style="margin-top:1rem;">
                New here? Switch to <span style="color:#63b3ed;">Create Account</span> above.
            </div>
            """, unsafe_allow_html=True)

        # ── Register ──────────────────────────────────────────────────────────
        else:
            st.markdown('<span class="field-label">Email address</span>', unsafe_allow_html=True)
            email = st.text_input("e", placeholder="you@example.com",
                                  key="reg_email", label_visibility="collapsed")

            st.markdown('<span class="field-label">Password</span>', unsafe_allow_html=True)
            password = st.text_input("p", type="password",
                                     placeholder="At least 6 characters",
                                     key="reg_pw", label_visibility="collapsed")

            st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

            if st.button("Create Account", key="do_register", use_container_width=True, type="primary"):
                if not email or not password:
                    st.error("Please fill in all fields.")
                elif len(password) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    with st.spinner(""):
                        try:
                            res = requests.post(
                                f"{BACKEND_URL}/auth/register",
                                json={"email": email, "password": password, "baseline_mhi": 75},
                                timeout=10,
                            )
                            res.raise_for_status()
                            st.session_state.jwt = res.json()["access_token"]
                            st.rerun()
                        except requests.exceptions.HTTPError as e:
                            code = e.response.status_code if e.response is not None else 0
                            if code == 409:
                                st.error("An account with this email already exists.")
                            else:
                                st.error("Registration failed. Please try again.")
                        except Exception:
                            st.error("Could not reach the server.")

            st.markdown("""
            <div class="auth-footer" style="margin-top:1rem;">
                Already have an account? Switch to <span style="color:#63b3ed;">Sign In</span> above.
            </div>
            """, unsafe_allow_html=True)

        st.markdown("""
        <div class="divider-line"></div>
        <div class="legal-note">
            By continuing you agree to our Terms of Service.<br>
            Your data is encrypted and never shared with third parties.
        </div>
        """, unsafe_allow_html=True)


def render_language_selection() -> None:
    """Full-page language picker shown once after login."""
    st.markdown(LANG_CSS, unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center; padding: 4rem 0 0.8rem;">
        <div style="width:64px;height:64px;border-radius:50%;
                    background:linear-gradient(135deg,rgba(99,179,237,0.12),rgba(79,209,197,0.10));
                    border:1px solid rgba(99,179,237,0.15);
                    display:inline-flex;align-items:center;justify-content:center;
                    font-size:1.6rem;margin-bottom:1.2rem;">
            &#127760;
        </div>
        <div style="font-size:1.6rem;font-weight:600;
                    background:linear-gradient(135deg,#e8edf5,#a8d0f0);
                    -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                    background-clip:text;letter-spacing:-0.02em;margin-bottom:0.4rem;">
            Choose Your Language
        </div>
        <div style="font-size:0.82rem;color:#546a82;max-width:400px;margin:0 auto;line-height:1.7;">
            The assistant will communicate with you entirely in your chosen language.
            You can change this anytime from the sidebar.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

    # Render language cards in a 4-column grid
    num_cols = 4
    rows = [LANGUAGES[i:i + num_cols] for i in range(0, len(LANGUAGES), num_cols)]
    for row in rows:
        cols = st.columns(num_cols, gap="small")
        for j, lang in enumerate(row):
            with cols[j]:
                label = f"{lang['native']}  \u00b7  {lang['name']}"
                if st.button(label, key=f"lang_{lang['code']}", use_container_width=True):
                    st.session_state.selected_language = lang["code"]
                    st.rerun()

    st.markdown("""
    <div style="text-align:center;margin-top:2rem;font-size:0.68rem;color:#2a3545;line-height:1.8;">
        All 14 Indian languages are supported with native voice synthesis.<br>
        Language can also be auto-detected from your speech.
    </div>
    """, unsafe_allow_html=True)
