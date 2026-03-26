import streamlit as st
import pandas as pd
import numpy as np
import sys
import os

# Ensure the app directory is always on the path, both locally and on Streamlit Cloud
APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from data.universe import load_universe, get_sectors, get_ticker_metadata
from data.fetcher import fetch_metrics
from logic.multiples import build_comps_table, compute_stats
from logic.formatting import apply_display_formats
from components.table import (
    COLUMN_GROUPS,
    render_group_headers,
    render_stats_row,
    style_table,
)
from components.charts import (
    render_ev_ebitda_chart,
    render_pe_chart,
    render_growth_margin_scatter,
    render_market_cap_treemap,
)

# ─── Page Config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Trading Comps",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #ffffff;
    border-right: 1px solid #e2e8f0;
}
[data-testid="stSidebar"] .stRadio > label {
    font-size: 13px;
    font-weight: 500;
    color: #374151;
}

/* Top header bar */
.top-bar {
    background: linear-gradient(135deg, #1e3a8a 0%, #1a56db 100%);
    border-radius: 10px;
    padding: 18px 28px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.top-bar h1 {
    color: white;
    font-size: 22px;
    font-weight: 700;
    margin: 0;
    letter-spacing: -0.02em;
}
.top-bar .subtitle {
    color: #bfdbfe;
    font-size: 13px;
    margin: 4px 0 0 0;
}
.top-bar .badge {
    background: rgba(255,255,255,0.15);
    color: white;
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 12px;
    font-weight: 600;
    border: 1px solid rgba(255,255,255,0.25);
}

/* Section label above table */
.section-label {
    font-size: 11px;
    font-weight: 600;
    color: #64748b;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 4px;
}
.note-text {
    font-size: 11px;
    color: #94a3b8;
    margin-bottom: 8px;
}

/* Stats row styling */
.stats-row-mean td { background: #f0fdf4 !important; font-style: italic; color: #374151; }
.stats-row-median td { background: #fefce8 !important; font-style: italic; color: #374151; }

/* Column group header colors */
.col-group-market { background: #dbeafe; color: #1e40af; }
.col-group-ntm { background: #dcfce7; color: #166534; }
.col-group-ltm { background: #e0e7ef; color: #374151; }
.col-group-ga { background: #fce7f3; color: #9d174d; }
.col-group-gm { background: #fef9c3; color: #854d0e; }

/* Metric cards */
.metric-card {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 14px 18px;
    text-align: center;
}
.metric-card .metric-label {
    font-size: 11px;
    color: #64748b;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.metric-card .metric-value {
    font-size: 22px;
    font-weight: 700;
    color: #0f172a;
    line-height: 1.2;
    margin-top: 4px;
}
.metric-card .metric-sub {
    font-size: 11px;
    color: #94a3b8;
    margin-top: 2px;
}

/* Sidebar sector button active */
.sector-active {
    background: #eff6ff !important;
    border-left: 3px solid #1a56db !important;
    color: #1e40af !important;
    font-weight: 600 !important;
}

/* Streamlit dataframe container */
[data-testid="stDataFrame"] {
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    overflow: hidden;
}

/* Tab styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: #f8fafc;
    border-radius: 8px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    font-size: 13px;
    font-weight: 500;
    border-radius: 6px;
    padding: 6px 16px;
}
.stTabs [aria-selected="true"] {
    background: white;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

/* Loading spinner */
.stSpinner > div { border-top-color: #1a56db !important; }

/* Footer note */
.footer-note {
    font-size: 11px;
    color: #94a3b8;
    text-align: right;
    margin-top: 8px;
    padding-top: 8px;
    border-top: 1px solid #f1f5f9;
}
</style>
""", unsafe_allow_html=True)


# ─── Load Static Data ────────────────────────────────────────────────────────
universe_df = load_universe()
ticker_meta = get_ticker_metadata()
all_sectors = get_sectors()


# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding: 12px 0 8px 0;'>
        <div style='font-size:18px;font-weight:700;color:#0f172a;letter-spacing:-0.02em;'>📊 Trading Comps</div>
        <div style='font-size:12px;color:#64748b;margin-top:2px;'>Services Universe · US & UK</div>
    </div>
    <hr style='border:none;border-top:1px solid #e2e8f0;margin:8px 0 16px 0;'>
    """, unsafe_allow_html=True)

    st.markdown("<div style='font-size:11px;font-weight:700;color:#94a3b8;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:8px;'>Sector</div>", unsafe_allow_html=True)

    selected_sector = st.radio(
        label="sector_radio",
        options=["All Sectors"] + all_sectors,
        index=0,
        label_visibility="collapsed",
    )

    st.markdown("<hr style='border:none;border-top:1px solid #e2e8f0;margin:16px 0;'>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:11px;font-weight:700;color:#94a3b8;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:8px;'>Filters</div>", unsafe_allow_html=True)

    country_filter = st.multiselect(
        "Country",
        options=["US", "UK"],
        default=["US", "UK"],
    )

    min_tev = st.number_input(
        "Min TEV ($M)",
        min_value=0,
        max_value=1_000_000,
        value=0,
        step=500,
    )

    st.markdown("<hr style='border:none;border-top:1px solid #e2e8f0;margin:16px 0;'>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:11px;font-weight:700;color:#94a3b8;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:8px;'>Display</div>", unsafe_allow_html=True)

    max_companies = st.slider("Max companies to load", 10, 100, 30, 5,
                              help="Loading more companies takes longer due to API rate limits.")

    show_charts = st.toggle("Show charts", value=True)

    st.markdown("<hr style='border:none;border-top:1px solid #e2e8f0;margin:16px 0;'>", unsafe_allow_html=True)

    # Sector summary
    if selected_sector == "All Sectors":
        sector_df = universe_df
    else:
        sector_df = universe_df[universe_df["sector"] == selected_sector]

    sector_df = sector_df[sector_df["listing_country"].isin(country_filter)]
    n_companies = len(sector_df)
    n_us = len(sector_df[sector_df["listing_country"] == "US"])
    n_uk = len(sector_df[sector_df["listing_country"] == "UK"])

    st.markdown(f"""
    <div style='background:#f8fafc;border-radius:8px;padding:12px;'>
        <div style='font-size:11px;color:#64748b;font-weight:500;margin-bottom:6px;'>Universe Summary</div>
        <div style='display:flex;justify-content:space-between;'>
            <span style='font-size:12px;color:#374151;'>Companies</span>
            <span style='font-size:12px;font-weight:700;color:#0f172a;'>{n_companies}</span>
        </div>
        <div style='display:flex;justify-content:space-between;margin-top:3px;'>
            <span style='font-size:12px;color:#374151;'>US Listed</span>
            <span style='font-size:12px;font-weight:600;color:#1a56db;'>{n_us}</span>
        </div>
        <div style='display:flex;justify-content:space-between;margin-top:3px;'>
            <span style='font-size:12px;color:#374151;'>UK Listed</span>
            <span style='font-size:12px;font-weight:600;color:#1a56db;'>{n_uk}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ─── Determine tickers to load ───────────────────────────────────────────────
if selected_sector == "All Sectors":
    filtered_df = universe_df[universe_df["listing_country"].isin(country_filter)]
else:
    filtered_df = universe_df[
        (universe_df["sector"] == selected_sector) &
        (universe_df["listing_country"].isin(country_filter))
    ]

tickers_to_load = filtered_df["ticker"].tolist()[:max_companies]


# ─── Header ──────────────────────────────────────────────────────────────────
sector_display = selected_sector if selected_sector != "All Sectors" else "All Sectors"
st.markdown(f"""
<div class="top-bar">
    <div>
        <div style="font-size:11px;color:#93c5fd;font-weight:500;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:4px;">
            Services Universe · US & UK
        </div>
        <h1 style="color:white;font-size:22px;font-weight:700;margin:0;letter-spacing:-0.02em;">
            {sector_display}
        </h1>
        <p class="subtitle">All financials in millions ($M). Sorted by TEV descending.</p>
    </div>
    <div>
        <span class="badge">{len(tickers_to_load)} companies loaded</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ─── Fetch Data ───────────────────────────────────────────────────────────────
if not tickers_to_load:
    st.warning("No companies match the selected filters.")
    st.stop()

with st.spinner(f"Fetching market data for {len(tickers_to_load)} companies..."):
    metrics = fetch_metrics(tuple(tickers_to_load))


# ─── Build Table ─────────────────────────────────────────────────────────────
raw_df = build_comps_table(metrics, ticker_meta)

# Apply TEV filter
if min_tev > 0:
    raw_df = raw_df[pd.to_numeric(raw_df["TEV ($M)"], errors="coerce").fillna(0) >= min_tev]

# Add Sub Sector column after Company/Ticker
display_df = raw_df.copy()
stats = compute_stats(display_df)

# Build list of all value columns in order
all_value_cols = []
for group_info in COLUMN_GROUPS.values():
    all_value_cols.extend(group_info["cols"])

display_cols = ["Company", "Ticker"] + [c for c in all_value_cols if c in display_df.columns]
display_df = display_df[display_cols]


# ─── Tabs ────────────────────────────────────────────────────────────────────
tab_table, tab_charts, tab_universe = st.tabs(["📋  Comps Table", "📈  Charts", "🌐  Universe"])


# ═══════════════════════════════════════════════════════════════
# TAB 1 — COMPS TABLE
# ═══════════════════════════════════════════════════════════════
with tab_table:

    # Column group header
    st.markdown(render_group_headers(display_cols), unsafe_allow_html=True)

    # Format display values
    formatted_df = apply_display_formats(display_df)

    # Build stats rows
    mean_row = render_stats_row(stats, display_cols, "Mean", "mean")
    median_row = render_stats_row(stats, display_cols, "Median", "median")

    stats_df = pd.DataFrame([mean_row, median_row])
    company_df = formatted_df.copy()

    # Combine: stats rows first (matching reference image), then companies
    full_display = pd.concat([stats_df, company_df], ignore_index=True)
    full_display = full_display[display_cols].fillna("")

    # Render styled table
    def highlight_stats(row):
        idx = row.name
        if idx == 0:
            return ["background-color: #f0fdf4; font-style: italic; color: #374151;"] * len(row)
        elif idx == 1:
            return ["background-color: #fefce8; font-style: italic; color: #374151;"] * len(row)
        return [""] * len(row)

    styled = (
        full_display.style
        .apply(highlight_stats, axis=1)
        .set_properties(**{"font-size": "12px", "padding": "4px 8px", "white-space": "nowrap"})
        .set_table_styles([
            {"selector": "thead th", "props": [
                ("font-size", "11px"), ("font-weight", "700"),
                ("text-align", "center"), ("padding", "6px 8px"),
                ("border-bottom", "2px solid #e2e8f0"),
                ("background-color", "#f8fafc"),
            ]},
            {"selector": "tbody tr:nth-child(n+3):nth-child(even)", "props": [
                ("background-color", "#f8fafc"),
            ]},
            {"selector": "tbody tr:hover", "props": [("background-color", "#eff6ff")]},
            {"selector": "tbody td", "props": [
                ("text-align", "right"), ("border-bottom", "1px solid #f1f5f9"),
            ]},
            {"selector": "tbody td:first-child, tbody td:nth-child(2)", "props": [
                ("text-align", "left"),
            ]},
        ])
        .hide(axis="index")
    )

    st.dataframe(styled, use_container_width=True, height=600)

    st.markdown(
        "<div class='footer-note'>Data sourced from Yahoo Finance via yfinance. Refreshed hourly. NTM estimates use forward consensus proxies.</div>",
        unsafe_allow_html=True,
    )

    # Download button
    csv = display_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇ Download CSV",
        data=csv,
        file_name=f"trading_comps_{selected_sector.replace(' ', '_').lower()}.csv",
        mime="text/csv",
    )


# ═══════════════════════════════════════════════════════════════
# TAB 2 — CHARTS
# ═══════════════════════════════════════════════════════════════
with tab_charts:
    if not show_charts:
        st.info("Charts are disabled. Toggle 'Show charts' in the sidebar to enable.")
    else:
        # KPI summary row
        c1, c2, c3, c4, c5 = st.columns(5)
        def safe_stat(key, stat_key, multiplier=1, suffix="x"):
            try:
                v = stats[key][stat_key]
                if v is None:
                    return "n/a"
                return f"{v * multiplier:.1f}{suffix}"
            except Exception:
                return "n/a"

        with c1:
            st.metric("Median NTM EV/EBITDA", safe_stat("NTM EV/EBITDA", "median"))
        with c2:
            st.metric("Median NTM P/E", safe_stat("NTM P/E", "median"))
        with c3:
            st.metric("Median LTM EV/EBITDA", safe_stat("LTM EV/EBITDA", "median"))
        with c4:
            st.metric("Median Rev Growth", safe_stat("NTM Rev Gr%", "median", 100, "%"))
        with c5:
            st.metric("Median EBITDA Margin", safe_stat("EBITDA Mgn", "median", 100, "%"))

        st.markdown("<br>", unsafe_allow_html=True)

        # Chart grid
        numeric_raw = raw_df.copy()
        numeric_raw["Sub Sector"] = numeric_raw["Ticker"].map(
            lambda t: ticker_meta.get(t, {}).get("sub_sector", "")
        )

        col_a, col_b = st.columns(2)
        with col_a:
            render_ev_ebitda_chart(numeric_raw)
        with col_b:
            render_pe_chart(numeric_raw)

        col_c, col_d = st.columns(2)
        with col_c:
            render_growth_margin_scatter(numeric_raw)
        with col_d:
            render_market_cap_treemap(numeric_raw)


# ═══════════════════════════════════════════════════════════════
# TAB 3 — UNIVERSE EXPLORER
# ═══════════════════════════════════════════════════════════════
with tab_universe:
    st.markdown("#### Full Universe")
    st.markdown(f"<div class='note-text'>{len(filtered_df)} companies in selected view · {len(universe_df)} total in universe</div>", unsafe_allow_html=True)

    show_cols = ["name", "ticker", "sector", "sub_sector", "listing_country", "exchange"]
    st.dataframe(
        filtered_df[show_cols].rename(columns={
            "name": "Company", "ticker": "Ticker",
            "sector": "Sector", "sub_sector": "Sub Sector",
            "listing_country": "Country", "exchange": "Exchange",
        }).reset_index(drop=True),
        use_container_width=True,
        height=500,
    )

    # Sub-sector breakdown
    st.markdown("#### Sub Sector Breakdown")
    if selected_sector != "All Sectors":
        sub_counts = filtered_df["sub_sector"].value_counts().reset_index()
        sub_counts.columns = ["Sub Sector", "Count"]
        import plotly.express as px
        fig = px.bar(
            sub_counts, x="Count", y="Sub Sector", orientation="h",
            color="Count", color_continuous_scale=["#dbeafe", "#1a56db"],
            title=f"Companies per Sub Sector — {selected_sector}",
        )
        fig.update_layout(
            plot_bgcolor="white", paper_bgcolor="white",
            showlegend=False, coloraxis_showscale=False,
            yaxis=dict(categoryorder="total ascending"),
            height=max(300, len(sub_counts) * 28),
            margin=dict(l=10, r=20, t=50, b=20),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        sector_counts = filtered_df["sector"].value_counts().reset_index()
        sector_counts.columns = ["Sector", "Count"]
        import plotly.express as px
        fig = px.pie(
            sector_counts, values="Count", names="Sector",
            title="Universe Breakdown by Sector",
            color_discrete_sequence=px.colors.sequential.Blues_r,
        )
        fig.update_layout(
            font=dict(family="Inter, sans-serif", size=12),
            paper_bgcolor="white", height=420,
            margin=dict(l=10, r=10, t=50, b=10),
        )
        st.plotly_chart(fig, use_container_width=True)
