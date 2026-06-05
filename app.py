"""
BloodFlow Malaysia — Streamlit Dashboard (Data Product, GA2 Objective)
======================================================================
IMPROVED VERSION — Enhanced sidebar, dark navigation, live supply-status widget.

Changes from original:
  - Sidebar: dark theme (#0D1422), SVG blood-drop logo, styled nav (no circles),
    active-page highlight with red left-border accent
  - Sidebar: live Supply Status widget (pill + mini KPI cards + risk bar)
  - Sidebar: refined footer with data-date and info card
  - Global CSS: cleaner metric cards, consistent spacing
  - Code: data loaded before sidebar so the status widget can use it

Run locally:  streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from streamlit_option_menu import option_menu

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────
CRITICAL_THRESHOLD = 2000
OUTPUTS_DIR = "outputs"

BLOOD_RED = "#A61C2E"
DARK_RED  = "#7B1220"
NAVY      = "#1A3A5C"
GOLD      = "#E8A838"
GREEN     = "#157347"
GREY      = "#6C757D"

st.set_page_config(
    page_title="BloodFlow Malaysia",
    page_icon="🩸",
    layout="wide",
    initial_sidebar_state="expanded",
)

_theme_type = ((getattr(st.context, "theme", {}) or {}).get("type") or "light").lower()
_sidebar_dark = _theme_type == "dark"
SIDEBAR_BG = "#0D1422" if _sidebar_dark else "#F4F6FA"
SIDEBAR_CARD = "#111B2E" if _sidebar_dark else "#FFFFFF"
SIDEBAR_INFO = "#090F1C" if _sidebar_dark else "#FFFFFF"
SIDEBAR_TEXT = "#F8FAFC" if _sidebar_dark else "#172033"
SIDEBAR_MUTED = "#CBD5E1" if _sidebar_dark else "#4B5563"
SIDEBAR_SUBTLE = "#94A3B8" if _sidebar_dark else "#526071"
SIDEBAR_LINE = "#1A2540" if _sidebar_dark else "#D6DAE2"
SIDEBAR_HOVER = "rgba(255,255,255,0.06)" if _sidebar_dark else "rgba(166,28,46,0.06)"
SIDEBAR_ACTIVE = "rgba(166,28,46,0.20)" if _sidebar_dark else "rgba(166,28,46,0.12)"
SIDEBAR_ACCENT_TEXT = "#FF8090" if _sidebar_dark else "#A61C2E"
PILL_SAFE_TEXT = "#86EFAC" if _sidebar_dark else "#15803D"
PILL_WARN_TEXT = "#FDE68A" if _sidebar_dark else "#92400E"
PILL_CRIT_TEXT = "#FCA5A5" if _sidebar_dark else "#B91C1C"

CHART_DARK = _theme_type == "dark"
CHART_BG = "#0F172A" if CHART_DARK else "#FFFFFF"
CHART_PLOT_BG = "#111827" if CHART_DARK else "#FFFFFF"
CHART_TEXT = "#F8FAFC" if CHART_DARK else "#172033"
CHART_MUTED = "#CBD5E1" if CHART_DARK else "#5A6A80"
CHART_GRID = "rgba(148,163,184,0.24)" if CHART_DARK else "rgba(26,58,92,0.12)"
CHART_ZERO = "rgba(203,213,225,0.45)" if CHART_DARK else "rgba(26,58,92,0.22)"
CHART_HOVER_BG = "#111827" if CHART_DARK else "#FFFFFF"
CHART_HOVER_BORDER = "#334155" if CHART_DARK else "#D6DAE2"
CHART_BLUE = "#60A5FA" if CHART_DARK else NAVY
CHART_RED = "#FB7185" if CHART_DARK else BLOOD_RED
CHART_RED_SOFT = "rgba(248,113,113,0.45)" if CHART_DARK else "rgba(166,28,46,0.35)"
CHART_GOLD = "#FBBF24" if CHART_DARK else GOLD
CHART_GREY = "#CBD5E1" if CHART_DARK else GREY
CHART_INTERVAL_FILL = "rgba(96,165,250,0.20)" if CHART_DARK else "rgba(26,58,92,0.12)"
CHART_MARKER_LINE = CHART_BG if CHART_DARK else "#FFFFFF"
CHART_HOLIDAY_SCALE = (["#F87171", "#FB7185", "#FBBF24"] if CHART_DARK
                       else ["#7B1220", "#A61C2E", "#E8A838"])

# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL CSS  ── sidebar + main content
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ═══════════════════ SIDEBAR ═══════════════════ */

section[data-testid="stSidebar"] {
    background: __SIDEBAR_BG__ !important;
    color: __SIDEBAR_TEXT__ !important;

    /* KEY FIXES */
    height: 100vh !important;
    overflow-y: auto !important;
    overflow-x: hidden !important;
}

/* Remove forced clipping */
section[data-testid="stSidebar"] > div:first-child {
    padding: 0.65rem 0.7rem 1.2rem;
    height: auto !important;
    overflow: visible !important;
}

/* Improve spacing so content doesn't feel cramped */
section[data-testid="stSidebar"] .block-container {
    padding-bottom: 2rem !important;
}

/* Divider spacing */
section[data-testid="stSidebar"] hr {
    border-color: __SIDEBAR_LINE__ !important;
    margin: 0.6rem 0 !important;
}

/* Ensure option menu doesn't overflow awkwardly */
section[data-testid="stSidebar"] .st-emotion-cache-1d391kg {
    max-height: none !important;
}

/* Optional: smoother scrolling */
section[data-testid="stSidebar"] {
    scrollbar-width: thin;
}max-height: none !important;
}            

/* Dividers in sidebar */
section[data-testid="stSidebar"] hr {
    border-color: __SIDEBAR_LINE__ !important;
    margin: 0.38rem 0 !important;
}

section[data-testid="stSidebar"] .stSlider {
    padding: 0 0.1rem !important;
}
section[data-testid="stSidebar"] .stSlider [data-baseweb="slider"] {
    margin-top: -0.2rem !important;
}

/* ═══════════════════ MAIN CONTENT ═══════════════════ */

.main { background-color: #F5F7FB; }
div[data-testid="stMetricValue"] { font-size: 1.6rem; font-weight: 700; }
div[data-testid="stMetricLabel"] { font-size: 0.82rem; font-weight: 600; color: #5A6A80; }
div[data-testid="stMetricDelta"] { font-size: 0.75rem; }
.block-container { padding-top: 1.75rem; }

/* ═══════════════════ SIDEBAR MICRO-COMPONENTS ═══════════════════ */

/* Supply status pill */
.sb-pill {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 4px 9px;
    border-radius: 20px;
    font-size: 0.64rem;
    font-weight: 700;
    letter-spacing: 0.03em;
}
.sb-pill-safe { background: rgba(34,197,94,.16); color: __PILL_SAFE_TEXT__; border: 1px solid rgba(34,197,94,.36); }
.sb-pill-warn { background: rgba(245,158,11,.18); color: __PILL_WARN_TEXT__; border: 1px solid rgba(245,158,11,.38); }
.sb-pill-crit { background: rgba(239,68,68,.16); color: __PILL_CRIT_TEXT__; border: 1px solid rgba(239,68,68,.38); }

/* Mini stat cards */
.sb-stat {
    background: __SIDEBAR_CARD__;
    border: 1px solid __SIDEBAR_LINE__;
    border-radius: 7px;
    padding: 6px 8px;
    flex: 1;
}
.sb-stat-lbl {
    font-size: 0.5rem;
    color: __SIDEBAR_MUTED__;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.09em;
}
.sb-stat-val {
    font-size: 0.9rem;
    font-weight: 700;
    color: __SIDEBAR_TEXT__;
    margin-top: 1px;
    line-height: 1.2;
}
.sb-stat-unit { font-size: 0.5rem; color: __SIDEBAR_SUBTLE__; margin-top: 1px; }

/* Footer info card */
.sb-info {
    background: __SIDEBAR_INFO__;
    border-radius: 8px;
    padding: 10px 12px;
    border: 1px solid __SIDEBAR_LINE__;
    border-left: 3px solid #A61C2E;
}
            

</style>
""".replace("__SIDEBAR_BG__", SIDEBAR_BG)
    .replace("__SIDEBAR_CARD__", SIDEBAR_CARD)
    .replace("__SIDEBAR_INFO__", SIDEBAR_INFO)
    .replace("__SIDEBAR_TEXT__", SIDEBAR_TEXT)
    .replace("__SIDEBAR_MUTED__", SIDEBAR_MUTED)
    .replace("__SIDEBAR_SUBTLE__", SIDEBAR_SUBTLE)
    .replace("__SIDEBAR_LINE__", SIDEBAR_LINE)
    .replace("__SIDEBAR_HOVER__", SIDEBAR_HOVER)
    .replace("__SIDEBAR_ACTIVE__", SIDEBAR_ACTIVE)
    .replace("__SIDEBAR_ACCENT_TEXT__", SIDEBAR_ACCENT_TEXT)
    .replace("__PILL_SAFE_TEXT__", PILL_SAFE_TEXT)
    .replace("__PILL_WARN_TEXT__", PILL_WARN_TEXT)
    .replace("__PILL_CRIT_TEXT__", PILL_CRIT_TEXT),
    unsafe_allow_html=True,
)


