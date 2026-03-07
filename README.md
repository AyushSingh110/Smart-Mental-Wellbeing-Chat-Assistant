🧠** Smart Mental Well-Being Assistant**

A full-stack mental health support system combining clinical screening tools, real-time emotion and crisis detection, CBT-guided AI responses, multilingual voice interaction, and an MHI (Mental Health Index) tracking dashboard. Built for the Indian context with support for 14 languages.

---

## Overview

This system processes a user's text or speech input through a multi-layer ML pipeline that detects emotion, assesses crisis risk, computes a Mental Health Index score, and generates a response calibrated to the user's current state. All heavy computation runs locally. No patient data is sent to external services except the LLM.

The architecture is designed around one core principle: **safety before helpfulness**. Crisis detection runs before the LLM is ever called. For active suicidal language, the system bypasses the LLM entirely and returns a predefined, helpline-inclusive response.

---

## Features

**Emotion and Crisis Detection**
- Fine-tuned DistilBERT models for emotion classification and crisis tier detection
- Rule-based regex patterns as a safety-first second layer (active, passive, distress, none)
- Hard MHI ceilings enforced per crisis tier regardless of model output

**Mental Health Index**
- Composite score (0–100) from emotion, crisis probability, behavioral signals, PHQ-2/GAD-2 screening, and session history
- Nonlinear crisis amplification with hopeless-language penalty
- Hard floors: active crisis → MHI ≤ 20, passive → MHI ≤ 35

**CBT-Guided Responses**
- RAG (Retrieval-Augmented Generation) over a FAISS-indexed CBT knowledge base
- Response length adapts to risk category: Crisis gets a 1–2 sentence template, Stable gets 4–5 sentences
- LLM is bypassed entirely for active/passive crisis tiers

**Multilingual Voice**
- Language auto-detection via faster-whisper (supports 99 languages, runs locally)
- Indian language TTS via gTTS with co.in accent routing
- Emotion-matched speaking speed via pydub tempo adjustment
- Supported Indian languages: Hindi, Bengali, Tamil, Telugu, Marathi, Gujarati, Punjabi, Kannada, Malayalam, Urdu, Odia, Assamese, Nepali, and English

**Dashboard**
- Real-time MHI trend chart with zone bands
- Session statistics: peak/low MHI, emotion distribution, voice vs text breakdown
- PHQ-2/GAD-2 screening integration

**Authentication**
- JWT-based login/registration
- Per-user conversation history and timeline stored in MongoDB

---

## Architecture

```
User Input (text or audio)
         │
         ▼
┌────────────────────────────────────────────────────────────────┐
│  Layer 1 — ML Inference  (all run in thread pool, parallel)    │
│  EmotionService    → emotion label + score                     │
│  CrisisService     → crisis probability + tier                 │
│  IntentService     → intent classification                     │
│  BehavioralService → behavioral risk score (regex)             │
└────────────────────────────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────────────────────┐
│  Layer 2 — MHI Computation                                     │
│  MentalHealthMatrix.compute(emotion, crisis, behavioral,       │
│    screening, history, raw_text) → MHI score 0–100            │
│  MentalHealthMatrix.categorize() → category string            │
└────────────────────────────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────────────────────┐
│  Layer 3 — Response Generation                                 │
│  if active/passive crisis:                                     │
│    → SafetyService returns predefined template (LLM skipped)  │
│  else:                                                         │
│    → RAGService.retrieve_context() → FAISS top-k chunks       │
│    → LLM generates response with length instruction           │
│    → SafetyService.validate_response() trims + checks         │
└────────────────────────────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────────────────────┐
│  Layer 4 — Voice Output  (voice mode only)                     │
│  MultilingualVoiceService.synthesize()                         │
│    gTTS → Indian accent → pydub speed adjust → MP3            │
└────────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
├── backend/
│   ├── auth/
│   │   └── auth_router.py          JWT authentication routes
│   ├── config.py                   Pydantic settings (env vars)
│   ├── dependencies.py             FastAPI dependency injection
│   ├── rag/
│   │   ├── faiss_index.index       FAISS vector index (CBT knowledge)
│   │   └── metadata.json           Chunk metadata for retrieved docs
│   ├── routes/
│   │   └── routes_report.py        PDF report generation
│   └── services/
│       ├── behavioral_service.py   Regex-based behavioral risk scoring
│       ├── crisis_service.py       DistilBERT crisis detection + regex
│       ├── emotion_service.py      DistilBERT emotion classification
│       ├── history_service.py      Session history risk trend
│       ├── intent_service.py       Intent classification
│       ├── llm_service.py          LLM wrapper (Ollama/OpenAI)
│       ├── matrix_service.py       MHI computation and categorization
│       ├── multilingual_voice_service.py  Multilingual STT + TTS
│       ├── rag_service.py          FAISS retrieval + LLM prompt builder
│       ├── safety_service.py       Crisis override + response length control
│       └── screening_service.py    PHQ-2 / GAD-2 normalization
├── components/
│   ├── chat_ui.py                  Streamlit chat panel + voice mode
│   └── dashboard.py                MHI dashboard with trend chart
├── models/
│   ├── crisis/                     Fine-tuned DistilBERT (crisis)
│   └── emotion/                    Fine-tuned DistilBERT (emotion)
├── main.py                         FastAPI application entry point
├── app.py                          Streamlit frontend entry point
└── requirements.txt
```

