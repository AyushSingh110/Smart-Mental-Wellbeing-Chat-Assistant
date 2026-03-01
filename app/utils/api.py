import requests

BACKEND_URL = "http://localhost:8000"


def send_chat(user_id: str, message: str) -> dict:
    payload = {
        "user_id": user_id,
        "message": message,
    }
    response = requests.post(f"{BACKEND_URL}/chat", json=payload, timeout=20)
    response.raise_for_status()
    return response.json()


def submit_assessment(user_id: str, phq2: int, gad2: int):
    payload = {
        "user_id": user_id,
        "phq2": phq2,
        "gad2": gad2,
    }
    response = requests.post(f"{BACKEND_URL}/assessment", json=payload, timeout=10)
    response.raise_for_status()

def get_report(user_id: str):
    response = requests.get(
        f"{BACKEND_URL}/report/{user_id}",
        timeout=20
    )
    response.raise_for_status()
    return response.content

def get_timeline(user_id: str):
    response = requests.get(
        f"{BACKEND_URL}/user/{user_id}/timeline",
        timeout=10
    )
    response.raise_for_status()
    return response.json()