from __future__ import annotations

import logging
from datetime import datetime

import streamlit as st

logger = logging.getLogger(__name__)

# Colour maps
_CAT_COLOR: dict[str, str] = {
    "Stable":            "#48bb78",
    "Mild Stress":       "#68d391",
    "Moderate Distress": "#ed8936",
    "High Risk":         "#f56565",
    "Depression Risk":   "#fc8181",
    "Crisis Risk":       "#fc4e4e",
}

def _mhi_color(mhi: float) -> str:
    if mhi >= 82: return "#48bb78"
    if mhi >= 66: return "#68d391"
    if mhi >= 50: return "#ed8936"
    if mhi >= 32: return "#f56565"
    if mhi >= 16: return "#fc8181"
    return "#fc4e4e"


# ── Dashboard CSS ─────────────────────────────────────────────────────────────
_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Stat grid — 4 equal-width, equal-HEIGHT cards ── */
.stat-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    grid-auto-rows: 118px;          /* ALL cards same height — no exceptions */
    gap: 14px;
    margin-bottom: 22px;
    width: 100%;
    animation: fadeInDash .26s ease-out;
}
@media(max-width: 860px) {
    .stat-grid { grid-template-columns: repeat(2, 1fr); }
}
@media(max-width: 560px) {
    .stat-grid { grid-template-columns: 1fr; grid-auto-rows: 108px; }
}

