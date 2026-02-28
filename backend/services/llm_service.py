import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODEL_NAME = "gpt-4o-mini"
TEMPERATURE = 0.3
MAX_TOKENS = 600


def generate_llm_response(prompt: str) -> str:
    """
    Sends prompt to OpenAI model and returns structured CBT response.
    Includes error handling and safety fallback.
    """

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": "You are a CBT-based mental health support assistant."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"LLM Error: {e}")

        return (
            "I'm here to support you. It looks like there was a technical issue "
            "while generating a response. If you're feeling overwhelmed, "
            "please consider reaching out to a trusted person or a mental health professional."
        )