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
# ── Sync bridge — runs in a hidden components.html() iframe ───────────────────
# Accesses parent document (same-origin srcdoc) to relay postMessage data
# into the hidden Streamlit text_input, triggering st.rerun().
_SYNC_BRIDGE = """
<script>
(function(){
    if(window.__vSyncBridgeV5) return;
    window.__vSyncBridgeV5 = true;
    try {
        var pdoc = window.parent.document;
        function findInput(){
            var inputs = pdoc.querySelectorAll('input[type="text"]');
            for(var i=0;i<inputs.length;i++){
                var id = inputs[i].id;
                if(!id) continue;
                var lbl = pdoc.querySelector('label[for="'+id+'"]');
                if(lbl && lbl.textContent.indexOf('__vsync_v5_label__') !== -1)
                    return inputs[i];
            }
            return null;
        }
        window.parent.addEventListener('message', function(ev){
            if(!ev.data || ev.data.type !== 'VOICE_TURN_V5') return;
            try {
                var inp = findInput();
                if(!inp) return;
                var payload = JSON.stringify(ev.data);
                var setter = Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype, 'value').set;
                setter.call(inp, payload);
                inp.dispatchEvent(new Event('input',  {bubbles:true}));
                inp.dispatchEvent(new Event('change', {bubbles:true}));
            } catch(e){}
        });
    } catch(e){}
})();
</script>
"""


# ── Language names ────────────────────────────────────────────────────────────
_LANG_NAMES = {
    "hi": "Hindi", "bn": "Bengali", "ta": "Tamil", "te": "Telugu",
    "mr": "Marathi", "gu": "Gujarati", "pa": "Punjabi", "kn": "Kannada",
    "ml": "Malayalam", "ur": "Urdu", "or": "Odia", "as": "Assamese",
    "ne": "Nepali", "sa": "Sanskrit", "en": "English",
}

