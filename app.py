import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px

st.set_page_config(page_title="Trading Comps", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
[data-testid="stSidebar"] { background: #ffffff; border-right: 1px solid #e2e8f0; }
.top-bar { background: linear-gradient(135deg, #1e3a8a 0%, #1a56db 100%); border-radius: 10px; padding: 18px 28px; margin-bottom: 20px; display: flex; align-items: center; justify-content: space-between; }
.top-bar .badge { background: rgba(255,255,255,0.15); color: white; border-radius: 20px; padding: 4px 12px; font-size: 12px; font-weight: 600; border: 1px solid rgba(255,255,255,0.25); }
.note-text { font-size: 11px; color: #94a3b8; margin-bottom: 8px; }
[data-testid="stDataFrame"] { border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; }
.stTabs [data-baseweb="tab-list"] { gap: 4px; background: #f8fafc; border-radius: 8px; padding: 4px; }
.stTabs [data-baseweb="tab"] { font-size: 13px; font-weight: 500; border-radius: 6px; padding: 6px 16px; }
.stTabs [aria-selected="true"] { background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.footer-note { font-size: 11px; color: #94a3b8; text-align: right; margin-top: 8px; padding-top: 8px; border-top: 1px solid #f1f5f9; }
</style>
""", unsafe_allow_html=True)

# ── Universe ──────────────────────────────────────────────────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))
UNIVERSE_PATH = os.path.join(_HERE, "data", "expanded_services_universe_us_uk.xlsx")

@st.cache_data(show_spinner=False)
def load_universe():
    return pd.read_excel(UNIVERSE_PATH)

@st.cache_data(show_spinner=False)
def get_ticker_metadata():
    df = load_universe()
    return {row["ticker"]: {"name": row["name"], "sector": row["sector"], "sub_sector": row["sub_sector"], "country": row["listing_country"], "exchange": row["exchange"]} for _, row in df.iterrows()}

# ── Fetcher ───────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_metrics(tickers: tuple) -> dict:
    import yfinance as yf
    results = {}
    for ticker in tickers:
        try:
            info = yf.Ticker(ticker).info
            price = info.get("currentPrice") or info.get("regularMarketPrice")
            mc = info.get("marketCap")
            ev = info.get("enterpriseValue")
            ebitda = info.get("ebitda")
            revenue = info.get("totalRevenue")
            rev_growth = info.get("revenueGrowth")
            gross_mgn = info.get("grossMargins")
            ebitda_mgn = info.get("ebitdaMargins")
            w52hi = info.get("fiftyTwoWeekHigh")
            fwd_pe = info.get("forwardPE")
            trail_pe = info.get("trailingPE")
            peg = info.get("pegRatio")
            cagr = info.get("earningsGrowth") or rev_growth
            ntm_ebitda = (revenue * ebitda_mgn) if revenue and ebitda_mgn else None
            results[ticker] = {
                "market_cap": mc,
                "tev": ev,
                "pct_52w_hi": (price / w52hi) if price and w52hi and w52hi > 0 else None,
                "ntm_ev_ebitda": (ev / ntm_ebitda) if ev and ntm_ebitda else None,
                "ltm_ev_ebitda": (ev / ebitda) if ev and ebitda else None,
                "pe_ntm": fwd_pe,
                "pe_ltm": trail_pe,
                "peg": peg,
                "ntm_rev_growth": rev_growth,
                "cagr_3y": cagr,
                "gross_margin": gross_mgn,
                "ebitda_margin": ebitda_mgn,
                "rule_of_40": ((rev_growth or 0) * 100) + ((ebitda_mgn or 0) * 100),
            }
        except Exception:
            results[ticker] = {k: None for k in ["market_cap","tev","pct_52w_hi","ntm_ev_ebitda","ltm_ev_ebitda","pe_ntm","pe_ltm","peg","ntm_rev_growth","cagr_3y","gross_margin","ebitda_margin","rule_of_40"]}
    return results

# ── Column groups ─────────────────────────────────────────────────────────────
COLUMN_GROUPS = {
    "Market Data":      {"cols": ["Mkt Cap ($M)", "TEV ($M)", "% 52W Hi"],         "bg": "#dbeafe", "fg": "#1e40af"},
    "NTM Multiples":    {"cols": ["NTM EV/EBITDA", "NTM P/E"],                     "bg": "#dcfce7", "fg": "#166534"},
    "LTM Multiples":    {"cols": ["LTM EV/EBITDA", "LTM P/E"],                     "bg": "#e0e7ef", "fg": "#374151"},
    "Growth Adjusted":  {"cols": ["PEG"],                                           "bg": "#fce7f3", "fg": "#9d174d"},
    "Growth & Margins": {"cols": ["NTM Rev Gr%","3Y CAGR","Gross Mgn","EBITDA Mgn","Rule of 40"], "bg": "#fef9c3", "fg": "#854d0e"},
}
PCT_COLS   = ["% 52W Hi","NTM Rev Gr%","3Y CAGR","Gross Mgn","EBITDA Mgn"]
MULTI_COLS = ["NTM EV/EBITDA","NTM P/E","LTM EV/EBITDA","LTM P/E"]
CURR_COLS  = ["Mkt Cap ($M)","TEV ($M)"]

# ── Table builder ─────────────────────────────────────────────────────────────
def build_comps_table(metrics, ticker_meta):
    rows = []
    for ticker, m in metrics.items():
        meta = ticker_meta.get(ticker, {})
        mc = m.get("market_cap"); tev = m.get("tev")
        rows.append({
            "Company": meta.get("name", ticker), "Ticker": ticker, "Sub Sector": meta.get("sub_sector",""),
            "Mkt Cap ($M)": mc/1e6 if mc else None, "TEV ($M)": tev/1e6 if tev else None,
            "% 52W Hi": m.get("pct_52w_hi"), "NTM EV/EBITDA": m.get("ntm_ev_ebitda"), "NTM P/E": m.get("pe_ntm"),
            "LTM EV/EBITDA": m.get("ltm_ev_ebitda"), "LTM P/E": m.get("pe_ltm"), "PEG": m.get("peg"),
            "NTM Rev Gr%": m.get("ntm_rev_growth"), "3Y CAGR": m.get("cagr_3y"),
            "Gross Mgn": m.get("gross_margin"), "EBITDA Mgn": m.get("ebitda_margin"), "Rule of 40": m.get("rule_of_40"),
        })
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("TEV ($M)", ascending=False, na_position="last").reset_index(drop=True)
    return df

def compute_stats(df):
    all_cols = [c for g in COLUMN_GROUPS.values() for c in g["cols"]]
    return {col: {"mean": pd.to_numeric(df[col], errors="coerce").dropna().mean() if col in df.columns else None,
                  "median": pd.to_numeric(df[col], errors="coerce").dropna().median() if col in df.columns else None}
            for col in all_cols}

def _fmt(v, kind):
    if v is None or (isinstance(v, float) and np.isnan(v)): return ""
    if kind == "pct":  return f"{v*100:.0f}%"
    if kind == "mult": return f"{v:.1f}x"
    if kind == "peg":  return f"{v:.2f}x"
    if kind == "r40":  return f"{v:.0f}"
    if kind == "curr": return f"${v/1000:.1f}B" if abs(v) >= 1000 else f"${v:.0f}M"
    return str(v)

def apply_formats(df):
    d = df.copy()
    for c in PCT_COLS:
        if c in d.columns: d[c] = d[c].apply(lambda v: _fmt(v,"pct"))
    for c in MULTI_COLS:
        if c in d.columns: d[c] = d[c].apply(lambda v: _fmt(v,"mult"))
    if "PEG" in d.columns: d["PEG"] = d["PEG"].apply(lambda v: _fmt(v,"peg"))
    if "Rule of 40" in d.columns: d["Rule of 40"] = d["Rule of 40"].apply(lambda v: _fmt(v,"r40"))
    for c in CURR_COLS:
        if c in d.columns: d[c] = d[c].apply(lambda v: _fmt(v,"curr"))
    return d

def stats_row(stats, display_cols, label, key):
    row = {"Company": label, "Ticker": ""}
    for col in display_cols:
        v = stats.get(col, {}).get(key)
        if v is None: row[col] = ""
        elif col in PCT_COLS:   row[col] = f"{v*100:.0f}%"
        elif col in MULTI_COLS: row[col] = f"{v:.1f}x"
        elif col == "PEG":      row[col] = f"{v:.2f}x"
        elif col == "Rule of 40": row[col] = f"{v:.0f}"
        elif col in CURR_COLS:  row[col] = ""
        else: row[col] = f"{v:.1f}"
    return row

def group_header_html(display_cols):
    fixed = '<th colspan="2" style="background:#fff;border:none;"></th>'
    groups = ""
    for name, g in COLUMN_GROUPS.items():
        visible = [c for c in g["cols"] if c in display_cols]
        if not visible: continue
        groups += f'<th colspan="{len(visible)}" style="background:{g["bg"]};color:{g["fg"]};font-size:11px;font-weight:700;text-align:center;padding:5px 8px;border-left:2px solid #e2e8f0;letter-spacing:0.05em;">{name.upper()}</th>'
    return f'<table style="width:100%;border-collapse:collapse;"><tr>{fixed}{groups}</tr></table>'

# ── Load ──────────────────────────────────────────────────────────────────────
universe_df = load_universe()
ticker_meta = get_ticker_metadata()
all_sectors = sorted(universe_df["sector"].unique().tolist())

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("<div style='padding:12px 0 8px 0;'><div style='font-size:18px;font-weight:700;color:#0f172a;'>📊 Trading Comps</div><div style='font-size:12px;color:#64748b;margin-top:2px;'>Services Universe · US & UK</div></div><hr style='border:none;border-top:1px solid #e2e8f0;margin:8px 0 16px 0;'>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:11px;font-weight:700;color:#94a3b8;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:8px;'>Sector</div>", unsafe_allow_html=True)
    selected_sector = st.radio("sector", ["All Sectors"] + all_sectors, index=0, label_visibility="collapsed")
    st.markdown("<hr style='border:none;border-top:1px solid #e2e8f0;margin:16px 0;'>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:11px;font-weight:700;color:#94a3b8;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:8px;'>Filters</div>", unsafe_allow_html=True)
    country_filter = st.multiselect("Country", ["US","UK"], default=["US","UK"])
    min_tev = st.number_input("Min TEV ($M)", min_value=0, max_value=1_000_000, value=0, step=500)
    st.markdown("<hr style='border:none;border-top:1px solid #e2e8f0;margin:16px 0;'>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:11px;font-weight:700;color:#94a3b8;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:8px;'>Display</div>", unsafe_allow_html=True)
    max_companies = st.slider("Max companies to load", 10, 100, 30, 5)
    show_charts = st.toggle("Show charts", value=True)
    st.markdown("<hr style='border:none;border-top:1px solid #e2e8f0;margin:16px 0;'>", unsafe_allow_html=True)
    sdf = universe_df if selected_sector == "All Sectors" else universe_df[universe_df["sector"] == selected_sector]
    sdf = sdf[sdf["listing_country"].isin(country_filter)]
    st.markdown(f"<div style='background:#f8fafc;border-radius:8px;padding:12px;'><div style='font-size:11px;color:#64748b;font-weight:500;margin-bottom:6px;'>Universe Summary</div><div style='display:flex;justify-content:space-between;'><span style='font-size:12px;color:#374151;'>Companies</span><span style='font-size:12px;font-weight:700;color:#0f172a;'>{len(sdf)}</span></div><div style='display:flex;justify-content:space-between;margin-top:3px;'><span style='font-size:12px;color:#374151;'>US Listed</span><span style='font-size:12px;font-weight:600;color:#1a56db;'>{len(sdf[sdf['listing_country']=='US'])}</span></div><div style='display:flex;justify-content:space-between;margin-top:3px;'><span style='font-size:12px;color:#374151;'>UK Listed</span><span style='font-size:12px;font-weight:600;color:#1a56db;'>{len(sdf[sdf['listing_country']=='UK'])}</span></div></div>", unsafe_allow_html=True)

# ── Filter & fetch ────────────────────────────────────────────────────────────
filtered_df = universe_df[universe_df["listing_country"].isin(country_filter)] if selected_sector == "All Sectors" else universe_df[(universe_df["sector"] == selected_sector) & (universe_df["listing_country"].isin(country_filter))]
tickers_to_load = filtered_df["ticker"].tolist()[:max_companies]

st.markdown(f'<div class="top-bar"><div><div style="font-size:11px;color:#93c5fd;font-weight:500;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:4px;">Services Universe · US & UK</div><div style="color:white;font-size:22px;font-weight:700;letter-spacing:-0.02em;">{selected_sector}</div><div style="color:#bfdbfe;font-size:13px;margin-top:4px;">All financials in millions ($M). Sorted by TEV descending.</div></div><span class="badge">{len(tickers_to_load)} companies loaded</span></div>', unsafe_allow_html=True)

if not tickers_to_load:
    st.warning("No companies match the selected filters.")
    st.stop()

with st.spinner(f"Fetching market data for {len(tickers_to_load)} companies..."):
    metrics = fetch_metrics(tuple(tickers_to_load))

raw_df = build_comps_table(metrics, ticker_meta)
if min_tev > 0:
    raw_df = raw_df[pd.to_numeric(raw_df["TEV ($M)"], errors="coerce").fillna(0) >= min_tev]

stats = compute_stats(raw_df)
all_val_cols = [c for g in COLUMN_GROUPS.values() for c in g["cols"]]
display_cols = ["Company","Ticker"] + [c for c in all_val_cols if c in raw_df.columns]
display_df = raw_df[display_cols].copy()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_table, tab_charts, tab_universe = st.tabs(["📋  Comps Table", "📈  Charts", "🌐  Universe"])

with tab_table:
    st.markdown(group_header_html(display_cols), unsafe_allow_html=True)
    fmt = apply_formats(display_df)
    full = pd.concat([pd.DataFrame([stats_row(stats,display_cols,"Mean","mean"), stats_row(stats,display_cols,"Median","median")]), fmt], ignore_index=True)
    full = full[display_cols].fillna("")

    def hl(row):
        if row.name == 0: return ["background-color:#f0fdf4;font-style:italic;color:#374151;"]*len(row)
        if row.name == 1: return ["background-color:#fefce8;font-style:italic;color:#374151;"]*len(row)
        return [""]*len(row)

    styled = (full.style.apply(hl,axis=1)
        .set_properties(**{"font-size":"12px","padding":"4px 8px","white-space":"nowrap"})
        .set_table_styles([
            {"selector":"thead th","props":[("font-size","11px"),("font-weight","700"),("text-align","center"),("padding","6px 8px"),("border-bottom","2px solid #e2e8f0"),("background-color","#f8fafc")]},
            {"selector":"tbody tr:nth-child(n+3):nth-child(even)","props":[("background-color","#f8fafc")]},
            {"selector":"tbody tr:hover","props":[("background-color","#eff6ff")]},
            {"selector":"tbody td","props":[("text-align","right"),("border-bottom","1px solid #f1f5f9")]},
            {"selector":"tbody td:first-child, tbody td:nth-child(2)","props":[("text-align","left")]},
        ]).hide(axis="index"))
    st.dataframe(styled, use_container_width=True, height=600)
    st.markdown("<div class='footer-note'>Data sourced from Yahoo Finance. Refreshed hourly.</div>", unsafe_allow_html=True)
    st.download_button("⬇ Download CSV", display_df.to_csv(index=False).encode("utf-8"), file_name=f"trading_comps_{selected_sector.replace(' ','_').lower()}.csv", mime="text/csv")

with tab_charts:
    if not show_charts:
        st.info("Toggle 'Show charts' in the sidebar to enable.")
    else:
        def ss(k, sk, m=1, s="x"):
            try: v=stats[k][sk]; return "n/a" if v is None else f"{v*m:.1f}{s}"
            except: return "n/a"
        c1,c2,c3,c4,c5 = st.columns(5)
        c1.metric("Median NTM EV/EBITDA", ss("NTM EV/EBITDA","median"))
        c2.metric("Median NTM P/E",       ss("NTM P/E","median"))
        c3.metric("Median LTM EV/EBITDA", ss("LTM EV/EBITDA","median"))
        c4.metric("Median Rev Growth",    ss("NTM Rev Gr%","median",100,"%"))
        c5.metric("Median EBITDA Margin", ss("EBITDA Mgn","median",100,"%"))
        st.markdown("<br>", unsafe_allow_html=True)
        cd = raw_df.copy()
        cd["Sub Sector"] = cd["Ticker"].map(lambda t: ticker_meta.get(t,{}).get("sub_sector",""))

        def barchart(df,col,title,cs):
            d=df.copy(); d[col]=pd.to_numeric(d[col],errors="coerce"); d=d.dropna(subset=[col]).head(25)
            if d.empty: st.info(f"No {col} data."); return
            fig=px.bar(d,x="Ticker",y=col,color=col,color_continuous_scale=cs,title=title)
            fig.update_layout(plot_bgcolor="white",paper_bgcolor="white",coloraxis_showscale=False,xaxis=dict(tickangle=45,gridcolor="#f1f5f9"),yaxis=dict(gridcolor="#f1f5f9"),margin=dict(l=40,r=20,t=50,b=80),height=360)
            fig.update_traces(marker_line_width=0)
            st.plotly_chart(fig,use_container_width=True)

        ca,cb=st.columns(2)
        with ca: barchart(cd,"NTM EV/EBITDA","NTM EV/EBITDA",["#bfdbfe","#1a56db"])
        with cb: barchart(cd,"NTM P/E","NTM P/E",["#bbf7d0","#059669"])

        cc,c_d=st.columns(2)
        with cc:
            d=cd.copy(); d["NTM Rev Gr%"]=pd.to_numeric(d["NTM Rev Gr%"],errors="coerce"); d["EBITDA Mgn"]=pd.to_numeric(d["EBITDA Mgn"],errors="coerce"); d=d.dropna(subset=["NTM Rev Gr%","EBITDA Mgn"])
            if not d.empty:
                fig=px.scatter(d,x="NTM Rev Gr%",y="EBITDA Mgn",text="Ticker",title="Rev Growth vs EBITDA Margin",color_discrete_sequence=["#1a56db"])
                fig.update_traces(textposition="top center",textfont_size=10,marker=dict(size=8))
                fig.update_layout(plot_bgcolor="white",paper_bgcolor="white",xaxis=dict(tickformat=".0%",gridcolor="#f1f5f9"),yaxis=dict(tickformat=".0%",gridcolor="#f1f5f9"),margin=dict(l=40,r=20,t=50,b=40),height=420)
                st.plotly_chart(fig,use_container_width=True)
        with c_d:
            d=cd.copy(); d["Mkt Cap ($M)"]=pd.to_numeric(d["Mkt Cap ($M)"],errors="coerce"); d=d[d["Mkt Cap ($M)"]>0].dropna(subset=["Mkt Cap ($M)"])
            if not d.empty:
                fig=px.treemap(d,path=["Sub Sector","Ticker"],values="Mkt Cap ($M)",title="Market Cap by Sub Sector",color="Mkt Cap ($M)",color_continuous_scale=["#dbeafe","#1a56db"])
                fig.update_layout(paper_bgcolor="white",height=420,margin=dict(l=10,r=10,t=50,b=10))
                st.plotly_chart(fig,use_container_width=True)

with tab_universe:
    st.markdown("#### Full Universe")
    st.markdown(f"<div class='note-text'>{len(filtered_df)} companies in view · {len(universe_df)} total</div>", unsafe_allow_html=True)
    st.dataframe(filtered_df[["name","ticker","sector","sub_sector","listing_country","exchange"]].rename(columns={"name":"Company","ticker":"Ticker","sector":"Sector","sub_sector":"Sub Sector","listing_country":"Country","exchange":"Exchange"}).reset_index(drop=True), use_container_width=True, height=500)
    st.markdown("#### Sub Sector Breakdown")
    if selected_sector != "All Sectors":
        sc=filtered_df["sub_sector"].value_counts().reset_index(); sc.columns=["Sub Sector","Count"]
        fig=px.bar(sc,x="Count",y="Sub Sector",orientation="h",color="Count",color_continuous_scale=["#dbeafe","#1a56db"],title=f"Companies per Sub Sector — {selected_sector}")
        fig.update_layout(plot_bgcolor="white",paper_bgcolor="white",showlegend=False,coloraxis_showscale=False,yaxis=dict(categoryorder="total ascending"),height=max(300,len(sc)*28),margin=dict(l=10,r=20,t=50,b=20))
        st.plotly_chart(fig,use_container_width=True)
    else:
        sc=filtered_df["sector"].value_counts().reset_index(); sc.columns=["Sector","Count"]
        fig=px.pie(sc,values="Count",names="Sector",title="Universe by Sector",color_discrete_sequence=px.colors.sequential.Blues_r)
        fig.update_layout(paper_bgcolor="white",height=420,margin=dict(l=10,r=10,t=50,b=10))
        st.plotly_chart(fig,use_container_width=True)
