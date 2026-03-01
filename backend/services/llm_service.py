import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

MODEL_NAME = "gemini-2.5-flash-lite"
TEMPERATURE = 0.3
MAX_TOKENS = 800

# Initialize model once (singleton pattern)
model = genai.GenerativeModel(
    MODEL_NAME,
    generation_config={
        "temperature": TEMPERATURE,
        "max_output_tokens": MAX_TOKENS,
    }
)


def generate_llm_response(prompt: str) -> str:
    """
    Sends a fully constructed prompt to Gemini.
    Prompt engineering should be handled upstream (RAG service).
    """

    try:
        response = model.generate_content(prompt)

        if hasattr(response, "text") and response.text:
            return response.text.strip()

        return (
            "I'm here to support you. I couldn't generate a response just now. "
            "If you're feeling overwhelmed, please consider reaching out to a trusted person."
        )

    except Exception as e:
        print(f"LLM Error: {e}")

        return (
            "I'm here to support you. There was a technical issue generating a response. "
            "If you're feeling overwhelmed, consider reaching out to someone you trust."
        )