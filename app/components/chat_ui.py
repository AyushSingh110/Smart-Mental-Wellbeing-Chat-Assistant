"""
chat_ui.py

Dashboard sync — definitive fix:
  The voice panel iframe and the listener iframe are BOTH served by
  Streamlit's component server which is cross-origin relative to the
  main page.  window.parent.document access is blocked by the browser.

  Solution: Use Streamlit's st.query_params as the bridge.
    1. Voice panel JS writes the turn data into window.location (hash)
       of the LISTENER iframe.
    2. The listener iframe is served at the same origin as the main page
       (it uses window.parent.location.hash — same-origin, always works).
    3. A st.query_params polling trick: the listener writes to
       window.parent.location.hash which Streamlit DOES allow.
    4. We read window.location.hash in Python via a hidden st.text_input
       that the JS updates via the React setter — same approach as mic btn.

  Actually the simplest reliable approach for Streamlit:
    - Voice panel calls window.parent.postMessage (cross-origin allowed for
      POSTING, just not DOM access).
    - The MAIN PAGE (not a sub-iframe) has a <script> that receives it
      and writes the hidden input. We inject that script via st.markdown.
    - st.markdown scripts DO execute in the main page context.
"""
from __future__ import annotations

import json
import re
import streamlit as st
import requests
import streamlit.components.v1 as components
from datetime import datetime

BACKEND_URL = "http://localhost:8000"

_CATEGORY_META = {
    "Stable":            {"color": "#48bb78", "icon": "●"},
    "Mild Stress":       {"color": "#68d391", "icon": "●"},
    "Moderate Distress": {"color": "#ed8936", "icon": "●"},
    "Depression Risk":   {"color": "#fc8181", "icon": "▲"},
    "High Risk":         {"color": "#f56565", "icon": "▲"},
    "Crisis Risk":       {"color": "#fc4e4e", "icon": "⚠"},
}

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

_PREFERRED_VOICES = json.dumps([
    "Google UK English Female", "Samantha", "Karen",
    "Moira", "Tessa", "Victoria", "Google US English",
])


# ── CSS ───────────────────────────────────────────────────────────────────────

_CSS = """
<style>
.empty-state{text-align:center;padding:3.2rem 1rem 1.5rem;}
.empty-orb{
    width:72px;height:72px;border-radius:50%;
    background:radial-gradient(circle at 38% 35%,#63b3ed 0%,#4fd1c5 50%,#7c3aed 100%);
    margin:0 auto 1.1rem;animation:orbIdle 4s ease-in-out infinite;
}
@keyframes orbIdle{
    0%,100%{box-shadow:0 0 0 0 rgba(99,179,237,0),0 8px 32px rgba(99,179,237,0.2);transform:scale(1);}
    35%{box-shadow:0 0 0 9px rgba(99,179,237,0.07),0 8px 40px rgba(79,209,197,0.30);transform:scale(1.05);}
    70%{box-shadow:0 0 0 5px rgba(79,209,197,0.05),0 8px 36px rgba(99,179,237,0.24);transform:scale(1.02);}
}
.empty-headline{font-size:1.08rem;font-weight:600;color:#e8edf5;letter-spacing:-0.02em;margin-bottom:.4rem;}
.empty-sub{font-size:.80rem;color:#546070;line-height:1.75;max-width:275px;margin:0 auto 1.6rem;}
.empty-pills{display:flex;justify-content:center;gap:9px;flex-wrap:wrap;}
.empty-pill{font-size:.66rem;color:#3a4555;display:flex;align-items:center;gap:5px;padding:4px 10px;border:1px solid rgba(255,255,255,0.05);border-radius:20px;background:rgba(255,255,255,0.02);}
.empty-pill-dot{width:5px;height:5px;border-radius:50%;}
.typing-wrap{display:inline-flex;align-items:center;gap:5px;padding:11px 15px;background:rgba(26,32,53,0.85);border:1px solid rgba(255,255,255,0.06);border-radius:14px;border-bottom-left-radius:4px;}
.typing-dot{width:7px;height:7px;border-radius:50%;background:#546070;animation:typingBounce 1.3s ease-in-out infinite;}
.typing-dot:nth-child(1){animation-delay:0s;}.typing-dot:nth-child(2){animation-delay:.18s;}.typing-dot:nth-child(3){animation-delay:.36s;}
@keyframes typingBounce{0%,60%,100%{transform:translateY(0);opacity:.35;}30%{transform:translateY(-6px);opacity:1;}}
.msg-meta{display:flex;align-items:center;gap:5px;margin-top:7px;flex-wrap:wrap;}
.meta-chip{font-size:.60rem;font-weight:500;letter-spacing:.05em;padding:2px 8px;border-radius:20px;text-transform:capitalize;}
.chip-emotion{background:rgba(99,179,237,.10);color:#63b3ed;border:1px solid rgba(99,179,237,.18);}
.chip-mhi{background:rgba(79,209,197,.09);color:#4fd1c5;border:1px solid rgba(79,209,197,.16);}
.chip-category{border:1px solid;}
.speaking-row{display:inline-flex;align-items:center;gap:7px;padding:5px 11px;background:rgba(79,209,197,.08);border:1px solid rgba(79,209,197,.20);border-radius:20px;font-size:.70rem;color:#4fd1c5;margin-top:8px;animation:fadeUp .3s ease;}
.spk-bars{display:flex;align-items:flex-end;gap:2px;height:13px;}
.spk-bar{width:2px;background:#4fd1c5;border-radius:1px;height:3px;animation:spkPulse .65s ease-in-out infinite;}
.spk-bar:nth-child(1){animation-delay:.00s}.spk-bar:nth-child(2){animation-delay:.11s}.spk-bar:nth-child(3){animation-delay:.22s}.spk-bar:nth-child(4){animation-delay:.11s}.spk-bar:nth-child(5){animation-delay:.00s}
@keyframes spkPulse{0%,100%{height:3px;}50%{height:12px;}}
.crisis-passive,.crisis-active{display:flex;align-items:flex-start;gap:10px;border-radius:12px;padding:11px 14px;font-size:.75rem;line-height:1.6;margin-top:10px;animation:fadeUp .35s ease;}
.crisis-passive{background:rgba(237,137,54,.09);border:1px solid rgba(237,137,54,.25);color:#ed8936;}
.crisis-active{background:rgba(252,78,78,.10);border:1px solid rgba(252,78,78,.30);color:#fc8181;}
[data-testid="stChatInput"] textarea{padding-right:5.5rem!important}
[data-testid="stBottom"]{position:relative!important}
[data-testid="stBottom"]>div{position:relative!important}
[data-testid="stBottom"] iframe{position:absolute!important;right:54px!important;bottom:13px!important;width:36px!important;height:36px!important;z-index:200!important;border:none!important;background:transparent!important;pointer-events:all!important}
div[data-testid="stTextInput"]:has(input[aria-label="__vsync__"]){position:absolute!important;width:1px!important;height:1px!important;overflow:hidden!important;opacity:0!important;pointer-events:none!important;}
@keyframes fadeUp{from{opacity:0;transform:translateY(6px);}to{opacity:1;transform:translateY(0);}}
</style>
"""

