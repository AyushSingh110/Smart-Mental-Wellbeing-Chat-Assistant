#voice.py
from __future__ import annotations

import json
import streamlit as st
import streamlit.components.v1 as components

# ── Emotion-aware Web Speech synthesis profiles ───────────────────────────────
_WEB_SPEECH_PROFILES: dict[str, dict] = {
    "crisis":  {"rate": 0.76, "pitch": 0.94, "volume": 1.0},
    "sadness": {"rate": 0.82, "pitch": 0.97, "volume": 0.95},
    "fear":    {"rate": 0.83, "pitch": 0.99, "volume": 0.95},
    "anxiety": {"rate": 0.84, "pitch": 1.00, "volume": 0.95},
    "anger":   {"rate": 0.82, "pitch": 0.96, "volume": 0.90},
    "stress":  {"rate": 0.85, "pitch": 1.00, "volume": 0.95},
    "neutral": {"rate": 0.90, "pitch": 1.02, "volume": 1.00},
    "default": {"rate": 0.88, "pitch": 1.02, "volume": 1.00},
}

_PREFERRED_VOICES = json.dumps([
    "Google UK English Female",
    "Samantha", "Karen", "Moira", "Tessa", "Victoria",
    "Google US English",
])


# ─────────────────────────────────────────────────────────────────────────────
# Full voice-to-voice component
# Self-contained iframe: records → transcribes → chats → speaks
# Passes conversation up to Streamlit via postMessage when a round-trip completes
# ─────────────────────────────────────────────────────────────────────────────

def _build_voice_component_html(
    backend_url: str,
    jwt: str,
    assistant_name: str,
    profiles_json: str,
    preferred_voices_json: str,
) -> str:
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@400;500;600&display=swap" rel="stylesheet">
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{
    width:100%; background:transparent;
    font-family:'Sora',sans-serif; overflow:hidden;
    color:#e8edf5;
}}

