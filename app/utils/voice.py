import streamlit as st
import streamlit.components.v1 as components


# Compact 36×36 icon-only mic component — designed to sit visually
# inside the right side of Streamlit's chat input bar.
_MIC_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
* { margin:0; padding:0; box-sizing:border-box; }
html, body { width:36px; height:36px; overflow:hidden; background:transparent; }

#btn {
    width: 36px; height: 36px;
    border-radius: 50%;
    border: none;
    background: transparent;
    cursor: pointer;
    display: flex; align-items: center; justify-content: center;
    transition: background 0.2s;
    outline: none;
    position: relative;
}
#btn:hover { background: rgba(99,179,237,0.12); }
#btn.rec   { background: rgba(252,129,129,0.15); animation: glow 1.4s ease-out infinite; }

@keyframes glow {
    0%   { box-shadow: 0 0 0 0   rgba(252,129,129,0.55); }
    70%  { box-shadow: 0 0 0 10px rgba(252,129,129,0);    }
    100% { box-shadow: 0 0 0 0   rgba(252,129,129,0);    }
}

/* wave bars — shown when recording, replacing the icon */
#waves {
    display: none;
    align-items: flex-end;
    justify-content: center;
    gap: 2px;
    height: 18px;
}
#waves.on { display: flex; }
.b {
    width: 2px; border-radius: 1px;
    background: #fc8181; height: 3px;
    animation: wv 0.7s ease-in-out infinite;
}
.b:nth-child(1){animation-delay:0.00s}
.b:nth-child(2){animation-delay:0.10s}
.b:nth-child(3){animation-delay:0.20s}
.b:nth-child(4){animation-delay:0.30s}
.b:nth-child(5){animation-delay:0.20s}
.b:nth-child(6){animation-delay:0.10s}
.b:nth-child(7){animation-delay:0.00s}
@keyframes wv {
    0%,100%{ height:3px; opacity:0.5; }
    50%    { height:16px; opacity:1;  }
}
</style>
</head>
<body>
<button id="btn" title="Hold to speak">
  <!-- mic icon -->
  <svg id="mic" width="17" height="17" viewBox="0 0 24 24" fill="none"
       stroke="#63b3ed" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
    <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
    <line x1="12" y1="19" x2="12" y2="23"/>
    <line x1="8"  y1="23" x2="16" y2="23"/>
  </svg>
  <!-- wave bars (recording state) -->
  <div id="waves">
    <div class="b"></div><div class="b"></div><div class="b"></div>
    <div class="b"></div><div class="b"></div><div class="b"></div>
    <div class="b"></div>
  </div>
</button>

<script>
(function(){
  const btn    = document.getElementById('btn');
  const mic    = document.getElementById('mic');
  const waves  = document.getElementById('waves');
  let recog    = null;
  let active   = false;

  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) { btn.title='Not supported'; btn.style.opacity='0.3'; return; }

  function setActive(on) {
    active = on;
    btn.classList.toggle('rec', on);
    mic.style.display    = on ? 'none'  : 'block';
    waves.classList.toggle('on', on);
  }

  function inject(text) {
    const doc = window.parent.document;
    const ta  = doc.querySelector('textarea[data-testid="stChatInputTextArea"]');
    if (!ta) return;
    const setter = Object.getOwnPropertyDescriptor(
      window.HTMLTextAreaElement.prototype, 'value'
    ).set;
    setter.call(ta, text);
    ta.dispatchEvent(new Event('input',  { bubbles:true }));
    ta.dispatchEvent(new Event('change', { bubbles:true }));
    ta.focus();
  }

  function start() {
    recog = new SR();
    recog.lang = 'en-US';
    recog.interimResults = true;
    recog.continuous = false;

    recog.onstart  = () => setActive(true);
    recog.onresult = (e) => {
      let interim='', final='';
      for (let i=e.resultIndex; i<e.results.length; i++) {
        const t = e.results[i][0].transcript;
        e.results[i].isFinal ? (final+=t) : (interim+=t);
      }
      if (final) {
        inject(final.trim());
        stop();
      }
    };
    recog.onerror = () => stop();
    recog.onend   = () => setActive(false);
    try { recog.start(); } catch(_) { setActive(false); }
  }

  function stop() {
    if (recog) { try { recog.stop(); } catch(_){} recog=null; }
    setActive(false);
  }

  btn.addEventListener('click', () => active ? stop() : start());
})();
</script>
</body>
</html>"""


def render_mic_component() -> None:
    """Renders the compact mic icon (36×36) to be positioned inside the chat input."""
    components.html(_MIC_HTML, height=36, scrolling=False)


def speak_text(text: str) -> None:
    safe = text.replace("\\", "\\\\").replace('"', '\\"').replace('\n', ' ')
    st.markdown(f"""
    <script>
    (function(){{
        var u = new SpeechSynthesisUtterance("{safe}");
        u.rate=0.95; u.pitch=1.0;
        window.speechSynthesis.cancel();
        window.speechSynthesis.speak(u);
    }})();
    </script>
    """, unsafe_allow_html=True)
