from backend.services.llm_service import generate_llm_response

prompt = "Explain box breathing in simple terms."

response = generate_llm_response(prompt)

print("LLM Response:")
print(response)