import pandas as pd
import numpy as np


def build_comps_table(metrics: dict, ticker_meta: dict) -> pd.DataFrame:
    rows = []
    for ticker, m in metrics.items():
        meta = ticker_meta.get(ticker, {})
        mkt_cap = m.get("market_cap")
        tev = m.get("tev")

        rows.append({
            "Company": meta.get("name", ticker),
            "Ticker": ticker,
            "Country": meta.get("country", ""),
            "Sub Sector": meta.get("sub_sector", ""),
            "Mkt Cap ($M)": mkt_cap / 1e6 if mkt_cap else None,
            "TEV ($M)": tev / 1e6 if tev else None,
            "% 52W Hi": m.get("pct_52w_hi"),
            # NTM Multiples
            "NTM EV/EBITDA": m.get("ntm_ev_ebitda"),
            "NTM P/E": m.get("pe_ntm"),
            # LTM Multiples
            "LTM EV/EBITDA": m.get("ltm_ev_ebitda"),
            "LTM P/E": m.get("pe_ltm"),
            # Growth Adjusted
            "PEG": m.get("peg"),
            # Growth & Margins
            "NTM Rev Gr%": m.get("ntm_rev_growth"),
            "3Y CAGR": m.get("cagr_3y"),
            "Gross Mgn": m.get("gross_margin"),
            "EBITDA Mgn": m.get("ebitda_margin"),
            "Rule of 40": m.get("rule_of_40"),
        })

    df = pd.DataFrame(rows)
    if not df.empty and "TEV ($M)" in df.columns:
        df = df.sort_values("TEV ($M)", ascending=False, na_position="last")
    df = df.reset_index(drop=True)
    return df


def compute_stats(df: pd.DataFrame) -> dict:
    numeric_cols = [
        "Mkt Cap ($M)", "TEV ($M)", "% 52W Hi",
        "NTM EV/EBITDA", "NTM P/E",
        "LTM EV/EBITDA", "LTM P/E",
        "PEG", "NTM Rev Gr%", "3Y CAGR",
        "Gross Mgn", "EBITDA Mgn", "Rule of 40",
    ]
    stats = {}
    for col in numeric_cols:
        if col in df.columns:
            series = pd.to_numeric(df[col], errors="coerce").dropna()
            stats[col] = {
                "mean": series.mean() if len(series) else None,
                "median": series.median() if len(series) else None,
            }
    return stats