---

## Requirements

- Python 3.10 or higher
- MongoDB Atlas account (free tier works) or local MongoDB
- 4 GB RAM minimum (8 GB recommended for Whisper base model)
- Internet access for gTTS (TTS only) — all other processing is local

### Model requirements

The fine-tuned DistilBERT models must be present at:

```
models/
├── crisis/          (DistilBERT fine-tuned for crisis detection)
└── emotion/         (DistilBERT fine-tuned for emotion classification)
```

If the folders are absent the system falls back to keyword/regex detection automatically.

---

## Installation

### Step 1 — Clone the repository

```bash
git clone https://github.com/your-username/mental-wellbeing-assistant.git
cd mental-wellbeing-assistant
```

### Step 2 — Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

`requirements.txt` should contain:

```
fastapi
uvicorn
motor
pydantic
pydantic-settings
python-jose[cryptography]
passlib[bcrypt]
python-multipart
sentence-transformers
faiss-cpu
torch
transformers
faster-whisper
gtts
pydub
streamlit
streamlit-extras
plotly
fpdf2
requests
```

### Step 4 — Configure environment variables

Create a `.env` file in the project root:

```env
# MongoDB
MONGO_URI=mongodb+srv://<user>:<password>@cluster.mongodb.net/?retryWrites=true
MONGO_DB_NAME=mental_health_db

# JWT
JWT_SECRET_KEY=your-secret-key-at-least-32-characters
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# App
APP_NAME=Smart Mental Well-Being Assistant
APP_VERSION=2.0.0
DEBUG=false

# MHI thresholds
CRISIS_PROBABILITY_THRESHOLD=0.55
SAFETY_OVERRIDE_THRESHOLD=0.85

# MHI weights (must sum to a consistent ratio, not necessarily 1.0)
WEIGHT_EMOTION=0.25
WEIGHT_CRISIS=0.35
WEIGHT_SCREENING=0.15
WEIGHT_BEHAVIORAL=0.15
WEIGHT_HISTORY=0.10

# Whisper model size: tiny (39 MB) | base (74 MB) | small (244 MB)
# tiny  = fastest, good for most Indian accents
# base  = better accuracy for heavy regional accents
# small = best accuracy, slower on CPU
WHISPER_MODEL_SIZE=tiny
```

### Step 5 — Build the RAG index

If you have a CBT knowledge base (text files or PDFs):

```bash
python scripts/build_index.py --input data/cbt_docs/ --output backend/rag/
```

If you do not have a knowledge base yet, the RAG service will retrieve zero chunks and the LLM will respond from its own knowledge with the safety constraints still active.

### Step 6 — Set up the LLM

**Option A — Ollama (free, local, recommended)**

```bash
# Install Ollama from https://ollama.ai
ollama pull llama3
# or for a smaller model:
ollama pull phi3
```

In `backend/services/llm_service.py`, set the Ollama endpoint:

```python
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME  = "llama3"
```

**Option B — OpenAI API**

```env
OPENAI_API_KEY=sk-...
```

### Step 7 — Run the backend

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`.
Interactive API documentation is at `http://localhost:8000/docs`.

### Step 8 — Run the frontend

```bash
streamlit run app.py
```

The frontend will open in your browser at `http://localhost:8501`.

---

## Multilingual Voice Setup

No additional configuration is needed. The system uses:

- **faster-whisper** for speech-to-text with automatic language detection
- **gTTS** for text-to-speech with Indian accent routing
- **pydub** for emotion-matched audio speed adjustment

On first use, faster-whisper will download the Whisper model automatically (~39 MB for `tiny`). This requires an internet connection once.

### How language detection works

When a user speaks, faster-whisper runs one forward pass that simultaneously:

1. Detects the language from the first 30 seconds of audio
2. Transcribes the full audio in the detected language

The language code (e.g., `hi` for Hindi) is then:

- Returned in the `/voice/transcribe` API response
- Passed to the LLM as a prompt instruction: "Respond in Hindi"
- Passed to gTTS to produce speech in the correct language with the correct accent

The user does not need to select a language. The system adapts automatically each turn.

### Supported Indian languages

