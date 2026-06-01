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

# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL CSS  ── sidebar + main content
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ═══════════════════ SIDEBAR ═══════════════════ */

section[data-testid="stSidebar"] {
    background: #0D1422 !important;
}
section[data-testid="stSidebar"] > div:first-child {
    padding: 1.25rem 0.75rem 1rem;
}

/* Nav: section label ("NAVIGATE") */
section[data-testid="stSidebar"] .stRadio > div > label {
    font-size: 0.6rem !important;
    font-weight: 800 !important;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #253550 !important;
    padding: 0.9rem 0.4rem 0.35rem !important;
    display: block;
}

/* Nav: hide radio circles */
section[data-testid="stSidebar"] [role="radio"] {
    display: none !important;
}

/* Nav: each option row */
section[data-testid="stSidebar"] .stRadio label {
    width: 100%;
    display: flex !important;
    align-items: center;
    padding: 0.6rem 0.85rem !important;
    border-radius: 8px;
    margin: 2px 0;
    color: #5A7090 !important;
    font-size: 0.86rem;
    font-weight: 500;
    border-left: 3px solid transparent;
    transition: background 0.15s, color 0.15s;
    cursor: pointer;
    line-height: 1.3;
}
section[data-testid="stSidebar"] .stRadio label:hover {
    background: rgba(255,255,255,0.04) !important;
    color: #8AAAC8 !important;
}

/* Nav: active page — label wrapping the checked radio */
section[data-testid="stSidebar"] .stRadio label:has([aria-checked="true"]) {
    background: rgba(166,28,46,0.16) !important;
    color: #FF8090 !important;
    border-left: 3px solid #A61C2E !important;
    font-weight: 600;
}

