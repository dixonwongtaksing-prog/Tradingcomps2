import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np


CHART_COLORS = {
    "blue": "#1a56db",
    "green": "#059669",
    "amber": "#d97706",
    "rose": "#e11d48",
    "slate": "#475569",
}


def _clean_numeric(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """Return df with col converted to numeric, dropping NaN rows."""
    out = df.copy()
    out[col] = pd.to_numeric(out[col], errors="coerce")
    return out.dropna(subset=[col])


def render_ev_ebitda_chart(df: pd.DataFrame):
    col = "NTM EV/EBITDA"
    clean = _clean_numeric(df, col).head(25)
    if clean.empty:
        st.info("No EV/EBITDA data available.")
        return
    fig = px.bar(
        clean, x="Ticker", y=col, color=col,
        color_continuous_scale=["#bfdbfe", "#1a56db"],
        title="NTM EV/EBITDA by Company",
        labels={col: "EV/EBITDA (x)"},
    )
    fig.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Inter, sans-serif", size=12),
        title_font_size=14, coloraxis_showscale=False,
        xaxis=dict(tickangle=45, gridcolor="#f1f5f9"),
        yaxis=dict(gridcolor="#f1f5f9"),
        margin=dict(l=40, r=20, t=50, b=80),
        height=360,
    )
    fig.update_traces(marker_line_width=0)
    st.plotly_chart(fig, use_container_width=True)


def render_pe_chart(df: pd.DataFrame):
    col = "NTM P/E"
    clean = _clean_numeric(df, col).head(25)
    if clean.empty:
        st.info("No P/E data available.")
        return
    fig = px.bar(
        clean, x="Ticker", y=col, color=col,
        color_continuous_scale=["#bbf7d0", "#059669"],
        title="NTM P/E by Company",
        labels={col: "P/E (x)"},
    )
    fig.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Inter, sans-serif", size=12),
        title_font_size=14, coloraxis_showscale=False,
        xaxis=dict(tickangle=45, gridcolor="#f1f5f9"),
        yaxis=dict(gridcolor="#f1f5f9"),
        margin=dict(l=40, r=20, t=50, b=80),
        height=360,
    )
    fig.update_traces(marker_line_width=0)
    st.plotly_chart(fig, use_container_width=True)


def render_growth_margin_scatter(df: pd.DataFrame):
    x_col, y_col = "NTM Rev Gr%", "EBITDA Mgn"
    clean = df.copy()
    clean[x_col] = pd.to_numeric(clean[x_col], errors="coerce")
    clean[y_col] = pd.to_numeric(clean[y_col], errors="coerce")
    clean = clean.dropna(subset=[x_col, y_col])
    if clean.empty:
        st.info("Insufficient data for scatter plot.")
        return

    fig = px.scatter(
        clean, x=x_col, y=y_col,
        text="Ticker",
        title="Revenue Growth vs EBITDA Margin",
        labels={x_col: "NTM Revenue Growth", y_col: "EBITDA Margin"},
        color_discrete_sequence=[CHART_COLORS["blue"]],
    )
    fig.update_traces(
        textposition="top center", textfont_size=10,
        marker=dict(size=8, line=dict(width=1, color="white")),
    )
    fig.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Inter, sans-serif", size=12),
        title_font_size=14,
        xaxis=dict(tickformat=".0%", gridcolor="#f1f5f9", zeroline=True, zerolinecolor="#e2e8f0"),
        yaxis=dict(tickformat=".0%", gridcolor="#f1f5f9", zeroline=True, zerolinecolor="#e2e8f0"),
        margin=dict(l=40, r=20, t=50, b=40),
        height=420,
    )
    st.plotly_chart(fig, use_container_width=True)


def render_market_cap_treemap(df: pd.DataFrame):
    col = "Mkt Cap ($M)"
    clean = _clean_numeric(df, col)
    clean = clean[clean[col] > 0]
    if clean.empty:
        st.info("No market cap data available.")
        return
    fig = px.treemap(
        clean, path=["Sub Sector", "Ticker"], values=col,
        title="Market Cap Distribution by Sub Sector",
        color=col,
        color_continuous_scale=["#dbeafe", "#1a56db"],
    )
    fig.update_layout(
        font=dict(family="Inter, sans-serif", size=12),
        title_font_size=14,
        margin=dict(l=10, r=10, t=50, b=10),
        height=420,
    )
    st.plotly_chart(fig, use_container_width=True)
