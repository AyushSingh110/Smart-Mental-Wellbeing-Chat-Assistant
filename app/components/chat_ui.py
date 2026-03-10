"""
chat_ui.py  —  Voice-Only Mental Well-Being Companion
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Changes vs chat_ui_v4.py
─────────────────────────
1. TEXT MODE REMOVED ENTIRELY.
   No tabs, no chat input box, no text mode button.
   The entire UI is the voice panel.

2. INTERRUPT SUPPORT.
   While the AI is speaking, a background SpeechRecognition
   instance watches for ANY voice activity onset. The moment
   the browser detects it (onstart fires, sub-100ms), the
   current Audio element is paused synchronously. The user's
   full utterance is then captured by MediaRecorder and
   processed normally. The AI never finishes a sentence once
   the user starts speaking.

3. LANGUAGE DETECTION + MATCHING.
   /voice/transcribe now returns language_code, language_name,
   confidence alongside transcript. This is stored as sessionLang.
   /voice/speak is called with that language_code so gTTS picks
   the correct Indian-language voice. The Web Speech API fallback
   uses the matching BCP-47 locale. Language badge updates live.

4. FRIENDLY THERAPIST PERSONA.
   Warm, informal greeting. The AI sounds like a trusted friend
   who happens to know CBT — not a clinical bot. See rag_service.py
   for the matching system prompt changes.

5. DASHBOARD SYNC.
   Identical postMessage → hidden input → st.rerun() mechanism
   from v4, carried forward unchanged.
"""
from __future__ import annotations

import json
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components

BACKEND_URL = "http://localhost:8000"

# ── BCP-47 map for Web Speech API fallback ─────────────────────────────────────
_BCP47 = {
    "hi": "hi-IN", "bn": "bn-IN", "ta": "ta-IN", "te": "te-IN",
    "mr": "mr-IN", "gu": "gu-IN", "pa": "pa-IN", "kn": "kn-IN",
    "ml": "ml-IN", "ur": "ur-PK", "or": "or-IN", "as": "as-IN",
    "ne": "ne-NP", "sa": "hi-IN", "en": "en-IN",
}

# ── Emotion → Web Speech rate/pitch/volume ─────────────────────────────────────
_WEB_SPEECH_PROFILES = {
    "crisis":  {"rate": 0.76, "pitch": 0.93, "volume": 1.0},
    "sadness": {"rate": 0.82, "pitch": 0.97, "volume": 0.95},
    "fear":    {"rate": 0.83, "pitch": 0.99, "volume": 0.95},
    "anxiety": {"rate": 0.84, "pitch": 1.00, "volume": 0.95},
    "anger":   {"rate": 0.82, "pitch": 0.96, "volume": 0.90},
    "stress":  {"rate": 0.85, "pitch": 1.00, "volume": 0.95},
    "neutral": {"rate": 0.90, "pitch": 1.02, "volume": 1.00},
    "default": {"rate": 0.88, "pitch": 1.02, "volume": 1.00},
}

# ── CSS injected into Streamlit main page ─────────────────────────────────────
_CSS = """
<style>
/* Hide the hidden sync input completely */
div[data-testid="stTextInput"]:has(input[aria-label="__vsync_v5__"]),
div[data-testid="stTextInput"]:has(input[aria-label="__vsync_v5__"]) * {
    position:absolute!important;width:1px!important;height:1px!important;
    overflow:hidden!important;opacity:0!important;pointer-events:none!important;
}
/* Remove default Streamlit padding so voice panel fills nicely */
.block-container { padding-top: 1rem !important; padding-bottom: 0 !important; }
</style>
"""

# ── postMessage listener injected into the main Streamlit page ────────────────
# Runs at top-level (NOT inside an iframe) so it can access parent DOM.
_LISTENER_SCRIPT = """
<script>
(function(){
    if(window.__vSyncV5) return;
    window.__vSyncV5 = true;
    window.addEventListener('message', function(ev){
        if(!ev.data || ev.data.type !== 'VOICE_TURN_V5') return;
        try {
            var payload = JSON.stringify(ev.data);
            var inputs  = document.querySelectorAll('input[type="text"]');
            for(var i=0; i<inputs.length; i++){
                if(inputs[i].getAttribute('aria-label') === '__vsync_v5__'){
                    var setter = Object.getOwnPropertyDescriptor(
                        window.HTMLInputElement.prototype, 'value').set;
                    setter.call(inputs[i], payload);
                    inputs[i].dispatchEvent(new Event('input',  {bubbles:true}));
                    inputs[i].dispatchEvent(new Event('change', {bubbles:true}));
                    break;
                }
            }
        } catch(e){ console.debug('vsync-v5 error', e); }
    });
})();
</script>
"""