# ── Greetings per language ────────────────────────────────────────────────────
_GREETINGS = {
    "en": "Hey, really glad you\u2019re here. This is your space \u2014 completely private and just for you. You can talk to me about anything. How are you doing today?",
    "hi": "\u0939\u0948\u0932\u094b, \u092e\u0941\u091d\u0947 \u092c\u0939\u0941\u0924 \u0916\u0941\u0936\u0940 \u0939\u0948 \u0915\u093f \u0906\u092a \u092f\u0939\u093e\u0901 \u0939\u0948\u0902\u0964 \u092f\u0939 \u0906\u092a\u0915\u0940 \u0905\u092a\u0928\u0940 \u091c\u0917\u0939 \u0939\u0948 \u2014 \u092a\u0942\u0930\u0940 \u0924\u0930\u0939 \u0938\u0947 \u0928\u093f\u091c\u0940\u0964 \u0906\u092a \u092e\u0941\u091d\u0938\u0947 \u0915\u093f\u0938\u0940 \u092d\u0940 \u092c\u093e\u0930\u0947 \u092e\u0947\u0902 \u092c\u093e\u0924 \u0915\u0930 \u0938\u0915\u0924\u0947 \u0939\u0948\u0902\u0964 \u0906\u091c \u0906\u092a \u0915\u0948\u0938\u0947 \u0939\u0948\u0902?",
    "bn": "\u09b9\u09cd\u09af\u09be\u09b2\u09cb, \u0986\u09aa\u09a8\u09bf \u098f\u0996\u09be\u09a8\u09c7 \u098f\u09b8\u09c7\u099b\u09c7\u09a8 \u09a6\u09c7\u0996\u09c7 \u0996\u09c1\u09ac \u09ad\u09be\u09b2\u09cb \u09b2\u09be\u0997\u099b\u09c7\u0964 \u098f\u099f\u09be \u0986\u09aa\u09a8\u09be\u09b0 \u09a8\u09bf\u099c\u09c7\u09b0 \u099c\u09be\u09af\u09bc\u0997\u09be \u2014 \u09b8\u09ae\u09cd\u09aa\u09c2\u09b0\u09cd\u09a3 \u09ac\u09cd\u09af\u0995\u09cd\u09a4\u09bf\u0997\u09a4\u0964 \u0986\u09aa\u09a8\u09bf \u0986\u09ae\u09be\u09b0 \u09b8\u09be\u09a5\u09c7 \u09af\u09c7\u0995\u09cb\u09a8\u09cb \u09ac\u09bf\u09b7\u09af\u09bc\u09c7 \u0995\u09a5\u09be \u09ac\u09b2\u09a4\u09c7 \u09aa\u09be\u09b0\u09c7\u09a8\u0964 \u0986\u099c \u0986\u09aa\u09a8\u09bf \u0995\u09c7\u09ae\u09a8 \u0986\u099b\u09c7\u09a8?",
    "ta": "\u0bb5\u0ba3\u0b95\u0bcd\u0b95\u0bae\u0bcd, \u0ba8\u0bc0\u0b99\u0bcd\u0b95\u0bb3\u0bcd \u0b87\u0b99\u0bcd\u0b95\u0bc7 \u0bb5\u0ba8\u0bcd\u0ba4\u0ba4\u0bbf\u0bb2\u0bcd \u0bae\u0bbf\u0b95\u0bb5\u0bc1\u0bae\u0bcd \u0bae\u0b95\u0bbf\u0bb4\u0bcd\u0b9a\u0bcd\u0b9a\u0bbf. \u0b87\u0ba4\u0bc1 \u0b89\u0b99\u0bcd\u0b95\u0bb3\u0bcd \u0b9a\u0bca\u0ba8\u0bcd\u0ba4 \u0b87\u0b9f\u0bae\u0bcd \u2014 \u0bae\u0bc1\u0bb1\u0bcd\u0bb1\u0bbf\u0bb2\u0bc1\u0bae\u0bcd \u0ba4\u0ba9\u0bbf\u0baa\u0bcd\u0baa\u0b9f\u0bcd\u0b9f\u0ba4\u0bc1. \u0ba8\u0bc0\u0b99\u0bcd\u0b95\u0bb3\u0bcd \u0b8e\u0ba4\u0bc8\u0baa\u0bcd \u0baa\u0bb1\u0bcd\u0bb1\u0bbf\u0baf\u0bc1\u0bae\u0bcd \u0b8e\u0ba9\u0bcd\u0ba9\u0bbf\u0b9f\u0bae\u0bcd \u0baa\u0bc7\u0b9a\u0bb2\u0bbe\u0bae\u0bcd. \u0b87\u0ba9\u0bcd\u0bb1\u0bc1 \u0ba8\u0bc0\u0b99\u0bcd\u0b95\u0bb3\u0bcd \u0b8e\u0baa\u0bcd\u0baa\u0b9f\u0bbf \u0b87\u0bb0\u0bc1\u0b95\u0bcd\u0b95\u0bbf\u0bb1\u0bc0\u0bb0\u0bcd\u0b95\u0bb3\u0bcd?",
    "te": "\u0c39\u0c32\u0c4b, \u0c2e\u0c40\u0c30\u0c41 \u0c07\u0c15\u0c4d\u0c15\u0c21 \u0c09\u0c28\u0c4d\u0c28\u0c02\u0c26\u0c41\u0c15\u0c41 \u0c1a\u0c3e\u0c32\u0c3e \u0c38\u0c02\u0c24\u0c4b\u0c37\u0c02. \u0c07\u0c26\u0c3f \u0c2e\u0c40 \u0c38\u0c4d\u0c35\u0c02\u0c24 \u0c38\u0c4d\u0c25\u0c32\u0c02 \u2014 \u0c2a\u0c42\u0c30\u0c4d\u0c24\u0c3f\u0c17\u0c3e \u0c2a\u0c4d\u0c30\u0c48\u0c35\u0c47\u0c1f\u0c4d. \u0c2e\u0c40\u0c30\u0c41 \u0c28\u0c3e\u0c24\u0c4b \u0c0f\u0c26\u0c48\u0c28\u0c3e \u0c17\u0c41\u0c30\u0c3f\u0c02\u0c1a\u0c3f \u0c2e\u0c3e\u0c1f\u0c4d\u0c32\u0c3e\u0c21\u0c35\u0c1a\u0c4d\u0c1a\u0c41. \u0c08\u0c30\u0c4b\u0c1c\u0c41 \u0c2e\u0c40\u0c30\u0c41 \u0c0e\u0c32\u0c3e \u0c09\u0c28\u0c4d\u0c28\u0c3e\u0c30\u0c41?",
    "mr": "\u0939\u0945\u0932\u094b, \u0924\u0941\u092e\u094d\u0939\u0940 \u0907\u0925\u0947 \u0906\u0932\u093e\u0924 \u092f\u093e\u091a\u093e \u0916\u0942\u092a \u0906\u0928\u0902\u0926 \u0935\u093e\u091f\u0924\u094b. \u0939\u0940 \u0924\u0941\u092e\u091a\u0940 \u0938\u094d\u0935\u0924\u0903\u091a\u0940 \u091c\u093e\u0917\u093e \u0906\u0939\u0947 \u2014 \u092a\u0942\u0930\u094d\u0923\u092a\u0923\u0947 \u0916\u093e\u091c\u0917\u0940. \u0924\u0941\u092e\u094d\u0939\u0940 \u092e\u093e\u091d\u094d\u092f\u093e\u0936\u0940 \u0915\u0936\u093e\u092c\u0926\u094d\u0926\u0932\u0939\u0940 \u092c\u094b\u0932\u0942 \u0936\u0915\u0924\u093e. \u0906\u091c \u0924\u0941\u092e\u094d\u0939\u0940 \u0915\u0938\u0947 \u0906\u0939\u093e\u0924?",
    "ur": "\u06c1\u06cc\u0644\u0648\u060c \u0622\u067e \u06cc\u06c1\u0627\u06ba \u0622\u0626\u06d2 \u0645\u062c\u06be\u06d2 \u0628\u06c1\u062a \u062e\u0648\u0634\u06cc \u06c1\u0648\u0626\u06cc\u06d4 \u06cc\u06c1 \u0622\u067e \u06a9\u06cc \u0627\u067e\u0646\u06cc \u062c\u06af\u06c1 \u06c1\u06d2 \u2014 \u0645\u06a9\u0645\u0644 \u0637\u0648\u0631 \u067e\u0631 \u0646\u062c\u06cc\u06d4 \u0622\u067e \u0645\u062c\u06be \u0633\u06d2 \u06a9\u0633\u06cc \u0628\u06be\u06cc \u0628\u0627\u0631\u06d2 \u0645\u06cc\u06ba \u0628\u0627\u062a \u06a9\u0631 \u0633\u06a9\u062a\u06d2 \u06c1\u06cc\u06ba\u06d4 \u0622\u062c \u0622\u067e \u06a9\u06cc\u0633\u06d2 \u06c1\u06cc\u06ba\u061f",
    "gu": "\u0aa8\u0aae\u0ab8\u0acd\u0aa4\u0ac7, \u0aa4\u0aae\u0ac7 \u0a85\u0ab9\u0ac0\u0a82 \u0a86\u0ab5\u0acd\u0aaf\u0abe \u0aa4\u0ac7 \u0a9c\u0acb\u0a88\u0aa8\u0ac7 \u0a96\u0ac2\u0aac \u0a86\u0aa8\u0a82\u0aa6 \u0aa5\u0aaf\u0acb. \u0a86 \u0aa4\u0aae\u0abe\u0ab0\u0ac0 \u0aaa\u0acb\u0aa4\u0abe\u0aa8\u0ac0 \u0a9c\u0a97\u0acd\u0aaf\u0abe \u0a9b\u0ac7 \u2014 \u0aaa\u0ac2\u0ab0\u0ac0 \u0ab0\u0ac0\u0aa4\u0ac7 \u0a96\u0abe\u0aa8\u0a97\u0ac0. \u0aa4\u0aae\u0ac7 \u0aae\u0abe\u0ab0\u0ac0 \u0ab8\u0abe\u0aa5\u0ac7 \u0a95\u0acb\u0a88\u0aaa\u0aa3 \u0ab5\u0abe\u0aa4 \u0a95\u0ab0\u0ac0 \u0ab6\u0a95\u0acb \u0a9b\u0acb. \u0a86\u0a9c\u0ac7 \u0aa4\u0aae\u0ac7 \u0a95\u0ac7\u0aae \u0a9b\u0acb?",
    "pa": "\u0a38\u0a24 \u0a38\u0a4d\u0a30\u0a40 \u0a05\u0a15\u0a3e\u0a32, \u0a24\u0a41\u0a38\u0a40\u0a02 \u0a07\u0a71\u0a25\u0a47 \u0a06\u0a0f \u0a2c\u0a39\u0a41\u0a24 \u0a1a\u0a70\u0a17\u0a3e \u0a32\u0a71\u0a17\u0a3e. \u0a07\u0a39 \u0a24\u0a41\u0a39\u0a3e\u0a21\u0a40 \u0a05\u0a2a\u0a23\u0a40 \u0a25\u0a3e\u0a02 \u0a39\u0a48 \u2014 \u0a2a\u0a42\u0a30\u0a40 \u0a24\u0a30\u0a4d\u0a39\u0a3e\u0a02 \u0a28\u0a3f\u0a71\u0a1c\u0a40. \u0a24\u0a41\u0a38\u0a40\u0a02 \u0a2e\u0a47\u0a30\u0a47 \u0a28\u0a3e\u0a32 \u0a15\u0a3f\u0a38\u0a47 \u0a35\u0a40 \u0a2c\u0a3e\u0a30\u0a47 \u0a17\u0a71\u0a32 \u0a15\u0a30 \u0a38\u0a15\u0a26\u0a47 \u0a39\u0a4b. \u0a05\u0a71\u0a1c \u0a24\u0a41\u0a38\u0a40\u0a02 \u0a15\u0a3f\u0a35\u0a47\u0a02 \u0a39\u0a4b?",
    "kn": "\u0ca8\u0cae\u0cb8\u0ccd\u0c95\u0cbe\u0cb0, \u0ca8\u0cc0\u0cb5\u0cc1 \u0c87\u0cb2\u0ccd\u0cb2\u0cbf \u0cac\u0c82\u0ca6\u0cbf\u0ca6\u0ccd\u0ca6\u0cc0\u0cb0\u0cbf \u0ca4\u0cc1\u0c82\u0cac\u0cbe \u0c96\u0cc1\u0cb7\u0cbf \u0c86\u0caf\u0cbf\u0ca4\u0cc1. \u0c87\u0ca6\u0cc1 \u0ca8\u0cbf\u0cae\u0ccd\u0cae\u0ca6\u0cc7 \u0c86\u0ca6 \u0c9c\u0cbe\u0c97 \u2014 \u0cb8\u0c82\u0caa\u0cc2\u0cb0\u0ccd\u0ca3\u0cb5\u0cbe\u0c97\u0cbf \u0c96\u0cbe\u0cb8\u0c97\u0cbf. \u0ca8\u0cc0\u0cb5\u0cc1 \u0ca8\u0ca8\u0ccd\u0ca8 \u0c9c\u0cca\u0ca4\u0cc6 \u0c8f\u0ca8\u0cbe\u0ca6\u0cb0\u0cc2 \u0cac\u0c97\u0ccd\u0c97\u0cc6 \u0cae\u0cbe\u0ca4\u0ca8\u0cbe\u0ca1\u0cac\u0cb9\u0cc1\u0ca6\u0cc1. \u0c88\u0c97 \u0ca8\u0cc0\u0cb5\u0cc1 \u0cb9\u0cc7\u0c97\u0cbf\u0ca6\u0ccd\u0ca6\u0cc0\u0cb0\u0cbf?",
    "ml": "\u0d39\u0d3e\u0d2f\u0d4d, \u0d28\u0d3f\u0d19\u0d4d\u0d19\u0d33\u0d4d\u200d \u0d07\u0d35\u0d3f\u0d1f\u0d46 \u0d35\u0d28\u0d4d\u0d28\u0d24\u0d3f\u0d32\u0d4d\u200d \u0d24\u0d41\u0d02\u0d2c \u0d38\u0d28\u0d4d\u0d24\u0d4b\u0d37\u0d02. \u0d07\u0d24\u0d4d \u0d28\u0d3f\u0d19\u0d4d\u0d19\u0d33\u0d41\u0d1f\u0d46 \u0d38\u0d4d\u0d35\u0d28\u0d4d\u0d24\u0d02 \u0d07\u0d1f\u0d2e\u0d3e\u0d23\u0d4d \u2014 \u0d2a\u0d42\u0d7c\u0d23\u0d4d\u0d23\u0d2e\u0d3e\u0d2f\u0d41\u0d02 \u0d38\u0d4d\u0d35\u0d15\u0d3e\u0d30\u0d4d\u0d2f\u0d02. \u0d28\u0d3f\u0d19\u0d4d\u0d19\u0d33\u0d4d\u200d\u0d15\u0d4d\u0d15\u0d4d \u0d0e\u0d28\u0d4d\u0d24\u0d41\u0d02 \u0d0e\u0d28\u0d4d\u0d28\u0d4b\u0d1f\u0d4d \u0d38\u0d02\u0d38\u0d3e\u0d30\u0d3f\u0d15\u0d4d\u0d15\u0d3e\u0d02. \u0d07\u0d28\u0d4d\u0d28\u0d4d \u0d28\u0d3f\u0d19\u0d4d\u0d19\u0d33\u0d4d\u200d \u0d0e\u0d19\u0d4d\u0d19\u0d28\u0d46\u0d2f\u0d3e\u0d23\u0d4d?",
    "or": "\u0b28\u0b2e\u0b38\u0b4d\u0b15\u0b3e\u0b30, \u0b06\u0b2a\u0b23 \u0b0f\u0b20\u0b3f \u0b06\u0b38\u0b3f\u0b32\u0b47 \u0b2c\u0b39\u0b41\u0b24 \u0b2d\u0b32 \u0b32\u0b3e\u0b17\u0b3f\u0b32\u0b3e. \u0b0f\u0b39\u0b3e \u0b06\u0b2a\u0b23\u0b19\u0b4d\u0b15\u0b30 \u0b28\u0b3f\u0b1c\u0b30 \u0b1c\u0b3e\u0b17\u0b3e \u2014 \u0b38\u0b2e\u0b4d\u0b2a\u0b42\u0b30\u0b4d\u0b23 \u0b17\u0b4b\u0b2a\u0b28\u0b40\u0b5f. \u0b06\u0b2a\u0b23 \u0b2e\u0b4b\u0b24\u0b47 \u0b38\u0b3e\u0b19\u0b4d\u0b17\u0b30\u0b47 \u0b2f\u0b47\u0b15\u0b4b\u0b23\u0b38\u0b3f \u0b2c\u0b3f\u0b37\u0b5f\u0b30\u0b47 \u0b15\u0b25\u0b3e \u0b39\u0b47\u0b07\u0b2a\u0b3e\u0b30\u0b3f\u0b2c\u0b47. \u0b06\u0b1c\u0b3f \u0b06\u0b2a\u0b23 \u0b15\u0b47\u0b2e\u0b3f\u0b24\u0b3f \u0b05\u0b1b\u0b28\u0b4d\u0b24\u0b3f?",
    "as": "\u09a8\u09ae\u09b8\u09cd\u0995\u09be\u09f0, \u0986\u09aa\u09c1\u09a8\u09bf \u0987\u09af\u09bc\u09be\u09a4 \u0985\u09b9\u09be\u09a4 \u09ac\u09b0 \u09ad\u09be\u09b2 \u09b2\u09be\u0997\u09bf\u09b2\u0964 \u098f\u0987\u099f\u09cb \u0986\u09aa\u09cb\u09a8\u09be\u09f0 \u09a8\u09bf\u099c\u09f0 \u09a0\u09be\u0987 \u2014 \u09b8\u09ae\u09cd\u09aa\u09c2\u09f0\u09cd\u09a3 \u09ac\u09cd\u09af\u0995\u09cd\u09a4\u09bf\u0997\u09a4\u0964 \u0986\u09aa\u09c1\u09a8\u09bf \u09ae\u09cb\u09f0 \u09b2\u0997\u09a4 \u09af\u09bf\u0995\u09cb\u09a8\u09cb \u0995\u09a5\u09be \u09aa\u09be\u09a4\u09bf\u09ac \u09aa\u09be\u09f0\u09c7\u0964 \u0986\u099c\u09bf \u0986\u09aa\u09c1\u09a8\u09bf \u0995\u09c7\u09a8\u09c7\u0995\u09c1\u09f1\u09be \u0986\u099b\u09c7?",
    "ne": "\u0928\u092e\u0938\u094d\u0924\u0947, \u0924\u092a\u093e\u0908\u0902 \u092f\u0939\u093e\u0901 \u0906\u0909\u0928\u0941\u092d\u092f\u094b \u0916\u0941\u0938\u0940 \u0932\u093e\u0917\u094d\u092f\u094b\u0964 \u092f\u094b \u0924\u092a\u093e\u0908\u0902\u0915\u094b \u0905\u092a\u094d\u0928\u0948 \u0920\u093e\u0909\u0901 \u0939\u094b \u2014 \u092a\u0942\u0930\u094d\u0923 \u0930\u0942\u092a\u092e\u093e \u0928\u093f\u091c\u0940\u0964 \u0924\u092a\u093e\u0908\u0902 \u092e\u0938\u0901\u0917 \u091c\u0941\u0928\u0938\u0941\u0915\u0948 \u0915\u0941\u0930\u093e\u0915\u094b \u092c\u093e\u0930\u0947\u092e\u093e \u0915\u0941\u0930\u093e \u0917\u0930\u094d\u0928 \u0938\u0915\u094d\u0928\u0941\u0939\u0941\u0928\u094d\u091b\u0964 \u0906\u091c \u0924\u092a\u093e\u0908\u0902 \u0915\u0938\u094d\u0924\u094b \u0939\u0941\u0928\u0941\u0939\u0941\u0928\u094d\u091b?",
    "sa": "\u0928\u092e\u0938\u094d\u0915\u093e\u0930\u0903, \u092d\u0935\u0924\u0903 \u0905\u0924\u094d\u0930 \u0906\u0917\u092e\u0928\u0947\u0928 \u092e\u092e \u0905\u0924\u0940\u0935 \u0939\u0930\u094d\u0937\u0903 \u091c\u093e\u0924\u0903\u0964 \u0907\u0926\u0902 \u092d\u0935\u0924\u0903 \u0938\u094d\u0935\u0915\u0940\u092f\u0902 \u0938\u094d\u0925\u093e\u0928\u092e\u094d \u2014 \u0938\u0930\u094d\u0935\u0925\u093e \u0917\u094b\u092a\u0928\u0940\u092f\u092e\u094d\u0964 \u092d\u0935\u093e\u0928\u094d \u092e\u092f\u093e \u0938\u0939 \u0915\u093f\u092e\u092a\u093f \u0935\u093e\u0930\u094d\u0924\u093e\u0902 \u0915\u0930\u094d\u0924\u0941\u0902 \u0936\u0915\u094d\u0928\u094b\u0924\u093f\u0964 \u0905\u0926\u094d\u092f \u092d\u0935\u093e\u0928\u094d \u0915\u0925\u092e\u094d \u0905\u0938\u094d\u0924\u093f?",
}


