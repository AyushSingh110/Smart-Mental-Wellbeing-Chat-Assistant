Smart Mental Well-Being Assistant

An AI-powered mental health support assistant that analyzes emotional signals from user conversations and provides supportive responses while monitoring a Mental Health Index (MHI) to track well-being trends.

The system combines machine learning models, rule-based behavioral analysis, conversational AI, and safety escalation logic to provide supportive interaction while identifying high-risk situations.

Overview

The Smart Mental Well-Being Assistant is designed to act as a supportive conversational companion.

The system:

Detects emotional signals

Identifies crisis risk

Tracks mental health trends

Generates supportive responses

Escalates to crisis support when necessary

Unlike simple chatbots, the assistant uses a multi-signal mental health scoring system that evaluates emotional, behavioral, screening, and historical indicators.

Core Features
AI Mental Health Analysis

Analyzes user messages using multiple signals:

Emotion detection

Crisis detection

Behavioral patterns

Psychological screening scores

Conversation history trends

Mental Health Index (MHI)

The system calculates a Mental Health Index (0–100) representing overall well-being.

Range	Category
80 – 100	Stable
65 – 79	Mild Stress
45 – 64	Moderate Distress
25 – 44	High Risk
0 – 24	Crisis Risk

The index is updated every conversation message.

Crisis Detection & Safety Escalation

The system detects signals such as:

self-harm intent

suicide ideation

hopelessness language

behavioral withdrawal

When high risk is detected, the assistant:

bypasses the LLM response

returns crisis support messaging

provides helpline resources

Conversational AI Support

The assistant provides supportive responses that aim to:

validate emotions

encourage small coping strategies

guide reflection

promote seeking professional support when necessary

Dashboard Monitoring

The dashboard displays:

Mental Health Index gauge

Well-being trend over time

Session statistics

Risk category history

Tech Stack
Backend

FastAPI
MongoDB (Motor Async Driver)
JWT Authentication

AI & Machine Learning

Transformers (HuggingFace)
DistilBERT fine-tuned models
Sentence Transformers
FAISS vector search
OpenAI / Gemini LLM support

Frontend

Streamlit

Voice Processing

Faster Whisper (Speech-to-Text)
pyttsx3 / gTTS (Text-to-Speech)

Data Processing

Python
Regex-based behavioral detection

Project Architecture
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
System Workflow

The assistant processes messages through a multi-stage analysis pipeline.

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
Screening Score (PHQ-2 / GAD-2)
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
Response Generation (RAG)
      │
      ▼
Safety Validation
      │
      ▼
Assistant Response
AI Service Components
Emotion Service

Predicts emotional signals from user text.

Possible emotions:

sadness

anxiety

anger

joy

neutral

Uses a fine-tuned DistilBERT classifier.

Crisis Service

Detects potential self-harm or suicide risk using a binary classifier.

Outputs:

crisis_score ∈ [0,1]

If the score crosses a threshold, the system triggers safety protocols.

Behavioral Service

Detects behavioral warning signs using pattern recognition.

Signals include:

social withdrawal

lack of motivation

substance coping

hopelessness language

sleep disruption

The service outputs a behavioral risk score.

Screening Service

Implements psychological screening metrics:

PHQ-2 (depression screening)
GAD-2 (anxiety screening)

Scores are normalized to generate a screening risk score.

History Service

Analyzes previous conversations to detect mental health trends.

Uses exponential decay weighting so recent sessions influence risk more strongly.

This helps detect:

improving trends

declining trends

stable states

Mental Health Matrix

Combines all signals to compute the Mental Health Index (MHI).

Inputs include:

emotion_score
crisis_score
behavioral_score
screening_score
history_score

Weighted scoring produces a final 0–100 index.

RAG Service

Generates conversational responses using a language model.

Inputs include:

user message

emotional context

intent

MHI score

crisis probability

The model generates supportive conversational responses.

Safety Service

Validates LLM responses to ensure safe outputs.

Responsibilities:

crisis override

response validation

helpline insertion

emergency escalation

If high risk is detected, the system bypasses the LLM response entirely.

Voice Interaction

The assistant supports speech interaction.

Speech flow:

User Speech
   │
   ▼
Whisper STT
   │
   ▼
Text Processing Pipeline
   │
   ▼
AI Response
   │
   ▼
Text-to-Speech Output
API Endpoints
Authentication
POST /auth/register
POST /auth/login
Chat
POST /chat

Processes user messages through the full analysis pipeline.

Mental Health Screening
POST /assessment

Stores PHQ-2 and GAD-2 scores for the user.

Conversation History
GET /user/history

Returns previous messages.

MHI Timeline
GET /user/timeline

Used for dashboard visualization.

Voice Processing
POST /voice/transcribe
POST /voice/speak

Handles speech input and output.

Report Generation
GET /report/{user_id}

Generates a PDF summary of the user’s mental health session.

Database Structure
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
Safety Considerations

The assistant does not replace professional care.

Safety mechanisms include:

suicide risk detection

crisis escalation

helpline recommendations

emergency messaging

When severe distress is detected, the assistant encourages contacting real-world support.

Future Improvements

Potential enhancements:

therapist-guided dialogue framework

advanced cognitive distortion detection

long-term mental health trajectory modeling

adaptive intervention strategies

multilingual support

improved crisis sensitivity models

Disclaimer

This project is designed as a supportive well-being assistant, not a substitute for professional mental health care.

If a user is in immediate danger, they should contact emergency services or a mental health professional.