def style_chart(fig, height, **layout_kwargs):
    """Keep Plotly chart text readable in Streamlit light and dark themes."""
    fig.update_layout(
        height=height,
        paper_bgcolor=CHART_BG,
        plot_bgcolor=CHART_PLOT_BG,
        font=dict(color=CHART_TEXT),
        hoverlabel=dict(
            bgcolor=CHART_HOVER_BG,
            bordercolor=CHART_HOVER_BORDER,
            font=dict(color=CHART_TEXT),
        ),
    )
    fig.update_xaxes(
        automargin=True,
        title_standoff=14,
        color=CHART_MUTED,
        title_font=dict(color=CHART_TEXT),
        tickfont=dict(color=CHART_MUTED),
        gridcolor=CHART_GRID,
        zerolinecolor=CHART_ZERO,
        linecolor=CHART_ZERO,
    )
    fig.update_yaxes(
        automargin=True,
        title_standoff=12,
        color=CHART_MUTED,
        title_font=dict(color=CHART_TEXT),
        tickfont=dict(color=CHART_MUTED),
        gridcolor=CHART_GRID,
        zerolinecolor=CHART_ZERO,
        linecolor=CHART_ZERO,
    )
    if layout_kwargs:
        fig.update_layout(**layout_kwargs)
    fig.update_layout(
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color=CHART_TEXT),
        )
    )
    fig.update_annotations(font=dict(color=CHART_TEXT))
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# DATA LOADING  (moved before sidebar so status widget can read it)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data
def load_csv(name):
    """Load a CSV from the outputs folder. Returns None if missing."""
    try:
        return pd.read_csv(f"{OUTPUTS_DIR}/{name}")
    except FileNotFoundError:
        return None


