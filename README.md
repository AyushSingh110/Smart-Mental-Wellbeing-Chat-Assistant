🧠 Smart Mental Well-Being Chat Assistant

An AI-powered mental well-being assistant that combines:

Emotion detection

Crisis risk assessment

Mental Health Index (MHI) scoring

Retrieval-Augmented CBT support

Voice-to-voice conversational interface

Session analytics dashboard

AI-generated PDF session reports

Built using FastAPI + Streamlit + MongoDB + FAISS + Gemini/OpenAI LLM.

System Overview

This system is designed to provide structured, emotionally intelligent mental well-being support in a conversational format.

It goes beyond simple chatbot replies by:

Analyzing emotional state

Estimating crisis probability

Computing a Mental Health Index (MHI)

Retrieving relevant CBT knowledge

Generating grounded, safe responses

Tracking trends over time

Producing downloadable session reports

🏗️ Architecture
Backend (FastAPI)

EmotionService

CrisisService

IntentService

MentalHealthMatrix (MHI scoring)

RAGService (FAISS + SentenceTransformer)

LLMService (Gemini / OpenAI)

SafetyService

MongoDB (Motor async client)

ReportService (PDF generation using ReportLab)

Frontend (Streamlit Modular UI)
app/
│
├── components/
│   ├── chat_ui.py
│   ├── dashboard.py
│   ├── sidebar.py
│   ├── tools_panel.py
│
├── utils/
│   ├── api.py
│   ├── voice.py
│
├── streamlit_app.py
├── styles.py
🔁 Full Processing Flow
1️⃣ User Input (Text or Voice)

User can:

Type message

Click mic and speak

Use voice-to-voice mode

Voice is:

Transcribed using Speech Recognition

Sent to backend

Displayed in chat UI

2️⃣ Backend Processing Pipeline

When /chat is called:

Step A — Emotion Detection

Predicts emotional distribution (e.g., sadness, anger, anxiety).

Step B — Crisis Detection

Computes crisis probability score.

Step C — Intent Detection

Understands whether user seeks:

Support

Venting

Advice

Crisis help

Step D — Mental Health Index (MHI)

MHI is computed using:

emotion_score + crisis_score → scaled to 0–100

Categories:

Normal

Mild Stress

Anxiety

Depression

Crisis

3️⃣ RAG (Retrieval-Augmented Generation)

Instead of generating generic responses:

SentenceTransformer embeds user message

FAISS retrieves top CBT knowledge chunks

Prompt is constructed using:

Retrieved CBT context

Emotional state

MHI score

Crisis probability

LLM then generates grounded response.

This ensures:

No hallucinated therapy

CBT-aligned coping strategies

Context-based emotional support

4️⃣ Conversational CBT Integration

The assistant:

Acknowledges emotional experience

Explores thoughts and patterns gently

Applies CBT principles naturally

Avoids worksheet-style responses

Avoids over-clinical language

Maintains warm supportive tone

5️⃣ Safety Layer

Before sending response:

SafetyService checks:

High crisis probability

Self-harm indicators

Unsafe suggestions

If high risk:

Crisis stabilization message returned

Emergency recommendation shown

6️⃣ Database Logging

Each interaction stores:

{
  user_id,
  timestamp,
  message,
  emotion_scores,
  crisis_score,
  intent,
  mhi,
  category
}

Used for:

Trend analytics

Report generation

Session tracking

7️⃣ Dashboard Analytics

Displays:

Latest MHI (Gauge)

Session average MHI

Number of check-ins

Category history

MHI trend line chart

This helps identify behavioral patterns over time.

8️⃣ AI-Generated PDF Report

User can download a full session report.

Backend:

Retrieves conversation history

Computes average MHI

Generates session summary via LLM

Builds structured PDF (ReportLab)

PDF includes:

User ID

Date

Average MHI

AI session summary

Emotional insights