def _build_voice_panel(backend_url: str, jwt: str) -> str:
    """
    Builds the complete self-contained voice panel HTML.
    All JS runs inside this iframe — no external deps except Google Fonts.
    """
    profiles_json = json.dumps(_WEB_SPEECH_PROFILES)
    bcp47_json    = json.dumps(_BCP47)
    cat_colors    = json.dumps({
        "Stable":            "#48bb78",
        "Mild Stress":       "#68d391",
        "Moderate Distress": "#ed8936",
        "Depression Risk":   "#fc8181",
        "High Risk":         "#f56565",
        "Crisis Risk":       "#fc4e4e",
    })

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
/* ── Reset ── */
*{{margin:0;padding:0;box-sizing:border-box;}}
html,body{{
    font-family:'Sora',sans-serif;
    background:radial-gradient(ellipse at 50% 0%, #0c1829 0%, #060c18 68%);
    color:#e8edf5;width:100%;min-height:100vh;overflow-x:hidden;scroll-behavior:smooth;
}}

/* ── Orb ── */
.orb-wrap{{display:flex;flex-direction:column;align-items:center;padding:24px 0 10px;gap:12px;}}
.orb{{
    width:106px;height:106px;border-radius:50%;cursor:pointer;border:none;outline:none;
    position:relative;flex-shrink:0;
    background:radial-gradient(circle at 38% 32%, #63b3ed 0%, #4fd1c5 48%, #7c3aed 100%);
    animation:orbIdle 4.5s ease-in-out infinite;
    transition:transform .13s ease;
}}
.orb:hover{{transform:scale(1.05);}}
.orb:active{{transform:scale(0.96);}}
.orb.listening{{
    background:radial-gradient(circle at 38% 32%, #fc8181 0%, #f6ad55 48%, #fc4e4e 100%)!important;
    animation:orbListen .65s ease-in-out infinite!important;
}}
.orb.thinking{{
    background:radial-gradient(circle at 38% 32%, #b794f4 0%, #7c3aed 48%, #553c9a 100%)!important;
    animation:orbThink 1.1s ease-in-out infinite!important;
}}
.orb.speaking{{
    animation:orbSpeak .75s ease-in-out infinite!important;
}}
@keyframes orbIdle{{
    0%,100%{{box-shadow:0 0 0 0 rgba(99,179,237,0),0 14px 44px rgba(99,179,237,.18);transform:scale(1);}}
    42%    {{box-shadow:0 0 0 10px rgba(99,179,237,.06),0 14px 52px rgba(79,209,197,.26);transform:scale(1.04);}}
    78%    {{box-shadow:0 0 0 5px rgba(79,209,197,.04),0 14px 48px rgba(99,179,237,.20);transform:scale(1.02);}}
}}
@keyframes orbListen{{
    0%,100%{{box-shadow:0 0 0 0 rgba(252,129,129,.82);transform:scale(1);}}
    50%    {{box-shadow:0 0 0 28px rgba(252,129,129,0);transform:scale(1.13);}}
}}
@keyframes orbThink{{
    0%,100%{{box-shadow:0 0 0 0 rgba(183,148,244,.72);transform:scale(1);}}
    50%    {{box-shadow:0 0 0 24px rgba(183,148,244,0);transform:scale(1.08);}}
}}
@keyframes orbSpeak{{
    0%,100%{{box-shadow:0 0 0 0 rgba(99,179,237,.82);transform:scale(1.02);}}
    50%    {{box-shadow:0 0 0 26px rgba(99,179,237,0);transform:scale(1.13);}}
}}

/* Wave bars inside orb */
.orb-waves{{
    display:none;position:absolute;bottom:20px;left:50%;
    transform:translateX(-50%);align-items:flex-end;gap:3px;height:24px;
}}
.orb.listening .orb-waves{{display:flex;}}
.ow{{width:3px;border-radius:2px;background:rgba(255,255,255,.92);height:4px;
     animation:owAnim .58s ease-in-out infinite;}}
.ow:nth-child(1){{animation-delay:.00s}} .ow:nth-child(2){{animation-delay:.10s}}
.ow:nth-child(3){{animation-delay:.20s}} .ow:nth-child(4){{animation-delay:.30s}}
.ow:nth-child(5){{animation-delay:.20s}} .ow:nth-child(6){{animation-delay:.10s}}
.ow:nth-child(7){{animation-delay:.00s}}
@keyframes owAnim{{0%,100%{{height:4px;opacity:.45;}}50%{{height:22px;opacity:1;}}}}

/* Status text */
.orb-status{{
    font-size:.66rem;color:#8fa2bc;letter-spacing:.10em;
    text-transform:uppercase;min-height:18px;text-align:center;
    transition:color .3s;
}}

/* Language badge */
.lang-badge{{
    display:none;align-items:center;gap:7px;
    padding:5px 14px;border-radius:22px;
    background:rgba(79,209,197,.08);border:1px solid rgba(79,209,197,.22);
    font-size:.64rem;color:#4fd1c5;letter-spacing:.05em;
    animation:fadeUp .3s ease;
}}
.lang-badge.show{{display:flex;}}
.lang-dot{{
    width:6px;height:6px;border-radius:50%;background:#4fd1c5;
    animation:ldPulse 2.2s ease-in-out infinite;
}}
@keyframes ldPulse{{0%,100%{{opacity:.30;transform:scale(1);}}50%{{opacity:1;transform:scale(1.4);}}}}

/* Controls */
.controls{{display:flex;gap:10px;padding:0 16px 12px;}}
.ctrl-btn{{
    flex:1;padding:10px 0;border:none;border-radius:11px;
    font-family:'Sora',sans-serif;font-size:.71rem;font-weight:600;
    letter-spacing:.04em;cursor:pointer;transition:opacity .15s,transform .12s,box-shadow .2s;
}}
.ctrl-btn:hover{{opacity:.80;}} .ctrl-btn:active{{transform:scale(.97);}}
.ctrl-btn:focus-visible{{outline:none;box-shadow:0 0 0 3px rgba(99,179,237,.25);}}
.btn-start{{background:linear-gradient(135deg,#2a6496,#1a7a6e);color:#d6f0ff;}}
.btn-stop {{background:rgba(252,129,129,.14);color:#fc8181;border:1px solid rgba(252,129,129,.28);}}
.btn-mute {{background:rgba(255,255,255,.05);color:#718096;border:1px solid rgba(255,255,255,.08);}}

/* Crisis banner */
.crisis-bar{{
    margin:0 14px 10px;padding:10px 14px;border-radius:11px;
    font-size:.72rem;line-height:1.6;display:none;
}}
.crisis-bar.show{{display:block;animation:fadeUp .3s ease;}}
.crisis-bar.passive{{background:rgba(237,137,54,.09);border:1px solid rgba(237,137,54,.28);color:#ed8936;}}
.crisis-bar.active {{background:rgba(252,78,78,.11); border:1px solid rgba(252,78,78,.32); color:#fc8181;}}

/* Transcript */
.transcript{{
    margin:0 14px 10px;
    border:1px solid rgba(255,255,255,.06);border-radius:16px;
    background:rgba(10,19,34,.74);backdrop-filter:blur(10px);
    overflow-y:auto;max-height:290px;padding:12px;scroll-behavior:smooth;
    transition:border-color .2s ease, box-shadow .2s ease;
}}
.transcript:hover{{border-color:rgba(99,179,237,.2);box-shadow:inset 0 0 0 1px rgba(255,255,255,.03);}}
.transcript::-webkit-scrollbar{{width:3px;}}
.transcript::-webkit-scrollbar-thumb{{background:rgba(255,255,255,.08);border-radius:2px;}}

/* Turns */
.turn{{margin-bottom:13px;animation:fadeUp .28s ease;}}
.turn-row{{display:flex;align-items:flex-start;gap:9px;}}
.turn-row.user-row{{flex-direction:row-reverse;}}
.avatar{{
    width:28px;height:28px;border-radius:50%;flex-shrink:0;
    display:flex;align-items:center;justify-content:center;
    font-size:.56rem;font-weight:700;letter-spacing:.02em;
}}
.avatar-ai  {{background:linear-gradient(135deg,#1a3050,#0d2840);color:#4fd1c5;border:1px solid rgba(79,209,197,.22);}}
.avatar-user{{background:linear-gradient(135deg,#1e3a5f,#162d4a);color:#63b3ed;border:1px solid rgba(99,179,237,.22);}}
.bubble{{max-width:81%;padding:9px 13px;font-size:.79rem;line-height:1.65;word-break:break-word;}}
.bubble-ai  {{background:rgba(20,28,50,.92);border:1px solid rgba(255,255,255,.07);
              border-radius:4px 14px 14px 14px;color:#c8d4e6;}}
.bubble-user{{background:rgba(28,52,90,.88);border:1px solid rgba(99,179,237,.16);
              border-radius:14px 4px 14px 14px;color:#bdd4f0;}}
.turn-meta{{font-size:.58rem;color:#8fa2bc;margin-top:4px;display:flex;align-items:center;gap:5px;}}
.turn-row.user-row .turn-meta{{justify-content:flex-end;}}
.meta-dot{{width:4px;height:4px;border-radius:50%;}}
.lang-tag{{
    font-size:.55rem;padding:1px 6px;border-radius:10px;
    background:rgba(79,209,197,.08);border:1px solid rgba(79,209,197,.18);color:#4fd1c5;
}}

/* Footer hint */
.panel-hint{{
    text-align:center;font-size:.62rem;color:#8fa2bc;
    letter-spacing:.06em;padding-bottom:12px;
}}

@media (max-width: 560px) {{
    .orb{{width:92px;height:92px;}}
    .controls{{flex-direction:column;padding:0 14px 10px;gap:8px;}}
    .ctrl-btn{{padding:9px 0;font-size:.68rem;}}
    .transcript{{max-height:250px;margin:0 10px 10px;padding:10px;}}
    .bubble{{max-width:88%;font-size:.75rem;}}
    .panel-hint{{padding:0 10px 10px;line-height:1.5;}}
}}

@media (prefers-reduced-motion: reduce) {{
    *{{animation:none !important;transition:none !important;scroll-behavior:auto !important;}}
}}

@keyframes fadeUp{{from{{opacity:0;transform:translateY(5px);}}to{{opacity:1;transform:translateY(0);}}}}
</style>
</head>
<body>

<div class="orb-wrap">
    <button class="orb" id="orb">
        <div class="orb-waves">
            <div class="ow"></div><div class="ow"></div><div class="ow"></div>
            <div class="ow"></div><div class="ow"></div><div class="ow"></div>
            <div class="ow"></div>
        </div>
    </button>
    <div class="lang-badge" id="langBadge">
        <div class="lang-dot"></div>
        <span id="langText">Detecting…</span>
    </div>
    <div class="orb-status" id="orbStatus">Tap Start or press the orb to begin</div>
</div>

<div class="controls">
    <button class="ctrl-btn btn-start" id="btnStart">&#9654;&nbsp;Start</button>
    <button class="ctrl-btn btn-stop"  id="btnStop">&#9632;&nbsp;Stop</button>
    <button class="ctrl-btn btn-mute"  id="btnMute">&#128263;&nbsp;Mute</button>
</div>

<div class="crisis-bar" id="crisisBar"></div>
<div class="transcript"  id="transcript"></div>
<div class="panel-hint">Speak naturally &nbsp;&#183;&nbsp; interrupt anytime &nbsp;&#183;&nbsp; any language</div>

<script>
(function(){{

/* ── Config ── */
const BACKEND    = "{backend_url}";
const JWT        = "{jwt}";
const PROFILES   = {profiles_json};
const BCP47      = {bcp47_json};
const CAT_COLORS = {cat_colors};

/* ── DOM ── */
const orb        = document.getElementById('orb');
const orbStatus  = document.getElementById('orbStatus');
const langBadge  = document.getElementById('langBadge');
const langText   = document.getElementById('langText');
const transcript = document.getElementById('transcript');
const crisisBar  = document.getElementById('crisisBar');
const btnStart   = document.getElementById('btnStart');
const btnStop    = document.getElementById('btnStop');
const btnMute    = document.getElementById('btnMute');

/* ── State ── */
let recorder      = null;
let audioChunks   = [];
let micStream     = null;
let isListening   = false;
let isProcessing  = false;
let isMuted       = false;
let continuous    = false;

// The currently playing Audio element — so we can interrupt it instantly
let currentAudio  = null;

// Language state — updated by Whisper detection each turn
let sessionLang     = 'en';
let sessionLangName = 'English';

// SpeechRecognition API — used ONLY for interrupt detection while AI speaks
const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
let interruptSR   = null;
let interruptDone = false;

/* ── Helpers ── */
function setStatus(t) {{ orbStatus.textContent = t; }}
function setOrb(s)    {{ orb.classList.remove('listening','thinking','speaking'); if(s) orb.classList.add(s); }}
function hhmm()       {{ return new Date().toLocaleTimeString([],{{hour:'2-digit',minute:'2-digit'}}); }}

function updateLangBadge(name, conf) {{
    const pct = conf > 0 ? ' \u00b7 ' + Math.round(conf*100) + '%' : '';
    langText.textContent = name + pct;
    langBadge.classList.add('show');
}}

function esc(s) {{
    return String(s)
        .replace(/&/g,'&amp;').replace(/</g,'&lt;')
        .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}}

function appendTurn(role, text, meta) {{
    const isUser = (role === 'user');
    const div    = document.createElement('div');
    div.className = 'turn';
    const catColor  = (meta && meta.catColor) ? meta.catColor : '#8fa2bc';
    const langTag   = (meta && meta.langName && meta.langName !== 'English')
        ? `<span class="lang-tag">${{esc(meta.langName)}}</span>` : '';
    const metaHtml  = meta
        ? `<span class="meta-dot" style="background:${{catColor}}"></span>MHI&nbsp;${{meta.mhi}}&nbsp;\u00b7&nbsp;${{esc(meta.category)}}&nbsp;${{langTag}}`
        : '';
    div.innerHTML =
        `<div class="turn-row ${{isUser?'user-row':''}}">
            <div class="avatar ${{isUser?'avatar-user':'avatar-ai'}}">${{isUser?'You':'AI'}}</div>
            <div style="flex:1;min-width:0;">
                <div class="bubble ${{isUser?'bubble-user':'bubble-ai'}}">${{esc(text)}}</div>
                <div class="turn-meta">${{hhmm()}}&nbsp;${{metaHtml}}</div>
            </div>
        </div>`;
    transcript.appendChild(div);
    transcript.scrollTop = transcript.scrollHeight;
}}

function showCrisis(tier, score) {{
    if (tier==='active' || score>=0.85) {{
        crisisBar.className='crisis-bar active show';
        crisisBar.innerHTML='&#9888; Please reach out now &mdash; <strong>AASRA:</strong> +91-9820466626 &nbsp;\u00b7&nbsp; <strong>Kiran:</strong> 1800-599-0019 (free, 24/7)';
    }} else if (tier==='passive' || score>=0.55) {{
        crisisBar.className='crisis-bar passive show';
        crisisBar.innerHTML='Support is here &mdash; <strong>Kiran:</strong> 1800-599-0019 &nbsp;\u00b7&nbsp; <strong>Vandrevala:</strong> +91-1860-2662-345';
    }} else {{
        crisisBar.className='crisis-bar';
    }}
}}

/* ── Dashboard sync (postMessage to parent Streamlit window) ── */
function syncDashboard(userText, reply, mhi, category, tier, langCode) {{
    try {{
        window.parent.postMessage({{
            type:           'VOICE_TURN_V5',
            user_text:      userText,
            assistant_text: reply,
            mhi:            mhi,
            category:       category,
            crisis_tier:    tier,
            language_code:  langCode,
            ts:             new Date().toISOString(),
        }}, '*');
    }} catch(e) {{ console.debug('syncDash', e); }}
}}

/* ══════════════════════════════════════════════════════════════
   INTERRUPT MECHANISM
   ─────────────────────────────────────────────────────────────
   While AI is speaking we keep a SpeechRecognition instance
   running in the background purely for ONSET detection.
   The moment the browser hears ANY audio (onstart fires),
   we pause the current Audio element synchronously — AI stops
   within <100ms. We then capture the full utterance with
   MediaRecorder and process it normally.
   ══════════════════════════════════════════════════════════════ */

function startInterruptWatcher() {{
    if (!SR || !currentAudio) return;
    interruptDone = false;
    interruptSR   = new SR();
    interruptSR.lang          = BCP47[sessionLang] || 'en-IN';
    interruptSR.continuous    = false;
    interruptSR.interimResults= true;
    interruptSR.maxAlternatives = 1;

    interruptSR.onstart = function() {{
        // User started speaking — stop AI immediately
        if (currentAudio && !currentAudio.paused) {{
            currentAudio.pause();
            currentAudio.currentTime = 0;
        }}
        window.speechSynthesis.cancel();
        currentAudio = null;

        if (!interruptDone) {{
            interruptDone = true;
            stopInterruptWatcher();
            // Small buffer so MediaRecorder catches from start of speech
            setTimeout(function() {{
                if (!isListening && !isProcessing) {{
                    setOrb('listening');
                    setStatus('Listening\u2026');
                    _startMediaRecorder();
                }}
            }}, 60);
        }}
    }};
    interruptSR.onerror = function() {{ stopInterruptWatcher(); }};
    interruptSR.onend   = function() {{ if (!interruptDone) stopInterruptWatcher(); }};

    try {{ interruptSR.start(); }}
    catch(e) {{ /* ignore — SR may not be available */ }}
}}

function stopInterruptWatcher() {{
    if (interruptSR) {{
        try {{ interruptSR.abort(); }} catch(e) {{}}
        interruptSR = null;
    }}
}}

/* ══════════════════════════════════════════════════════════════
   TTS — speaks in detected language with Indian accent
   ══════════════════════════════════════════════════════════════ */

async function speakResponse(text, langCode, emotion, tier) {{
    if (isMuted) return;
    setOrb('speaking');
    setStatus('Speaking\u2026 (speak to interrupt)');
    stopInterruptWatcher();

    try {{
        const res = await fetch(`${{BACKEND}}/voice/speak`, {{
            method:  'POST',
            headers: {{'Content-Type':'application/json','Authorization':`Bearer ${{JWT}}`}},
            body:    JSON.stringify({{
                text:          text,
                language_code: langCode,
                emotion_label: emotion,
                crisis_tier:   tier,
            }}),
        }});
        if (!res.ok) throw new Error('tts-' + res.status);

        const blob  = await res.blob();
        const url   = URL.createObjectURL(blob);
        const audio = new Audio(url);
        currentAudio = audio;

        // Start interrupt watcher as soon as playback begins
        audio.onplay = function() {{ startInterruptWatcher(); }};

        await new Promise(function(resolve) {{
            audio.onended = function() {{ currentAudio=null; resolve(); }};
            audio.onerror = function() {{ currentAudio=null; resolve(); }};
            audio.play().catch(function() {{ currentAudio=null; resolve(); }});
        }});
        URL.revokeObjectURL(url);
    }} catch(_) {{
        // Browser TTS fallback — also interruptible via stopInterruptWatcher()
        await speakBrowserTTS(text, langCode, emotion, tier);
    }}

    stopInterruptWatcher();
    currentAudio = null;
}}

function speakBrowserTTS(text, langCode, emotion, tier) {{
    return new Promise(function(resolve) {{
        window.speechSynthesis.cancel();
        const key   = (tier==='active'||tier==='passive') ? 'crisis' : (emotion||'default');
        const prof  = PROFILES[key] || PROFILES['default'];
        const u     = new SpeechSynthesisUtterance(text.replace(/[*#`_]/g,''));
        u.lang      = BCP47[langCode] || 'en-IN';
        u.rate      = prof.rate;
        u.pitch     = prof.pitch;
        u.volume    = prof.volume;

        function go() {{
            const voices = window.speechSynthesis.getVoices();
            // Try exact lang match first, then language prefix
            const match  = voices.find(v => v.lang === u.lang)
                        || voices.find(v => v.lang.startsWith(u.lang.split('-')[0]));
            if (match) u.voice = match;
            u.onend  = resolve;
            u.onerror = resolve;
            window.speechSynthesis.speak(u);
        }}
        window.speechSynthesis.getVoices().length > 0 ? go() :
            (window.speechSynthesis.onvoiceschanged = go);
    }});
}}

/* ══════════════════════════════════════════════════════════════
   STT — calls /voice/transcribe, reads language_code from response
   ══════════════════════════════════════════════════════════════ */

async function transcribeBlob(blob) {{
    try {{
        const form = new FormData();
        form.append('audio', blob, 'recording.webm');
        const res  = await fetch(`${{BACKEND}}/voice/transcribe`, {{
            method:  'POST',
            headers: {{'Authorization': `Bearer ${{JWT}}`}},
            body:    form,
        }});
        if (!res.ok) return null;
        // Returns: {{ transcript, language_code, language_name, confidence }}
        return await res.json();
    }} catch(e) {{ return null; }}
}}

/* ══════════════════════════════════════════════════════════════
   CHAT — sends text to /chat, reads full response
   ══════════════════════════════════════════════════════════════ */

async function sendChat(userText) {{
    setOrb('thinking');
    setStatus('Thinking\u2026');

    try {{
        const res = await fetch(`${{BACKEND}}/chat`, {{
            method:  'POST',
            headers: {{'Content-Type':'application/json','Authorization':`Bearer ${{JWT}}`}},
            body:    JSON.stringify({{message: userText, language_code: sessionLang}}),
        }});
        if (!res.ok) throw new Error('chat-' + res.status);

        const data     = await res.json();
        const reply    = data.response     || '';
        const mhi      = data.mhi          || 0;
        const category = data.category     || '';
        const tier     = data.crisis_tier  || 'none';
        const score    = data.crisis_score || 0;
        const scores   = data.emotion_scores || {{}};
        // Dominant emotion for TTS speed
        const emotion  = Object.keys(scores).length
            ? Object.keys(scores).reduce((a,b) => scores[a]>scores[b] ? a : b, 'neutral')
            : 'neutral';

        showCrisis(tier, score);
        appendTurn('assistant', reply, {{
            mhi:      mhi,
            category: category,
            catColor: CAT_COLORS[category] || '#8fa2bc',
            langName: sessionLangName,
        }});
        syncDashboard(userText, reply, mhi, category, tier, sessionLang);

        // Speak in the detected language
        await speakResponse(reply, sessionLang, emotion, tier);

        if (continuous && tier !== 'active') {{
            startListening();
        }} else {{
            setOrb('');
            setStatus(continuous ? 'Listening\u2026' : 'Tap orb or Start to continue');
            isProcessing = false;
        }}

    }} catch(err) {{
        console.error('sendChat error:', err);
        setOrb('');
        setStatus('Something went wrong \u2014 tap to retry');
        isProcessing = false;
    }}
}}

/* ══════════════════════════════════════════════════════════════
   RECORDING
   ══════════════════════════════════════════════════════════════ */

function _startMediaRecorder() {{
    if (isListening) return;
    audioChunks = [];
    const mime  = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
                  ? 'audio/webm;codecs=opus' : 'audio/webm';
    recorder    = new MediaRecorder(micStream, {{mimeType: mime}});

    recorder.ondataavailable = function(e) {{
        if (e.data && e.data.size > 0) audioChunks.push(e.data);
    }};

    recorder.onstop = async function() {{
        isListening  = false;
        isProcessing = true;

        const blob = new Blob(audioChunks, {{type:'audio/webm'}});
        setOrb('thinking');
        setStatus('Processing\u2026');

        // ── Language-detecting STT ──
        const stt = await transcribeBlob(blob);

        if (!stt || !stt.transcript || !stt.transcript.trim()) {{
            setStatus('No speech detected \u2014 tap orb to try again');
            setOrb('');
            isProcessing = false;
            if (continuous) setTimeout(startListening, 900);
            return;
        }}

        // Update session language from Whisper detection
        sessionLang     = stt.language_code || 'en';
        sessionLangName = stt.language_name  || 'English';
        updateLangBadge(sessionLangName, stt.confidence || 0);

        appendTurn('user', stt.transcript, null);
        await sendChat(stt.transcript);
    }};

    recorder.start(200);  // 200ms chunks
    isListening = true;
    setOrb('listening');
    setStatus('Listening\u2026 speak naturally');

    // Auto-stop after 10 s silence guard
    const autoStopTimer = setTimeout(function() {{ stopRecording(); }}, 10000);
    // Tap orb to stop early
    orb.onclick = function() {{ clearTimeout(autoStopTimer); stopRecording(); }};
}}

async function startListening() {{
    if (isListening || isProcessing) return;

    // Interrupt any ongoing AI speech
    if (currentAudio && !currentAudio.paused) {{
        currentAudio.pause();
        currentAudio = null;
    }}
    window.speechSynthesis.cancel();
    stopInterruptWatcher();

    // Get mic if we don't have it yet
    if (!micStream) {{
        try {{
            micStream = await navigator.mediaDevices.getUserMedia({{audio: true}});
        }} catch(e) {{
            setStatus('Microphone access denied \u2014 allow in browser settings');
            return;
        }}
    }}
    _startMediaRecorder();
}}

function stopRecording() {{
    if (!isListening) return;
    if (recorder && recorder.state !== 'inactive') recorder.stop();
}}

function fullStop() {{
    continuous = false;
    if (isListening) stopRecording();
    if (currentAudio) {{ currentAudio.pause(); currentAudio = null; }}
    window.speechSynthesis.cancel();
    stopInterruptWatcher();
    setOrb('');
    setStatus('Stopped \u2014 tap Start or orb to resume');
    isProcessing = false;
}}

/* ── Greeting ── */
async function greet() {{
    const msg = "Hey, really glad you're here. This is your space \u2014 completely private and just for you. You can talk to me about anything, in any language you feel comfortable with. How are you doing today?";
    appendTurn('assistant', msg, null);
    if (!isMuted) {{
        await speakResponse(msg, 'en', 'neutral', 'none');
    }}
    if (continuous) startListening();
    else {{ setOrb(''); setStatus('Tap Start to begin talking'); }}
}}

/* ── Button handlers ── */
btnStart.addEventListener('click', function() {{
    continuous = true;
    window.speechSynthesis.cancel();
    if (currentAudio) {{ currentAudio.pause(); currentAudio = null; }}
    if (!isListening && !isProcessing) startListening();
}});

btnStop.addEventListener('click', fullStop);

btnMute.addEventListener('click', function() {{
    isMuted = !isMuted;
    btnMute.textContent = isMuted ? '\U0001F50A\u00A0Unmute' : '\U0001F507\u00A0Mute';
    if (isMuted) {{
        if (currentAudio) {{ currentAudio.pause(); currentAudio = null; }}
        window.speechSynthesis.cancel();
        stopInterruptWatcher();
    }}
}});

orb.addEventListener('click', function() {{
    if (isProcessing) return;
    if (isListening) {{ stopRecording(); }}
    else {{ continuous = false; startListening(); }}
}});

/* ── Init ── */
greet();

}})();
</script>
</body>
</html>"""


# ── Inject aria-label patcher (runs in Streamlit main page) ─────────────────
_LABEL_PATCHER = """
<script>
(function(){
    function patch(){
        var inputs = document.querySelectorAll('input[type="text"]');
        for(var i=0;i<inputs.length;i++){
            var lbl = document.querySelector('label[for="'+inputs[i].id+'"]');
            if(lbl && lbl.textContent.trim().indexOf('__vsync_v5_label__') !== -1){
                inputs[i].setAttribute('aria-label','__vsync_v5__');
            }
        }
    }
    setTimeout(patch, 300);
    setTimeout(patch, 900);
    setTimeout(patch, 2000);
})();
</script>
"""


# ── Main render ───────────────────────────────────────────────────────────────

def render_chat(voice_enabled: bool = False) -> None:
    """
    Drop-in replacement for render_chat().
    Voice-only — text mode removed entirely.
    """
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "mhi_log" not in st.session_state:
        st.session_state.mhi_log = []

    jwt = st.session_state.get("jwt", "")
    if not jwt:
        st.warning("Please log in to use the voice companion.")
        return

    st.markdown(_CSS, unsafe_allow_html=True)

    # Inject postMessage listener (main page context — not inside any iframe)
    st.markdown(_LISTENER_SCRIPT, unsafe_allow_html=True)
    st.markdown(_LABEL_PATCHER,   unsafe_allow_html=True)

    # Hidden sync input — receives VOICE_TURN_V5 payloads via JS
    raw_sync = st.text_input(
        "__vsync_v5_label__",
        value="",
        key="voice_sync_v5",
        label_visibility="hidden",
    )

    # Process incoming voice turn from panel
    if raw_sync and raw_sync != st.session_state.get("_vsync_v5_last", ""):
        st.session_state["_vsync_v5_last"] = raw_sync
        try:
            turn     = json.loads(raw_sync)
            mhi      = int(turn.get("mhi",     0))
            category = str(turn.get("category", ""))
            u_text   = str(turn.get("user_text",      ""))
            a_text   = str(turn.get("assistant_text",  ""))
            ts       = str(turn.get("ts", datetime.now().isoformat()))

            if mhi and category:
                st.session_state.mhi_log.append({
                    "timestamp": ts,
                    "mhi":       mhi,
                    "category":  category,
                    "source":    "voice",
                })
            if u_text:
                st.session_state.chat_history.append(
                    {"role": "user", "content": u_text}
                )
            if a_text:
                st.session_state.chat_history.append({
                    "role":    "assistant",
                    "content": a_text,
                    "meta":    {"mhi": mhi, "category": category},
                })
            st.rerun()
        except (json.JSONDecodeError, ValueError):
            pass

    # Render the voice panel
    components.html(
        _build_voice_panel(BACKEND_URL, jwt),
        height=640,
        scrolling=False,
    )