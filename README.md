# Smart Mental Well-Being Assistant

A full-stack mental health support system combining clinical screening tools, real-time emotion and crisis detection, CBT-guided AI responses, multilingual voice interaction, and an MHI (Mental Health Index) tracking dashboard. Built for the Indian context with support for 14 languages.

---

## Overview

This system processes a user's text or speech input through a multi-layer ML pipeline that detects emotion, assesses crisis risk, computes a Mental Health Index score, and generates a response calibrated to the user's current state. All heavy computation runs locally. No patient data is sent to external services except the LLM.

The architecture is designed around one core principle: **safety before helpfulness**. Crisis detection runs before the LLM is ever called. For active suicidal language, the system bypasses the LLM entirely and returns a predefined, helpline-inclusive response.

The frontend has been fully migrated from Streamlit to a modern **React + TypeScript + Tailwind CSS** single-page application with Google OAuth authentication, a real-time voice interface, and a responsive dashboard.

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
- Browser-native speech-to-text via Web Speech API (any language, no server round-trip)
- Supported Indian languages: Hindi, Bengali, Tamil, Telugu, Marathi, Gujarati, Punjabi, Kannada, Malayalam, Urdu, Odia, Assamese, Nepali, and English

**Dashboard**
- Real-time MHI trend chart with seven-day stability curve
- Session statistics: emotion distribution, weekly check-ins, streak tracking
- PHQ-2/GAD-2 screening integration with live score sliders

**Authentication**
- Google OAuth 2.0 via `@react-oauth/google`
- JWT tokens stored in localStorage, refreshed on page load
- Per-user conversation history and MHI timeline stored in MongoDB

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
│   │   ├── auth_router.py          Google OAuth + JWT authentication routes
│   │   └── auth_utils.py           JWT encoding, decoding, and user helpers
│   ├── config.py                   Pydantic settings (env vars)
│   ├── database/
│   │   ├── mongo_client.py         Async MongoDB client (motor) with sync fallback
│   │   └── schemas.py              Pydantic request/response models
│   ├── dependencies.py             FastAPI dependency injection (get_current_user)
│   ├── main.py                     FastAPI application entry point
│   ├── models/
│   │   ├── crisis/                 Fine-tuned DistilBERT (crisis detection)
│   │   └── emotion/                Fine-tuned DistilBERT (emotion classification)
│   ├── rag/
│   │   ├── faiss_index.index       FAISS vector index (CBT knowledge)
│   │   ├── metadata.json           Chunk metadata for retrieved docs
│   │   └── cbt_documents/          Source CBT text documents
│   ├── routes/
│   │   └── routes_report.py        PDF report generation
│   └── services/
│       ├── behavioral_service.py   Regex-based behavioral risk scoring
│       ├── crisis_service.py       DistilBERT crisis detection + regex
│       ├── emotion_service.py      DistilBERT emotion classification
│       ├── history_service.py      Session history risk trend
│       ├── intent_service.py       Intent classification
│       ├── matrix_service.py       MHI computation and categorization
│       ├── multilingual_voice_service.py  Multilingual STT + TTS
│       ├── rag_service.py          FAISS retrieval + LLM prompt builder
│       ├── safety_service.py       Crisis override + response length control
│       └── screening_service.py    PHQ-2 / GAD-2 normalization
│
├── frontend/                       React + TypeScript SPA (Vite)
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── chat/
│   │   │   │   ├── Composer.tsx        Message input with suggestion chips
│   │   │   │   ├── ConversationPanel.tsx  Chat bubble timeline
│   │   │   │   └── VoiceOrb.tsx        Browser Web Speech API voice input
│   │   │   ├── dashboard/
│   │   │   │   ├── EmotionPanel.tsx    Emotion signal bar chart
│   │   │   │   ├── MetricCard.tsx      Single KPI card with accent color
│   │   │   │   ├── SessionPanel.tsx    Recent session snapshot list
│   │   │   │   └── TrendPanel.tsx      Seven-day MHI SVG line chart
│   │   │   ├── layout/
│   │   │   │   └── AppShell.tsx        Sidebar navigation + page wrapper
│   │   │   └── shared/
│   │   │       └── PageHeader.tsx      Reusable page eyebrow + title header
│   │   ├── lib/
│   │   │   ├── api.ts              All FastAPI endpoint calls (typed)
│   │   │   └── auth.ts             AuthContext, useAuth hook, Google OAuth flow
│   │   ├── pages/
│   │   │   ├── ChatPage.tsx        Chat interface with voice + text
│   │   │   ├── DashboardPage.tsx   MHI dashboard with metrics and trends
│   │   │   ├── LoginPage.tsx       Google sign-in landing page
│   │   │   ├── ProfilePage.tsx     User identity and account details
│   │   │   └── SettingsPage.tsx    Preferences and account controls
│   │   ├── types/
│   │   │   └── index.ts            Shared TypeScript interfaces
│   │   ├── App.tsx                 Router setup and auth-gated routes
│   │   ├── main.tsx                React entry point
│   │   └── styles.css              Global styles and Tailwind directives
│   ├── .env.local                  Frontend environment variables
│   ├── index.html
│   ├── package.json
│   ├── tailwind.config.js          Custom color tokens and font families
│   ├── tsconfig.json
│   └── vite.config.ts
│
├── .env                            Backend environment variables
├── migrate_schema.py               MongoDB index and schema migration script
├── requirements.txt                Python dependencies
└── README.md
```

---

## Tech Stack

### Backend
| Layer | Technology |
|---|---|
| API framework | FastAPI + Uvicorn |
| Database | MongoDB Atlas via Motor (async) |
| Authentication | Google OAuth 2.0 + JWT (python-jose) |
| Emotion/Crisis ML | DistilBERT (fine-tuned, HuggingFace Transformers) |
| Speech-to-text | faster-whisper (local, 99 languages) |
| Text-to-speech | gTTS (Indian accent) + pyttsx3 (offline fallback) |
| RAG | FAISS + sentence-transformers |
| LLM | Gemini via Google AI SDK |

### Frontend
| Layer | Technology |
|---|---|
| Framework | React 18 + TypeScript |
| Build tool | Vite |
| Styling | Tailwind CSS with custom design tokens |
| Routing | React Router v6 |
| Auth | @react-oauth/google |
| Voice input | Web Speech API (browser-native, auto language detection) |
| Icons | lucide-react |
| HTTP client | Native fetch (typed wrappers in `src/lib/api.ts`) |

---

## Requirements

- Python 3.10 or higher
- Node.js 18 or higher
- MongoDB Atlas account (free tier works) or local MongoDB
- 4 GB RAM minimum (8 GB recommended for Whisper base model)
- Internet access for gTTS (TTS only) and Google OAuth — all other processing is local

### Model requirements

The fine-tuned DistilBERT models must be present at:

```
backend/models/
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

