from __future__ import annotations

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime


# ── Dashboard CSS ─────────────────────────────────────────────────────────────

_DASH_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Stat cards ── */
.stat-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    margin-bottom: 22px;
}
.stat-card {
    background: #1a2035;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px;
    padding: 18px 20px 16px;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s ease;
}
.stat-card:hover { border-color: rgba(99,179,237,0.25); }
.stat-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    border-radius: 14px 14px 0 0;
}
.stat-card.c-blue::before   { background: linear-gradient(90deg,#63b3ed,#4fd1c5); }
.stat-card.c-teal::before   { background: linear-gradient(90deg,#4fd1c5,#38b2ac); }
.stat-card.c-purple::before { background: linear-gradient(90deg,#b794f4,#9f7aea); }
.stat-card.c-green::before  { background: linear-gradient(90deg,#48bb78,#38a169); }
.stat-card.c-orange::before { background: linear-gradient(90deg,#ed8936,#dd6b20); }
.stat-card.c-red::before    { background: linear-gradient(90deg,#fc8181,#e53e3e); }

.stat-label {
    font-size: 0.62rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.10em;
    color: #546070;
    margin-bottom: 10px;
    font-family: 'Sora', sans-serif;
}
.stat-value {
    font-size: 2rem;
    font-weight: 600;
    line-height: 1;
    font-family: 'Sora', sans-serif;
    display: flex;
    align-items: baseline;
    gap: 3px;
}
.stat-suffix {
    font-size: 0.78rem;
    font-weight: 400;
    color: #546070;
}
.stat-sub {
    font-size: 0.70rem;
    color: #546070;
    margin-top: 8px;
    font-family: 'Sora', sans-serif;
}

/* ── Section labels ── */
.section-label {
    font-size: 0.62rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.10em;
    color: #546070;
    margin-bottom: 10px;
    margin-top: 4px;
    font-family: 'Sora', sans-serif;
    display: flex;
    align-items: center;
    gap: 8px;
}
.section-label::after {
    content: '';
    flex: 1;
    height: 1px;
    background: rgba(255,255,255,0.05);
}

/* ── Chart wrapper ── */
.chart-card {
    background: #1a2035;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px;
    padding: 16px 16px 8px;
    height: 100%;
}

/* ── Session history table ── */
.history-card {
    background: #1a2035;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px;
    overflow: hidden;
    margin-top: 4px;
}
.history-table {
    width: 100%;
    border-collapse: collapse;
    font-family: 'Sora', sans-serif;
}
.history-table thead tr {
    border-bottom: 1px solid rgba(255,255,255,0.07);
}
.history-table thead th {
    text-align: left;
    padding: 12px 16px;
    font-size: 0.60rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.10em;
    color: #546070;
}
.history-table tbody tr {
    border-bottom: 1px solid rgba(255,255,255,0.04);
    transition: background 0.15s;
}
.history-table tbody tr:last-child { border-bottom: none; }
.history-table tbody tr:hover { background: rgba(255,255,255,0.02); }
.history-table tbody td {
    padding: 10px 16px;
    font-size: 0.78rem;
    vertical-align: middle;
}
.ts-cell {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    color: #546070;
}
.score-cell {
    font-family: 'JetBrains Mono', monospace;
    font-weight: 500;
}
.cat-badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.68rem;
    font-weight: 500;
}
.src-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 2px 8px;
    border-radius: 20px;
    font-size: 0.60rem;
    font-weight: 600;
    letter-spacing: 0.04em;
}
.src-text  { background: rgba(99,179,237,0.10); color: #63b3ed; border: 1px solid rgba(99,179,237,0.18); }
.src-voice { background: rgba(79,209,197,0.10); color: #4fd1c5; border: 1px solid rgba(79,209,197,0.18); }

/* ── Empty state ── */
.dash-empty {
    background: #1a2035;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px;
    padding: 3.5rem 2rem;
    text-align: center;
}
.dash-empty-icon {
    width: 52px; height: 52px;
    border-radius: 50%;
    background: rgba(99,179,237,0.08);
    border: 1px solid rgba(99,179,237,0.15);
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 1.3rem;
    margin-bottom: 1rem;
}
.dash-empty-title {
    font-size: 0.95rem;
    font-weight: 600;
    color: #e8edf5;
    margin-bottom: 0.4rem;
}
.dash-empty-sub {
    font-size: 0.80rem;
    color: #546070;
    line-height: 1.7;
    max-width: 320px;
    margin: 0 auto;
}

/* ── Report section ── */
.report-strip {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: #1a2035;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px;
    padding: 18px 22px;
    margin-top: 22px;
    gap: 16px;
}
.report-strip-text .title {
    font-size: 0.82rem;
    font-weight: 600;
    color: #e8edf5;
    margin-bottom: 3px;
}
.report-strip-text .sub {
    font-size: 0.72rem;
    color: #546070;
    line-height: 1.5;
}
</style>
"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _mhi_color(mhi: float) -> str:
    if mhi >= 70: return "#48bb78"
    if mhi >= 55: return "#68d391"
    if mhi >= 40: return "#ed8936"
    if mhi >= 25: return "#fc8181"
    return "#fc4e4e"


def _mhi_accent(mhi: float) -> str:
    """Card accent class based on MHI."""
    if mhi >= 70: return "c-green"
    if mhi >= 55: return "c-teal"
    if mhi >= 40: return "c-orange"
    return "c-red"


_CAT_COLORS: dict[str, str] = {
    "Stable":            "#48bb78",
    "Mild Stress":       "#68d391",
    "Moderate Distress": "#ed8936",
    "High Risk":         "#fc8181",
    "Depression Risk":   "#f56565",
    "Crisis Risk":       "#fc4e4e",
}


def _fmt_ts(ts) -> str:
    """Format timestamp as clean HH:MM:SS — no milliseconds."""
    try:
        if isinstance(ts, str):
            # Handle ISO format with or without milliseconds
            dt = pd.to_datetime(ts)
        else:
            dt = ts
        return dt.strftime("%H:%M:%S")
    except Exception:
        return str(ts)[:8]


# ── Charts ────────────────────────────────────────────────────────────────────

def _gauge(mhi: float) -> go.Figure:
    color = _mhi_color(mhi)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=mhi,
        number={
            "font": {"color": color, "size": 44, "family": "Sora"},
            "suffix": "",
        },
        gauge={
            "axis": {
                "range": [0, 100],
                "tickvals": [0, 25, 40, 55, 70, 85, 100],
                "ticktext": ["0", "25", "40", "55", "70", "85", "100"],
                "tickcolor": "#2e3a4a",
                "tickfont": {"color": "#3a4a5a", "size": 9, "family": "Sora"},
                "linecolor": "rgba(255,255,255,0.05)",
                "linewidth": 1,
            },
            "bar": {"color": color, "thickness": 0.24},
            "bgcolor": "rgba(0,0,0,0)",
            "borderwidth": 0,
            "steps": [
                {"range": [0,  25], "color": "rgba(252,78,78,0.08)"},
                {"range": [25, 40], "color": "rgba(252,129,129,0.08)"},
                {"range": [40, 55], "color": "rgba(237,137,54,0.08)"},
                {"range": [55, 70], "color": "rgba(104,211,145,0.08)"},
                {"range": [70,100], "color": "rgba(72,187,120,0.08)"},
            ],
            "threshold": {
                "line": {"color": color, "width": 2},
                "thickness": 0.80,
                "value": mhi,
            },
        },
        title={
            "text": "Latest MHI",
            "font": {"color": "#546070", "size": 11, "family": "Sora"},
        },
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=24, r=24, t=40, b=16),
        height=240,
        font={"family": "Sora"},
    )
    return fig


def _trend_chart(df: pd.DataFrame) -> go.Figure:
    """Clean MHI trend line with reference zones."""
    fig = go.Figure()

    # Zone bands
    zone_data = [
        (0,  25, "rgba(252,78,78,0.04)"),
        (25, 40, "rgba(252,129,129,0.04)"),
        (40, 55, "rgba(237,137,54,0.04)"),
        (55, 70, "rgba(104,211,145,0.04)"),
        (70, 100,"rgba(72,187,120,0.04)"),
    ]
    x_range = [df["timestamp"].min(), df["timestamp"].max()]
    for y0, y1, fill in zone_data:
        fig.add_hrect(y0=y0, y1=y1, fillcolor=fill, line_width=0)

    # Threshold lines
    for y_val, color, dash in [
        (70, "rgba(72,187,120,0.20)", "dot"),
        (40, "rgba(237,137,54,0.20)", "dot"),
        (25, "rgba(252,78,78,0.20)",  "dot"),
    ]:
        fig.add_hline(y=y_val, line_color=color, line_dash=dash, line_width=1)

    # Main trend line
    fig.add_trace(go.Scatter(
        x=df["timestamp"],
        y=df["mhi"],
        mode="lines+markers",
        line=dict(color="#63b3ed", width=2.5, shape="spline", smoothing=0.6),
        marker=dict(
            color=df["mhi"].apply(_mhi_color),
            size=8,
            line=dict(color="#0f1117", width=2),
        ),
        hovertemplate=(
            "<b>MHI: %{y}</b><br>"
            "%{x|%H:%M:%S}<extra></extra>"
        ),
    ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Sora", "color": "#546070"},
        margin=dict(l=4, r=4, t=8, b=4),
        height=240,
        xaxis=dict(
            title=None,
            showgrid=False,
            zeroline=False,
            tickfont=dict(size=9, family="JetBrains Mono"),
            tickformat="%H:%M:%S",
            tickangle=0,
        ),
        yaxis=dict(
            title=None,
            range=[0, 105],
            showgrid=True,
            gridcolor="rgba(255,255,255,0.04)",
            gridwidth=1,
            zeroline=False,
            tickfont=dict(size=9),
            tickvals=[0, 25, 40, 55, 70, 85, 100],
        ),
        hovermode="x unified",
        showlegend=False,
    )
    return fig


# ── Main render ───────────────────────────────────────────────────────────────

def render_dashboard() -> None:
    st.markdown(_DASH_CSS, unsafe_allow_html=True)

    log = st.session_state.get("mhi_log", [])

    # ── Empty state ───────────────────────────────────────────────────────────
    if not log:
        st.markdown("""
        <div class="dash-empty">
            <div class="dash-empty-icon">📊</div>
            <div class="dash-empty-title">No session data yet</div>
            <div class="dash-empty-sub">
                Start a conversation — text or voice — and your
                Mental Health Index will appear here in real time.
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── Build DataFrame ───────────────────────────────────────────────────────
    df = pd.DataFrame(log)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)

    if df.empty:
        st.info("Session data could not be parsed.")
        return

    # Derived stats
    latest_mhi      = float(df["mhi"].iloc[-1])
    avg_mhi         = float(df["mhi"].mean())
    max_mhi         = float(df["mhi"].max())
    min_mhi         = float(df["mhi"].min())
    session_count   = len(df)
    latest_category = str(df["category"].iloc[-1]) if "category" in df.columns else "—"
    voice_count     = int((df.get("source", "") == "voice").sum()) if "source" in df.columns else 0
    text_count      = session_count - voice_count

    latest_color  = _mhi_color(latest_mhi)
    avg_color     = _mhi_color(avg_mhi)
    latest_accent = _mhi_accent(latest_mhi)
    avg_accent    = _mhi_accent(avg_mhi)
    cat_color     = _CAT_COLORS.get(latest_category, "#b794f4")

    # ── Top stat row ──────────────────────────────────────────────────────────
    st.markdown('<div class="stat-grid">', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)

    def _stat_card(col, label, value, suffix, color, accent, sub=""):
        col.markdown(f"""
        <div class="stat-card {accent}">
            <div class="stat-label">{label}</div>
            <div class="stat-value" style="color:{color};">
                {value}<span class="stat-suffix">{suffix}</span>
            </div>
            {f'<div class="stat-sub">{sub}</div>' if sub else ''}
        </div>
        """, unsafe_allow_html=True)

    _stat_card(c1, "Latest MHI",    int(latest_mhi), " / 100", latest_color, latest_accent,
               sub=f"↑ {int(max_mhi)} peak  ↓ {int(min_mhi)} low")
    _stat_card(c2, "Session Average", f"{avg_mhi:.0f}", " / 100", avg_color, avg_accent)
    _stat_card(c3, "Check-ins",
               session_count, "",  "#8b9ab0", "c-blue",
               sub=f"💬 {text_count} text  🎙 {voice_count} voice" if voice_count else f"💬 {text_count} text")
    _stat_card(c4, "Latest Category",
               latest_category, "", cat_color,
               "c-purple" if cat_color == "#b794f4" else latest_accent)

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Gauge + Trend chart ───────────────────────────────────────────────────
    st.markdown('<div class="section-label">Mental Health Index</div>', unsafe_allow_html=True)

    col_gauge, col_trend = st.columns([5, 7], gap="medium")

    with col_gauge:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.plotly_chart(
            _gauge(latest_mhi),
            use_container_width=True,
            config={"displayModeBar": False},
        )
        # Zone legend
        st.markdown("""
        <div style="display:flex;flex-wrap:wrap;gap:8px;padding:2px 4px 6px;justify-content:center;">
            <span style="font-size:0.60rem;color:#fc4e4e;display:flex;align-items:center;gap:3px;">
                <span style="width:6px;height:6px;border-radius:50%;background:#fc4e4e;display:inline-block;"></span>Crisis
            </span>
            <span style="font-size:0.60rem;color:#fc8181;display:flex;align-items:center;gap:3px;">
                <span style="width:6px;height:6px;border-radius:50%;background:#fc8181;display:inline-block;"></span>High Risk
            </span>
            <span style="font-size:0.60rem;color:#ed8936;display:flex;align-items:center;gap:3px;">
                <span style="width:6px;height:6px;border-radius:50%;background:#ed8936;display:inline-block;"></span>Distress
            </span>
            <span style="font-size:0.60rem;color:#68d391;display:flex;align-items:center;gap:3px;">
                <span style="width:6px;height:6px;border-radius:50%;background:#68d391;display:inline-block;"></span>Mild
            </span>
            <span style="font-size:0.60rem;color:#48bb78;display:flex;align-items:center;gap:3px;">
                <span style="width:6px;height:6px;border-radius:50%;background:#48bb78;display:inline-block;"></span>Stable
            </span>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_trend:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown("""
        <div style="font-size:0.68rem;font-weight:600;text-transform:uppercase;
                    letter-spacing:0.08em;color:#546070;margin-bottom:2px;">
            MHI Over Session
        </div>""", unsafe_allow_html=True)
        st.plotly_chart(
            _trend_chart(df),
            use_container_width=True,
            config={"displayModeBar": False},
        )
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    # ── Session history table ─────────────────────────────────────────────────
    if "category" in df.columns and df["category"].notna().any():
        st.markdown('<div class="section-label">Session History</div>', unsafe_allow_html=True)

        rows_html = ""
        for _, row in df.iloc[::-1].iterrows():
            mhi_val  = int(row["mhi"])
            c        = _mhi_color(mhi_val)
            cat      = str(row.get("category", "—") or "—")
            cat_col  = _CAT_COLORS.get(cat, "#b794f4")
            ts       = _fmt_ts(row["timestamp"])
            src      = str(row.get("source", "text"))
            src_cls  = "src-voice" if src == "voice" else "src-text"
            src_icon = "🎙" if src == "voice" else "💬"
            src_lbl  = "Voice" if src == "voice" else "Text"

            rows_html += f"""
            <tr>
                <td class="ts-cell">{ts}</td>
                <td>
                    <span class="score-cell" style="color:{c};">{mhi_val}</span>
                    <span style="color:#3a4a5a;font-family:'JetBrains Mono',monospace;font-size:0.68rem;"> /100</span>
                </td>
                <td>
                    <span class="cat-badge"
                          style="background:{cat_col}14;border:1px solid {cat_col}30;color:{cat_col};">
                        {cat}
                    </span>
                </td>
                <td>
                    <span class="src-badge {src_cls}">{src_icon} {src_lbl}</span>
                </td>
            </tr>"""

        st.markdown(f"""
        <div class="history-card">
            <table class="history-table">
                <thead>
                    <tr>
                        <th style="width:18%;">Time</th>
                        <th style="width:16%;">Score</th>
                        <th style="width:40%;">Category</th>
                        <th style="width:16%;">Source</th>
                    </tr>
                </thead>
                <tbody>{rows_html}</tbody>
            </table>
        </div>
        """, unsafe_allow_html=True)

    # ── Download report ───────────────────────────────────────────────────────
    _render_report_strip(avg_mhi, df)


def _render_report_strip(avg_mhi: float, df: pd.DataFrame) -> None:
    categories = (
        df["category"].dropna().unique().tolist()
        if "category" in df.columns else []
    )
    session_count = len(df)
    voice_count   = int((df.get("source", "") == "voice").sum()) if "source" in df.columns else 0

    st.markdown(f"""
    <div class="report-strip">
        <div class="report-strip-text">
            <div class="title">📄 Session Report</div>
            <div class="sub">
                {session_count} check-in{"s" if session_count!=1 else ""} &nbsp;·&nbsp;
                Avg MHI {avg_mhi:.0f}/100 &nbsp;·&nbsp;
                {", ".join(categories[:3]) if categories else "No categories"}
                {f" &nbsp;·&nbsp; {voice_count} via voice" if voice_count else ""}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    _, btn_col, _ = st.columns([3, 2, 3])
    with btn_col:
        if st.button("Download PDF Report", use_container_width=True, key="dl_report"):
            with st.spinner("Generating report…"):
                try:
                    from utils.api import get_report
                    pdf_bytes = get_report()
                    filename  = f"wellbeing_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    st.download_button(
                        label="💾  Save PDF",
                        data=pdf_bytes,
                        file_name=filename,
                        mime="application/pdf",
                        use_container_width=True,
                        key="save_pdf",
                    )
                except Exception as e:
                    st.error(f"Could not generate report: {e}")