# ── postMessage listener injected into MAIN page via st.markdown ──────────────
# st.markdown scripts run in the top-level Streamlit page context, NOT inside
# an iframe. So window here IS the main page — postMessage from the voice
# panel iframe arrives here correctly.
#
# When we receive VOICE_TURN we write the JSON into the hidden st.text_input
# using the React native setter. Streamlit registers the change and the
# Python code reads it on the next rerun.

def _inject_postmessage_listener() -> None:
    st.markdown("""
    <script>
    (function(){
        // Avoid registering multiple listeners on reruns
        if (window.__voiceSyncRegistered) return;
        window.__voiceSyncRegistered = true;

        window.addEventListener('message', function(evt) {
            if (!evt.data || evt.data.type !== 'VOICE_TURN') return;
            try {
                var payload = JSON.stringify(evt.data);
                // Find the hidden sync input by aria-label
                var inputs = document.querySelectorAll('input[type="text"]');
                var syncInput = null;
                for (var i = 0; i < inputs.length; i++) {
                    if (inputs[i].getAttribute('aria-label') === '__vsync__') {
                        syncInput = inputs[i];
                        break;
                    }
                }
                if (!syncInput) return;
                var setter = Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype, 'value'
                ).set;
                setter.call(syncInput, payload);
                syncInput.dispatchEvent(new Event('input',  {bubbles: true}));
                syncInput.dispatchEvent(new Event('change', {bubbles: true}));
            } catch(e) {
                console.debug('vsync error:', e);
            }
        });
    })();
    </script>
    """, unsafe_allow_html=True)


# ── Voice panel HTML ──────────────────────────────────────────────────────────

