import streamlit as st
import requests
import uuid
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ==============================
# CONFIG
# ==============================
BACKEND_URL = "http://localhost:8000"
st.set_page_config(page_title="Smart Mental Well-Being", layout="wide")

# ==============================
# MODERN UI CSS
# ==============================
st.markdown("""
<style>

.main {
    background: linear-gradient(-45deg, #f4f8fb, #e3f2fd, #f8f9fc, #edf7fa);
    background-size: 400% 400%;
    animation: gradientBG 12s ease infinite;
}

@keyframes gradientBG {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

.hero {
    padding: 30px;
    border-radius: 20px;
    background: linear-gradient(135deg, #4e73df, #1cc88a);
    color: white;
    text-align: center;
    margin-bottom: 25px;
}

.glass-card {
    background: rgba(255, 255, 255, 0.75);
    backdrop-filter: blur(10px);
    padding: 20px;
    border-radius: 15px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.05);
}

.metric-box {
    padding: 15px;
    border-radius: 12px;
    background: linear-gradient(135deg, #f8f9fc, #e3f2fd);
    text-align: center;
}

.badge {
    padding: 8px 14px;
    border-radius: 20px;
    font-weight: bold;
    font-size: 14px;
}

.normal { background:#d4edda; color:#155724; }
.stress { background:#fff3cd; color:#856404; }
.anxiety { background:#f8d7da; color:#721c24; }
.depression { background:#f5c6cb; color:#4a0000; }
.crisis { background:#ff4d4d; color:white; }

</style>
""", unsafe_allow_html=True)

# ==============================
# SESSION INIT
# ==============================
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ==============================
# SIDEBAR
# ==============================
st.sidebar.title("Mental Health Monitor")
st.sidebar.write(f"User ID: {st.session_state.user_id}")

st.sidebar.subheader("Quick Assessment")

phq1 = st.sidebar.slider("Little interest?", 0, 3, 0)
phq2 = st.sidebar.slider("Feeling hopeless?", 0, 3, 0)
gad1 = st.sidebar.slider("Feeling anxious?", 0, 3, 0)
gad2 = st.sidebar.slider("Can't stop worrying?", 0, 3, 0)

if st.sidebar.button("Submit Assessment"):
    payload = {
        "user_id": st.session_state.user_id,
        "phq2": phq1 + phq2,
        "gad2": gad1 + gad2
    }
    try:
        requests.post(f"{BACKEND_URL}/assessment", json=payload)
        st.sidebar.success("Assessment submitted")
    except:
        st.sidebar.error("Backend not reachable")

st.sidebar.markdown("---")
st.sidebar.subheader("Wellness Summary")
st.sidebar.progress(75)
st.sidebar.caption("Weekly Stability Score")

# ==============================
# HERO HEADER
# ==============================
st.markdown("""
<div class="hero">
    <h1>Smart Mental Well-Being Assistant</h1>
    <p>AI Emotion Detection • Mental Health Index • Crisis Monitoring • CBT Support</p>
</div>
""", unsafe_allow_html=True)

# ==============================
# CHAT DISPLAY
# ==============================
avatar_user = "👤"
avatar_bot = "🧠"

for message in st.session_state.chat_history:
    avatar = avatar_user if message["role"] == "user" else avatar_bot
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# ==============================
# USER INPUT
# ==============================
user_input = st.chat_input("Share how you're feeling...")

if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})

    payload = {
        "user_id": st.session_state.user_id,
        "message": user_input
    }

    with st.spinner("Analyzing emotional state..."):
        try:
            response = requests.post(f"{BACKEND_URL}/chat", json=payload)
            data = response.json()

            assistant_reply = data.get("response")
            mhi = data.get("mhi", 0)
            category = data.get("category", "Unknown")
            crisis_flag = data.get("crisis", False)

            st.session_state.chat_history.append(
                {"role": "assistant", "content": assistant_reply}
            )

            with st.chat_message("assistant", avatar=avatar_bot):
                st.markdown(assistant_reply)
                st.markdown("---")

                col1, col2 = st.columns(2)

                col1.markdown(f"""
                <div class="metric-box">
                    <h3>Mental Health Index</h3>
                    <h2>{mhi}/100</h2>
                </div>
                """, unsafe_allow_html=True)

                col1.progress(int(mhi))

                category_class = {
                    "Normal": "normal",
                    "Mild Stress": "stress",
                    "Anxiety": "anxiety",
                    "Depression": "depression"
                }.get(category, "crisis")

                col2.markdown(f"""
                <div class="badge {category_class}">
                    {category}
                </div>
                """, unsafe_allow_html=True)

                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=mhi,
                    title={'text': "Mental Health Index"},
                    gauge={
                        'axis': {'range': [0, 100]},
                        'bar': {'color': "green" if mhi > 70 else "orange" if mhi > 40 else "red"},
                    }
                ))

                st.plotly_chart(fig, use_container_width=True)

                if crisis_flag:
                    st.error("Immediate support recommended. Contact emergency services or a trusted person.")

        except requests.exceptions.RequestException as e:
            st.error(f"Backend error: {e}")

# ==============================
# TREND DASHBOARD
# ==============================
st.markdown("---")
st.subheader("Mental Health Trend Over Time")

try:
    trend = requests.get(
        f"{BACKEND_URL}/user/{st.session_state.user_id}/timeline"
    )
    trend_data = trend.json()

    if trend_data:
        df = pd.DataFrame(trend_data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp")

        fig = px.line(
            df,
            x="timestamp",
            y="mhi",
            markers=True,
            title="Mental Health Index Over Time"
        )

        fig.update_layout(
            template="plotly_white",
            xaxis_title="Date",
            yaxis_title="MHI Score",
            yaxis=dict(range=[0,100])
        )

        st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("No historical data yet.")

except:
    st.warning("Unable to load trend data.")

# ==============================
# CBT SUPPORT PANEL
# ==============================
st.markdown("---")
st.subheader("Self-Help Tools")

def tool_card(title, description):
    st.markdown(f"""
    <div class="glass-card">
        <h4>{title}</h4>
        <p>{description}</p>
    </div>
    """, unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Breathing Exercise"):
        tool_card("Breathing Exercise",
                  "Inhale 4s → Hold 4s → Exhale 6s. Repeat 5 times.")

with col2:
    if st.button("Grounding 5-4-3-2-1"):
        tool_card("Grounding Technique",
                  "5 see • 4 feel • 3 hear • 2 smell • 1 taste")

with col3:
    if st.button("Cognitive Reframe"):
        tool_card("Cognitive Reframe",
                  "Challenge evidence. Identify alternative explanations.")