### Step 2 — Backend setup

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

### Step 3 — Frontend setup

```bash
cd frontend
npm install
```

### Step 4 — Configure backend environment variables

Create a `.env` file in the project root:

```env
# MongoDB
MONGO_URI=mongodb+srv://<user>:<password>@cluster.mongodb.net/smart_mental_health?retryWrites=true&w=majority
MONGO_DB_NAME=smart_mental_health

# JWT
JWT_SECRET=your-secret-key-at-least-32-characters
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback
FRONTEND_URL=http://localhost:5173

# LLM
GEMINI_API_KEY=your-gemini-api-key
LLM_MODEL=gemini-2.5-flash-lite

# App
APP_NAME=Smart Mental Well-Being Assistant
APP_VERSION=2.0.0
DEBUG=false

# MHI thresholds
CRISIS_PROBABILITY_THRESHOLD=0.65
SAFETY_OVERRIDE_THRESHOLD=0.80

# MHI weights
WEIGHT_EMOTION=0.30
WEIGHT_CRISIS=0.25
WEIGHT_SCREENING=0.20
WEIGHT_BEHAVIORAL=0.10
WEIGHT_HISTORY=0.15

# Whisper model size: tiny | base | small
WHISPER_MODEL_SIZE=tiny
```

### Step 5 — Configure frontend environment variables

Create a `.env.local` file inside the `frontend/` folder:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
```

### Step 6 — Build the RAG index (optional)

If you have a CBT knowledge base (text files or PDFs):

```bash
python scripts/build_index.py --input data/cbt_docs/ --output backend/rag/
```

If you do not have a knowledge base yet, the RAG service will retrieve zero chunks and the LLM will respond from its own knowledge with the safety constraints still active.

### Step 7 — Run the backend

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`.  
Interactive API documentation is at `http://localhost:8000/docs`.

### Step 8 — Run the frontend

```bash
cd frontend
npm run dev
```