def _build_voice_panel(backend_url: str, jwt: str, language_code: str = "en") -> str:
    """
    Builds the complete self-contained voice panel HTML.
    All JS runs inside this iframe — no external deps except Google Fonts.
    Features: canvas-based audio waveform visualizer, real-time mic reactivity,
    smooth speaking waves, language-aware greeting in selected language.
    """
    profiles_json  = json.dumps(_WEB_SPEECH_PROFILES)
    bcp47_json     = json.dumps(_BCP47)
    greetings_json = json.dumps(_GREETINGS, ensure_ascii=False)
    lang_names_json = json.dumps(_LANG_NAMES)
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
    background:radial-gradient(ellipse at 50% -10%, #0e1f38 0%, #060c18 70%);
    color:#e8edf5;width:100%;min-height:100vh;overflow-x:hidden;scroll-behavior:smooth;
}}

/* ── Orb Container ── */
.orb-section{{
    display:flex;flex-direction:column;align-items:center;
    padding:18px 0 6px;position:relative;
}}
.canvas-wrap{{
    position:relative;width:240px;height:240px;
    display:flex;align-items:center;justify-content:center;
}}
#vizCanvas{{
    position:absolute;top:0;left:0;width:100%;height:100%;
    pointer-events:none;
}}

/* ── Orb ── */
.orb{{
    width:96px;height:96px;border-radius:50%;cursor:pointer;border:none;outline:none;
    position:relative;z-index:2;flex-shrink:0;
    background:radial-gradient(circle at 36% 30%, #63b3ed 0%, #4fd1c5 45%, #7c3aed 100%);
    box-shadow:0 0 50px rgba(99,179,237,.25), 0 0 100px rgba(79,209,197,.10), inset 0 0 30px rgba(255,255,255,.05);
    transition:transform .15s ease, box-shadow .3s ease;
}}
.orb:hover{{transform:scale(1.06);}}
.orb:active{{transform:scale(0.95);}}

/* Orb glow ring */
.orb::after{{
    content:'';position:absolute;inset:-8px;border-radius:50%;
    border:2px solid rgba(99,179,237,.15);
    animation:ringPulse 4s ease-in-out infinite;
    pointer-events:none;
}}
@keyframes ringPulse{{
    0%,100%{{opacity:.3;transform:scale(1);}}
    50%{{opacity:.7;transform:scale(1.08);}}
}}

/* State-specific orb styles */
.orb.listening{{
    background:radial-gradient(circle at 36% 30%, #fc8181 0%, #f6ad55 45%, #fc4e4e 100%)!important;
    box-shadow:0 0 60px rgba(252,129,129,.35), 0 0 120px rgba(246,173,85,.15)!important;
}}
.orb.listening::after{{border-color:rgba(252,129,129,.25)!important;animation:ringPulseRed .8s ease-in-out infinite!important;}}
@keyframes ringPulseRed{{
    0%,100%{{opacity:.3;transform:scale(1);border-color:rgba(252,129,129,.25);}}
    50%{{opacity:1;transform:scale(1.15);border-color:rgba(252,129,129,.5);}}
}}

.orb.thinking{{
    background:radial-gradient(circle at 36% 30%, #b794f4 0%, #7c3aed 45%, #553c9a 100%)!important;
    box-shadow:0 0 60px rgba(183,148,244,.35), 0 0 110px rgba(124,58,237,.15)!important;
    animation:orbSpin 2s linear infinite!important;
}}
.orb.thinking::after{{border-color:rgba(183,148,244,.3)!important;animation:ringThink 1.2s ease-in-out infinite!important;}}
@keyframes orbSpin{{
    0%{{background:radial-gradient(circle at 36% 30%, #b794f4 0%, #7c3aed 45%, #553c9a 100%);}}
    33%{{background:radial-gradient(circle at 60% 60%, #b794f4 0%, #7c3aed 45%, #553c9a 100%);}}
    66%{{background:radial-gradient(circle at 30% 65%, #b794f4 0%, #7c3aed 45%, #553c9a 100%);}}
    100%{{background:radial-gradient(circle at 36% 30%, #b794f4 0%, #7c3aed 45%, #553c9a 100%);}}
}}
@keyframes ringThink{{
    0%,100%{{opacity:.2;transform:scale(1) rotate(0deg);}}
    50%{{opacity:.6;transform:scale(1.12) rotate(180deg);}}
}}

.orb.speaking{{
    box-shadow:0 0 60px rgba(99,179,237,.4), 0 0 120px rgba(79,209,197,.2)!important;
}}
.orb.speaking::after{{animation:ringPulseSpeaking .9s ease-in-out infinite!important;}}
@keyframes ringPulseSpeaking{{
    0%,100%{{opacity:.3;transform:scale(1);border-color:rgba(79,209,197,.2);}}
    50%{{opacity:.9;transform:scale(1.18);border-color:rgba(79,209,197,.5);}}
}}

/* ── Orb icon (mic SVG inside) ── */
.orb-icon{{
    position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);
    width:32px;height:32px;opacity:.7;transition:opacity .2s;
    pointer-events:none;
}}
.orb:hover .orb-icon{{opacity:.9;}}

/* ── Status area ── */
.status-area{{
    display:flex;flex-direction:column;align-items:center;gap:8px;
    padding:2px 0 8px;
}}
.orb-status{{
    font-size:.68rem;color:#8fa2bc;letter-spacing:.10em;
    text-transform:uppercase;min-height:18px;text-align:center;
    transition:color .3s, opacity .3s;
}}

/* Language badge */
.lang-badge{{
    display:none;align-items:center;gap:7px;
    padding:5px 14px;border-radius:22px;
    background:rgba(79,209,197,.06);border:1px solid rgba(79,209,197,.18);
    backdrop-filter:blur(8px);
    font-size:.64rem;color:#4fd1c5;letter-spacing:.05em;
    animation:fadeUp .3s ease;
}}
.lang-badge.show{{display:flex;}}
.lang-dot{{
    width:6px;height:6px;border-radius:50%;
    background:linear-gradient(135deg,#4fd1c5,#63b3ed);
    animation:ldPulse 2.2s ease-in-out infinite;
}}
@keyframes ldPulse{{0%,100%{{opacity:.30;transform:scale(1);}}50%{{opacity:1;transform:scale(1.4);}}}}

/* ── Controls ── */
.controls{{display:flex;gap:10px;padding:0 16px 12px;}}
.ctrl-btn{{
    flex:1;padding:10px 0;border:none;border-radius:12px;
    font-family:'Sora',sans-serif;font-size:.71rem;font-weight:600;
    letter-spacing:.04em;cursor:pointer;
    transition:all .18s ease;
    backdrop-filter:blur(6px);
}}
.ctrl-btn:hover{{opacity:.85;transform:translateY(-1px);}}
.ctrl-btn:active{{transform:scale(.97) translateY(0);}}
.ctrl-btn:focus-visible{{outline:none;box-shadow:0 0 0 3px rgba(99,179,237,.25);}}
.btn-start{{
    background:linear-gradient(135deg,rgba(42,100,150,.8),rgba(26,122,110,.8));
    color:#d6f0ff;border:1px solid rgba(99,179,237,.2);
}}
.btn-stop{{
    background:rgba(252,129,129,.1);color:#fc8181;
    border:1px solid rgba(252,129,129,.25);
}}
.btn-mute{{
    background:rgba(255,255,255,.04);color:#718096;
    border:1px solid rgba(255,255,255,.08);
}}

/* ── Crisis banner ── */
.crisis-bar{{
    margin:0 14px 10px;padding:10px 14px;border-radius:12px;
    font-size:.72rem;line-height:1.6;display:none;
    backdrop-filter:blur(8px);
}}
.crisis-bar.show{{display:block;animation:fadeUp .3s ease;}}
.crisis-bar.passive{{background:rgba(237,137,54,.08);border:1px solid rgba(237,137,54,.25);color:#ed8936;}}
.crisis-bar.active {{background:rgba(252,78,78,.10); border:1px solid rgba(252,78,78,.30); color:#fc8181;}}

/* ── Transcript ── */
.transcript{{
    margin:0 14px 10px;
    border:1px solid rgba(255,255,255,.06);border-radius:16px;
    background:rgba(8,15,28,.7);backdrop-filter:blur(12px);
    overflow-y:auto;max-height:260px;padding:12px;scroll-behavior:smooth;
    transition:border-color .25s ease, box-shadow .25s ease;
}}
.transcript:hover{{
    border-color:rgba(99,179,237,.15);
    box-shadow:inset 0 0 0 1px rgba(255,255,255,.02), 0 4px 24px rgba(0,0,0,.2);
}}
.transcript::-webkit-scrollbar{{width:3px;}}
.transcript::-webkit-scrollbar-thumb{{background:rgba(255,255,255,.08);border-radius:2px;}}

/* ── Turns ── */
.turn{{margin-bottom:13px;animation:fadeUp .28s ease;}}
.turn-row{{display:flex;align-items:flex-start;gap:9px;}}
.turn-row.user-row{{flex-direction:row-reverse;}}
.avatar{{
    width:30px;height:30px;border-radius:50%;flex-shrink:0;
    display:flex;align-items:center;justify-content:center;
    font-size:.56rem;font-weight:700;letter-spacing:.02em;
}}
.avatar-ai{{
    background:linear-gradient(135deg,#0e2a45,#0a1e35);color:#4fd1c5;
    border:1px solid rgba(79,209,197,.2);
    box-shadow:0 0 12px rgba(79,209,197,.08);
}}
.avatar-user{{
    background:linear-gradient(135deg,#1c3558,#14294a);color:#63b3ed;
    border:1px solid rgba(99,179,237,.2);
    box-shadow:0 0 12px rgba(99,179,237,.08);
}}
.bubble{{max-width:81%;padding:10px 14px;font-size:.79rem;line-height:1.65;word-break:break-word;}}
.bubble-ai{{
    background:rgba(16,24,44,.88);
    border:1px solid rgba(255,255,255,.06);
    border-radius:4px 14px 14px 14px;color:#c8d4e6;
}}
.bubble-user{{
    background:rgba(24,48,82,.82);
    border:1px solid rgba(99,179,237,.14);
    border-radius:14px 4px 14px 14px;color:#bdd4f0;
}}
.turn-meta{{font-size:.58rem;color:#8fa2bc;margin-top:4px;display:flex;align-items:center;gap:5px;}}
.turn-row.user-row .turn-meta{{justify-content:flex-end;}}
.meta-dot{{width:4px;height:4px;border-radius:50%;}}
.lang-tag{{
    font-size:.55rem;padding:1px 6px;border-radius:10px;
    background:rgba(79,209,197,.06);border:1px solid rgba(79,209,197,.15);color:#4fd1c5;
}}

/* ── Footer ── */
.panel-hint{{
    text-align:center;font-size:.60rem;color:#566a84;
    letter-spacing:.06em;padding:2px 0 10px;
}}

/* ── Responsive ── */
@media (max-width: 560px) {{
    .canvas-wrap{{width:200px;height:200px;}}
    .orb{{width:80px;height:80px;}}
    .controls{{flex-direction:column;padding:0 14px 10px;gap:8px;}}
    .ctrl-btn{{padding:9px 0;font-size:.68rem;}}
    .transcript{{max-height:220px;margin:0 10px 10px;padding:10px;}}
    .bubble{{max-width:88%;font-size:.75rem;}}
}}

@media (prefers-reduced-motion: reduce) {{
    *{{animation:none!important;transition:none!important;scroll-behavior:auto!important;}}
}}

@keyframes fadeUp{{from{{opacity:0;transform:translateY(5px);}}to{{opacity:1;transform:translateY(0);}}}}
</style>
</head>
<body>

<!-- Orb + Canvas Visualizer -->
<div class="orb-section">
    <div class="canvas-wrap">
        <canvas id="vizCanvas"></canvas>
        <button class="orb" id="orb">
            <svg class="orb-icon" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
                <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                <line x1="12" y1="19" x2="12" y2="23"/>
                <line x1="8" y1="23" x2="16" y2="23"/>
            </svg>
        </button>
    </div>
    <div class="status-area">
        <div class="lang-badge" id="langBadge">
            <div class="lang-dot"></div>
            <span id="langText">Detecting\u2026</span>
        </div>
        <div class="orb-status" id="orbStatus">Tap Start or press the orb to begin</div>
    </div>
</div>

<!-- Controls -->
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
const GREETINGS  = {greetings_json};
const LANG_NAMES_MAP = {lang_names_json};
const SELECTED_LANG  = "{language_code}";

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
const vizCanvas  = document.getElementById('vizCanvas');
const ctx        = vizCanvas.getContext('2d');

/* ── State ── */
let recorder      = null;
let audioChunks   = [];
let micStream     = null;
let isListening   = false;
let isProcessing  = false;
let isMuted       = false;
let continuous    = false;
let currentAudio  = null;
let sessionLang     = SELECTED_LANG;
let sessionLangName = LANG_NAMES_MAP[SELECTED_LANG] || 'English';

const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
let interruptSR   = null;
let interruptDone = false;

/* ══════════════════════════════════════════════════════════════
   CANVAS AUDIO VISUALIZER
   ─────────────────────────────────────────────────────────────
   Real-time circular waveform around the orb.
   - Listening: draws bars from mic AnalyserNode frequency data
   - Speaking:  smooth sine waves radiating outward
   - Thinking:  rotating particle dots
   - Idle:      gentle breathing ring
   ══════════════════════════════════════════════════════════════ */
let audioCtx      = null;
let analyser      = null;
let micSource     = null;
let freqData      = null;
let vizState      = 'idle';   // idle | listening | speaking | thinking
let vizFrame      = null;
let vizAngle      = 0;
let speakPhase    = 0;

function initCanvas() {{
    const dpr = window.devicePixelRatio || 1;
    const rect = vizCanvas.getBoundingClientRect();
    vizCanvas.width  = rect.width * dpr;
    vizCanvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);
    ctx.lineCap = 'round';
}}
initCanvas();
window.addEventListener('resize', initCanvas);

function connectMicAnalyser(stream) {{
    try {{
        if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        if (micSource) {{ try {{ micSource.disconnect(); }} catch(_) {{}} }}
        micSource = audioCtx.createMediaStreamSource(stream);
        analyser  = audioCtx.createAnalyser();
        analyser.fftSize = 256;
        analyser.smoothingTimeConstant = 0.75;
        micSource.connect(analyser);
        freqData = new Uint8Array(analyser.frequencyBinCount);
    }} catch(e) {{ console.warn('Audio analyser init failed', e); }}
}}

function disconnectMicAnalyser() {{
    if (micSource) {{ try {{ micSource.disconnect(); }} catch(_) {{}} micSource = null; }}
}}

function setVizState(s) {{ vizState = s; }}

/* Main render loop */
function drawViz() {{
    vizFrame = requestAnimationFrame(drawViz);
    const W = vizCanvas.clientWidth;
    const H = vizCanvas.clientHeight;
    const cx = W / 2, cy = H / 2;
    ctx.clearRect(0, 0, W, H);

    if (vizState === 'listening')       drawListeningViz(cx, cy);
    else if (vizState === 'speaking')   drawSpeakingViz(cx, cy);
    else if (vizState === 'thinking')   drawThinkingViz(cx, cy);
    else                                drawIdleViz(cx, cy);
}}

/* ── Idle: gentle glowing ring ── */
function drawIdleViz(cx, cy) {{
    const t = Date.now() / 2000;
    const r = 62 + Math.sin(t) * 4;
    const alpha = 0.08 + Math.sin(t * 1.5) * 0.04;
    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, Math.PI * 2);
    ctx.strokeStyle = `rgba(99,179,237,${{alpha}})`;
    ctx.lineWidth = 2;
    ctx.stroke();
    // Second ring
    const r2 = 70 + Math.cos(t * 0.8) * 3;
    ctx.beginPath();
    ctx.arc(cx, cy, r2, 0, Math.PI * 2);
    ctx.strokeStyle = `rgba(79,209,197,${{alpha * 0.6}})`;
    ctx.lineWidth = 1;
    ctx.stroke();
}}

/* ── Listening: real-time mic circular bars ── */
function drawListeningViz(cx, cy) {{
    if (analyser && freqData) {{
        analyser.getByteFrequencyData(freqData);
    }}
    const bars = 64;
    const baseR = 60;
    const maxBarH = 42;
    const step = (Math.PI * 2) / bars;

    for (let i = 0; i < bars; i++) {{
        const fi = freqData ? freqData[Math.floor(i * freqData.length / bars)] || 0 : 0;
        const norm = fi / 255;
        const h = 3 + norm * maxBarH;
        const angle = i * step - Math.PI / 2;
        const x1 = cx + Math.cos(angle) * baseR;
        const y1 = cy + Math.sin(angle) * baseR;
        const x2 = cx + Math.cos(angle) * (baseR + h);
        const y2 = cy + Math.sin(angle) * (baseR + h);

        const hue = 0 + norm * 30; // red-orange range
        const alpha = 0.35 + norm * 0.65;
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.strokeStyle = `hsla(${{hue}},85%,${{55 + norm*20}}%,${{alpha}})`;
        ctx.lineWidth = 2.5;
        ctx.stroke();
    }}

    // Inner glow ring
    const t = Date.now() / 600;
    const avgLevel = freqData ? Array.from(freqData).reduce((a,b)=>a+b,0) / freqData.length / 255 : 0;
    ctx.beginPath();
    ctx.arc(cx, cy, baseR - 2, 0, Math.PI * 2);
    ctx.strokeStyle = `rgba(252,129,129,${{0.15 + avgLevel * 0.3}})`;
    ctx.lineWidth = 1.5 + avgLevel * 2;
    ctx.stroke();
}}

/* ── Speaking: smooth sine waves radiating outward ── */
function drawSpeakingViz(cx, cy) {{
    speakPhase += 0.04;
    const rings = 3;
    for (let r = 0; r < rings; r++) {{
        const baseR = 62 + r * 14;
        const points = 120;
        const step = (Math.PI * 2) / points;
        const alpha = 0.35 - r * 0.10;
        const amplitude = 6 + r * 3;

        ctx.beginPath();
        for (let i = 0; i <= points; i++) {{
            const angle = i * step;
            const wave = Math.sin(angle * 6 + speakPhase + r * 0.8) * amplitude
                       + Math.sin(angle * 3 - speakPhase * 0.7) * (amplitude * 0.5);
            const rad = baseR + wave;
            const x = cx + Math.cos(angle) * rad;
            const y = cy + Math.sin(angle) * rad;
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        }}
        ctx.closePath();

        const grad = ctx.createRadialGradient(cx, cy, baseR - 10, cx, cy, baseR + amplitude + 5);
        grad.addColorStop(0, `rgba(99,179,237,${{alpha}})`);
        grad.addColorStop(0.5, `rgba(79,209,197,${{alpha * 0.8}})`);
        grad.addColorStop(1, `rgba(99,179,237,0)`);
        ctx.strokeStyle = grad;
        ctx.lineWidth = 2 - r * 0.3;
        ctx.stroke();
    }}
}}

/* ── Thinking: rotating particles ── */
function drawThinkingViz(cx, cy) {{
    vizAngle += 0.025;
    const particles = 12;
    const baseR = 65;
    const step = (Math.PI * 2) / particles;
    for (let i = 0; i < particles; i++) {{
        const angle = vizAngle + i * step;
        const wobble = Math.sin(Date.now() / 400 + i) * 5;
        const r = baseR + wobble;
        const x = cx + Math.cos(angle) * r;
        const y = cy + Math.sin(angle) * r;
        const size = 2.5 + Math.sin(Date.now() / 300 + i * 0.5) * 1.5;
        const alpha = 0.3 + Math.sin(Date.now() / 350 + i) * 0.3;

        ctx.beginPath();
        ctx.arc(x, y, size, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(183,148,244,${{alpha}})`;
        ctx.fill();
    }}
    // Connecting lines
    for (let i = 0; i < particles; i++) {{
        const a1 = vizAngle + i * step;
        const a2 = vizAngle + ((i+1) % particles) * step;
        const w1 = Math.sin(Date.now()/400 + i) * 5;
        const w2 = Math.sin(Date.now()/400 + i+1) * 5;
        ctx.beginPath();
        ctx.moveTo(cx + Math.cos(a1)*(baseR+w1), cy + Math.sin(a1)*(baseR+w1));
        ctx.lineTo(cx + Math.cos(a2)*(baseR+w2), cy + Math.sin(a2)*(baseR+w2));
        ctx.strokeStyle = 'rgba(183,148,244,0.08)';
        ctx.lineWidth = 1;
        ctx.stroke();
    }}
}}

/* Start the visualizer loop */
drawViz();

/* ── Helpers ── */
function setStatus(t) {{ orbStatus.textContent = t; }}
function setOrb(s) {{
    orb.classList.remove('listening','thinking','speaking');
    if (s) orb.classList.add(s);
    setVizState(s || 'idle');
}}
function hhmm() {{ return new Date().toLocaleTimeString([],{{hour:'2-digit',minute:'2-digit'}}); }}

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

/* ── Dashboard sync — direct DOM access + postMessage fallback ── */
function syncDashboard(userText, reply, mhi, category, tier, langCode) {{
    var data = {{
        type:           'VOICE_TURN_V5',
        user_text:      userText,
        assistant_text: reply,
        mhi:            mhi,
        category:       category,
        crisis_tier:    tier,
        language_code:  langCode,
        ts:             new Date().toISOString(),
    }};
    var payload = JSON.stringify(data);
    try {{
        var pdoc = window.parent.document;
        var inputs = pdoc.querySelectorAll('input[type="text"]');
        for (var i = 0; i < inputs.length; i++) {{
            var id = inputs[i].id;
            if (!id) continue;
            var lbl = pdoc.querySelector('label[for="' + id + '"]');
            if (lbl && lbl.textContent.indexOf('__vsync_v5_label__') !== -1) {{
                var setter = Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype, 'value').set;
                setter.call(inputs[i], payload);
                inputs[i].dispatchEvent(new Event('input',  {{bubbles:true}}));
                inputs[i].dispatchEvent(new Event('change', {{bubbles:true}}));
                return;
            }}
        }}
    }} catch(e) {{}}
    try {{ window.parent.postMessage(data, '*'); }} catch(e) {{}}
}}

/* ══════════════════════════════════════════════════════════════
   INTERRUPT MECHANISM
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
        if (currentAudio && !currentAudio.paused) {{
            currentAudio.pause();
            currentAudio.currentTime = 0;
        }}
        window.speechSynthesis.cancel();
        currentAudio = null;

        if (!interruptDone) {{
            interruptDone = true;
            stopInterruptWatcher();
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
    catch(e) {{}}
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

        audio.onplay = function() {{ startInterruptWatcher(); }};

        await new Promise(function(resolve) {{
            audio.onended = function() {{ currentAudio=null; resolve(); }};
            audio.onerror = function() {{ currentAudio=null; resolve(); }};
            audio.play().catch(function() {{ currentAudio=null; resolve(); }});
        }});
        URL.revokeObjectURL(url);
    }} catch(_) {{
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
        form.append('language', sessionLang);
        const res  = await fetch(`${{BACKEND}}/voice/transcribe`, {{
            method:  'POST',
            headers: {{'Authorization': `Bearer ${{JWT}}`}},
            body:    form,
        }});
        if (!res.ok) return null;
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
            body:    JSON.stringify({{message: userText, language_code: sessionLang, source: 'voice'}}),
        }});
        if (!res.ok) throw new Error('chat-' + res.status);

        const data     = await res.json();
        const reply    = data.response     || '';
        const mhi      = data.mhi          || 0;
        const category = data.category     || '';
        const tier     = data.crisis_tier  || 'none';
        const score    = data.crisis_score || 0;
        const scores   = data.emotion_scores || {{}};
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
        disconnectMicAnalyser();

        const blob = new Blob(audioChunks, {{type:'audio/webm'}});
        setOrb('thinking');
        setStatus('Processing\u2026');

        const stt = await transcribeBlob(blob);

        if (!stt || !stt.transcript || !stt.transcript.trim()) {{
            setStatus('No speech detected \u2014 tap orb to try again');
            setOrb('');
            isProcessing = false;
            if (continuous) setTimeout(startListening, 900);
            return;
        }}

        updateLangBadge(sessionLangName, stt.confidence || 0);

        appendTurn('user', stt.transcript, null);
        await sendChat(stt.transcript);
    }};

    recorder.start(200);
    isListening = true;

    /* Connect mic to analyser for real-time visualization */
    if (micStream) connectMicAnalyser(micStream);

    setOrb('listening');
    setStatus('Listening\u2026 speak naturally');

    const autoStopTimer = setTimeout(function() {{ stopRecording(); }}, 10000);
    orb.onclick = function() {{ clearTimeout(autoStopTimer); stopRecording(); }};
}}

async function startListening() {{
    if (isListening || isProcessing) return;

    if (currentAudio && !currentAudio.paused) {{
        currentAudio.pause();
        currentAudio = null;
    }}
    window.speechSynthesis.cancel();
    stopInterruptWatcher();

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
    disconnectMicAnalyser();
    setOrb('');
    setStatus('Stopped \u2014 tap Start or orb to resume');
    isProcessing = false;
}}

/* ── Greeting in selected language ── */
async function greet() {{
    const msg = GREETINGS[sessionLang] || GREETINGS['en'];
    appendTurn('assistant', msg, null);
    updateLangBadge(sessionLangName, 1.0);
    if (!isMuted) {{
        await speakResponse(msg, sessionLang, 'neutral', 'none');
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

    # Sync bridge — runs in hidden iframe, relays postMessage to hidden input
    components.html(_SYNC_BRIDGE, height=0)

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
    lang = st.session_state.get("selected_language", "en")
    components.html(
        _build_voice_panel(BACKEND_URL, jwt, lang),
        height=640,
        scrolling=False,
    )
