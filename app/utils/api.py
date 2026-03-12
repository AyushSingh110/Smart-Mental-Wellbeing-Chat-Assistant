#api.py
import requests
import streamlit as st

BACKEND_URL = "http://localhost:8000"


def _get_headers():
    if "jwt" not in st.session_state or not st.session_state.jwt:
        raise Exception("User not authenticated")

    return {
        "Authorization": f"Bearer {st.session_state.jwt}"
    }

# Chat
def send_chat(message: str) -> dict:
    headers = {
        "Authorization": f"Bearer {st.session_state.jwt}"
    }

    response = requests.post(
        f"{BACKEND_URL}/chat",
        json={"message": message},
        headers=headers,
        timeout=20
    )

    response.raise_for_status()
    return response.json()

# Assessment
def submit_assessment(phq2: int, gad2: int):
    payload = {
        "phq2": phq2,
        "gad2": gad2,
    }

    response = requests.post(
        f"{BACKEND_URL}/assessment",
        json=payload,
        headers=_get_headers(),
        timeout=10
    )

    response.raise_for_status()

# PDF Report
def get_report():
    response = requests.get(
        f"{BACKEND_URL}/report",
        headers=_get_headers(),
        timeout=20
    )

    response.raise_for_status()
    return response.content

# Timeline
def get_timeline():
    response = requests.get(
        f"{BACKEND_URL}/user/timeline",
        headers=_get_headers(),
        timeout=10
    )

    response.raise_for_status()
    return response.json()