The React app will open at `http://localhost:5173`.

---

## Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select an existing one
3. Navigate to **APIs & Services → Credentials**
4. Click **Create Credentials → OAuth 2.0 Client ID**
5. Set application type to **Web application**
6. Add `http://localhost:5173` to **Authorised JavaScript origins**
7. Add `http://localhost:8000/auth/google/callback` to **Authorised redirect URIs**
8. Copy the **Client ID** and **Client Secret** into your `.env` and `frontend/.env.local`

---

## Multilingual Voice Setup

No additional configuration is needed. The system uses two independent voice paths:

**Browser-side (VoiceOrb component)**
- Uses the Web Speech API built into Chrome and Edge
- Auto-detects the spoken language — no selection needed
- Transcript is appended directly into the message composer
- Works in Hindi, English, and most Indian languages
- Not supported in Firefox (gracefully disabled with a status message)

**Server-side (POST /voice/transcribe)**
- Uses faster-whisper running locally for high-accuracy transcription
- Supports all 99 Whisper languages including all 14 supported Indian languages
- On first use, faster-whisper downloads the model (~39 MB for `tiny`)

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

### POST /auth/google

Exchanges a Google credential token for a JWT access token.

**Request**
```json
{ "credential": "google-id-token-here" }
```

**Response**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "email": "user@gmail.com",
    "name": "Ayush Singh",
    "picture": "https://..."
  }
}
```

### POST /chat

Processes a text message through the full ML pipeline.

**Request**
```json
{ "message": "I have been feeling very low lately", "language_code": "en", "source": "text" }
```

**Response**
```json
{
  "response":       "It sounds like things have been really difficult...",
  "emotion_scores": {"sadness": 0.72, "anxiety": 0.18, "neutral": 0.06},
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

**Response**: `audio/mpeg` (gTTS) or `audio/wav` (pyttsx3 fallback)

### POST /assessment

Submits PHQ-2 and GAD-2 scores.

**Request**
```json
{ "phq2": 3, "gad2": 4 }
```

### GET /user/dashboard-summary

Returns a full snapshot for the React dashboard including MHI, emotion mix, weekly trend, and recent sessions.

### GET /user/timeline

Returns MHI scores over time for the trend chart.

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

All thresholds are configurable via environment variables.

| Variable | Default | Description |
|---|---|---|
| `CRISIS_PROBABILITY_THRESHOLD` | 0.65 | Score above which passive crisis template is used |
| `SAFETY_OVERRIDE_THRESHOLD` | 0.80 | Score above which active crisis template is used |
| `WHISPER_MODEL_SIZE` | tiny | Whisper model: tiny / base / small |
| `WEIGHT_CRISIS` | 0.25 | Crisis score weight in MHI computation |
| `WEIGHT_EMOTION` | 0.30 | Emotion score weight in MHI computation |
| `WEIGHT_SCREENING` | 0.20 | PHQ-2/GAD-2 weight in MHI computation |
| `WEIGHT_BEHAVIORAL` | 0.10 | Behavioral score weight in MHI computation |
| `WEIGHT_HISTORY` | 0.15 | Session history weight in MHI computation |

---

## Limitations

- The system is not a replacement for professional mental health care.
- The LLM may occasionally produce responses that do not perfectly follow the language instruction for less common languages. Crisis responses are hardcoded in English and the detected language simultaneously for safety.
- Whisper `tiny` model may have reduced accuracy for heavy regional accents. Use `base` or `small` via the `WHISPER_MODEL_SIZE` environment variable for better results.
- The browser Web Speech API for voice input is only supported in Chrome and Edge. Firefox users will see a graceful fallback message.
- gTTS requires an internet connection for TTS. The pyttsx3 fallback works offline but has limited Indian language support depending on installed OS voices.
- The fine-tuned models in `backend/models/crisis/` and `backend/models/emotion/` are not included in this repository due to size. Instructions for training or obtaining them are in `docs/model_training.md`.

---

## Contributing

Pull requests are welcome. For significant changes, open an issue first to discuss the proposed change. When contributing to the crisis detection or safety systems, include test cases with example phrases and expected outputs.

---

## License

This project is released under the MIT License. See `LICENSE` for details.

---

## Disclaimer

This software is provided for educational and research purposes. It is not a licensed medical device and should not be used as a substitute for professional mental health diagnosis or treatment. If you or someone you know is in crisis, please contact a qualified mental health professional or call a crisis helpline immediately.