.stat-card {
    background: #101d31;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px;
    padding: 0 20px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    gap: 4px;
    position: relative;
    overflow: hidden;
    transition: border-color .2s, transform .2s, box-shadow .2s;
}
.stat-card:hover {
    border-color: rgba(99,179,237,0.22);
    transform: translateY(-1px);
    box-shadow: 0 10px 24px rgba(5, 10, 24, 0.35);
}
.stat-card::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0;
    height: 3px;
    background: var(--accent, #4fd1c5);
    border-radius: 14px 14px 0 0;
}
.stat-label {
    font-size: .60rem; font-weight: 600; text-transform: uppercase;
    letter-spacing: .10em; color: #8ea0b8;
    font-family: 'Sora', sans-serif;
    white-space: nowrap;
}
.stat-value {
    font-size: 1.85rem; font-weight: 600; line-height: 1.05;
    font-family: 'Sora', sans-serif;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.stat-suffix {
    font-size: .72rem; font-weight: 400; color: #8ea0b8;
}
.stat-sub {
    font-size: .64rem; color: #8ea0b8;
    font-family: 'Sora', sans-serif;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}

/* ── Section label ── */
.section-lbl {
    font-size: .62rem; font-weight: 600; text-transform: uppercase;
    letter-spacing: .10em; color: #8ea0b8;
    margin: 4px 0 10px;
    display: flex; align-items: center; gap: 8px;
}
.section-lbl::after {
    content: ''; flex: 1; height: 1px;
    background: rgba(255,255,255,.05);
}

/* ── Chart wrapper ── */
.chart-card {
    background: #101d31;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px;
    padding: 16px 16px 8px;
    transition: border-color .2s ease;
}
.chart-card:hover { border-color: rgba(99,179,237,0.2); }
.chart-sub-lbl {
    font-size: .62rem; font-weight: 600; text-transform: uppercase;
    letter-spacing: .08em; color: #8ea0b8;
    margin-bottom: 6px;
    font-family: 'Sora', sans-serif;
}

/* ── Session history table ── */
.hist-wrap {
    background: #101d31;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px;
    overflow-x: auto;
    overflow-y: hidden;
    margin-top: 4px;
}
.hist-table {
    width: 100%; min-width: 620px; border-collapse: collapse;
    font-family: 'Sora', sans-serif;
}
.hist-table thead tr {
    border-bottom: 1px solid rgba(255,255,255,.07);
}
.hist-table thead th {
    text-align: left; padding: 12px 16px;
    font-size: .60rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: .10em; color: #8ea0b8;
}
.hist-table tbody tr {
    border-bottom: 1px solid rgba(255,255,255,.04);
    transition: background .15s;
}
.hist-table tbody tr:last-child { border-bottom: none; }
.hist-table tbody tr:hover { background: rgba(255,255,255,.02); }
.hist-table tbody td {
    padding: 10px 16px;
    font-size: .78rem;
    vertical-align: middle;
}
.ts-cell {
    font-family: 'JetBrains Mono', monospace;
    font-size: .70rem; color: #8ea0b8;
}
.score-cell {
    font-family: 'JetBrains Mono', monospace;
    font-weight: 500;
}
.cat-badge, .src-badge {
    display: inline-flex; align-items: center; gap: 5px;
    padding: 3px 9px; border-radius: 20px;
    font-size: .65rem; font-weight: 500;
}
.src-voice { background: rgba(79,209,197,.10);  color:#4fd1c5; border:1px solid rgba(79,209,197,.20); }
.src-text  { background: rgba(99,179,237,.10);  color:#63b3ed; border:1px solid rgba(99,179,237,.20); }
.lang-tag  { background: rgba(183,148,244,.10); color:#b794f4; border:1px solid rgba(183,148,244,.20);
             display:inline-flex;align-items:center;padding:2px 7px;border-radius:10px;
             font-size:.58rem;margin-left:5px; }

/* ── Zone legend ── */
.zone-legend {
    display: flex; flex-wrap: wrap; gap: 8px;
    padding: 4px 2px 6px; justify-content: center;
}
.zone-pill {
    display: flex; align-items: center; gap: 4px;
    font-size: .60rem; color: #8ea0b8;
}
.zone-dot { width: 6px; height: 6px; border-radius: 50%; display: inline-block; }

/* ── Empty state ── */
.dash-empty {
    background: #101d31;
    border: 1px solid rgba(255,255,255,.07);
    border-radius: 14px;
    padding: 3.5rem 2rem; text-align: center;
}
.dash-empty-icon {
    width: 52px; height: 52px; border-radius: 50%;
    background: rgba(99,179,237,.08); border: 1px solid rgba(99,179,237,.14);
    display: inline-flex; align-items: center; justify-content: center;
    font-size: 1.4rem; margin-bottom: 1rem;
}
.dash-empty-title { font-size: .95rem; font-weight: 600; color: #e8edf5; margin-bottom: .4rem; }
.dash-empty-sub   { font-size: .80rem; color: #8ea0b8; line-height: 1.75; max-width: 300px; margin: 0 auto; }

@keyframes fadeInDash {
    from { opacity: 0; transform: translateY(5px); }
    to { opacity: 1; transform: translateY(0); }
}

@media (prefers-reduced-motion: reduce) {
    .stat-grid, .stat-card, .chart-card, .turn {
        animation: none !important;
        transition: none !important;
    }
}
</style>
"""

# ── Zone legend rows ──────────────────────────────────────────────────────────
_ZONES = [
    ("#48bb78", "Stable",            "82+"),
    ("#68d391", "Mild Stress",       "66–81"),
    ("#ed8936", "Moderate Distress", "50–65"),
    ("#f56565", "High Risk",         "32–49"),
    ("#fc8181", "Depression Risk",   "16–31"),
    ("#fc4e4e", "Crisis Risk",       "< 16"),
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fmt_ts(ts: str) -> str:
    try:
        import pandas as pd
        return pd.to_datetime(ts).strftime("%H:%M:%S")
    except Exception:
        return str(ts)[:8]


def _stat_card(label: str, value: str, suffix: str, color: str, accent: str, sub: str = "") -> str:
    sub_html = f'<div class="stat-sub">{sub}</div>' if sub else ""
    return (
        f'<div class="stat-card" style="--accent:{accent}">'
        f'<div class="stat-label">{label}</div>'
        f'<div class="stat-value" style="color:{color};">'
        f'{value}<span class="stat-suffix">{suffix}</span></div>'
        f'{sub_html}'
        f'</div>'
    )


# ── Gauge chart ───────────────────────────────────────────────────────────────

def _gauge(mhi: float) -> None:
    try:
        import plotly.graph_objects as go
    except ImportError:
        st.metric("MHI", f"{mhi:.0f}")
        return

    color = _mhi_color(mhi)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=mhi,
        number={"font": {"color": color, "size": 44, "family": "Sora"}, "suffix": ""},
        gauge={
            "axis": {
                "range": [0, 100],
                "tickvals": [0, 16, 32, 50, 66, 82, 100],
                "ticktext": ["0", "16", "32", "50", "66", "82", "100"],
                "tickcolor": "#7388a6",
                "tickfont":  {"color": "#8ea0b8", "size": 9, "family": "Sora"},
                "linecolor": "rgba(255,255,255,.05)",
            },
            "bar":      {"color": color, "thickness": 0.24},
            "bgcolor":  "rgba(0,0,0,0)",
            "borderwidth": 0,
            "steps": [
                {"range": [0,   16], "color": "rgba(252,78,78,0.09)"},
                {"range": [16,  32], "color": "rgba(252,129,129,0.08)"},
                {"range": [32,  50], "color": "rgba(245,101,101,0.07)"},
                {"range": [50,  66], "color": "rgba(237,137,54,0.07)"},
                {"range": [66,  82], "color": "rgba(104,211,145,0.07)"},
                {"range": [82, 100], "color": "rgba(72,187,120,0.09)"},
            ],
            "threshold": {"line": {"color": color, "width": 2}, "thickness": .80, "value": mhi},
        },
        title={"text": "Latest MHI", "font": {"color": "#8ea0b8", "size": 11, "family": "Sora"}},
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=22, r=22, t=38, b=14), height=230,
        font={"family": "Sora"},
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ── Trend chart ───────────────────────────────────────────────────────────────

def _trend_chart(log: list[dict]) -> None:
    try:
        import plotly.graph_objects as go
        import pandas as pd
    except ImportError:
        st.line_chart([e["mhi"] for e in log])
        return

    df = (
        pd.DataFrame(log)
        .assign(timestamp=lambda d: pd.to_datetime(d["timestamp"], errors="coerce"))
        .dropna(subset=["timestamp"])
        .sort_values("timestamp")
        .reset_index(drop=True)
    )
    if df.empty:
        return

    fig = go.Figure()

    # Zone bands (match tightened MHI thresholds)
    for y0, y1, fill in [
        (0,  16, "rgba(252,78,78,.05)"),
        (16, 32, "rgba(252,129,129,.04)"),
        (32, 50, "rgba(245,101,101,.04)"),
        (50, 66, "rgba(237,137,54,.04)"),
        (66, 82, "rgba(104,211,145,.04)"),
        (82,100, "rgba(72,187,120,.05)"),
    ]:
        fig.add_hrect(y0=y0, y1=y1, fillcolor=fill, line_width=0)

    # Threshold dotted lines
    for y, col in [(82,"rgba(72,187,120,.22)"),(66,"rgba(104,211,145,.18)"),
                   (50,"rgba(237,137,54,.18)"),(32,"rgba(245,101,101,.20)"),(16,"rgba(252,78,78,.22)")]:
        fig.add_hline(y=y, line_color=col, line_dash="dot", line_width=1)

    fig.add_trace(go.Scatter(
        x=df["timestamp"],
        y=df["mhi"],
        mode="lines+markers",
        line=dict(color="#63b3ed", width=2.5, shape="spline", smoothing=0.7),
        marker=dict(
            color=[_mhi_color(v) for v in df["mhi"]],
            size=8, line=dict(color="#0a0f1e", width=2),
        ),
        hovertemplate="<b>MHI: %{y}</b><br>%{x|%H:%M:%S}<extra></extra>",
    ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Sora", "color": "#8ea0b8"},
        margin=dict(l=4, r=4, t=8, b=4), height=230,
        xaxis=dict(showgrid=False, zeroline=False,
                   tickfont=dict(size=9, family="JetBrains Mono"), tickformat="%H:%M:%S"),
        yaxis=dict(range=[0, 104], showgrid=True,
                   gridcolor="rgba(255,255,255,.04)", zeroline=False,
                   tickfont=dict(size=9),
                   tickvals=[0, 16, 32, 50, 66, 82, 100]),
        hovermode="x unified", showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ── Main render ───────────────────────────────────────────────────────────────

def render_dashboard() -> None:
    """
    Shows session MHI data. Fetches from backend API for reliability,
    falls back to session state cache.
    """
    st.markdown(_CSS, unsafe_allow_html=True)

    # Always try to refresh from backend API (most reliable source)
    log = st.session_state.get("mhi_log", [])
    try:
        from utils.api import get_timeline
        api_data = get_timeline()
        if api_data:
            log = [
                {
                    "timestamp": entry.get("timestamp", ""),
                    "mhi":       entry.get("mhi", 0),
                    "category":  entry.get("category", ""),
                    "source":    "voice",
                    "language_code": entry.get("language_code", "en"),
                }
                for entry in api_data
            ]
            st.session_state.mhi_log = log
    except Exception:
        pass

    # ── Empty state ───────────────────────────────────────────────────────────
    if not log:
        st.markdown("""
        <div class="dash-empty">
            <div class="dash-empty-icon">&#128200;</div>
            <div class="dash-empty-title">No session data yet</div>
            <div class="dash-empty-sub">
                Start a voice conversation and your Mental Health Index
                will appear here in real time, updating after every turn.
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── Derive stats ──────────────────────────────────────────────────────────
    mhi_vals      = [float(e.get("mhi", 0)) for e in log]
    latest_mhi    = mhi_vals[-1]
    avg_mhi       = sum(mhi_vals) / len(mhi_vals)
    peak_mhi      = max(mhi_vals)
    low_mhi       = min(mhi_vals)
    n             = len(log)
    n_voice       = sum(1 for e in log if e.get("source") == "voice")
    latest_cat    = str(log[-1].get("category", ""))
    cat_color     = _CAT_COLOR.get(latest_cat, "#b794f4")

    # Trend arrow
    trend_arrow = ""
    if len(mhi_vals) >= 2:
        delta = mhi_vals[-1] - mhi_vals[-2]
        trend_arrow = f" &nbsp; {'&#9650;' if delta >= 0 else '&#9660;'} {abs(delta):.0f} pts"

    # ── Stat cards — all same height via CSS grid ─────────────────────────────
    st.markdown(
        '<div class="stat-grid">'
        + _stat_card("Latest MHI",
                     str(int(latest_mhi)), " / 100",
                     _mhi_color(latest_mhi), _mhi_color(latest_mhi),
                     sub=latest_cat + trend_arrow)
        + _stat_card("Session Average",
                     f"{avg_mhi:.0f}", " / 100",
                     _mhi_color(avg_mhi), _mhi_color(avg_mhi),
                     sub=f"Peak {int(peak_mhi)}  &nbsp;&#183;&nbsp;  Low {int(low_mhi)}")
        + _stat_card("Check-ins",
                     str(n), "",
                     "#8b9ab0", "#63b3ed",
                     sub=f"&#127908;&nbsp;{n_voice} voice &nbsp;&#183;&nbsp; &#128172;&nbsp;{n - n_voice} text")
        + _stat_card("Risk Category",
                     latest_cat or "—", "",
                     cat_color, cat_color)
        + '</div>',
        unsafe_allow_html=True,
    )

    # ── Gauge + Trend ─────────────────────────────────────────────────────────
    st.markdown('<div class="section-lbl">Mental Health Index</div>', unsafe_allow_html=True)

    col_g, col_t = st.columns([5, 7], gap="medium")

    with col_g:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        _gauge(latest_mhi)
        zone_pills = "".join(
            f'<div class="zone-pill">'
            f'<span class="zone-dot" style="background:{c}"></span>'
            f'<span style="color:{c}">{name}</span>'
            f'<span style="color:#8ea0b8">&nbsp;{rng}</span>'
            f'</div>'
            for c, name, rng in _ZONES
        )
        st.markdown(f'<div class="zone-legend">{zone_pills}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_t:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown('<div class="chart-sub-lbl">MHI Over Session</div>', unsafe_allow_html=True)
        _trend_chart(log)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── Session history table ─────────────────────────────────────────────────
    if n > 1:
        st.markdown('<div class="section-lbl">Session History</div>', unsafe_allow_html=True)

        rows = ""
        for entry in reversed(log[-25:]):   # newest first, last 25
            mhi_val   = int(entry.get("mhi", 0))
            cat       = str(entry.get("category", "—") or "—")
            ts        = _fmt_ts(entry.get("timestamp", ""))
            src       = str(entry.get("source", "voice"))
            lang_code = str(entry.get("language_code", "en"))
            mhi_col   = _mhi_color(mhi_val)
            cat_col   = _CAT_COLOR.get(cat, "#b794f4")
            src_cls   = "src-voice" if src == "voice" else "src-text"
            src_icon  = "&#127908;" if src == "voice" else "&#128172;"
            src_lbl   = "Voice" if src == "voice" else "Text"
            lang_tag  = (
                f'<span class="lang-tag">{lang_code.upper()}</span>'
                if lang_code not in ("en", "") else ""
            )

            rows += (
                f"<tr>"
                f"<td class='ts-cell'>{ts}</td>"
                f"<td><span class='score-cell' style='color:{mhi_col}'>{mhi_val}</span>"
                f"<span style='color:#8ea0b8;font-family:JetBrains Mono,monospace;font-size:.68rem'> /100</span></td>"
                f"<td><span class='cat-badge' style='background:{cat_col}14;"
                f"border:1px solid {cat_col}30;color:{cat_col}'>{cat}</span>{lang_tag}</td>"
                f"<td><span class='src-badge {src_cls}'>{src_icon}&nbsp;{src_lbl}</span></td>"
                f"</tr>"
            )

        st.markdown(
            '<div class="hist-wrap">'
            '<table class="hist-table">'
            '<thead><tr>'
            '<th style="width:18%">Time</th>'
            '<th style="width:14%">Score</th>'
            '<th style="width:44%">Category</th>'
            '<th style="width:14%">Source</th>'
            '</tr></thead>'
            f'<tbody>{rows}</tbody>'
            '</table></div>',
            unsafe_allow_html=True,
        )

    # ── Report strip ──────────────────────────────────────────────────────────
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    _, btn_col, _ = st.columns([3, 2, 3])
    with btn_col:
        if st.button("Download PDF Report", use_container_width=True, key="dl_report_v5"):
            with st.spinner("Generating report…"):
                try:
                    from utils.api import get_report
                    pdf = get_report()
                    fname = f"wellbeing_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    st.download_button(
                        "&#128190;&nbsp; Save PDF",
                        data=pdf, file_name=fname,
                        mime="application/pdf",
                        use_container_width=True,
                        key="save_pdf_v5",
                    )
                except Exception as e:
                    st.error(f"Could not generate report: {e}")