def _build_voice_panel(backend_url: str, jwt: str) -> str:
    profiles_json = json.dumps(_WEB_SPEECH_PROFILES)
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@400;500;600&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
html,body{{font-family:'Sora',sans-serif;background:transparent;color:#e8edf5;width:100%;overflow-x:hidden;}}
.orb-section{{display:flex;flex-direction:column;align-items:center;padding:20px 0 8px;gap:10px;}}
.orb{{width:90px;height:90px;border-radius:50%;cursor:pointer;border:none;outline:none;position:relative;flex-shrink:0;background:radial-gradient(circle at 38% 32%,#63b3ed 0%,#4fd1c5 50%,#7c3aed 100%);animation:orbIdle 4s ease-in-out infinite;transition:transform .15s ease;}}
.orb:hover{{transform:scale(1.06);}} .orb:active{{transform:scale(0.96);}}
.orb.listening{{background:radial-gradient(circle at 38% 32%,#fc8181 0%,#f6ad55 50%,#fc4e4e 100%)!important;animation:orbListen .6s ease-in-out infinite!important;}}
.orb.thinking {{background:radial-gradient(circle at 38% 32%,#b794f4 0%,#7c3aed 50%,#553c9a 100%)!important;animation:orbThink  1s ease-in-out infinite!important;}}
.orb.speaking {{animation:orbSpeak .7s ease-in-out infinite!important;}}
@keyframes orbIdle{{0%,100%{{box-shadow:0 0 0 0 rgba(99,179,237,0),0 12px 40px rgba(99,179,237,.20);transform:scale(1);}}40%{{box-shadow:0 0 0 9px rgba(99,179,237,.07),0 12px 48px rgba(79,209,197,.28);transform:scale(1.04);}}80%{{box-shadow:0 0 0 5px rgba(79,209,197,.04),0 12px 44px rgba(99,179,237,.22);transform:scale(1.02);}}}}
@keyframes orbListen{{0%,100%{{box-shadow:0 0 0 0 rgba(252,129,129,.8);transform:scale(1);}}50%{{box-shadow:0 0 0 26px rgba(252,129,129,0);transform:scale(1.12);}}}}
@keyframes orbThink {{0%,100%{{box-shadow:0 0 0 0 rgba(183,148,244,.7);transform:scale(1);}}50%{{box-shadow:0 0 0 22px rgba(183,148,244,0);transform:scale(1.07);}}}}
@keyframes orbSpeak {{0%,100%{{box-shadow:0 0 0 0 rgba(99,179,237,.8);transform:scale(1.02);}}50%{{box-shadow:0 0 0 24px rgba(99,179,237,0);transform:scale(1.12);}}}}
.orb-waves{{display:none;position:absolute;bottom:18px;left:50%;transform:translateX(-50%);align-items:flex-end;gap:3px;height:22px;}}
.orb.listening .orb-waves{{display:flex;}}
.ow{{width:3px;border-radius:2px;background:rgba(255,255,255,.9);height:4px;animation:owAnim .55s ease-in-out infinite;}}
.ow:nth-child(1){{animation-delay:.00s}}.ow:nth-child(2){{animation-delay:.10s}}.ow:nth-child(3){{animation-delay:.20s}}.ow:nth-child(4){{animation-delay:.10s}}.ow:nth-child(5){{animation-delay:.00s}}
@keyframes owAnim{{0%,100%{{height:4px;opacity:.5;}}50%{{height:20px;opacity:1;}}}}
.orb-status{{font-size:.66rem;color:#546070;letter-spacing:.09em;text-transform:uppercase;height:16px;text-align:center;}}
.controls{{display:flex;gap:8px;padding:0 14px 10px;}}
.ctrl-btn{{flex:1;padding:9px 0;border:none;border-radius:10px;font-family:'Sora',sans-serif;font-size:.71rem;font-weight:600;letter-spacing:.04em;cursor:pointer;transition:opacity .15s,transform .12s;}}
.ctrl-btn:hover{{opacity:.82;}} .ctrl-btn:active{{transform:scale(.97);}}
.btn-start{{background:linear-gradient(135deg,#2a6496,#1a7a6e);color:#e8f4ff;}}
.btn-stop {{background:rgba(252,129,129,.14);color:#fc8181;border:1px solid rgba(252,129,129,.28);}}
.btn-mute {{background:rgba(255,255,255,.05);color:#8b9ab0;border:1px solid rgba(255,255,255,.08);}}
.panel-crisis{{margin:0 12px 8px;padding:9px 13px;border-radius:10px;font-size:.70rem;line-height:1.55;display:none;}}
.panel-crisis.show{{display:block;animation:fadeUp .3s ease;}}
.panel-crisis.passive{{background:rgba(237,137,54,.10);border:1px solid rgba(237,137,54,.28);color:#ed8936;}}
.panel-crisis.active {{background:rgba(252,78,78,.12); border:1px solid rgba(252,78,78,.30); color:#fc8181;}}
.transcript{{margin:0 12px 10px;border:1px solid rgba(255,255,255,.07);border-radius:14px;background:rgba(8,12,24,.60);backdrop-filter:blur(8px);overflow-y:auto;max-height:265px;padding:10px;scroll-behavior:smooth;}}
.transcript::-webkit-scrollbar{{width:3px;}} .transcript::-webkit-scrollbar-thumb{{background:rgba(255,255,255,.09);border-radius:2px;}}
.turn{{margin-bottom:13px;animation:fadeUp .28s ease;}}
.turn-row{{display:flex;align-items:flex-start;gap:8px;}}
.turn-row.user-row{{flex-direction:row-reverse;}}
.avatar{{width:27px;height:27px;border-radius:50%;flex-shrink:0;display:flex;align-items:center;justify-content:center;font-size:.57rem;font-weight:700;letter-spacing:.02em;}}
.avatar-ai  {{background:linear-gradient(135deg,#1a3050,#0d2840);color:#4fd1c5;border:1px solid rgba(79,209,197,.22);}}
.avatar-user{{background:linear-gradient(135deg,#1e3a5f,#162d4a);color:#63b3ed;border:1px solid rgba(99,179,237,.22);}}
.bubble{{max-width:80%;padding:9px 13px;font-size:.77rem;line-height:1.62;word-break:break-word;}}
.bubble-ai  {{background:rgba(26,32,53,.92);border:1px solid rgba(255,255,255,.07);border-radius:4px 14px 14px 14px;color:#c8d4e6;}}
.bubble-user{{background:rgba(30,58,95,.88);border:1px solid rgba(99,179,237,.16);border-radius:14px 4px 14px 14px;color:#bdd4f0;}}
.turn-meta{{font-size:.58rem;color:#2e3a4a;margin-top:4px;display:flex;align-items:center;gap:5px;}}
.turn-row.user-row .turn-meta{{justify-content:flex-end;}}
.meta-dot{{width:4px;height:4px;border-radius:50%;}}
.panel-footer{{text-align:center;font-size:.58rem;color:#1e2a38;letter-spacing:.06em;padding-bottom:10px;}}
@keyframes fadeUp{{from{{opacity:0;transform:translateY(5px);}}to{{opacity:1;transform:translateY(0);}}}}
</style>
</head>
<body>
<div class="orb-section">
    <button class="orb" id="orb">
        <div class="orb-waves"><div class="ow"></div><div class="ow"></div><div class="ow"></div><div class="ow"></div><div class="ow"></div></div>
    </button>
    <div class="orb-status" id="orbStatus">Tap orb · or press Start</div>
</div>
<div class="controls">
    <button class="ctrl-btn btn-start" id="btnStart">▶&nbsp; Start</button>
    <button class="ctrl-btn btn-stop"  id="btnStop" >■&nbsp; Stop</button>
    <button class="ctrl-btn btn-mute"  id="btnMute" >🔇&nbsp; Mute</button>
</div>
<div class="panel-crisis" id="panelCrisis"></div>
<div class="transcript"   id="transcript"></div>
<div class="panel-footer">Voice session &nbsp;·&nbsp; Scroll to review</div>

<script>
(function(){{
    const BACKEND  = "{backend_url}";
    const JWT      = "{jwt}";
    const PROFILES = {profiles_json};
    const PREFERRED= {_PREFERRED_VOICES};

    const orb=document.getElementById('orb'),orbStatus=document.getElementById('orbStatus');
    const trans=document.getElementById('transcript'),crisis=document.getElementById('panelCrisis');
    const btnStart=document.getElementById('btnStart'),btnStop=document.getElementById('btnStop'),btnMute=document.getElementById('btnMute');

    let recorder=null,audioChunks=[],stream=null;
    let isListening=false,isProcessing=false,isMuted=false,continuous=false,srFallback='';

    function setStatus(t){{orbStatus.textContent=t;}}
    function setOrb(s){{orb.classList.remove('listening','thinking','speaking');if(s)orb.classList.add(s);}}
    function hhmm(){{return new Date().toLocaleTimeString([],{{hour:'2-digit',minute:'2-digit'}});}}

    function appendTurn(role,text,meta){{
        const isUser=role==='user';
        const div=document.createElement('div');
        div.className='turn';
        const catColor=(meta&&meta.catColor)?meta.catColor:'#546070';
        const metaHtml=meta?`<span class="meta-dot" style="background:${{catColor}}"></span>MHI&nbsp;${{meta.mhi}}&nbsp;·&nbsp;${{meta.category}}`:'';
        div.innerHTML=`<div class="turn-row ${{isUser?'user-row':''}}"><div class="avatar ${{isUser?'avatar-user':'avatar-ai'}}">${{isUser?'You':'AI'}}</div><div style="flex:1;min-width:0;"><div class="bubble ${{isUser?'bubble-user':'bubble-ai'}}">${{text}}</div><div class="turn-meta">${{hhmm()}}${{metaHtml}}</div></div></div>`;
        trans.appendChild(div);
        trans.scrollTop=trans.scrollHeight;
    }}

    function showCrisis(tier,score){{
        if(tier==='active'||score>=0.85){{crisis.className='panel-crisis active show';crisis.innerHTML='⚠ Please reach out now — <strong>AASRA:</strong> +91-9820466626 &nbsp;·&nbsp; <strong>Kiran:</strong> 1800-599-0019';}}
        else if(tier==='passive'||score>=0.55){{crisis.className='panel-crisis passive show';crisis.innerHTML='Support is here — <strong>Kiran:</strong> 1800-599-0019 &nbsp;·&nbsp; <strong>Vandrevala:</strong> +91-1860-2662-345';}}
        else{{crisis.className='panel-crisis';}}
    }}

    function greet(){{
        const msg="Hi there. I'm your Well-Being companion. This is a safe, private space — just for you. Whenever you're ready, just speak and I'll listen.";
        appendTurn('assistant',msg,null);
        if(!isMuted)speakWS(msg,'default','none').catch(()=>{{}});
    }}

    async function speakResponse(text,emotion,tier){{
        if(isMuted)return;
        setOrb('speaking');setStatus('Speaking…');
        try{{
            const res=await fetch(`${{BACKEND}}/voice/speak`,{{method:'POST',headers:{{'Content-Type':'application/json','Authorization':`Bearer ${{JWT}}`}},body:JSON.stringify({{text,emotion_label:emotion,crisis_tier:tier}})}});
            if(!res.ok)throw new Error('tts');
            const blob=await res.blob();
            const url=URL.createObjectURL(blob);
            const aud=new Audio(url);
            await new Promise(r=>{{aud.onended=r;aud.onerror=r;aud.play().catch(r);}});
            URL.revokeObjectURL(url);
        }}catch(_){{await speakWS(text,emotion,tier);}}
        setOrb('');
    }}

    function speakWS(text,emotion,tier){{
        return new Promise(resolve=>{{
            window.speechSynthesis.cancel();
            const key=(tier==='active'||tier==='passive')?'crisis':(emotion||'default');
            const p=PROFILES[key]||PROFILES['default'];
            const u=new SpeechSynthesisUtterance(text.replace(/[*#`_]/g,''));
            u.rate=p.rate;u.pitch=p.pitch;u.volume=p.volume;
            function go(){{const vs=window.speechSynthesis.getVoices();for(const n of PREFERRED){{const v=vs.find(x=>x.name===n);if(v){{u.voice=v;break;}}}}u.onend=resolve;u.onerror=resolve;window.speechSynthesis.speak(u);}}
            window.speechSynthesis.getVoices().length>0?go():(window.speechSynthesis.onvoiceschanged=go);
        }});
    }}

    async function transcribeBlob(blob){{
        try{{
            const form=new FormData();form.append('audio',blob,'recording.webm');
            const res=await fetch(`${{BACKEND}}/voice/transcribe`,{{method:'POST',headers:{{'Authorization':`Bearer ${{JWT}}`}},body:form}});
            if(!res.ok)return null;
            const data=await res.json();return data.transcript||'';
        }}catch(_){{return null;}}
    }}

    // ── Dashboard sync via postMessage to parent window ──────────────────────
    // The MAIN Streamlit page has a listener injected by _inject_postmessage_listener()
    // postMessage from iframe → parent is ALWAYS allowed regardless of cross-origin.
    function syncDashboard(userText,reply,mhi,category,tier){{
        try{{
            window.parent.postMessage({{
                type:'VOICE_TURN',
                user_text:userText,
                assistant_text:reply,
                mhi:mhi,
                category:category,
                crisis_tier:tier,
                ts:new Date().toISOString()
            }},'*');
        }}catch(e){{console.debug('syncDashboard error:',e);}}
    }}

    async function sendChat(text){{
        setOrb('thinking');setStatus('Thinking…');
        try{{
            const res=await fetch(`${{BACKEND}}/chat`,{{method:'POST',headers:{{'Content-Type':'application/json','Authorization':`Bearer ${{JWT}}`}},body:JSON.stringify({{message:text}})}});
            if(!res.ok)throw new Error('chat');
            const data=await res.json();
            const reply=data.response||'',mhi=data.mhi||0,category=data.category||'',tier=data.crisis_tier||'none',score=data.crisis_score||0;
            const scores=data.emotion_scores||{{}},emotion=Object.keys(scores).reduce((a,b)=>scores[a]>scores[b]?a:b,'neutral');
            const catColors={{"Stable":"#48bb78","Mild Stress":"#68d391","Moderate Distress":"#ed8936","Depression Risk":"#fc8181","High Risk":"#f56565","Crisis Risk":"#fc4e4e"}};
            showCrisis(tier,score);
            appendTurn('assistant',reply,{{mhi,category,catColor:catColors[category]||'#546070'}});
            syncDashboard(text,reply,mhi,category,tier);
            await speakResponse(reply,emotion,tier);
            if(continuous&&tier!=='active'){{startListening();}}
            else{{setOrb('');setStatus(continuous?'Listening…':'Tap orb to speak again');isProcessing=false;}}
        }}catch(e){{
            console.error('Chat error:',e);setOrb('');setStatus('Error — tap to retry');isProcessing=false;
        }}
    }}

    async function startListening(){{
        if(isListening||isProcessing)return;
        try{{stream=await navigator.mediaDevices.getUserMedia({{audio:true}});}}
        catch(_){{setStatus('Microphone access denied');return;}}
        audioChunks=[];srFallback='';
        const mime=MediaRecorder.isTypeSupported('audio/webm;codecs=opus')?'audio/webm;codecs=opus':'audio/webm';
        recorder=new MediaRecorder(stream,{{mimeType:mime}});
        recorder.ondataavailable=e=>{{if(e.data?.size>0)audioChunks.push(e.data);}};
        const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
        let sr=null;
        if(SR){{sr=new SR();sr.lang='en-US';sr.interimResults=false;sr.continuous=false;sr.onresult=e=>{{for(let i=e.resultIndex;i<e.results.length;i++)if(e.results[i].isFinal)srFallback+=e.results[i][0].transcript;}};try{{sr.start();}}catch(_){{}}}}
        recorder.onstop=async()=>{{
            if(sr)try{{sr.stop();}}catch(_){{}}
            stream?.getTracks().forEach(t=>t.stop());stream=null;isListening=false;isProcessing=true;
            const blob=new Blob(audioChunks,{{type:'audio/webm'}});
            setOrb('thinking');setStatus('Processing…');
            let text=await transcribeBlob(blob);
            if(text===null||text==='')text=srFallback;
            if(!text?.trim()){{setStatus('No speech — tap orb to try again');setOrb('');isProcessing=false;if(continuous)setTimeout(startListening,1200);return;}}
            appendTurn('user',text,null);
            await sendChat(text);
        }};
        recorder.start(250);isListening=true;setOrb('listening');setStatus('Listening… tap orb to stop');
        let autoStop=setTimeout(()=>stopRecording(),9000);
        orb.onclick=()=>{{clearTimeout(autoStop);stopRecording();}};
    }}

    function stopRecording(){{if(!isListening)return;if(recorder?.state!=='inactive')recorder.stop();}}

    btnStart.addEventListener('click',()=>{{continuous=true;window.speechSynthesis.cancel();if(!isListening&&!isProcessing)startListening();}});
    btnStop.addEventListener('click',()=>{{continuous=false;if(isListening)stopRecording();window.speechSynthesis.cancel();setOrb('');setStatus('Stopped — tap orb or Start to resume');isProcessing=false;}});
    btnMute.addEventListener('click',()=>{{isMuted=!isMuted;btnMute.textContent=isMuted?'🔊  Unmute':'🔇  Mute';if(isMuted)window.speechSynthesis.cancel();}});
    orb.addEventListener('click',()=>{{if(isProcessing)return;if(isListening){{stopRecording();}}else{{continuous=false;startListening();}}}});

    greet();
}})();
</script>
</body>
</html>"""


# ── Compact mic button ────────────────────────────────────────────────────────

_MIC_BTN_HTML = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{margin:0;padding:0;box-sizing:border-box;}html,body{width:36px;height:36px;overflow:hidden;background:transparent;}
#b{width:36px;height:36px;border-radius:50%;border:none;background:transparent;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:background .18s;outline:none;}
#b:hover{background:rgba(99,179,237,.12);}#b.on{background:rgba(252,129,129,.14);animation:g 1.4s ease-out infinite;}
@keyframes g{0%{box-shadow:0 0 0 0 rgba(252,129,129,.6);}70%{box-shadow:0 0 0 10px rgba(252,129,129,0);}100%{box-shadow:0 0 0 0 rgba(252,129,129,0);}}
#ws{display:none;align-items:flex-end;justify-content:center;gap:2px;height:18px;}#ws.on{display:flex;}
.w{width:2px;border-radius:1px;background:#fc8181;height:3px;animation:wv .7s ease-in-out infinite;}
.w:nth-child(1){animation-delay:.00s}.w:nth-child(2){animation-delay:.10s}.w:nth-child(3){animation-delay:.20s}
.w:nth-child(4){animation-delay:.30s}.w:nth-child(5){animation-delay:.20s}.w:nth-child(6){animation-delay:.10s}.w:nth-child(7){animation-delay:.00s}
@keyframes wv{0%,100%{height:3px;opacity:.5;}50%{height:16px;opacity:1;}}
</style></head><body>
<button id="b" title="Tap to speak">
<svg id="mic" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#63b3ed" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
<line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>
<div id="ws"><div class="w"></div><div class="w"></div><div class="w"></div><div class="w"></div><div class="w"></div><div class="w"></div><div class="w"></div></div>
</button>
<script>
(function(){
    const b=document.getElementById('b'),m=document.getElementById('mic'),ws=document.getElementById('ws');
    let r=null,on=false;
    const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
    if(!SR){b.style.opacity='.3';return;}
    function setOn(v){on=v;b.classList.toggle('on',v);m.style.display=v?'none':'block';ws.classList.toggle('on',v);}
    function inject(t){
        const ta=window.parent.document.querySelector('textarea[data-testid="stChatInputTextArea"]');
        if(!ta)return;
        const s=Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype,'value').set;
        s.call(ta,t);ta.dispatchEvent(new Event('input',{bubbles:true}));ta.dispatchEvent(new Event('change',{bubbles:true}));ta.focus();
    }
    function go(){r=new SR();r.lang='en-US';r.interimResults=true;r.continuous=false;r.onstart=()=>setOn(true);r.onresult=e=>{let f='';for(let i=e.resultIndex;i<e.results.length;i++)if(e.results[i].isFinal)f+=e.results[i][0].transcript;if(f){inject(f.trim());stop();}};r.onerror=()=>stop();r.onend=()=>setOn(false);try{r.start();}catch(_){setOn(false);}}
    function stop(){if(r){try{r.stop();}catch(_){}r=null;}setOn(false);}
    b.addEventListener('click',()=>on?stop():go());
})();
</script></body></html>"""


# ── Backend helpers ───────────────────────────────────────────────────────────

def _headers():
    jwt = st.session_state.get("jwt")
    if not jwt: raise Exception("not authenticated")
    return {"Authorization": f"Bearer {jwt}"}

def send_chat(message: str) -> dict:
    r = requests.post(f"{BACKEND_URL}/chat", json={"message": message}, headers=_headers(), timeout=30)
    r.raise_for_status()
    return r.json()

def get_report() -> bytes:
    r = requests.get(f"{BACKEND_URL}/report", headers=_headers(), timeout=30)
    r.raise_for_status()
    return r.content

def get_timeline() -> list:
    r = requests.get(f"{BACKEND_URL}/user/timeline", headers=_headers(), timeout=10)
    r.raise_for_status()
    return r.json()


# ── UI sub-components ─────────────────────────────────────────────────────────

def _empty_state():
    st.markdown("""<div class="empty-state"><div class="empty-orb"></div>
    <div class="empty-headline">How are you feeling today?</div>
    <div class="empty-sub">A safe, private space — just for you.<br>Share whatever is on your mind.</div>
    <div class="empty-pills">
        <span class="empty-pill"><span class="empty-pill-dot" style="background:#63b3ed;"></span>Emotion aware</span>
        <span class="empty-pill"><span class="empty-pill-dot" style="background:#4fd1c5;"></span>Always private</span>
        <span class="empty-pill"><span class="empty-pill-dot" style="background:#b794f4;"></span>CBT guided</span>
    </div></div>""", unsafe_allow_html=True)

def _msg_meta(emotion, mhi, category):
    meta = _CATEGORY_META.get(category, {"color": "#546070", "icon": "●"})
    st.markdown(f"""<div class="msg-meta">
        <span class="meta-chip chip-emotion">{emotion}</span>
        <span class="meta-chip chip-mhi">MHI&nbsp;{mhi}</span>
        <span class="meta-chip chip-category" style="color:{meta['color']};border-color:{meta['color']}33;background:{meta['color']}12;">{meta['icon']}&nbsp;{category}</span>
    </div>""", unsafe_allow_html=True)

def _crisis_banner(tier, score):
    if tier == "active" or score >= 0.85:
        st.markdown("""<div class="crisis-active"><span style="font-size:1rem;">⚠</span>
        <span>Your safety matters. Please reach out right now:<br>
        <strong>AASRA:</strong> +91-9820466626 &nbsp;·&nbsp; <strong>Kiran:</strong> 1800-599-0019 (free, 24/7) &nbsp;·&nbsp; <strong>iCall:</strong> +91-9152987821</span></div>""", unsafe_allow_html=True)
    elif tier == "passive" or score >= 0.55:
        st.markdown("""<div class="crisis-passive"><span style="font-size:1rem;">◈</span>
        <span>What you shared sounds really heavy. Real support is here —<br>
        <strong>Kiran:</strong> 1800-599-0019 &nbsp;·&nbsp; <strong>Vandrevala:</strong> +91-1860-2662-345</span></div>""", unsafe_allow_html=True)

def _speaking_row():
    st.markdown("""<div class="speaking-row">
        <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/></svg>
        <span>Speaking</span>
        <div class="spk-bars"><div class="spk-bar"></div><div class="spk-bar"></div><div class="spk-bar"></div><div class="spk-bar"></div><div class="spk-bar"></div></div>
    </div>""", unsafe_allow_html=True)

def _speak_text_js(text, emotion, tier):
    clean = re.sub(r"\*{1,3}|#{1,6}\s?|`{1,3}|_{1,2}|-{2,}|\[|\]|\(.*?\)", "", text)
    clean = re.sub(r"\n+", " ", clean).strip()
    safe  = clean.replace("\\","\\\\").replace('"','\\"').replace("'","\\'")
    profile = _WEB_SPEECH_PROFILES["crisis"] if tier in ("active","passive") \
              else _WEB_SPEECH_PROFILES.get(emotion, _WEB_SPEECH_PROFILES["default"])
    st.markdown(f"""<script>(function(){{window.speechSynthesis.cancel();const u=new SpeechSynthesisUtterance("{safe}");u.rate={profile['rate']};u.pitch={profile['pitch']};u.volume={profile['volume']};const pref={_PREFERRED_VOICES};function go(){{const vs=window.speechSynthesis.getVoices();for(const n of pref){{const v=vs.find(x=>x.name===n);if(v){{u.voice=v;break;}}}}window.speechSynthesis.speak(u);}}window.speechSynthesis.getVoices().length>0?go():(window.speechSynthesis.onvoiceschanged=go);}})();</script>""", unsafe_allow_html=True)

def _cancel_speech_js():
    st.markdown("<script>window.speechSynthesis.cancel();</script>", unsafe_allow_html=True)


# ── Mode renders ──────────────────────────────────────────────────────────────

def _render_text_mode(voice_enabled: bool) -> None:
    if not st.session_state.chat_history:
        _empty_state()

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and msg.get("meta"):
                m = msg["meta"]
                _msg_meta(m.get("emotion","neutral"), m.get("mhi",0), m.get("category",""))

    st.markdown("""<style>
    [data-testid="stChatInput"] textarea{padding-right:5.5rem!important}
    [data-testid="stBottom"]{position:relative!important}
    [data-testid="stBottom"]>div{position:relative!important}
    [data-testid="stBottom"] iframe{position:absolute!important;right:54px!important;bottom:13px!important;width:36px!important;height:36px!important;z-index:200!important;border:none!important;background:transparent!important;pointer-events:all!important}
    </style>""", unsafe_allow_html=True)
    components.html(_MIC_BTN_HTML, height=36, scrolling=False)

    user_input = st.chat_input("Share how you're feeling…")
    if not user_input:
        return

    _cancel_speech_js()
    st.session_state.chat_history.append({"role":"user","content":user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        ph = st.empty()
        ph.markdown('<div class="typing-wrap"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div>', unsafe_allow_html=True)
        try:
            data         = send_chat(user_input)
            reply        = data.get("response","")
            mhi          = data.get("mhi",0)
            category     = data.get("category","")
            crisis_score = data.get("crisis_score",0.0)
            crisis_tier  = data.get("crisis_tier","none")
            scores       = data.get("emotion_scores",{"neutral":1.0})
            emotion      = max(scores, key=scores.get)

            if mhi:
                st.session_state.mhi_log.append({
                    "timestamp": datetime.now().isoformat(),
                    "mhi": mhi, "category": category, "source": "text",
                })
            st.session_state.chat_history.append({
                "role":"assistant","content":reply,
                "meta":{"emotion":emotion,"mhi":mhi,"category":category},
            })
            ph.empty()
            st.markdown(reply)
            _msg_meta(emotion, mhi, category)
            if voice_enabled and reply:
                _speak_text_js(reply, emotion, crisis_tier)
                _speaking_row()
            _crisis_banner(crisis_tier, crisis_score)

        except Exception as exc:
            ph.empty()
            if "not authenticated" in str(exc).lower():
                st.error("Session expired — please log in again.")
                st.session_state.pop("jwt", None)
            else:
                st.error("Something went wrong. Please try again.")


def _render_voice_mode() -> None:
    jwt = st.session_state.get("jwt","")
    if not jwt:
        st.warning("Not authenticated.")
        return

    # ── Inject postMessage listener into the MAIN page context ───────────────
    # This is the key fix: st.markdown scripts run in the top Streamlit window,
    # NOT inside an iframe. So this listener correctly receives postMessages
    # from the voice panel iframe and writes to the hidden input below.
    _inject_postmessage_listener()

    # ── Hidden sync input (invisible data bridge) ─────────────────────────────
    raw_sync = st.text_input(
        "vsync",
        value="",
        key="voice_sync_bridge",
        label_visibility="hidden",
    )
    # Override label so JS can find it by aria-label="__vsync__"
    st.markdown("""<script>
    (function(){
        var inputs=document.querySelectorAll('input[type="text"]');
        for(var i=0;i<inputs.length;i++){
            var lbl=document.querySelector('label[for="'+inputs[i].id+'"]');
            if(lbl&&lbl.textContent.trim()==='vsync'){
                inputs[i].setAttribute('aria-label','__vsync__');
                break;
            }
        }
    })();
    </script>""", unsafe_allow_html=True)

    # ── Process incoming voice turn data ──────────────────────────────────────
    if raw_sync and raw_sync != st.session_state.get("_last_vsync",""):
        st.session_state["_last_vsync"] = raw_sync
        try:
            turn     = json.loads(raw_sync)
            mhi      = int(turn.get("mhi",0))
            category = str(turn.get("category",""))
            u_text   = str(turn.get("user_text",""))
            a_text   = str(turn.get("assistant_text",""))
            ts       = str(turn.get("ts", datetime.now().isoformat()))

            if mhi and category:
                st.session_state.mhi_log.append({
                    "timestamp": ts,
                    "mhi":       mhi,
                    "category":  category,
                    "source":    "voice",
                })
            if u_text:
                st.session_state.chat_history.append({"role":"user","content":u_text})
            if a_text:
                st.session_state.chat_history.append({
                    "role":"assistant","content":a_text,
                    "meta":{"emotion":"voice","mhi":mhi,"category":category},
                })
            # Force rerun so dashboard updates immediately
            st.rerun()
        except (json.JSONDecodeError, ValueError):
            pass

    st.markdown("""<div style="text-align:center;margin-bottom:6px;">
        <span style="font-size:.74rem;color:#3a4a5a;">
        Press <strong style="color:#63b3ed;">Start</strong> for continuous conversation
        &nbsp;·&nbsp; Tap the orb to speak once</span></div>""", unsafe_allow_html=True)

    components.html(_build_voice_panel(BACKEND_URL, jwt), height=585, scrolling=False)

    st.markdown("""<div style="text-align:center;margin-top:4px;">
        <span style="font-size:.60rem;color:#1e2a38;letter-spacing:.05em;">
        Transcript scrollable above &nbsp;·&nbsp; Switch to 💬 Text to review full history
        </span></div>""", unsafe_allow_html=True)


# ── Main entry ────────────────────────────────────────────────────────────────

def render_chat(voice_enabled: bool = False) -> None:
    if "chat_history" not in st.session_state: st.session_state.chat_history = []
    if "mhi_log"      not in st.session_state: st.session_state.mhi_log      = []
    if "chat_mode"    not in st.session_state: st.session_state.chat_mode    = "text"

    st.markdown(_CSS, unsafe_allow_html=True)

    _, mid, _ = st.columns([1, 2.4, 1])
    with mid:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("💬  Text", use_container_width=True, key="btn_text_mode",
                         type="primary" if st.session_state.chat_mode=="text" else "secondary"):
                _cancel_speech_js()
                st.session_state.chat_mode = "text"
                st.rerun()
        with c2:
            if st.button("🎙  Voice", use_container_width=True, key="btn_voice_mode",
                         type="primary" if st.session_state.chat_mode=="voice" else "secondary"):
                st.session_state.chat_mode = "voice"
                st.rerun()

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    if st.session_state.chat_mode == "voice":
        _render_voice_mode()
    else:
        _render_text_mode(voice_enabled=voice_enabled)