| Language   | Code | Script     |
|------------|------|------------|
| Hindi      | hi   | Devanagari |
| Bengali    | bn   | Bengali    |
| Tamil      | ta   | Tamil      |
| Telugu     | te   | Telugu     |
| Marathi    | mr   | Devanagari |
| Gujarati   | gu   | Gujarati   |
| Punjabi    | pa   | Gurmukhi   |
| Kannada    | kn   | Kannada    |
| Malayalam  | ml   | Malayalam  |
| Urdu       | ur   | Arabic     |
| Odia       | or   | Odia       |
| Assamese   | as   | Bengali    |
| Nepali     | ne   | Devanagari |
| English    | en   | Latin (Indian accent) |

---

## API Reference

### POST /chat

Processes a text message through the full ML pipeline.

**Request**
```json
{ "message": "I have been feeling very low lately" }
```

**Response**
```json
{
    "response":       "It sounds like things have been really difficult...",
    "emotion_scores": {"sadness": 0.72, "anxiety": 0.18, "neutral": 0.06, ...},
    "crisis_score":   0.12,
    "crisis_tier":    "distress",
    "intent":         "emotional_support",
    "mhi":            54,
    "category":       "Moderate Distress"
}
```

### POST /voice/transcribe

Transcribes audio and detects the spoken language.

**Request**: multipart/form-data with `audio` field (WebM/OGG/WAV/MP4)

**Response**
```json
{
    "transcript":    "मुझे बहुत बुरा लग रहा है",
    "language_code": "hi",
    "language_name": "Hindi",
    "confidence":    0.97
}
```

`transcript` is empty string for silence — HTTP 200 is returned regardless.

### POST /voice/speak

Synthesizes speech in the specified language with Indian accent.

**Request**
```json
{
    "text":          "यह सुनकर दुख हुआ",
    "language_code": "hi",
    "emotion_label": "sadness",
    "crisis_tier":   "none"
}
```

**Response**: audio/mpeg (gTTS) or audio/wav (pyttsx3 fallback)

### POST /assessment

Submits PHQ-2 and GAD-2 scores.

**Request**
```json
{ "phq2": 3, "gad2": 4 }
```

### GET /user/timeline

Returns MHI scores over time for the dashboard chart.

**Response**
```json
[
    {"timestamp": "2025-01-15T10:23:00", "mhi": 72, "category": "Mild Stress", "crisis_tier": "none"},
    ...
]
```

---

## Crisis Safety System

The safety system operates in layers:

**Layer 1 — Crisis detection** runs before any LLM call. The CrisisService combines a fine-tuned DistilBERT model with regex pattern matching. The higher severity result always wins.

**Layer 2 — Early exit** in the `/chat` route. If `crisis_tier` is `active` or `passive`, the LLM is never called. A predefined, clinically reviewed response template is returned immediately with helpline numbers.

**Layer 3 — Response validation** runs on all non-crisis LLM output. It checks for blocked content patterns, trims to the appropriate length for the risk category, and appends professional referral language for distress-tier responses.

**Layer 4 — MHI hard ceilings** ensure that crisis language can never produce a high MHI score regardless of other factors.

**Helplines included in crisis responses:**
- AASRA: +91-9820466626
- iCall: +91-9152987821
- Kiran Mental Health (free, 24/7): 1800-599-0019
- Vandrevala Foundation: +91-1860-2662-345

---

## Configuration Reference

All thresholds are configurable via environment variables. Key settings:

| Variable | Default | Description |
|---|---|---|
| `CRISIS_PROBABILITY_THRESHOLD` | 0.55 | Score above which passive crisis template is used |
| `SAFETY_OVERRIDE_THRESHOLD` | 0.85 | Score above which active crisis template is used |
| `WHISPER_MODEL_SIZE` | tiny | Whisper model: tiny / base / small |
| `WEIGHT_CRISIS` | 0.35 | Crisis score weight in MHI computation |
| `WEIGHT_EMOTION` | 0.25 | Emotion score weight in MHI computation |

---

## Limitations

- The system is not a replacement for professional mental health care.
- The LLM may occasionally produce responses that do not perfectly follow the language instruction for less common languages. Crisis responses are hardcoded in English and the detected language simultaneously for safety.
- Whisper `tiny` model may have reduced accuracy for heavy regional accents. Use `base` or `small` via the `WHISPER_MODEL_SIZE` environment variable for better results.
- gTTS requires an internet connection for TTS. The pyttsx3 fallback works offline but has limited Indian language support depending on installed OS voices.
- The fine-tuned models in `models/crisis/` and `models/emotion/` are not included in this repository due to size. Instructions for training or obtaining them are in `docs/model_training.md`.

---

## Contributing

Pull requests are welcome. For significant changes, open an issue first to discuss the proposed change. When contributing to the crisis detection or safety systems, include test cases with example phrases and expected outputs.

---

## License

This project is released under the MIT License. See `LICENSE` for details.

---

## Disclaimer

This software is provided for educational and research purposes. It is not a licensed medical device and should not be used as a substitute for professional mental health diagnosis or treatment. If you or someone you know is in crisis, please contact a qualified mental health professional or call a crisis helpline immediately.