def load_all():
    data = {
        "cleaned":  load_csv("cleaned_donations.csv"),
        "forecast": load_csv("full_forecast.csv"),
        "next30":   load_csv("30day_forecast.csv"),
        "holiday":  load_csv("holiday_impact_matrix.csv"),
        "metrics":  load_csv("evaluation_metrics.csv"),
    }
    if data["cleaned"] is not None:
        data["cleaned"]["date"] = pd.to_datetime(data["cleaned"]["date"])
    if data["forecast"] is not None:
        data["forecast"]["ds"] = pd.to_datetime(data["forecast"]["ds"])
    if data["next30"] is not None:
        data["next30"]["ds"] = pd.to_datetime(data["next30"]["ds"])
    return data


def metric_value(metrics_df, name):
    """Safely pull a single metric value from the metrics table."""
    if metrics_df is None:
        return None
    row = metrics_df[metrics_df["Metric"] == name]
    if row.empty:
        return None
    return row["Value"].iloc[0]


data = load_all()

# Hard stop if the outputs folder is empty
if all(v is None for v in data.values()):
    st.error(
        "No data found. Please run **BloodFlow_GA2_FINAL.ipynb** first to "
        "generate the CSV files in the `outputs/` folder, then place that "
        "folder next to this app."
    )
    st.stop()


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────

# ── 1. Logo & Branding ──────────────────────────────────────────────────────
st.sidebar.markdown(f"""
<div style="display:flex;align-items:center;gap:9px;padding:0.05rem 0.25rem 0.25rem;">
  <svg width="28" height="34" viewBox="0 0 28 34" fill="none"
       xmlns="http://www.w3.org/2000/svg">
    <path d="M14 1C14 1 1.5 13.5 1.5 21C1.5 27.9 7.1 33.5 14 33.5
             C20.9 33.5 26.5 27.9 26.5 21C26.5 13.5 14 1 14 1Z"
          fill="{BLOOD_RED}"/>
    <path d="M14 11C14 11 8 18 8 22C8 25.3 10.7 28 14 28
             C17.3 28 20 25.3 20 22C20 18 14 11 14 11Z"
          fill="{DARK_RED}" opacity="0.5"/>
    <path d="M11.5 19.5C11.5 19.5 10.5 21.5 10.5 23"
          stroke="white" stroke-width="1.3" stroke-linecap="round" opacity="0.35"/>
  </svg>
  <div>
    <div style="font-size:1.12rem;font-weight:800;color:#E81A2C;
                letter-spacing:-0.01em;line-height:1.1;">BloodFlow</div>
    <div style="font-size:0.57rem;color:{SIDEBAR_MUTED};font-weight:800;
                letter-spacing:0.14em;text-transform:uppercase;">Malaysia</div>
  </div>
</div>
<div style="padding:0.1rem 0.3rem 0.2rem;">
  <div style="font-size:0.66rem;color:{SIDEBAR_MUTED};line-height:1.3;font-weight:500;">
    National Blood Supply Forecasting
  </div>
  <div style="margin-top:0.34rem;font-size:0.53rem;color:{SIDEBAR_SUBTLE};
              line-height:1.35;font-weight:700;letter-spacing:0.03em;">
    WQD7001 GA2 · Group 12 · Universiti Malaya
  </div>
</div>
""", unsafe_allow_html=True)
st.sidebar.divider()

# ── 2. Navigation ─────────────────────────────────────────────────────────────
with st.sidebar:
    page = option_menu(
        menu_title="Navigate",
        options=[
            "Overview / KPI Dashboard",
            "Historical Trend Explorer",
            "30-Day Forecast & Risk Calendar",
            "Holiday Impact Matrix",
            "Model Performance",
        ],
        icons=["speedometer2", "graph-up-arrow", "calendar-week", "brightness-high","activity",],
        menu_icon=None,
        default_index=0,
        styles={
            "container": {
                "padding": "none",
                "margin": "none",
                
                "border": "none",
            },
            "menu-title": {
                "font-size": "0.54rem",
                "font-weight": "800",
                "letter-spacing": "0.14em",
                "text-transform": "uppercase",
                "color": SIDEBAR_MUTED,
                "padding": "0.35rem 0.35rem 0.2rem",
                "display": "block",
            },
            "nav": {
                "gap": "6px",
                "display": "flex",
                "flex-direction": "column",
                "width": "100%",
            },
            "nav-link": {
                "display": "flex",
                "align-items": "center",
                "width": "100%",
                "padding": "0.38rem 0.62rem",
                "border-radius": "5px",
                "margin": "1px 0",
                "font-size": "0.9rem",
                "font-weight": "500",
                "line-height": "1.15",
                "color": SIDEBAR_TEXT,
                "background-color": "transparent",
                "border-left": "3px solid transparent",
                "transition": "background 0.15s, color 0.15s",
                "gap": "8px",
            },
            "nav-link-hover": {
                "background-color": SIDEBAR_HOVER,
                "color": SIDEBAR_ACCENT_TEXT,
            },
            "nav-link-selected": {
                "background-color": SIDEBAR_ACTIVE,
                "color": SIDEBAR_ACCENT_TEXT,
                "border-left": "3px solid #A61C2E",
                "font-weight": "600",
            },
            "icon": {
                "font-size": "0.95rem",
                "margin-right": "2px",
                "color": "inherit",  
            },
        }
    )
    

