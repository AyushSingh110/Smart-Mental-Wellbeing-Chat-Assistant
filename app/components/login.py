import streamlit as st
import requests

BACKEND_URL = "http://localhost:8000"

LOGIN_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700&display=swap');

html, body, .stApp {
    background: #080c14 !important;
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
    animation: authFadeIn 260ms ease-out;
}

@keyframes authFadeIn {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
}

/* Left panel */
.left-panel {
    min-height: 100vh;
    padding: 4rem 3rem;
    background: linear-gradient(145deg, #0d1520 0%, #0a1628 60%, #0d1a2e 100%);
    border-right: 1px solid rgba(99,179,237,0.07);
    display: flex;
    flex-direction: column;
    justify-content: center;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s ease;
}

.left-panel::before {
    content: '';
    position: absolute;
    top: -100px; left: -100px;
    width: 350px; height: 350px;
    background: radial-gradient(circle, rgba(99,179,237,0.08) 0%, transparent 70%);
    border-radius: 50%;
    pointer-events: none;
}

.left-panel::after {
    content: '';
    position: absolute;
    bottom: -60px; right: -60px;
    width: 260px; height: 260px;
    background: radial-gradient(circle, rgba(79,209,197,0.07) 0%, transparent 70%);
    border-radius: 50%;
    pointer-events: none;
}

.brand-logo {
    width: 54px; height: 54px;
    background: linear-gradient(135deg, #63b3ed, #4fd1c5);
    border-radius: 16px;
    display: inline-flex;
    align-items: center; justify-content: center;
    margin-bottom: 1.8rem;
    box-shadow: 0 8px 32px rgba(99,179,237,0.25);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.brand-logo:hover {
    transform: translateY(-1px);
    box-shadow: 0 12px 36px rgba(99,179,237,0.3);
}

.brand-title {
    font-size: 1.9rem;
    font-weight: 700;
    color: #e8edf5;
    letter-spacing: -0.03em;
    line-height: 1.2;
    margin-bottom: 0.7rem;
}

.brand-desc {
    font-size: 0.86rem;
    color: #546070;
    line-height: 1.8;
    max-width: 290px;
    margin-bottom: 2.8rem;
}

.feature-row {
    display: flex;
    align-items: center;
    gap: 11px;
    margin-bottom: 0.9rem;
}

.feature-dot {
    width: 7px; height: 7px;
    border-radius: 50%;
    flex-shrink: 0;
}

.feature-label {
    font-size: 0.81rem;
    color: #8b9ab0;
}

/* Right panel */
/* Targets the right auth column container without relying on open/close HTML wrappers */
.main .block-container > div[data-testid="stHorizontalBlock"] > div:nth-child(2) {
    display: flex;
    align-items: center;
    min-height: 100vh;
    padding: 0 2rem;
}

.main .block-container > div[data-testid="stHorizontalBlock"] > div:nth-child(2) > div[data-testid="stVerticalBlock"] {
    max-width: 430px;
    width: 100%;
    margin: 0 auto;
    padding: 1.4rem;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    background: linear-gradient(180deg, rgba(15, 22, 34, 0.9), rgba(10, 16, 26, 0.9));
    box-shadow: 0 16px 36px rgba(4, 8, 18, 0.35);
}

.form-heading {
    font-size: 1.5rem;
    font-weight: 600;
    color: #e8edf5;
    letter-spacing: -0.02em;
    margin-bottom: 0.3rem;
}

.form-sub {
    font-size: 0.8rem;
    color: #546070;
    margin-bottom: 1.6rem;
}

.field-label {
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #546070;
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
    background: rgba(255,255,255,0.05);
    margin: 2rem 0 1rem 0;
}

.legal-note {
    text-align: center;
    font-size: 0.7rem;
    color: #2a3545;
    line-height: 1.7;
}

/* Streamlit input overrides */
.stTextInput > label { display: none !important; }

.stTextInput > div > div > input {
    background: #0f1520 !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 12px !important;
    color: #e8edf5 !important;
    font-family: 'Sora', sans-serif !important;
    font-size: 0.88rem !important;
    padding: 0.75rem 1rem !important;
    height: 48px !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}

.stTextInput > div > div > input:focus {
    border-color: rgba(99,179,237,0.45) !important;
    box-shadow: 0 0 0 3px rgba(99,179,237,0.09) !important;
    outline: none !important;
}

.stTextInput > div > div > input::placeholder { color: #2e3d50 !important; }

/* Primary button */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #63b3ed, #4fd1c5) !important;
    border: none !important;
    border-radius: 12px !important;
    color: #080c14 !important;
    font-family: 'Sora', sans-serif !important;
    font-size: 0.88rem !important;
    font-weight: 600 !important;
    height: 48px !important;
    letter-spacing: 0.01em !important;
    box-shadow: 0 4px 20px rgba(99,179,237,0.2) !important;
    transition: opacity 0.18s, box-shadow 0.18s !important;
}
.stButton > button[kind="primary"]:hover {
    opacity: 0.88 !important;
    box-shadow: 0 6px 28px rgba(99,179,237,0.35) !important;
}
.stButton > button[kind="primary"]:focus-visible {
    outline: none !important;
    box-shadow: 0 0 0 3px rgba(99,179,237,0.25) !important;
}

/* Secondary (tab) button */
.stButton > button[kind="secondary"] {
    background: transparent !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 12px !important;
    color: #546070 !important;
    font-family: 'Sora', sans-serif !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    height: 44px !important;
    transition: border-color 0.18s, color 0.18s !important;
}
.stButton > button[kind="secondary"]:hover {
    border-color: rgba(99,179,237,0.3) !important;
    color: #63b3ed !important;
    background: rgba(99,179,237,0.05) !important;
}
.stButton > button[kind="secondary"]:focus-visible {
    outline: none !important;
    border-color: rgba(99,179,237,0.45) !important;
    box-shadow: 0 0 0 3px rgba(99,179,237,0.15) !important;
}

/* Alert */
[data-testid="stAlert"] {
    border-radius: 10px !important;
    font-size: 0.82rem !important;
    font-family: 'Sora', sans-serif !important;
    margin-top: 0.8rem !important;
}

@media (max-width: 1080px) {
    .left-panel { padding: 3rem 2rem; }
    .brand-title { font-size: 1.6rem; }
}

@media (max-width: 760px) {
    .left-panel {
        min-height: auto;
        padding: 2rem 1.2rem;
        border-right: none;
        border-bottom: 1px solid rgba(99,179,237,0.07);
    }
    .main .block-container > div[data-testid="stHorizontalBlock"] > div:nth-child(2) {
        min-height: auto;
        padding: 1.2rem 0.8rem 1.6rem;
    }
    .main .block-container > div[data-testid="stHorizontalBlock"] > div:nth-child(2) > div[data-testid="stVerticalBlock"] {
        max-width: 100%;
        padding: 1rem;
        border-radius: 14px;
    }
    .brand-desc { max-width: 100%; margin-bottom: 1.2rem; }
    .feature-row { margin-bottom: 0.6rem; }
}

@media (prefers-reduced-motion: reduce) {
    * {
        animation: none !important;
        transition: none !important;
        scroll-behavior: auto !important;
    }
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
                <svg width="26" height="26" viewBox="0 0 24 24" fill="none"
                     stroke="#080c14" stroke-width="2.2"
                     stroke-linecap="round" stroke-linejoin="round">
                    <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67
                             l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78
                             l1.06 1.06L12 21.23l7.78-7.78
                             1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
                </svg>
            </div>
            <div class="brand-title">Well-Being AI</div>
            <div class="brand-desc">
                A calm, private space to express yourself
                and receive compassionate AI support.
            </div>
            <div class="feature-row">
                <div class="feature-dot" style="background:#63b3ed;"></div>
                <span class="feature-label">Real-time emotion detection</span>
            </div>
            <div class="feature-row">
                <div class="feature-dot" style="background:#4fd1c5;"></div>
                <span class="feature-label">Mental Health Index tracking</span>
            </div>
            <div class="feature-row">
                <div class="feature-dot" style="background:#b794f4;"></div>
                <span class="feature-label">CBT-based guided conversations</span>
            </div>
            <div class="feature-row">
                <div class="feature-dot" style="background:#68d391;"></div>
                <span class="feature-label">Private and secure — always</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Right form panel ──────────────────────────────────────────────────────
    with right:
        # Heading
        if st.session_state.auth_tab == "login":
            st.markdown("""
            <div class="form-heading">Welcome back</div>
            <div class="form-sub">Sign in to continue your journey</div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="form-heading">Create your account</div>
            <div class="form-sub">Free, private, and always available</div>
            """, unsafe_allow_html=True)

        # Tab switcher — equal width, symmetric
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

        st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)

        # ── Login ─────────────────────────────────────────────────────────────
        if st.session_state.auth_tab == "login":
            st.markdown('<span class="field-label">Email address</span>', unsafe_allow_html=True)
            email = st.text_input("e", placeholder="you@example.com",
                                  key="li_email", label_visibility="collapsed")

            st.markdown('<span class="field-label">Password</span>', unsafe_allow_html=True)
            password = st.text_input("p", type="password", placeholder="Enter your password",
                                     key="li_pw", label_visibility="collapsed")

            st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)

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

            st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)

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
            Your data is encrypted and never shared.
        </div>
        """, unsafe_allow_html=True)