/* ── Orb ── */
.orb-area {{
    display:flex; flex-direction:column; align-items:center;
    padding: 20px 0 14px 0; gap:10px;
}}
.orb {{
    width:80px; height:80px; border-radius:50%; cursor:pointer;
    background: radial-gradient(circle at 38% 35%, #63b3ed 0%, #4fd1c5 55%, #7c3aed 100%);
    animation: idle 3.5s ease-in-out infinite;
    transition: transform 0.18s ease; flex-shrink:0;
    border: none; outline:none;
    position:relative;
}}
.orb:hover {{ transform:scale(1.08); }}
.orb.listening {{
    animation: listen 0.65s ease-in-out infinite !important;
    background: radial-gradient(circle at 38% 35%, #fc8181 0%, #f6ad55 55%, #fc4e4e 100%) !important;
}}
.orb.thinking {{
    animation: think 1.1s ease-in-out infinite !important;
    background: radial-gradient(circle at 38% 35%, #b794f4 0%, #7c3aed 55%, #63b3ed 100%) !important;
}}
.orb.speaking {{
    animation: pulse 0.72s ease-in-out infinite !important;
}}

@keyframes idle {{
    0%,100% {{ box-shadow:0 0 22px rgba(99,179,237,0.28); transform:scale(1); }}
    50%      {{ box-shadow:0 0 40px rgba(79,209,197,0.40); transform:scale(1.05); }}
}}
@keyframes listen {{
    0%,100% {{ box-shadow:0 0 0 0   rgba(252,129,129,0.80); transform:scale(1.00); }}
    50%      {{ box-shadow:0 0 0 22px rgba(252,129,129,0);   transform:scale(1.10); }}
}}
@keyframes think {{
    0%,100% {{ box-shadow:0 0 0 0   rgba(183,148,244,0.75); transform:scale(1.00); }}
    50%      {{ box-shadow:0 0 0 18px rgba(183,148,244,0);   transform:scale(1.06); }}
}}
@keyframes pulse {{
    0%,100% {{ box-shadow:0 0 0 0   rgba(99,179,237,0.80); transform:scale(1.02); }}
    50%      {{ box-shadow:0 0 0 22px rgba(99,179,237,0);   transform:scale(1.10); }}
}}

/* ── Wave bars (inside orb while listening) ── */
.wave-bars {{
    display:none; position:absolute;
    align-items:flex-end; justify-content:center;
    gap:3px; bottom:20px; left:50%; transform:translateX(-50%);
    height:20px;
}}
.orb.listening .wave-bars {{ display:flex; }}
.wb {{
    width:3px; border-radius:2px; background:rgba(255,255,255,0.9); height:4px;
    animation: wb 0.6s ease-in-out infinite;
}}
.wb:nth-child(1){{animation-delay:0.00s}}
.wb:nth-child(2){{animation-delay:0.10s}}
.wb:nth-child(3){{animation-delay:0.20s}}
.wb:nth-child(4){{animation-delay:0.30s}}
.wb:nth-child(5){{animation-delay:0.20s}}
@keyframes wb {{
    0%,100%{{height:4px; opacity:0.5;}}
    50%    {{height:18px; opacity:1.0;}}
}}

/* ── Status label ── */
.status-label {{
    font-size:0.70rem; color:#546070;
    letter-spacing:0.08em; text-transform:uppercase;
    height:16px; text-align:center;
}}

/* ── Controls row ── */
.controls {{
    display:flex; justify-content:center; gap:10px;
    padding:0 16px 12px 16px;
}}
.btn-ctrl {{
    flex:1; padding:7px 0; border:none; border-radius:8px; cursor:pointer;
    font-family:'Sora',sans-serif; font-size:0.72rem; font-weight:500;
    letter-spacing:0.04em; transition: opacity 0.15s, transform 0.12s;
}}
.btn-ctrl:hover {{ opacity:0.85; transform:scale(1.02); }}
.btn-ctrl:active {{ transform:scale(0.97); }}
.btn-start  {{ background:linear-gradient(135deg,#63b3ed,#4fd1c5); color:#0a0f1e; }}
.btn-stop   {{ background:rgba(252,129,129,0.18); color:#fc8181; border:1px solid rgba(252,129,129,0.3); }}
.btn-mute   {{ background:rgba(255,255,255,0.06); color:#8b9ab0; border:1px solid rgba(255,255,255,0.08); }}

/* ── Transcript area ── */
.transcript-wrap {{
    margin:0 12px 14px 12px;
    border:1px solid rgba(255,255,255,0.07);
    border-radius:12px;
    background:rgba(10,15,30,0.6);
    overflow-y:auto;
    max-height:260px;
    padding:10px 12px;
    scroll-behavior:smooth;
}}
.transcript-wrap::-webkit-scrollbar {{ width:3px; }}
.transcript-wrap::-webkit-scrollbar-thumb {{ background:rgba(255,255,255,0.1); border-radius:2px; }}

.msg {{
    margin-bottom:10px;
    animation: fadeIn 0.3s ease;
}}
@keyframes fadeIn {{ from{{opacity:0; transform:translateY(6px);}} to{{opacity:1;transform:translateY(0);}} }}

.msg-row {{ display:flex; gap:8px; align-items:flex-start; }}
.msg-row.user   {{ flex-direction:row-reverse; }}
.avatar {{
    width:24px; height:24px; border-radius:50%; flex-shrink:0;
    display:flex; align-items:center; justify-content:center;
    font-size:0.62rem; font-weight:600;
}}
.avatar.u {{ background:linear-gradient(135deg,#1e3a5f,#2a4a7f); color:#63b3ed; }}
.avatar.a {{ background:linear-gradient(135deg,#1a2035,#2a2a4a); color:#4fd1c5; }}

.bubble {{
    max-width:82%; padding:8px 12px; border-radius:12px;
    font-size:0.78rem; line-height:1.55; word-break:break-word;
}}
.bubble.user      {{ background:#1e3a5f; color:#c8d8f0; border-radius:12px 2px 12px 12px; }}
.bubble.assistant {{ background:#1a2035; color:#d4dce8; border-radius:2px 12px 12px 12px; }}

.msg-time {{
    font-size:0.60rem; color:#3a4555;
    margin-top:3px; text-align:right;
}}
.msg-row.user .msg-time {{ text-align:left; }}

/* ── Crisis alert ── */
.crisis-banner {{
    margin:0 12px 10px 12px; padding:9px 12px;
    background:rgba(252,129,129,0.10);
    border:1px solid rgba(252,129,129,0.28);
    border-radius:10px; font-size:0.72rem;
    color:#fc8181; line-height:1.5;
    display:none;
}}
.crisis-banner.show {{ display:block; animation:fadeIn 0.3s ease; }}

/* ── Footer note ── */
.footer-note {{
    text-align:center; font-size:0.62rem; color:#2e3a4a;
    padding-bottom:8px; letter-spacing:0.04em;
}}
</style>
</head>
<body>

<!-- Animated orb -->
<div class="orb-area">
    <button class="orb" id="orb" title="Click to start / stop listening">
        <div class="wave-bars">
            <div class="wb"></div><div class="wb"></div><div class="wb"></div>
            <div class="wb"></div><div class="wb"></div>
        </div>
    </button>
    <div class="status-label" id="status">Tap orb to start</div>
</div>

<!-- Controls -->
<div class="controls">
    <button class="btn-ctrl btn-start" id="btnStart">▶ Start</button>
    <button class="btn-ctrl btn-stop"  id="btnStop">■ Stop</button>
    <button class="btn-ctrl btn-mute"  id="btnMute">🔇 Mute AI</button>
</div>

<!-- Crisis banner -->
<div class="crisis-banner" id="crisisBanner">
    ⚠ If you're in distress, please reach out: AASRA +91-9820466626 · Kiran 1800-599-0019
</div>

<!-- Scrollable transcript -->
<div class="transcript-wrap" id="transcript"></div>

<div class="footer-note">Voice conversation · Scroll up to review</div>

<script>
(function(){{
    const BACKEND   = "{backend_url}";
    const JWT       = "{jwt}";
    const NAME      = "{assistant_name}";
    const PROFILES  = {profiles_json};
    const PREFERRED = {preferred_voices_json};

    const orb     = document.getElementById('orb');
    const status  = document.getElementById('status');
    const trans   = document.getElementById('transcript');
    const crisis  = document.getElementById('crisisBanner');
    const btnStart = document.getElementById('btnStart');
    const btnStop  = document.getElementById('btnStop');
    const btnMute  = document.getElementById('btnMute');

    let recorder     = null;
    let audioChunks  = [];
    let isListening  = false;
    let isProcessing = false;
    let isMuted      = false;
    let continuous   = false;  // set true after first Start press
    let mediaStream  = null;

    // ── Helpers ────────────────────────────────────────────────────────────

    function setStatus(txt) {{ status.textContent = txt; }}

    function setOrbState(state) {{
        orb.classList.remove('listening','thinking','speaking');
        if (state) orb.classList.add(state);
    }}

    function now() {{
        return new Date().toLocaleTimeString([], {{hour:'2-digit', minute:'2-digit'}});
    }}

    function appendMessage(role, text, extra) {{
        const isUser = role === 'user';
        const div = document.createElement('div');
        div.className = 'msg';
        div.innerHTML = `
            <div class="msg-row ${{isUser ? 'user' : ''}}">
                <div class="avatar ${{isUser ? 'u' : 'a'}}">${{isUser ? 'You' : 'AI'}}</div>
                <div>
                    <div class="bubble ${{isUser ? 'user' : 'assistant'}}">${{text}}</div>
                    <div class="msg-time">${{now()}}${{extra ? ' · ' + extra : ''}}</div>
                </div>
            </div>`;
        trans.appendChild(div);
        trans.scrollTop = trans.scrollHeight;   // always scroll to latest
    }}

    function showCrisis(show) {{
        crisis.classList.toggle('show', show);
    }}

    // ── Greeting ───────────────────────────────────────────────────────────

    function greet() {{
        const msg = `Hi there. I'm ${{NAME}}. This is a safe, private space — just for you. `
                  + `Whenever you're ready, just speak and I'll listen.`;
        appendMessage('assistant', msg);
        if (!isMuted) speakWebSpeech(msg, 'default', 'none');
    }}

    // ── STT: try backend Whisper, fall back to browser SR ─────────────────

    async function transcribeBlob(blob) {{
        try {{
            const form = new FormData();
            form.append('audio', blob, 'audio.webm');
            const res = await fetch(`${{BACKEND}}/voice/transcribe`, {{
                method: 'POST',
                headers: {{ Authorization: `Bearer ${{JWT}}` }},
                body: form,
            }});
            if (!res.ok) throw new Error('STT backend error');
            const data = await res.json();
            return data.transcript || '';
        }} catch(e) {{
            // Fallback handled in startListening via SpeechRecognition
            console.warn('Backend STT failed, using browser SR fallback.');
            return null;   // null signals caller to use SR result instead
        }}
    }}

    // ── TTS: try backend /voice/speak, fall back to browser WebSpeech ─────

    async function speakResponse(text, emotionLabel, crisisTier) {{
        if (isMuted) return;
        setOrbState('speaking');
        setStatus('Speaking…');

        try {{
            const res = await fetch(`${{BACKEND}}/voice/speak`, {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${{JWT}}`,
                }},
                body: JSON.stringify({{
                    text: text,
                    emotion_label: emotionLabel,
                    crisis_tier: crisisTier,
                }}),
            }});
            if (!res.ok) throw new Error('TTS backend error');
            const audioBlob = await res.blob();
            const url = URL.createObjectURL(audioBlob);
            const audio = new Audio(url);

            await new Promise((resolve) => {{
                audio.onended = resolve;
                audio.onerror = resolve;
                audio.play().catch(resolve);
            }});
            URL.revokeObjectURL(url);
        }} catch(e) {{
            // Fallback to browser WebSpeech
            console.warn('Backend TTS failed, using browser synthesis fallback.');
            await speakWebSpeech(text, emotionLabel, crisisTier);
        }}

        setOrbState('');
        setStatus(continuous ? 'Listening…' : 'Done — tap to speak again');
    }}

    function speakWebSpeech(text, emotionLabel, crisisTier) {{
        return new Promise((resolve) => {{
            window.speechSynthesis.cancel();
            const key = (crisisTier === 'active' || crisisTier === 'passive')
                        ? 'crisis' : (emotionLabel || 'default');
            const profile = PROFILES[key] || PROFILES['default'];
            const u = new SpeechSynthesisUtterance(text.replace(/[*#`_\[\]]/g, ''));
            u.rate   = profile.rate;
            u.pitch  = profile.pitch;
            u.volume = profile.volume;

            function applyVoice() {{
                const voices = window.speechSynthesis.getVoices();
                for (const name of PREFERRED) {{
                    const v = voices.find(x => x.name === name);
                    if (v) {{ u.voice = v; break; }}
                }}
                u.onend = resolve; u.onerror = resolve;
                window.speechSynthesis.speak(u);
            }}
            if (window.speechSynthesis.getVoices().length > 0) {{
                applyVoice();
            }} else {{
                window.speechSynthesis.onvoiceschanged = applyVoice;
            }}
        }});
    }}

    // ── Chat round-trip ────────────────────────────────────────────────────

    async function sendToBackend(transcript) {{
        setOrbState('thinking');
        setStatus('Thinking…');

        try {{
            const res = await fetch(`${{BACKEND}}/chat`, {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${{JWT}}`,
                }},
                body: JSON.stringify({{ message: transcript }}),
            }});
            if (!res.ok) throw new Error('Chat backend error');
            const data = await res.json();

            const reply      = data.response   || '';
            const mhi        = data.mhi         || 0;
            const category   = data.category    || '';
            const crisisTier = data.crisis_tier || 'none';
            const crisisScore = data.crisis_score || 0;
            const scores     = data.emotion_scores || {{}};
            const emotionLabel = Object.keys(scores).reduce(
                (a, b) => (scores[a] > scores[b] ? a : b), 'neutral'
            );

            // Show crisis banner if needed
            showCrisis(crisisTier === 'active' || crisisTier === 'passive' || crisisScore > 0.60);

            // Append assistant bubble to transcript
            appendMessage('assistant', reply, `MHI ${{mhi}} · ${{category}}`);

            // Post data up to Streamlit parent for mhi_log + chat_history sync
            window.parent.postMessage({{
                type: 'VOICE_ROUND_TRIP',
                user_text: transcript,
                assistant_text: reply,
                mhi: mhi,
                category: category,
                crisis_tier: crisisTier,
            }}, '*');

            // Speak response
            await speakResponse(reply, emotionLabel, crisisTier);

            // If continuous mode and not crisis, auto-restart listening
            if (continuous && crisisTier !== 'active') {{
                startListening();
            }} else {{
                setOrbState('');
                setStatus('Tap orb to speak');
                isProcessing = false;
            }}

        }} catch(e) {{
            console.error('Chat error:', e);
            setOrbState('');
            setStatus('Error — tap to retry');
            isProcessing = false;
        }}
    }}

    // ── MediaRecorder recording ────────────────────────────────────────────

    async function startListening() {{
        if (isListening || isProcessing) return;

        try {{
            mediaStream = await navigator.mediaDevices.getUserMedia({{ audio: true }});
        }} catch(e) {{
            setStatus('Mic permission denied');
            return;
        }}

        audioChunks = [];
        const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
            ? 'audio/webm;codecs=opus' : 'audio/webm';
        recorder = new MediaRecorder(mediaStream, {{ mimeType }});

        recorder.ondataavailable = (e) => {{
            if (e.data && e.data.size > 0) audioChunks.push(e.data);
        }};

        recorder.onstop = async () => {{
            const blob = new Blob(audioChunks, {{ type: 'audio/webm' }});
            isListening  = false;
            isProcessing = true;

            // Try backend STT first
            const transcript = await transcribeBlob(blob);

            if (transcript === null) {{
                // Backend failed, transcript was already captured by SR fallback
                // (srTranscript is set below)
                return;
            }}
            if (!transcript.trim()) {{
                setStatus('No speech detected — tap to try again');
                setOrbState('');
                isProcessing = false;
                return;
            }}
            appendMessage('user', transcript);
            await sendToBackend(transcript);
        }};

        // Also run browser SpeechRecognition in parallel as SR fallback
        // It will only be used if backend STT returns null
        let srTranscript = '';
        const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
        let sr = null;
        if (SR) {{
            sr = new SR();
            sr.lang = 'en-US'; sr.interimResults = false; sr.continuous = false;
            sr.onresult = (e) => {{
                for (let i = e.resultIndex; i < e.results.length; i++)
                    if (e.results[i].isFinal) srTranscript += e.results[i][0].transcript;
            }};
            sr.onerror = () => {{}};
            try {{ sr.start(); }} catch(_) {{}}
        }}

        recorder.start(250);   // collect chunks every 250ms
        isListening = true;
        setOrbState('listening');
        setStatus('Listening…');

        // Auto-stop after 8 seconds of silence detection via VAD simulation
        // (simple timeout — user can also click orb to stop early)
        let silenceTimer = setTimeout(() => stopListening(srTranscript), 8000);

        orb.onclick = () => {{
            clearTimeout(silenceTimer);
            stopListening(srTranscript, sr);
        }};
    }}

    function stopListening(srFallback, sr) {{
        if (!isListening) return;
        if (sr) {{ try {{ sr.stop(); }} catch(_) {{}} }}
        if (recorder && recorder.state !== 'inactive') {{
            recorder.stop();
        }}
        if (mediaStream) {{
            mediaStream.getTracks().forEach(t => t.stop());
            mediaStream = null;
        }}
        setOrbState('thinking');
        setStatus('Processing…');
        // srFallback is used in recorder.onstop if backend STT returned null
        recorder.onstop = async () => {{
            const blob = new Blob(audioChunks, {{ type:'audio/webm' }});
            isListening = false;
            isProcessing = true;
            let transcript = await transcribeBlob(blob);
            if (transcript === null) transcript = srFallback;  // use SR fallback
            if (!transcript || !transcript.trim()) {{
                setStatus('No speech detected — tap to try again');
                setOrbState(''); isProcessing = false; return;
            }}
            appendMessage('user', transcript);
            await sendToBackend(transcript);
        }};
    }}

    // ── Button wiring ──────────────────────────────────────────────────────

    btnStart.addEventListener('click', () => {{
        continuous = true;
        startListening();
    }});

    btnStop.addEventListener('click', () => {{
        continuous = false;
        if (isListening) stopListening('');
        window.speechSynthesis.cancel();
        setOrbState('');
        setStatus('Stopped — tap orb or Start to resume');
        isProcessing = false;
    }});

    btnMute.addEventListener('click', () => {{
        isMuted = !isMuted;
        btnMute.textContent = isMuted ? '🔊 Unmute AI' : '🔇 Mute AI';
        if (isMuted) window.speechSynthesis.cancel();
    }});

    // Orb tap — single shot (not continuous)
    orb.addEventListener('click', () => {{
        if (isProcessing) return;
        if (isListening) {{
            stopListening('');
        }} else {{
            continuous = false;
            startListening();
        }}
    }});

    // ── Boot ───────────────────────────────────────────────────────────────
    greet();
}})();
</script>
</body>
</html>"""


# ─────────────────────────────────────────────────────────────────────────────
# Compact mic button — sits inside chat input bar (text mode fallback)
# ─────────────────────────────────────────────────────────────────────────────

_MIC_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
* { margin:0; padding:0; box-sizing:border-box; }
html, body { width:36px; height:36px; overflow:hidden; background:transparent; }
#btn {
    width:36px; height:36px; border-radius:50%; border:none;
    background:transparent; cursor:pointer;
    display:flex; align-items:center; justify-content:center;
    transition:background 0.18s; outline:none;
}
#btn:hover { background: rgba(99,179,237,0.13); }
#btn.rec   { background: rgba(252,129,129,0.15); animation: glow 1.4s ease-out infinite; }
@keyframes glow {
    0%   { box-shadow:0 0 0 0   rgba(252,129,129,0.6); }
    70%  { box-shadow:0 0 0 10px rgba(252,129,129,0);  }
    100% { box-shadow:0 0 0 0   rgba(252,129,129,0);  }
}
#waves { display:none; align-items:flex-end; justify-content:center; gap:2px; height:18px; }
#waves.on { display:flex; }
.b { width:2px; border-radius:1px; background:#fc8181; height:3px; animation:wv 0.7s ease-in-out infinite; }
.b:nth-child(1){animation-delay:0.00s} .b:nth-child(2){animation-delay:0.10s}
.b:nth-child(3){animation-delay:0.20s} .b:nth-child(4){animation-delay:0.30s}
.b:nth-child(5){animation-delay:0.20s} .b:nth-child(6){animation-delay:0.10s}
.b:nth-child(7){animation-delay:0.00s}
@keyframes wv { 0%,100%{height:3px;opacity:0.5;} 50%{height:16px;opacity:1;} }
</style>
</head>
<body>
<button id="btn" title="Click to speak">
    <svg id="mic" width="17" height="17" viewBox="0 0 24 24" fill="none"
         stroke="#63b3ed" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
        <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
        <line x1="12" y1="19" x2="12" y2="23"/>
        <line x1="8"  y1="23" x2="16" y2="23"/>
    </svg>
    <div id="waves">
        <div class="b"></div><div class="b"></div><div class="b"></div>
        <div class="b"></div><div class="b"></div><div class="b"></div>
        <div class="b"></div>
    </div>
</button>
<script>
(function(){
    const btn=document.getElementById('btn'),mic=document.getElementById('mic'),
          waves=document.getElementById('waves');
    let recog=null,active=false;
    const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
    if(!SR){btn.style.opacity='0.3';return;}
    function setActive(on){active=on;btn.classList.toggle('rec',on);mic.style.display=on?'none':'block';waves.classList.toggle('on',on);}
    function inject(text){
        const doc=window.parent.document;
        const ta=doc.querySelector('textarea[data-testid="stChatInputTextArea"]');
        if(!ta)return;
        const setter=Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype,'value').set;
        setter.call(ta,text);
        ta.dispatchEvent(new Event('input',{bubbles:true}));
        ta.dispatchEvent(new Event('change',{bubbles:true}));
        ta.focus();
    }
    function start(){
        recog=new SR();recog.lang='en-US';recog.interimResults=true;recog.continuous=false;
        recog.onstart=()=>setActive(true);
        recog.onresult=(e)=>{let f='';for(let i=e.resultIndex;i<e.results.length;i++)if(e.results[i].isFinal)f+=e.results[i][0].transcript;if(f){inject(f.trim());stop();}};
        recog.onerror=()=>stop();recog.onend=()=>setActive(false);
        try{recog.start();}catch(_){setActive(false);}
    }
    function stop(){if(recog){try{recog.stop();}catch(_){}recog=null;}setActive(false);}
    btn.addEventListener('click',()=>active?stop():start());
})();
</script>
</body>
</html>"""


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def render_voice_assistant(
    backend_url: str = "http://localhost:8000",
    assistant_name: str = "your Well-Being companion",
    height: int = 560,
) -> None:
    """
    Renders the full voice-to-voice assistant component.

    Flow inside the iframe:
      Tap orb / Start → mic opens → audio recorded → /voice/transcribe
      → /chat → /voice/speak → plays audio + appends transcript
      → auto-restarts if continuous mode

    Passes completed round-trips to Streamlit via postMessage so
    chat_history and mhi_log stay in sync.
    """
    jwt = st.session_state.get("jwt", "")
    if not jwt:
        st.warning("Not authenticated.")
        return

    profiles_json = json.dumps(_WEB_SPEECH_PROFILES)

    html = _build_voice_component_html(
        backend_url=backend_url,
        jwt=jwt,
        assistant_name=assistant_name,
        profiles_json=profiles_json,
        preferred_voices_json=_PREFERRED_VOICES,
    )
    components.html(html, height=height, scrolling=False)


def render_mic_component() -> None:
    """Compact 36×36 mic button for text-mode chat input bar."""
    components.html(_MIC_HTML, height=36, scrolling=False)


def speak_text(
    text: str,
    emotion_label: str = "default",
    crisis_tier: str = "none",
) -> None:
    """
    Browser-side TTS fallback used by text-mode chat.
    Called after receiving a response from /chat when voice mode is OFF.
    """
    import re
    clean = re.sub(r"\*{1,3}|#{1,6}\s?|`{1,3}|_{1,2}|-{2,}|\[|\]|\(.*?\)", "", text)
    clean = re.sub(r"\n+", " ", clean).strip()
    safe  = clean.replace("\\","\\\\").replace('"','\\"').replace("'","\\'")

    if crisis_tier in ("active","passive"):
        profile = _WEB_SPEECH_PROFILES["crisis"]
    else:
        profile = _WEB_SPEECH_PROFILES.get(emotion_label, _WEB_SPEECH_PROFILES["default"])

    st.markdown(f"""
    <script>
    (function(){{
        window.speechSynthesis.cancel();
        const u=new SpeechSynthesisUtterance("{safe}");
        u.rate={profile['rate']}; u.pitch={profile['pitch']}; u.volume={profile['volume']};
        const preferred={_PREFERRED_VOICES};
        function go(){{
            const voices=window.speechSynthesis.getVoices();
            for(const n of preferred){{const v=voices.find(x=>x.name===n);if(v){{u.voice=v;break;}}}}
            window.speechSynthesis.speak(u);
        }}
        if(window.speechSynthesis.getVoices().length>0)go();
        else window.speechSynthesis.onvoiceschanged=go;
    }})();
    </script>
    """, unsafe_allow_html=True)


def cancel_speech() -> None:
    st.markdown("<script>window.speechSynthesis.cancel();</script>", unsafe_allow_html=True)
