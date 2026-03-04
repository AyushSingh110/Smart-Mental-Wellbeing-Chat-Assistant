🧠** Smart Mental Well-Being Assistant**

An AI-powered mental health support assistant designed to understand emotional signals from user conversations and provide supportive responses while tracking a Mental Health Index (MHI) to monitor well-being trends.

The system integrates machine learning models, behavioral analysis, conversational AI, and safety mechanisms to deliver empathetic support while detecting potential high-risk situations.

🌟 **Key Capabilities**

The assistant is designed to act as a supportive conversational companion that can:

🧠 Detect emotional signals from text
⚠️ Identify potential crisis or self-harm risk
📊 Track mental health trends over time
💬 Generate supportive conversational responses
🚑 Escalate to crisis resources when necessary

Unlike traditional chatbots, this system evaluates multiple psychological indicators simultaneously to produce a more realistic well-being assessment.

📊 **Mental Health Index (MHI)**

The Mental Health Index (MHI) is a score between 0 and 100 representing a user's overall mental well-being based on conversation analysis.

Score Range	Category
80 – 100	🟢 Stable
65 – 79	🟡 Mild Stress
45 – 64	🟠 Moderate Distress
25 – 44	🔴 High Risk
0 – 24	🚨 Crisis Risk

The MHI is updated after each conversation message using multiple signals.

🧩** AI Signal Analysis**

To evaluate mental health signals, the system combines several independent analysis modules.

🧠 Emotion Detection

Identifies emotional tone in user messages.

Possible emotions include:

sadness

anxiety

anger

joy

neutral

This is implemented using a fine-tuned DistilBERT transformer model.

⚠️ Crisis Detection

Detects potential self-harm or suicide risk from conversation text.

The system outputs a probability score:

crisis_score ∈ [0,1]

If the score exceeds a defined threshold, safety protocols are triggered automatically.

🧍 Behavioral Signal Detection

A rule-based behavioral analysis detects patterns such as:

social withdrawal

loss of motivation

substance coping

hopelessness language

sleep disturbance

These signals contribute to the behavioral risk score.

📋 Psychological Screening

The system integrates validated screening tools:

• PHQ-2 – depression screening
• GAD-2 – anxiety screening

Scores are normalized and incorporated into the overall risk calculation.

📈 Historical Trend Analysis

The assistant analyzes previous conversations to identify trends.

Recent sessions are weighted more strongly using exponential decay, allowing the system to detect:

improving mental state

declining mental state

stable trends

🧮 Mental Health Matrix

All signals are combined using a weighted scoring model.

Inputs:

emotion_score
crisis_score
behavioral_score
screening_score
history_score

These signals are processed by the Mental Health Matrix, which produces the final Mental Health Index (MHI).

💬 Conversational AI Support

The assistant generates supportive responses using Retrieval-Augmented Generation (RAG).

Response generation considers:

user message

detected emotion

conversation intent

current MHI score

crisis probability

The assistant aims to:

validate user emotions

suggest coping strategies

encourage reflection

guide toward professional help when needed

🛡️ Safety Layer

Safety is a core design principle.

The Safety Service ensures responses remain responsible and supportive.

It performs:

• crisis response override
• response validation
• helpline insertion
• emergency escalation

If severe distress is detected, the assistant bypasses the language model entirely and returns crisis support guidance.

🎤 Voice Interaction

The assistant supports speech-based interaction.

Voice Processing Flow
User Speech
     ↓
Speech-to-Text (Whisper)
     ↓
Conversation Analysis Pipeline
     ↓
AI Response
     ↓
Text-to-Speech Output

Speech technologies used:

🎙 Faster-Whisper – speech recognition
🔊 pyttsx3 / gTTS – speech synthesis

🏗 **System Architecture**
Backend Structure
backend/
│
├── auth/
│   ├── auth_router.py
│   └── auth_utils.py
│
├── database/
│   └── mongo_client.py
│
├── routes/
│   └── routes_report.py
│
├── services/
│   ├── emotion_service.py
│   ├── crisis_service.py
│   ├── behavioral_service.py
│   ├── screening_service.py
│   ├── history_service.py
│   ├── matrix_service.py
│   ├── rag_service.py
│   ├── safety_service.py
│   ├── report_service.py
│   └── voice_service.py
│
├── models/
│   └── user_models.py
│
├── dependencies.py
├── config.py
└── main.py

Each component is modular to allow independent improvement of AI subsystems.

🔄** System Workflow**

The assistant processes every message through a multi-stage analysis pipeline.

User Message
     │
     ▼
Emotion Detection
     │
     ▼
Crisis Detection
     │
     ▼
Behavioral Pattern Analysis
     │
     ▼
Psychological Screening
     │
     ▼
Historical Trend Analysis
     │
     ▼
Mental Health Matrix
     │
     ▼
Mental Health Index (MHI)
     │
     ▼
AI Response Generation (RAG)
     │
     ▼
Safety Validation
     │
     ▼
Assistant Response
⚙️ Tech Stack
Backend

🚀 FastAPI
🗄 MongoDB (Motor Async Driver)
🔐 JWT Authentication

AI & Machine Learning

🤗 HuggingFace Transformers
🧠 DistilBERT fine-tuned models
🔎 Sentence Transformers
📚 FAISS Vector Search
🧩 OpenAI / Gemini LLM integration

Frontend

🎨 Streamlit Dashboard

Voice Processing

🎙 Faster-Whisper
🔊 pyttsx3 / gTTS

🔗 API Endpoints
Authentication
POST /auth/register
POST /auth/login
Chat
POST /chat

Processes messages through the full mental health analysis pipeline.

Screening
POST /assessment

Stores PHQ-2 and GAD-2 screening scores.

Conversation Data
GET /user/history
GET /user/timeline
Voice Interaction
POST /voice/transcribe
POST /voice/speak
Report Generation
GET /report/{user_id}

Generates a PDF summary of mental health trends.

🗄 Database Schema
Users Collection
{
  _id,
  email,
  hashed_password,
  baseline_mhi,
  phq2_total,
  gad2_total,
  created_at,
  last_login
}
Conversations Collection
{
  user_id,
  timestamp,
  message,
  emotion_scores,
  crisis_score,
  behavioral_score,
  screening_score,
  history_score,
  intent,
  mhi,
  category
}
⚠️ Important Disclaimer

This system is designed as a supportive mental well-being assistant, not a replacement for professional care.

If a user is experiencing severe distress or crisis, they should seek help from licensed mental health professionals or emergency services.

🚀 Future Improvements

Potential future enhancements include:

• therapist-guided conversational frameworks
• cognitive distortion detection
• advanced long-term mental health modeling
• adaptive intervention strategies
• multilingual support
