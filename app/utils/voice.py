from __future__ import annotations

import re
import json
import streamlit as st
import streamlit.components.v1 as components


# ── Preferred TTS voices (ordered by warmth / naturalness) ───────────────────
_PREFERRED_VOICES = [
    "Google UK English Female",
    "Samantha",
    "Karen",
    "Moira",
    "Tessa",
    "Victoria",
    "Google US English",
]

# ── Emotion-aware voice profiles ──────────────────────────────────────────────
_VOICE_PROFILES: dict[str, dict] = {
    "crisis":  {"rate": 0.76, "pitch": 0.94, "volume": 1.0},
    "sadness": {"rate": 0.82, "pitch": 0.97, "volume": 0.95},
    "fear":    {"rate": 0.83, "pitch": 0.99, "volume": 0.95},
    "anxiety": {"rate": 0.84, "pitch": 1.00, "volume": 0.95},
    "anger":   {"rate": 0.82, "pitch": 0.96, "volume": 0.90},
    "stress":  {"rate": 0.85, "pitch": 1.00, "volume": 0.95},
    "neutral": {"rate": 0.90, "pitch": 1.02, "volume": 1.00},
    "default": {"rate": 0.88, "pitch": 1.02, "volume": 1.00},
}

_VOICES_JSON = json.dumps(_PREFERRED_VOICES)


