import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from utils.api import get_report


def _mhi_color(mhi: float) -> str:
    if mhi >= 70: return "#48bb78"
    if mhi >= 40: return "#ed8936"
    return "#fc8181"


def _gauge(mhi: float) -> go.Figure:
    color = _mhi_color(mhi)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=mhi,
        number={"font": {"color": color, "size": 40, "family": "Sora"}},
        gauge={
            "axis": {
                "range": [0, 100],
                "tickcolor": "#546070",
                "tickfont": {"color": "#546070", "size": 10},
            },
            "bar": {"color": color, "thickness": 0.22},
            "bgcolor": "#1a2035",
            "borderwidth": 0,
            "steps": [
                {"range": [0,  40], "color": "rgba(252,129,129,0.10)"},
                {"range": [40, 70], "color": "rgba(237,137,54,0.10)"},
                {"range": [70,100], "color": "rgba(72,187,120,0.10)"},
            ],
            "threshold": {
                "line": {"color": color, "width": 2},
                "thickness": 0.75,
                "value": mhi,
            },
        },
        title={"text": "Latest MHI", "font": {"color": "#8b9ab0", "size": 12, "family": "Sora"}},
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=50, b=20),
        height=230,
        font={"family": "Sora"},
    )
    return fig


def _trend_chart(df: pd.DataFrame) -> go.Figure:
    fig = px.line(df, x="timestamp", y="mhi", markers=True)
    fig.update_traces(
        line=dict(color="#63b3ed", width=2),
        marker=dict(color="#63b3ed", size=7, line=dict(color="#0f1117", width=2)),
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Sora", "color": "#8b9ab0"},
        margin=dict(l=0, r=0, t=10, b=0),
        height=220,
        xaxis=dict(title=None, showgrid=False, zeroline=False, tickfont=dict(size=10)),
        yaxis=dict(
            title=None, range=[0, 100],
            showgrid=True, gridcolor="rgba(255,255,255,0.04)",
            zeroline=False, tickfont=dict(size=10),
        ),
        hovermode="x unified",
    )
    return fig


