import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from backend.services.llm_service import generate_llm_response

MODEL_NAME = "all-MiniLM-L6-v2"
INDEX_PATH = "backend/rag/faiss_index.index"
METADATA_PATH = "backend/rag/metadata.json"

SIMILARITY_THRESHOLD = 2.0
TOP_K = 3

class RAGService:

    def __init__(self):
        self.model = SentenceTransformer(MODEL_NAME)
        self.index = faiss.read_index(INDEX_PATH)

        with open(METADATA_PATH, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)

        self.system_prompt = """
You are a structured Cognitive Behavioral Therapy (CBT)-based mental well-being assistant.

Your Purpose:
- Provide emotionally supportive, evidence-based coping guidance.
- Base your response primarily on the retrieved CBT context.
- Adapt guidance to the user's emotional state and mental health index.
- Maintain a calm, empathetic, and non-judgmental tone.

Strict Rules:
- Use ONLY techniques or concepts grounded in the retrieved context.
- Do NOT invent new therapeutic methods.
- Do NOT provide medical diagnoses.
- Do NOT provide medication recommendations.
- Do NOT minimize emotional distress.
- Do NOT validate self-harm thoughts.

Safety Protocol:
- If crisis probability is high, prioritize crisis stabilization steps.
- Encourage seeking professional or emergency support when risk is moderate to high.
- Never provide instructions for self-harm.
- If unsure, default to safety-oriented language.

Response Structure:
1. Acknowledge and validate the user’s emotional experience.
2. Provide a CBT-based coping strategy grounded in retrieved context.
3. Briefly explain why the technique may help.
4. Offer practical step-by-step guidance if appropriate.
5. End with a gentle supportive check-in question.

Tone Guidelines:
- Clear and supportive.
- Professional but warm.
- Not overly clinical.
- Not overly casual.
"""

    def retrieve_context(self, query: str):

        query_embedding = self.model.encode([query])
        distances, indices = self.index.search(np.array(query_embedding), TOP_K)

        results = []

        for i, idx in enumerate(indices[0]):
            if distances[0][i] <= SIMILARITY_THRESHOLD:
                results.append(self.metadata[idx])

    # fallback if nothing passes threshold
        if not results:
            results = [self.metadata[indices[0][0]]]

        return results

    def build_prompt(
        self,
        user_message,
        emotion_label,
        emotion_score,
        intent,
        mental_health_index,
        crisis_probability,
        retrieved_chunks
    ):

        context_text = "\n\n".join(
            [f"Technique {i+1}:\n{chunk['text']}" for i, chunk in enumerate(retrieved_chunks)]
     )

        prompt = f"""
{self.system_prompt}

Retrieved CBT Context:
{context_text}

User Emotional State:
- Emotion: {emotion_label}
- Emotion Score: {emotion_score}
- Intent: {intent}
- Mental Health Index: {mental_health_index}
- Crisis Probability: {crisis_probability}

User Message:
{user_message}

Instructions:
- You MUST ground your response in the retrieved CBT context.
- Do NOT provide generic psychoeducation.
- Do NOT invent new techniques.
- Align with the user’s emotional state and mental health index.
- Adapt tone to emotional intensity.

Apply CBT principles conversationally without explicitly naming techniques.
Integrate the method naturally into the conversation.
Focus on exploring thoughts, emotions, and behavioral patterns gently.
Avoid sounding like a worksheet, therapist manual, or instructional guide.

End with one gentle, reflective, supportive question.
"""

        return prompt

    def generate_response(
        self,
        user_message,
        emotion_label,
        emotion_score,
        intent,
        mental_health_index,
        crisis_probability
    ):
        if crisis_probability > 0.75:
            return (
                "I’m really concerned about your safety right now. "
                "If you are in immediate danger, please contact emergency services "
                "or a suicide prevention hotline immediately. "
                "You deserve real-time professional support."
        )


        retrieved_chunks = self.retrieve_context(user_message)
        if mental_health_index < 60:
            depth_instruction = "Provide detailed structured CBT steps."
        elif mental_health_index < 80:
            depth_instruction = "Provide moderate structured coping guidance."
        else:
            depth_instruction = "Provide supportive and light CBT reframing."

        prompt = self.build_prompt(
            user_message,
            emotion_label,
            emotion_score,
            intent,
            mental_health_index,
            crisis_probability,
            retrieved_chunks
        )

        response = generate_llm_response(prompt)

        return response