# ── Greeting orb HTML ─────────────────────────────────────────────────────────
_GREETING_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@400;500&display=swap" rel="stylesheet">
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{
    width:100%; height:130px; background:transparent;
    display:flex; align-items:center; justify-content:center;
    font-family:'Sora',sans-serif; overflow:hidden;
}}
.wrap {{ display:flex; flex-direction:column; align-items:center; gap:12px; }}
.orb {{
    width:62px; height:62px; border-radius:50%; cursor:pointer;
    background: radial-gradient(circle at 38% 35%, #63b3ed 0%, #4fd1c5 55%, #7c3aed 100%);
    animation: idle 3.5s ease-in-out infinite;
    transition: transform 0.2s ease; flex-shrink:0;
}}
.orb:hover {{ transform: scale(1.1); }}
.orb.speaking {{ animation: pulse 0.75s ease-in-out infinite; }}

@keyframes idle {{
    0%,100% {{ box-shadow:0 0 20px rgba(99,179,237,0.25); transform:scale(1);    }}
    50%      {{ box-shadow:0 0 36px rgba(79,209,197,0.38); transform:scale(1.05); }}
}}
@keyframes pulse {{
    0%,100% {{ box-shadow:0 0 0 0   rgba(99,179,237,0.75); transform:scale(1.02); }}
    50%      {{ box-shadow:0 0 0 20px rgba(99,179,237,0);   transform:scale(1.09); }}
}}

.label {{
    font-size:0.68rem; color:#546070;
    letter-spacing:0.08em; text-transform:uppercase;
}}
</style>
</head>
<body>
<div class="wrap">
    <div class="orb" id="orb" title="Click to replay greeting"></div>
    <div class="label" id="lbl">Starting…</div>
</div>
<script>
(function(){{
    const orb  = document.getElementById('orb');
    const lbl  = document.getElementById('lbl');
    const text = {text_json};
    const preferred = {voices_json};

    function speak() {{
        window.speechSynthesis.cancel();
        const u = new SpeechSynthesisUtterance(text);
        u.rate = 0.86; u.pitch = 1.04; u.volume = 1.0;

        const voices = window.speechSynthesis.getVoices();
        for (const name of preferred) {{
            const v = voices.find(x => x.name === name);
            if (v) {{ u.voice = v; break; }}
        }}

        orb.classList.add('speaking');
        lbl.textContent = 'Speaking…';
        u.onend = () => {{ orb.classList.remove('speaking'); lbl.textContent = 'Tap to replay'; }};
        window.speechSynthesis.speak(u);
    }}

    if (window.speechSynthesis.getVoices().length > 0) {{
        setTimeout(speak, 700);
    }} else {{
        window.speechSynthesis.onvoiceschanged = () => setTimeout(speak, 400);
    }}

    orb.addEventListener('click', speak);
}})();
</script>
</body>
</html>"""


# ── Compact mic button (36×36 iframe) ─────────────────────────────────────────
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
    0%   { box-shadow: 0 0 0 0   rgba(252,129,129,0.6); }
    70%  { box-shadow: 0 0 0 10px rgba(252,129,129,0);  }
    100% { box-shadow: 0 0 0 0   rgba(252,129,129,0);  }
}

#waves { display:none; align-items:flex-end; justify-content:center; gap:2px; height:18px; }
#waves.on { display:flex; }
.b {
    width:2px; border-radius:1px; background:#fc8181; height:3px;
    animation: wv 0.7s ease-in-out infinite;
}
.b:nth-child(1){animation-delay:0.00s} .b:nth-child(2){animation-delay:0.10s}
.b:nth-child(3){animation-delay:0.20s} .b:nth-child(4){animation-delay:0.30s}
.b:nth-child(5){animation-delay:0.20s} .b:nth-child(6){animation-delay:0.10s}
.b:nth-child(7){animation-delay:0.00s}

@keyframes wv {
    0%,100%{ height:3px;  opacity:0.5; }
    50%    { height:16px; opacity:1;   }
}
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
    const btn=document.getElementById('btn'), mic=document.getElementById('mic'),
          waves=document.getElementById('waves');
    let recog=null, active=false;
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) { btn.title='Not supported'; btn.style.opacity='0.3'; return; }

    function setActive(on) {
        active=on;
        btn.classList.toggle('rec',on);
        mic.style.display = on?'none':'block';
        waves.classList.toggle('on',on);
    }
    function inject(text) {
        const doc=window.parent.document;
        const ta=doc.querySelector('textarea[data-testid="stChatInputTextArea"]');
        if(!ta) return;
        const setter=Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype,'value').set;
        setter.call(ta,text);
        ta.dispatchEvent(new Event('input',{bubbles:true}));
        ta.dispatchEvent(new Event('change',{bubbles:true}));
        ta.focus();
    }
    function start() {
        recog=new SR();
        recog.lang='en-US'; recog.interimResults=true; recog.continuous=false;
        recog.onstart=()=>setActive(true);
        recog.onresult=(e)=>{
            let final='';
            for(let i=e.resultIndex;i<e.results.length;i++)
                if(e.results[i].isFinal) final+=e.results[i][0].transcript;
            if(final){ inject(final.trim()); stop(); }
        };
        recog.onerror=()=>stop();
        recog.onend=()=>setActive(false);
        try{ recog.start(); }catch(_){ setActive(false); }
    }
    function stop() {
        if(recog){ try{recog.stop();}catch(_){} recog=null; }
        setActive(false);
    }
    btn.addEventListener('click', ()=>active?stop():start());
})();
</script>
</body>
</html>"""


def render_greeting(assistant_name: str = "your Well-Being companion") -> None:
    """
    Renders an animated gradient orb that auto-speaks a warm welcome
    greeting when the chat tab first loads. Click the orb to replay.
    Place this at the top of render_chat() when chat_history is empty.
    """
    greeting = (
        f"Hi there. I'm {assistant_name}. "
        "This is a safe and private space — just for you. "
        "There's no rush, no judgment here. "
        "Whenever you feel ready, just share what's on your mind. "
        "I'm listening."
    )
    html = _GREETING_TEMPLATE.format(
        text_json=json.dumps(greeting),
        voices_json=_VOICES_JSON,
    )
    components.html(html, height=130, scrolling=False)


def render_mic_component() -> None:
    """Renders the 36×36 mic button. CSS in chat_ui.py positions it inside the input bar."""
    components.html(_MIC_HTML, height=36, scrolling=False)


def speak_text(
    text: str,
    emotion_label: str = "default",
    crisis_tier: str = "none",
) -> None:
    """
    Speaks text via browser Web Speech Synthesis.

    - Selects voice profile based on emotion_label
    - Crisis tier (active/passive) always overrides to calmest profile
    - Strips markdown symbols before speaking
    - Prefers warm natural voices (Google UK English Female, Samantha, etc.)
    """
    # Crisis always overrides voice profile
    if crisis_tier in ("active", "passive"):
        profile = _VOICE_PROFILES["crisis"]
    else:
        profile = _VOICE_PROFILES.get(emotion_label, _VOICE_PROFILES["default"])

    # Strip markdown noise from text before speaking
    clean = re.sub(r"\*{1,3}|#{1,6}\s?|`{1,3}|_{1,2}|-{2,}|\[|\]|\(.*?\)", "", text)
    clean = re.sub(r"\n+", " ", clean).strip()

    # Escape for safe JS string embedding
    safe = clean.replace("\\", "\\\\").replace('"', '\\"').replace("'", "\\'")

    st.markdown(f"""
    <script>
    (function(){{
        window.speechSynthesis.cancel();
        const u = new SpeechSynthesisUtterance("{safe}");
        u.rate   = {profile['rate']};
        u.pitch  = {profile['pitch']};
        u.volume = {profile['volume']};

        const preferred = {_VOICES_JSON};
        function applyAndSpeak() {{
            const voices = window.speechSynthesis.getVoices();
            for (const name of preferred) {{
                const v = voices.find(x => x.name === name);
                if (v) {{ u.voice = v; break; }}
            }}
            window.speechSynthesis.speak(u);
        }}

        if (window.speechSynthesis.getVoices().length > 0) {{
            applyAndSpeak();
        }} else {{
            window.speechSynthesis.onvoiceschanged = applyAndSpeak;
        }}
    }})();
    </script>
    """, unsafe_allow_html=True)


def cancel_speech() -> None:
    """Immediately stops any playing TTS."""
    st.markdown(
        "<script>window.speechSynthesis.cancel();</script>",
        unsafe_allow_html=True,
    )