/* Dividers in sidebar */
section[data-testid="stSidebar"] hr {
    border-color: #1A2540 !important;
    margin: 0.6rem 0 !important;
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
    padding: 5px 11px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.03em;
}
.sb-pill-safe { background: #071A0E; color: #34D399; border: 1px solid rgba(6,78,59,.33); }
.sb-pill-warn { background: #1C1300; color: #FBBF24; border: 1px solid rgba(113,63,8,.33); }
.sb-pill-crit { background: #1C0307; color: #F87171; border: 1px solid rgba(127,29,29,.33); }

/* Mini stat cards */
.sb-stat {
    background: #111B2E;
    border-radius: 7px;
    padding: 8px 10px;
    flex: 1;
}
.sb-stat-lbl {
    font-size: 0.56rem;
    color: #2A3E58;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.09em;
}
.sb-stat-val {
    font-size: 1.02rem;
    font-weight: 700;
    color: #9DBAD5;
    margin-top: 1px;
    line-height: 1.2;
}
.sb-stat-unit { font-size: 0.55rem; color: #243348; margin-top: 1px; }

/* Footer info card */
.sb-info {
    background: #090F1C;
    border-radius: 8px;
    padding: 10px 12px;
    border-left: 3px solid #172A45;
}
</style>
""", unsafe_allow_html=True)


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
<div style="display:flex;align-items:center;gap:10px;padding:0.2rem 0.3rem 0.4rem;">
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
    <div style="font-size:1.28rem;font-weight:800;color:#E81A2C;
                letter-spacing:-0.01em;line-height:1.1;">BloodFlow</div>
    <div style="font-size:0.57rem;color:#233248;font-weight:800;
                letter-spacing:0.14em;text-transform:uppercase;">Malaysia</div>
  </div>
</div>
<div style="padding:0.1rem 0.3rem 0.2rem;">
  <div style="font-size:0.72rem;color:#2E4565;line-height:1.45;font-weight:500;">
    National Blood Supply Forecasting
  </div>
</div>
""", unsafe_allow_html=True)

st.sidebar.divider()

# ── 2. Supply Status Widget ──────────────────────────────────────────────────
_n30 = data["next30"]
if _n30 is not None:
    _risk_count = (
        int(_n30["risk"].sum()) if "risk" in _n30.columns
        else int((_n30["yhat"] < CRITICAL_THRESHOLD).sum())
    )
    _avg_pred = _n30["yhat"].mean()

    if _risk_count >= 10:
        _pill_cls = "sb-pill-crit"
        _pill_txt = "🔴 HIGH RISK"
        _bar_clr  = "#EF4444"
    elif _risk_count > 0:
        _pill_cls = "sb-pill-warn"
        _pill_txt = "🟡 MODERATE"
        _bar_clr  = "#F59E0B"
    else:
        _pill_cls = "sb-pill-safe"
        _pill_txt = "🟢 HEALTHY"
        _bar_clr  = "#22C55E"

    _risk_pct   = max(2, min(100, int(_risk_count / 30 * 100)))
    _risk_val_c = "#F87171" if _risk_count > 0 else "#34D399"

    st.sidebar.markdown(f"""
<div style="padding:0 0.15rem;">
  <div style="font-size:0.58rem;font-weight:800;color:#233248;
              text-transform:uppercase;letter-spacing:0.13em;margin-bottom:7px;">
    Supply Status
  </div>
  <span class="sb-pill {_pill_cls}">{_pill_txt}</span>

  <div style="display:flex;gap:5px;margin-top:9px;">
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

  <div style="margin-top:9px;">
    <div style="display:flex;justify-content:space-between;
                font-size:0.57rem;color:#233248;margin-bottom:3px;">
      <span>Risk exposure</span>
      <span>{_risk_pct}%</span>
    </div>
    <div style="background:#090F1C;border-radius:3px;height:4px;overflow:hidden;">
      <div style="height:100%;border-radius:3px;width:{_risk_pct}%;
                  background:{_bar_clr};"></div>
    </div>
    <div style="display:flex;justify-content:space-between;
                font-size:0.54rem;color:#182233;margin-top:2px;">
      <span>Safe ←</span><span>→ Critical</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    st.sidebar.divider()

# ── 3. Navigation ─────────────────────────────────────────────────────────────
page = st.sidebar.radio(
    "Navigate",
    [
        "📊 Overview / KPI Dashboard",
        "📈 Historical Trend Explorer",
        "🗓️ 30-Day Forecast & Risk Calendar",
        "🎉 Holiday Impact Matrix",
        "🎯 Model Performance",
    ],
)

st.sidebar.divider()

# ── 4. Sidebar Footer ─────────────────────────────────────────────────────────
_last_date = (
    data["cleaned"]["date"].max().strftime("%d %b %Y")
    if data["cleaned"] is not None else "N/A"
)

st.sidebar.markdown(f"""
<div style="padding:0 0.15rem;">
  <div class="sb-info">
    <div style="font-size:0.62rem;font-weight:700;color:#2A4060;margin-bottom:4px;">
      ℹ️ Read-only Mode
    </div>
    <div style="font-size:0.61rem;color:#1E3250;line-height:1.55;">
      Reads CSVs exported by the notebook · No live modelling
    </div>
    <div style="margin-top:7px;padding-top:6px;border-top:1px solid #111E32;">
      <div style="margin-bottom:3px;">
        <span style="font-size:0.6rem;color:#1E3250;">Data through: </span>
        <span style="font-size:0.6rem;font-weight:700;color:#2A5080;">{_last_date}</span>
      </div>
      <div>
        <span style="font-size:0.62rem;font-weight:700;color:#8B1A28;">
          ⚠ Threshold: {CRITICAL_THRESHOLD:,} bags/day
        </span>
      </div>
    </div>
  </div>
  <div style="margin-top:8px;font-size:0.57rem;color:#182233;text-align:center;
              letter-spacing:0.03em;">
    WQD7001 GA2 · Group 12 · Universiti Malaya
  </div>
</div>
""", unsafe_allow_html=True)


# =============================================================================
# PAGE 1 — OVERVIEW / KPI DASHBOARD
# =============================================================================
if page.startswith("📊"):
    st.title("📊 Overview Dashboard")
    st.caption("National blood supply at a glance, based on the latest 30-day forecast.")

    n30 = data["next30"]
    cleaned = data["cleaned"]

    if n30 is None:
        st.warning("30day_forecast.csv not found.")
    else:
        # KPI cards
        avg_pred   = n30["yhat"].mean()
        next_pred  = n30["yhat"].iloc[0]
        risk_count = int(n30["risk"].sum()) if "risk" in n30 else int((n30["yhat"] < CRITICAL_THRESHOLD).sum())
        min_pred   = n30["yhat"].min()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Next predicted day", f"{next_pred:,.0f} bags",
                  delta=f"{next_pred - CRITICAL_THRESHOLD:,.0f} vs threshold",
                  delta_color="normal")
        c2.metric("30-day average", f"{avg_pred:,.0f} bags")
        c3.metric("Risk days (next 30)", f"{risk_count} / 30",
                  delta="below 2,000 bags", delta_color="inverse")
        c4.metric("Lowest predicted day", f"{min_pred:,.0f} bags")

        st.divider()

        # Status banner
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

        # Mini forecast preview
        st.subheader("30-day forecast preview")
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=n30["ds"], y=n30["yhat"], mode="lines+markers",
            line=dict(color=NAVY, width=2), name="Predicted donations"))
        if {"yhat_lower", "yhat_upper"}.issubset(n30.columns):
            fig.add_trace(go.Scatter(
                x=list(n30["ds"]) + list(n30["ds"][::-1]),
                y=list(n30["yhat_upper"]) + list(n30["yhat_lower"][::-1]),
                fill="toself", fillcolor="rgba(26,58,92,0.12)",
                line=dict(color="rgba(0,0,0,0)"), name="80% interval", showlegend=True))
        # risk points
        if "risk" in n30:
            rd = n30[n30["risk"] == 1]
            fig.add_trace(go.Scatter(
                x=rd["ds"], y=rd["yhat"], mode="markers",
                marker=dict(color=BLOOD_RED, size=10, line=dict(color="white", width=1)),
                name="Risk day"))
        fig.add_hline(y=CRITICAL_THRESHOLD, line_dash="dash", line_color=BLOOD_RED,
                      annotation_text=f"MOH threshold {CRITICAL_THRESHOLD:,}", annotation_position="top left")
        fig.update_layout(height=380, margin=dict(t=30, b=10), plot_bgcolor="white",
                          yaxis_title="Predicted donations (bags)", xaxis_title="Date",
                          legend=dict(orientation="h", yanchor="bottom", y=1.02))
        st.plotly_chart(fig, use_container_width=True)

        if cleaned is not None:
            st.caption(
                f"Historical data covers {cleaned['date'].min().date()} to "
                f"{cleaned['date'].max().date()} ({len(cleaned):,} daily records)."
            )


# =============================================================================
# PAGE 2 — HISTORICAL TREND EXPLORER
# =============================================================================
elif page.startswith("📈"):
    st.title("📈 Historical Trend Explorer")
    st.caption("Daily national donations, 2006 onward, with optional rolling average and MCO annotation.")

    cleaned = data["cleaned"]
    if cleaned is None:
        st.warning("cleaned_donations.csv not found.")
    else:
        # Controls
        col1, col2, col3 = st.columns([2, 1, 1])
        min_d = cleaned["date"].min().date()
        max_d = cleaned["date"].max().date()
        date_range = col1.slider("Date range", min_value=min_d, max_value=max_d,
                                 value=(min_d, max_d))
        show_roll = col2.toggle("365-day rolling average", value=True)
        show_mco  = col3.toggle("Shade MCO period", value=True)

        mask = (cleaned["date"].dt.date >= date_range[0]) & (cleaned["date"].dt.date <= date_range[1])
        d = cleaned.loc[mask].copy()

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=d["date"], y=d["donations"], mode="lines",
                                 line=dict(color="rgba(166,28,46,0.35)", width=1),
                                 name="Daily donations"))
        if show_roll:
            d["roll"] = d["donations"].rolling(365, min_periods=30).mean()
            fig.add_trace(go.Scatter(x=d["date"], y=d["roll"], mode="lines",
                                     line=dict(color=NAVY, width=3),
                                     name="365-day rolling average"))
        if show_mco and "is_mco" in d.columns and d["is_mco"].any():
            mco = d[d["is_mco"] == 1]
            fig.add_vrect(x0=mco["date"].min(), x1=mco["date"].max(),
                          fillcolor=GOLD, opacity=0.18, line_width=0,
                          annotation_text="COVID-19 MCO", annotation_position="top left")
        fig.add_hline(y=CRITICAL_THRESHOLD, line_dash="dash", line_color=GREY,
                      annotation_text=f"{CRITICAL_THRESHOLD:,} threshold")
        fig.update_layout(height=480, plot_bgcolor="white",
                          yaxis_title="Donations (bags)", xaxis_title="Date",
                          legend=dict(orientation="h", yanchor="bottom", y=1.02))
        st.plotly_chart(fig, use_container_width=True)

        # quick stats for the selected range
        c1, c2, c3 = st.columns(3)
        c1.metric("Average", f"{d['donations'].mean():,.0f} bags/day")
        c2.metric("Minimum", f"{d['donations'].min():,.0f} bags")
        c3.metric("Maximum", f"{d['donations'].max():,.0f} bags")


# =============================================================================
# PAGE 3 — 30-DAY FORECAST & RISK CALENDAR
# =============================================================================
elif page.startswith("🗓️"):
    st.title("🗓️ 30-Day Forecast & Risk Calendar")
    st.caption("Day-by-day predicted donations with supply-risk flags for PDN planning.")

    n30 = data["next30"]
    if n30 is None:
        st.warning("30day_forecast.csv not found.")
    else:
        n30 = n30.copy()
        n30["Date"] = n30["ds"].dt.strftime("%Y-%m-%d (%a)")
        n30["Predicted (bags)"] = n30["yhat"].round(0).astype(int)
        if "risk" not in n30:
            n30["risk"] = (n30["yhat"] < CRITICAL_THRESHOLD).astype(int)
        n30["Status"] = n30["risk"].map({1: "🔴 Risk", 0: "🟢 Safe"})

        risk_count = int(n30["risk"].sum())
        st.metric("Days below threshold", f"{risk_count} of {len(n30)}")

        # Colour-coded table
        show = n30[["Date", "Predicted (bags)", "Status"]]

        def highlight(row):
            if "Risk" in row["Status"]:
                colour = "background-color: #FCE8EA; color: #C5221F; font-weight: bold;"
            else:
                colour = "background-color: #E8F6EE; color: #137333; font-weight: bold;"
            return [colour] * len(row)

        st.dataframe(show.style.apply(highlight, axis=1), use_container_width=True,
                     height=560, hide_index=True)
        

        # Download button
        csv = n30[["ds", "yhat", "yhat_lower", "yhat_upper", "risk"]].to_csv(index=False) \
            if {"yhat_lower", "yhat_upper"}.issubset(n30.columns) \
            else n30[["ds", "yhat", "risk"]].to_csv(index=False)
        st.download_button("⬇️ Download forecast (CSV)", data=csv,
                           file_name="bloodflow_30day_forecast.csv", mime="text/csv")

        st.info(
            "**Recommended action:** launch mobile donation drives at least 14 days "
            "before the first red (risk) day in any cluster. Weekend drives recover "
            "the most supply, since Sunday is the strongest donation day."
        )


# =============================================================================
# PAGE 4 — HOLIDAY IMPACT MATRIX
# =============================================================================
elif page.startswith("🎉"):
    st.title("🎉 Holiday Impact Matrix")
    st.caption("How major Malaysian festivals affect daily donations (Objective 1 result).")

    h = data["holiday"]
    if h is None:
        st.warning("holiday_impact_matrix.csv not found.")
    else:
        # Detect the impact column (name may vary slightly)
        impact_col = next((c for c in h.columns if "Impact" in c), None)
        name_col   = next((c for c in h.columns if "Holiday" in c or "holiday" in c), h.columns[0])

        if impact_col:
            hs = h.sort_values(impact_col)
            fig = px.bar(hs, x=impact_col, y=name_col, orientation="h",
                         color=impact_col, color_continuous_scale=["#7B1220", "#A61C2E", "#E8A838"])
            fig.update_layout(height=420, plot_bgcolor="white", coloraxis_showscale=False,
                              xaxis_title="Impact % (vs 7-day pre-holiday average)",
                              yaxis_title="")
            for _, r in hs.iterrows():
                fig.add_annotation(x=r[impact_col], y=r[name_col],
                                   text=f"{r[impact_col]:+.1f}%", showarrow=False,
                                   xshift=-28 if r[impact_col] < 0 else 28,
                                   font=dict(size=12, color=NAVY))
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("Detail table")
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
elif page.startswith("🎯"):
    st.title("🎯 Model Performance")
    st.caption("Out-of-sample accuracy of the Prophet model on the 2025 holdout.")

    m = data["metrics"]
    if m is None:
        st.warning("evaluation_metrics.csv not found.")
    else:
        mae   = metric_value(m, "MAE")
        rmse  = metric_value(m, "RMSE")
        nmae  = metric_value(m, "Naive_MAE")
        nrmse = metric_value(m, "Naive_RMSE")
        mape_adj = metric_value(m, "MAPE_adjusted")
        smape    = metric_value(m, "sMAPE")

        c1, c2, c3 = st.columns(3)
        if mae is not None and nmae:
            c1.metric("MAE (bags/day)", f"{mae:,.2f}",
                      delta=f"{(nmae-mae)/nmae*100:.0f}% better than naive", delta_color="normal")
        if rmse is not None and nrmse:
            c2.metric("RMSE (bags/day)", f"{rmse:,.2f}",
                      delta=f"{(nrmse-rmse)/nrmse*100:.0f}% better than naive", delta_color="normal")
        if mape_adj is not None:
            c3.metric("MAPE (adjusted)", f"{mape_adj:,.1f}%")

        # MAPE note
        with st.expander("ℹ️ Note on MAPE"):
            st.write(
                "Raw MAPE is undefined (infinite) because the holdout includes a "
                "zero-donation public holiday (31 March 2025), and MAPE divides by the "
                "actual value. Excluding that day gives an adjusted MAPE of "
                f"**{mape_adj:.1f}%**" + (f", and sMAPE gives **{smape:.1f}%**." if smape is not None else ".") +
                " The team relies on MAE and RMSE as the primary metrics, both well defined "
                "and expressed in bags per day."
            )

        st.divider()

        # Actual vs predicted on the holdout
        st.subheader("Actual vs predicted (2025 holdout)")
        cleaned  = data["cleaned"]
        forecast = data["forecast"]
        if cleaned is not None and forecast is not None:
            merged = cleaned[["date", "donations"]].merge(
                forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]],
                left_on="date", right_on="ds", how="inner")
            holdout = merged[merged["date"] >= "2025-01-01"]
            if not holdout.empty:
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=holdout["date"], y=holdout["donations"],
                                         mode="lines", line=dict(color=BLOOD_RED, width=1.3),
                                         name="Actual"))
                fig.add_trace(go.Scatter(x=holdout["date"], y=holdout["yhat"],
                                         mode="lines", line=dict(color=NAVY, width=1.3),
                                         name="Predicted"))
                fig.add_trace(go.Scatter(
                    x=list(holdout["date"]) + list(holdout["date"][::-1]),
                    y=list(holdout["yhat_upper"]) + list(holdout["yhat_lower"][::-1]),
                    fill="toself", fillcolor="rgba(26,58,92,0.12)",
                    line=dict(color="rgba(0,0,0,0)"), name="80% interval"))
                fig.update_layout(height=450, plot_bgcolor="white",
                                  yaxis_title="Donations (bags)", xaxis_title="Date",
                                  legend=dict(orientation="h", yanchor="bottom", y=1.02))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No overlapping holdout dates found between actuals and forecast.")
        else:
            st.info("Need both cleaned_donations.csv and full_forecast.csv to draw this chart.")


        #table
        if m is not None:
            m_display = m.copy()
            m_display['Value'] = m_display['Value'].astype(object)
            m_display.loc[m_display['Metric'] == 'MAPE_raw', 'Value'] = "N/A" #mape_RAW
            
            if mape_adj is not None:
                m_display.loc[m_display['Metric'] == 'MAPE_adjusted', 'Value'] = f"{mape_adj:.2f}%"
            if smape is not None:
                m_display.loc[m_display['Metric'] == 'sMAPE', 'Value'] = f"{smape:.2f}%"
                
            for metric_name in ['MAE', 'RMSE', 'Naive_MAE', 'Naive_RMSE']:
                val = metric_value(m, metric_name)
                if val is not None:
                    m_display.loc[m_display['Metric'] == metric_name, 'Value'] = f"{val:,.2f}"

            st.dataframe(m_display, use_container_width=True, hide_index=True)
        else:
            st.dataframe(m, use_container_width=True, hide_index=True)