def render_dashboard() -> None:
    log = st.session_state.get("mhi_log", [])

    if not log:
        st.markdown("""
        <div style="
            background:#1a2035; border:1px solid rgba(255,255,255,0.07);
            border-radius:12px; padding:3rem; text-align:center;
            color:#546070; font-size:0.88rem; line-height:1.7;
        ">
            No session data yet.<br>
            Start a conversation and your Mental Health Index will appear here.
        </div>
        """, unsafe_allow_html=True)
        return

    df = pd.DataFrame(log)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)

    latest_mhi      = df["mhi"].iloc[-1]
    avg_mhi         = df["mhi"].mean()
    session_count   = len(df)
    latest_category = df["category"].iloc[-1] if "category" in df.columns else "—"
    latest_color    = _mhi_color(latest_mhi)
    avg_color       = _mhi_color(avg_mhi)

    # ── Top stat row ──────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)

    def stat(col, label, value, color="#e8edf5", suffix=""):
        col.markdown(f"""
        <div class="stat-card">
            <div class="label">{label}</div>
            <div class="value" style="color:{color};">{value}<span style="font-size:0.9rem;color:#546070;">{suffix}</span></div>
        </div>
        """, unsafe_allow_html=True)

    stat(c1, "Latest MHI",   int(latest_mhi), latest_color, "/100")
    stat(c2, "Session Avg",  f"{avg_mhi:.0f}", avg_color,   "/100")
    stat(c3, "Check-ins",    session_count)
    stat(c4, "Last Category", latest_category, "#b794f4")

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

    # ── Gauge + trend side by side ─────────────────────────────────────────────
    col_gauge, col_trend = st.columns([2, 3])

    with col_gauge:
        st.markdown('<div class="mhi-container" style="padding:0.5rem;">', unsafe_allow_html=True)
        st.plotly_chart(_gauge(latest_mhi), use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

    with col_trend:
        st.markdown("""
        <div style="font-size:0.68rem;font-weight:600;text-transform:uppercase;
             letter-spacing:0.08em;color:#546070;margin-bottom:0.6rem;">
            MHI Over Session
        </div>
        """, unsafe_allow_html=True)
        st.markdown('<div class="mhi-container" style="padding:1rem;">', unsafe_allow_html=True)
        st.plotly_chart(_trend_chart(df), use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Category history table ─────────────────────────────────────────────────
    if "category" in df.columns and df["category"].notna().any():
        st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div style="font-size:0.68rem;font-weight:600;text-transform:uppercase;
             letter-spacing:0.08em;color:#546070;margin-bottom:0.6rem;">
            Session History
        </div>
        """, unsafe_allow_html=True)

        rows_html = ""
        for _, row in df.iloc[::-1].iterrows():
            c = _mhi_color(row["mhi"])
            cat = row.get("category", "—") or "—"
            ts  = row["timestamp"].strftime("%H:%M:%S")
            rows_html += f"""
            <tr>
                <td style="color:#546070;font-family:'JetBrains Mono',monospace;font-size:0.75rem;padding:8px 12px;">{ts}</td>
                <td style="padding:8px 12px;">
                    <span style="font-size:1rem;font-weight:600;color:{c};">{int(row['mhi'])}</span>
                    <span style="color:#546070;font-size:0.75rem;">/100</span>
                </td>
                <td style="padding:8px 12px;">
                    <span style="background:rgba(183,148,244,0.12);border:1px solid rgba(183,148,244,0.2);
                          border-radius:20px;padding:2px 10px;font-size:0.73rem;color:#b794f4;">{cat}</span>
                </td>
            </tr>"""

        st.markdown(f"""
        <div class="mhi-container" style="padding:0; overflow:hidden;">
            <table style="width:100%;border-collapse:collapse;">
                <thead>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.06);">
                        <th style="text-align:left;padding:10px 12px;font-size:0.68rem;font-weight:600;
                                   text-transform:uppercase;letter-spacing:0.07em;color:#546070;">Time</th>
                        <th style="text-align:left;padding:10px 12px;font-size:0.68rem;font-weight:600;
                                   text-transform:uppercase;letter-spacing:0.07em;color:#546070;">Score</th>
                        <th style="text-align:left;padding:10px 12px;font-size:0.68rem;font-weight:600;
                                   text-transform:uppercase;letter-spacing:0.07em;color:#546070;">Category</th>
                    </tr>
                </thead>
                <tbody>{rows_html}</tbody>
            </table>
        </div>
        """, unsafe_allow_html=True)

    # ── Download Report ────────────────────────────────────────────────────────
    _render_download_report(
        user_id=st.session_state.get("user_id", "unknown"),
        avg_mhi=avg_mhi,
        df=df,
    )


def _render_download_report(user_id: str, avg_mhi: float, df: pd.DataFrame) -> None:
    st.markdown("<div style='height:2rem'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style="border-top:1px solid rgba(255,255,255,0.07); padding-top:1.5rem;
                display:flex; align-items:center; justify-content:space-between;">
        <div>
            <div style="font-size:0.68rem;font-weight:600;text-transform:uppercase;
                        letter-spacing:0.08em;color:#546070;margin-bottom:4px;">Session Report</div>
            <div style="font-size:0.82rem;color:#8b9ab0;">
                Download a full PDF report generated by the AI, including your MHI summary and session analysis.
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

    # Build a plain-text summary from the session log to send to the backend LLM
    categories = df["category"].dropna().unique().tolist() if "category" in df.columns else []
    summary_text = (
        f"This session had {len(df)} check-in(s). "
        f"The average Mental Health Index was {avg_mhi:.1f}/100. "
        f"Categories observed: {', '.join(categories) if categories else 'N/A'}. "
        f"Latest MHI score: {int(df['mhi'].iloc[-1])}/100."
    )

    _, btn_col, _ = st.columns([3, 2, 3])
    with btn_col:
        if st.button("Download PDF Report", use_container_width=True, key="dl_report"):
            with st.spinner("Generating report…"):
                try:
                    pdf_bytes = get_report(user_id)
                    from datetime import datetime
                    filename = f"wellbeing_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    st.download_button(
                        label="Save PDF",
                        data=pdf_bytes,
                        file_name=filename,
                        mime="application/pdf",
                        use_container_width=True,
                        key="save_pdf",
                    )
                except Exception as e:
                    st.error(f"Could not generate report: {e}")
