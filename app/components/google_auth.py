import streamlit as st
from streamlit_oauth import OAuth2Component
import requests

CLIENT_ID = "YOUR_GOOGLE_CLIENT_ID"
CLIENT_SECRET = "YOUR_GOOGLE_CLIENT_SECRET"

AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
REVOKE_URL = "https://oauth2.googleapis.com/revoke"

REDIRECT_URI = "http://localhost:8501"

def google_login():

    oauth2 = OAuth2Component(
        CLIENT_ID,
        CLIENT_SECRET,
        AUTHORIZE_URL,
        TOKEN_URL,
        REVOKE_URL
    )

    if "token" not in st.session_state:
        st.session_state.token = None

    if st.session_state.token is None:
        result = oauth2.authorize_button(
            name="Login with Google",
            redirect_uri=REDIRECT_URI,
            scope="openid email profile",
            key="google"
        )

        if result:
            st.session_state.token = result.get("token")

    if st.session_state.token:
        userinfo = requests.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={
                "Authorization":
                f"Bearer {st.session_state.token['access_token']}"
            }
        ).json()

        return userinfo

    return None