# ── 3. Critical Threshold Control ─────────────────────────────────────────────
st.sidebar.markdown(
    f"""
<div style="padding:0 0.15rem;">
  <div style="font-size:0.62rem;font-weight:800;color:{SIDEBAR_MUTED};
              text-transform:uppercase;letter-spacing:0.13em;margin-bottom:2px;">
    Critical Threshold
  </div>
</div>
""",
    unsafe_allow_html=True,
)
CRITICAL_THRESHOLD = st.sidebar.slider(
    "bags/day",
    min_value=1500,
    max_value=2500,
    value=CRITICAL_THRESHOLD,
    step=50,
    label_visibility="collapsed",
)
st.sidebar.markdown(
    f"""
<div style="padding:0 0.15rem;margin-top:-0.3rem;font-size:0.61rem;color:{SIDEBAR_MUTED};line-height:1.35;">
  MOH benchmark: <b style="color:{SIDEBAR_TEXT};">{CRITICAL_THRESHOLD:,}</b> bags/day
</div>
""",
    unsafe_allow_html=True,
)

st.sidebar.divider()

# ── 4. Supply Status Widget ──────────────────────────────────────────────────
_n30 = data["next30"]
if _n30 is not None:
    _risk_count = int((_n30["yhat"] < CRITICAL_THRESHOLD).sum())
    _avg_pred = _n30["yhat"].mean()

    if _risk_count >= 10:
        _pill_cls = "sb-pill-crit"
        _pill_txt = "HIGH RISK"
        _bar_clr  = "#EF4444"
    elif _risk_count > 0:
        _pill_cls = "sb-pill-warn"
        _pill_txt = "MODERATE"
        _bar_clr  = "#F59E0B"
    else:
        _pill_cls = "sb-pill-safe"
        _pill_txt = "HEALTHY"
        _bar_clr  = "#22C55E"

    _risk_pct   = max(2, min(100, int(_risk_count / 30 * 100)))
    _risk_val_c = PILL_CRIT_TEXT if _risk_count > 0 else PILL_SAFE_TEXT

    st.sidebar.markdown(f"""
<div style="padding:0 0.15rem;">
  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
    <div style="font-size:0.55rem;font-weight:800;color:{SIDEBAR_MUTED};
                text-transform:uppercase;letter-spacing:0.12em;">
      Supply Status
    </div>
    <span class="sb-pill {_pill_cls}">{_pill_txt}</span>
  </div>

  <div style="display:flex;gap:5px;">
    <div class="sb-stat">
      <div class="sb-stat-lbl">30-day avg</div>
      <div class="sb-stat-val">{_avg_pred:,.0f}</div>
      <div class="sb-stat-unit">bags / day</div>
    </div>
    <div class="sb-stat">
      <div class="sb-stat-lbl">Risk days</div>
      <div class="sb-stat-val" style="color:{_risk_val_c};">{_risk_count}/30</div>
      <div class="sb-stat-unit">below threshold</div>
    </div>
  </div>

  <div style="margin-top:7px;">
    <div style="display:flex;justify-content:space-between;
                font-size:0.52rem;color:{SIDEBAR_MUTED};margin-bottom:3px;">
      <span>Risk exposure</span>
      <span>{_risk_pct}%</span>
    </div>
    <div style="background:{SIDEBAR_CARD};border-radius:3px;height:4px;overflow:hidden;border:1px solid {SIDEBAR_LINE};">
      <div style="height:100%;border-radius:3px;width:{_risk_pct}%;
                  background:{_bar_clr};"></div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


# =============================================================================
# PAGE 1 — OVERVIEW / KPI DASHBOARD
# =============================================================================
if page == "Overview / KPI Dashboard":
    st.title("Overview Dashboard")
    st.caption("National blood supply at a glance, based on the latest 30-day forecast.")

    n30     = data["next30"]
    cleaned = data["cleaned"]

    if n30 is None:
        st.warning("30day_forecast.csv not found.")
    else:
        # ── Interactive horizon selector ──────────────────────────────
        horizon_cols = st.columns([3, 1])
        horizon = horizon_cols[1].selectbox(
            "Forecast horizon",
            ["Next 7 days", "Next 14 days", "Next 30 days"],
            index=2,
            label_visibility="collapsed",
        )
        horizon_days = {"Next 7 days": 7, "Next 14 days": 14, "Next 30 days": 30}[horizon]
        n30_view = n30.head(horizon_days).copy()
        horizon_cols[0].markdown(f"**Viewing: {horizon}** &nbsp; · &nbsp; "
                                 f"{n30_view['ds'].min().strftime('%d %b')} → "
                                 f"{n30_view['ds'].max().strftime('%d %b %Y')}")

        avg_pred   = n30_view["yhat"].mean()
        next_pred  = n30_view["yhat"].iloc[0]
        risk_count = (int(n30_view["risk"].sum()) if "risk" in n30_view
                      else int((n30_view["yhat"] < CRITICAL_THRESHOLD).sum()))
        min_pred   = n30_view["yhat"].min()
        min_date   = n30_view.loc[n30_view["yhat"].idxmin(), "ds"].strftime("%d %b")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Next predicted day", f"{next_pred:,.0f} bags",
                  delta=f"{next_pred - CRITICAL_THRESHOLD:,.0f} vs threshold",
                  delta_color="normal")
        c2.metric(f"{horizon} average", f"{avg_pred:,.0f} bags")
        c3.metric(f"Risk days ({horizon_days})", f"{risk_count} / {horizon_days}",
                  delta="below 2,000 bags", delta_color="inverse")
        c4.metric("Lowest predicted day", f"{min_pred:,.0f} bags",
                  delta=f"on {min_date}", delta_color="off")

        st.divider()

        if risk_count >= 15:
            st.error(
                f"⚠️ **High supply risk.** {risk_count} of the next 30 days are "
                f"predicted below the {CRITICAL_THRESHOLD:,}-bag threshold. "
                f"Launch mobile donation drives at least 14 days before the first risk day."
            )
        elif risk_count > 0:
            st.warning(
                f"🟡 **Moderate risk.** {risk_count} days predicted below threshold. "
                f"Monitor and prepare campaigns for the flagged dates."
            )
        else:
            st.success("🟢 **Supply healthy.** No days predicted below the threshold in the next 30 days.")

        st.subheader(f"Forecast preview — {horizon}")
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=n30_view["ds"], y=n30_view["yhat"], mode="lines+markers",
            line=dict(color=CHART_BLUE, width=2), name="Predicted donations",
            hovertemplate="<b>%{x|%a, %d %b %Y}</b><br>"
                          "Predicted: %{y:,.0f} bags<br>"
                          "<extra></extra>"))
        if {"yhat_lower", "yhat_upper"}.issubset(n30_view.columns):
            fig.add_trace(go.Scatter(
                x=list(n30_view["ds"]) + list(n30_view["ds"][::-1]),
                y=list(n30_view["yhat_upper"]) + list(n30_view["yhat_lower"][::-1]),
                fill="toself", fillcolor=CHART_INTERVAL_FILL,
                line=dict(color="rgba(0,0,0,0)"), name="80% interval",
                showlegend=True, hoverinfo="skip"))
        if "risk" in n30_view:
            rd = n30_view[n30_view["risk"] == 1]
            fig.add_trace(go.Scatter(
                x=rd["ds"], y=rd["yhat"], mode="markers",
                marker=dict(color=CHART_RED, size=12,
                            line=dict(color=CHART_MARKER_LINE, width=2)),
                name="Risk day",
                hovertemplate="<b>⚠️ %{x|%a, %d %b %Y}</b><br>"
                              "Risk day: %{y:,.0f} bags<br>"
                              "<extra></extra>"))
        fig.add_hline(y=CRITICAL_THRESHOLD, line_dash="dash", line_color=CHART_RED,
                      annotation_text=f"MOH threshold {CRITICAL_THRESHOLD:,}",
                      annotation_position="top left")
        style_chart(fig, height=410, margin=dict(t=30, b=72),
                    yaxis_title="Predicted donations (bags)",
                    xaxis_title="Date",
                    hovermode="x unified",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02))
        st.plotly_chart(fig, use_container_width=True, theme=None)

        if cleaned is not None:
            st.caption(
                f"Historical data covers {cleaned['date'].min().date()} to "
                f"{cleaned['date'].max().date()} ({len(cleaned):,} daily records)."
            )


# =============================================================================
# PAGE 2 — HISTORICAL TREND EXPLORER
# =============================================================================
elif page == "Historical Trend Explorer":
    st.title("Historical Trend Explorer")
    st.caption("Daily national donations, 2006 onward, with optional rolling average and MCO annotation.")

    cleaned = data["cleaned"]
    if cleaned is None:
        st.warning("cleaned_donations.csv not found.")
    else:
        # ── Quick view buttons ────────────────────────────────────────
        min_d = cleaned["date"].min().date()
        max_d = cleaned["date"].max().date()

        from datetime import timedelta as _td
        quick_views = {
            "📅 All time":     (min_d, max_d),
            "📅 Last 10 yrs":  (max(min_d, max_d.replace(year=max_d.year - 10)), max_d),
            "📅 Last 5 yrs":   (max(min_d, max_d.replace(year=max_d.year - 5)), max_d),
            "📅 Last year":    (max(min_d, max_d.replace(year=max_d.year - 1)), max_d),
            "📅 COVID era":    (pd.Timestamp("2020-03-18").date(),
                                pd.Timestamp("2021-12-31").date()),
        }

        if "hist_range" not in st.session_state:
            st.session_state["hist_range"] = (min_d, max_d)

        st.markdown("**Quick views**")
        qv_cols = st.columns(len(quick_views))
        for i, (label, rng) in enumerate(quick_views.items()):
            if qv_cols[i].button(label, use_container_width=True, key=f"qv_{i}"):
                st.session_state["hist_range"] = rng
                st.rerun()

        # ── Manual controls ───────────────────────────────────────────
        col1, col2, col3 = st.columns([2, 1, 1])
        date_range = col1.slider(
            "Custom date range",
            min_value=min_d, max_value=max_d,
            value=st.session_state["hist_range"],
        )
        st.session_state["hist_range"] = date_range
        show_roll = col2.toggle("365-day rolling average", value=True)
        show_mco  = col3.toggle("Shade MCO period", value=True)

        mask = ((cleaned["date"].dt.date >= date_range[0]) &
                (cleaned["date"].dt.date <= date_range[1]))
        d = cleaned.loc[mask].copy()

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=d["date"], y=d["donations"], mode="lines",
            line=dict(color=CHART_RED_SOFT, width=1),
            name="Daily donations",
            hovertemplate="<b>%{x|%a, %d %b %Y}</b><br>"
                          "Donations: %{y:,.0f} bags<extra></extra>"))
        if show_roll:
            d["roll"] = d["donations"].rolling(365, min_periods=30).mean()
            fig.add_trace(go.Scatter(
                x=d["date"], y=d["roll"], mode="lines",
                line=dict(color=CHART_BLUE, width=3),
                name="365-day rolling average",
                hovertemplate="<b>%{x|%b %Y}</b><br>"
                              "Rolling avg: %{y:,.0f} bags<extra></extra>"))
        if show_mco and "is_mco" in d.columns and d["is_mco"].any():
            mco = d[d["is_mco"] == 1]
            fig.add_vrect(x0=mco["date"].min(), x1=mco["date"].max(),
                          fillcolor=CHART_GOLD, opacity=0.18, line_width=0,
                          annotation_text="COVID-19 MCO",
                          annotation_position="top left")
        fig.add_hline(y=CRITICAL_THRESHOLD, line_dash="dash", line_color=CHART_GREY,
                      annotation_text=f"{CRITICAL_THRESHOLD:,} threshold")
        style_chart(fig, height=480,
                    yaxis_title="Donations (bags)", xaxis_title="Date",
                    hovermode="x unified",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02))
        st.plotly_chart(fig, use_container_width=True, theme=None)

        # ── Stats summary ─────────────────────────────────────────────
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Average", f"{d['donations'].mean():,.0f} bags/day")
        c2.metric("Minimum", f"{d['donations'].min():,.0f} bags",
                  delta=f"on {d.loc[d['donations'].idxmin(), 'date'].strftime('%d %b %Y')}",
                  delta_color="off")
        c3.metric("Maximum", f"{d['donations'].max():,.0f} bags",
                  delta=f"on {d.loc[d['donations'].idxmax(), 'date'].strftime('%d %b %Y')}",
                  delta_color="off")
        c4.metric("Records", f"{len(d):,} days")


# =============================================================================
# PAGE 3 — 30-DAY FORECAST & RISK CALENDAR
# =============================================================================
elif page == "30-Day Forecast & Risk Calendar":
    st.title("30-Day Forecast & Risk Calendar")
    st.caption("Day-by-day predicted donations with supply-risk flags for PDN planning.")

    n30 = data["next30"]
    if n30 is None:
        st.warning("30day_forecast.csv not found.")
    else:
        n30 = n30.copy()
        if "risk" not in n30:
            n30["risk"] = (n30["yhat"] < CRITICAL_THRESHOLD).astype(int)

        # ── Interactive filters ───────────────────────────────────────
        fcol1, fcol2, fcol3 = st.columns(3)
        status_filter = fcol1.selectbox(
            "Filter by status",
            ["All days", "🔴 Risk days only", "🟢 Safe days only"],
        )
        day_filter = fcol2.multiselect(
            "Filter by day of week",
            ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            default=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        )
        sort_order = fcol3.selectbox(
            "Sort by",
            ["Date (earliest first)", "Date (latest first)",
             "Predicted (lowest first)", "Predicted (highest first)"],
        )

        # Build display data
        n30["Date"]             = n30["ds"].dt.strftime("%Y-%m-%d (%a)")
        n30["Day"]              = n30["ds"].dt.strftime("%a")
        n30["Predicted (bags)"] = n30["yhat"].round(0).astype(int)
        n30["Gap vs threshold"] = (n30["yhat"] - CRITICAL_THRESHOLD).round(0).astype(int)
        n30["Status"]           = n30["risk"].map({1: "🔴 Risk", 0: "🟢 Safe"})
        n30["Recommended campaign"] = (n30["ds"] - pd.Timedelta(days=14)).dt.strftime("%d %b %Y")
        n30.loc[n30["risk"] == 0, "Recommended campaign"] = "—"

        # Apply filters
        filtered = n30.copy()
        if status_filter == "🔴 Risk days only":
            filtered = filtered[filtered["risk"] == 1]
        elif status_filter == "🟢 Safe days only":
            filtered = filtered[filtered["risk"] == 0]
        filtered = filtered[filtered["Day"].isin(day_filter)]

        # Apply sort
        if sort_order == "Date (latest first)":
            filtered = filtered.sort_values("ds", ascending=False)
        elif sort_order == "Predicted (lowest first)":
            filtered = filtered.sort_values("yhat", ascending=True)
        elif sort_order == "Predicted (highest first)":
            filtered = filtered.sort_values("yhat", ascending=False)

        # ── Summary metrics ───────────────────────────────────────────
        total_risk = int(n30["risk"].sum())
        filtered_risk = int(filtered["risk"].sum())
        worst_day = n30.loc[n30["yhat"].idxmin()]

        m1, m2, m3 = st.columns(3)
        m1.metric("Risk days (total)", f"{total_risk} / {len(n30)}")
        m2.metric("Days shown", f"{len(filtered)} / {len(n30)}")
        m3.metric("Worst predicted day",
                  f"{worst_day['Predicted (bags)']:,} bags",
                  delta=f"on {worst_day['ds'].strftime('%d %b')}",
                  delta_color="off")

        st.divider()

        # ── Table ─────────────────────────────────────────────────────
        show = filtered[["Date", "Predicted (bags)", "Gap vs threshold",
                         "Status", "Recommended campaign"]]

        def highlight(row):
            s = ("background-color:#FCE8EA; color:#7B1220"
                 if "Risk" in row["Status"]
                 else "background-color:#E8F6EE; color:#0F5132")
            return [s] * len(row)

        st.dataframe(show.style.apply(highlight, axis=1),
                     use_container_width=True, height=480, hide_index=True)

        # ── Download (export filtered view) ───────────────────────────
        csv = filtered[["ds", "yhat", "risk", "Recommended campaign"]].to_csv(index=False)
        st.download_button(f"⬇️ Download filtered view ({len(filtered)} rows)",
                           data=csv,
                           file_name="bloodflow_30day_forecast.csv",
                           mime="text/csv")

        if filtered_risk > 0:
            st.error(
                f"⚠️ **Action required for {filtered_risk} risk day(s) in current view.** "
                f"Launch mobile donation drives 14 days before each red day. "
                f"Weekend drives recover the most supply — Sunday is the strongest donation day."
            )
        else:
            st.success("🟢 No risk days in the current filtered view.")


# =============================================================================
# PAGE 4 — HOLIDAY IMPACT MATRIX
# =============================================================================
elif page == "Holiday Impact Matrix":
    st.title("Holiday Impact Matrix")
    st.caption("How major Malaysian festivals affect daily donations (Objective 1 result).")

    h = data["holiday"]
    if h is None:
        st.warning("holiday_impact_matrix.csv not found.")
    else:
        impact_col = next((c for c in h.columns if "Impact" in c), None)
        name_col   = next((c for c in h.columns
                           if "Holiday" in c or "holiday" in c), h.columns[0])

        # ── Sort selector ─────────────────────────────────────────────
        sort_cols = st.columns([1, 2])
        sort_choice = sort_cols[0].radio(
            "Sort holidays by",
            ["Most severe drop", "Least severe drop", "Alphabetical"],
            horizontal=False,
        )

        if impact_col:
            if sort_choice == "Most severe drop":
                hs = h.sort_values(impact_col, ascending=True)
            elif sort_choice == "Least severe drop":
                hs = h.sort_values(impact_col, ascending=False)
            else:
                hs = h.sort_values(name_col)

            # Build hover text with rich details
            hover_texts = []
            for _, r in hs.iterrows():
                txt = f"<b>{r[name_col]}</b><br>"
                txt += f"Impact: <b>{r[impact_col]:+.2f}%</b><br>"
                for c in hs.columns:
                    if c != name_col and c != impact_col:
                        val = r[c]
                        if isinstance(val, (int, float)):
                            txt += f"{c}: {val:,.0f}<br>"
                        else:
                            txt += f"{c}: {val}<br>"
                hover_texts.append(txt)

            fig = px.bar(hs, x=impact_col, y=name_col, orientation="h",
                         color=impact_col,
                         color_continuous_scale=CHART_HOLIDAY_SCALE)
            fig.update_traces(hovertemplate=hover_texts, name="")
            style_chart(fig, height=420,
                        coloraxis_showscale=False,
                        xaxis_title="Impact % (vs 7-day pre-holiday average)",
                        yaxis_title="")
            for _, r in hs.iterrows():
                fig.add_annotation(
                    x=r[impact_col], y=r[name_col],
                    text=f"{r[impact_col]:+.1f}%", showarrow=False,
                    xshift=-28 if r[impact_col] < 0 else 28,
                    font=dict(size=12, color=CHART_TEXT))
            sort_cols[1].plotly_chart(fig, use_container_width=True, theme=None)

        # ── KPI cards for the worst holidays ──────────────────────────
        st.divider()
        st.markdown("**Top 3 most disruptive festivals**")
        if impact_col:
            top3 = h.sort_values(impact_col).head(3)
            cols = st.columns(3)
            for i, (_, r) in enumerate(top3.iterrows()):
                with cols[i]:
                    st.metric(
                        r[name_col],
                        f"{r[impact_col]:+.1f}%",
                        delta="below baseline",
                        delta_color="inverse"
                    )

        # ── Detail table (sortable) ───────────────────────────────────
        st.subheader("Detail table")
        st.caption("Click any column header to sort.")
        st.dataframe(h, use_container_width=True, hide_index=True)

        st.info(
            "Hari Raya Aidilfitri and Aidiladha cut donations by roughly three-quarters, "
            "and Chinese New Year by about 43%, with the effect beginning up to a week "
            "before the festival. These predictable dips are what the forecasting system "
            "is designed to anticipate."
        )


# =============================================================================
# PAGE 5 — MODEL PERFORMANCE
# =============================================================================
elif page == "Model Performance":
    st.title("Model Performance")
    st.caption("Out-of-sample accuracy of the Prophet model on the 2025 holdout.")

    m = data["metrics"]
    if m is None:
        st.warning("evaluation_metrics.csv not found.")
    else:
        mae      = metric_value(m, "MAE")
        rmse     = metric_value(m, "RMSE")
        nmae     = metric_value(m, "Naive_MAE")
        nrmse    = metric_value(m, "Naive_RMSE")
        mape_adj = metric_value(m, "MAPE_adjusted")
        smape    = metric_value(m, "sMAPE")

        c1, c2, c3 = st.columns(3)
        if mae is not None and nmae:
            c1.metric("MAE (bags/day)", f"{mae:,.2f}",
                      delta=f"{(nmae-mae)/nmae*100:.0f}% better than naive",
                      delta_color="normal")
        if rmse is not None and nrmse:
            c2.metric("RMSE (bags/day)", f"{rmse:,.2f}",
                      delta=f"{(nrmse-rmse)/nrmse*100:.0f}% better than naive",
                      delta_color="normal")
        if mape_adj is not None:
            c3.metric("MAPE (adjusted)", f"{mape_adj:,.1f}%")

        with st.expander("ℹ️ Note on MAPE"):
            st.write(
                "Raw MAPE is undefined (infinite) because the holdout includes a "
                "zero-donation public holiday (31 March 2025), and MAPE divides by the "
                "actual value. Excluding that day gives an adjusted MAPE of "
                f"**{mape_adj:.1f}%**"
                + (f", and sMAPE gives **{smape:.1f}%**." if smape is not None else ".")
                + " The team relies on MAE and RMSE as the primary metrics, both well "
                "defined and expressed in bags per day."
            )

        st.divider()
        st.subheader("Actual vs predicted (2025 holdout)")
        cleaned  = data["cleaned"]
        forecast = data["forecast"]
        if cleaned is not None and forecast is not None:
            merged  = cleaned[["date", "donations"]].merge(
                forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]],
                left_on="date", right_on="ds", how="inner")
            holdout = merged[merged["date"] >= "2025-01-01"]
            if not holdout.empty:
                # ── Interactive sub-period selector ───────────────────
                min_h = holdout["date"].min().date()
                max_h = holdout["date"].max().date()

                st.markdown("**Evaluate model on a custom date range**")
                sub_range = st.slider(
                    "Evaluation period",
                    min_value=min_h, max_value=max_h,
                    value=(min_h, max_h),
                    key="model_eval_range",
                    label_visibility="collapsed",
                )

                sub_mask = ((holdout["date"].dt.date >= sub_range[0]) &
                            (holdout["date"].dt.date <= sub_range[1]))
                sub = holdout.loc[sub_mask].copy()

                # Recompute metrics on the sub-period
                if len(sub) > 0:
                    sub_mae  = (sub["donations"] - sub["yhat"]).abs().mean()
                    sub_rmse = ((sub["donations"] - sub["yhat"]) ** 2).mean() ** 0.5
                    sub_nonzero = sub[sub["donations"] > 0]
                    sub_mape = (((sub_nonzero["donations"] - sub_nonzero["yhat"])
                                / sub_nonzero["donations"]).abs().mean() * 100
                                if len(sub_nonzero) > 0 else 0)

                    sc1, sc2, sc3, sc4 = st.columns(4)
                    sc1.metric("Period MAE", f"{sub_mae:,.2f}",
                               delta=f"{sub_mae - mae:+,.1f} vs overall",
                               delta_color="inverse")
                    sc2.metric("Period RMSE", f"{sub_rmse:,.2f}",
                               delta=f"{sub_rmse - rmse:+,.1f} vs overall",
                               delta_color="inverse")
                    sc3.metric("Period MAPE", f"{sub_mape:,.1f}%")
                    sc4.metric("Days in period", f"{len(sub):,}")

                # Plot the sub-period
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=sub["date"], y=sub["donations"],
                    mode="lines", line=dict(color=CHART_RED, width=1.3),
                    name="Actual",
                    hovertemplate="<b>%{x|%a, %d %b %Y}</b><br>"
                                  "Actual: %{y:,.0f}<extra></extra>"))
                fig.add_trace(go.Scatter(
                    x=sub["date"], y=sub["yhat"],
                    mode="lines", line=dict(color=CHART_BLUE, width=1.3),
                    name="Predicted",
                    hovertemplate="<b>%{x|%a, %d %b %Y}</b><br>"
                                  "Predicted: %{y:,.0f}<extra></extra>"))
                fig.add_trace(go.Scatter(
                    x=list(sub["date"]) + list(sub["date"][::-1]),
                    y=list(sub["yhat_upper"]) + list(sub["yhat_lower"][::-1]),
                    fill="toself", fillcolor=CHART_INTERVAL_FILL,
                    line=dict(color="rgba(0,0,0,0)"), name="80% interval",
                    hoverinfo="skip"))
                style_chart(fig, height=450,
                            yaxis_title="Donations (bags)",
                            xaxis_title="Date",
                            hovermode="x unified",
                            legend=dict(orientation="h",
                                        yanchor="bottom", y=1.02))
                st.plotly_chart(fig, use_container_width=True, theme=None)
            else:
                st.info("No overlapping holdout dates found between actuals and forecast.")
        else:
            st.info("Need both cleaned_donations.csv and full_forecast.csv to draw this chart.")

        st.subheader("All metrics")
        metrics_display = m.copy()

        def format_metric_value(row):
            metric = row["Metric"]
            value = pd.to_numeric(row["Value"], errors="coerce")
            if metric == "MAPE_raw" or not np.isfinite(value):
                return "N/A"
            if metric in {"MAPE_adjusted", "sMAPE"}:
                return f"{value:,.2f}%"
            return f"{value:,.2f}"

        metrics_display["Value"] = metrics_display.apply(format_metric_value, axis=1)
        st.dataframe(metrics_display, use_container_width=True, hide_index=True)
