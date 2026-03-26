import yfinance as yf
import streamlit as st
import pandas as pd


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_metrics(tickers: tuple) -> dict:
    results = {}
    for ticker in tickers:
        try:
            t = yf.Ticker(ticker)
            info = t.info
            fast_info = t.fast_info

            price = info.get("currentPrice") or info.get("regularMarketPrice") or fast_info.get("last_price")
            market_cap = info.get("marketCap") or fast_info.get("market_cap")
            ev = info.get("enterpriseValue")
            ebitda = info.get("ebitda")
            revenue = info.get("totalRevenue")
            net_income = info.get("netIncomeToCommon")
            eps_ttm = info.get("trailingEps")
            eps_fwd = info.get("forwardEps")
            rev_growth = info.get("revenueGrowth")
            gross_margins = info.get("grossMargins")
            ebitda_margins = info.get("ebitdaMargins")
            week52_high = info.get("fiftyTwoWeekHigh")
            week52_low = info.get("fiftyTwoWeekLow")
            fwd_pe = info.get("forwardPE")
            trailing_pe = info.get("trailingPE")
            peg_ratio = info.get("pegRatio")

            # NTM estimates (yfinance doesn't provide NTM directly; use forward as proxy)
            ntm_revenue = info.get("revenueEstimate") or info.get("totalRevenue")
            ntm_ebitda = None
            if ntm_revenue and ebitda_margins:
                ntm_ebitda = ntm_revenue * ebitda_margins

            # % of 52W high
            pct_52w = None
            if price and week52_high and week52_high > 0:
                pct_52w = price / week52_high

            # EV multiples
            ev_ntm_ebitda = ev / ntm_ebitda if ev and ntm_ebitda else None
            ev_ltm_ebitda = ev / ebitda if ev and ebitda else None

            # P/E
            pe_ntm = fwd_pe
            pe_ltm = trailing_pe

            # 3Y CAGR proxy using analyst growth
            cagr_3y = info.get("earningsGrowth") or info.get("revenueGrowth")

            results[ticker] = {
                "price": price,
                "market_cap": market_cap,
                "tev": ev,
                "pct_52w_hi": pct_52w,
                "ntm_ev_ebitda": ev_ntm_ebitda,
                "ltm_ev_ebitda": ev_ltm_ebitda,
                "pe_ntm": pe_ntm,
                "pe_ltm": pe_ltm,
                "peg": peg_ratio,
                "ntm_rev_growth": rev_growth,
                "cagr_3y": cagr_3y,
                "gross_margin": gross_margins,
                "ebitda_margin": ebitda_margins,
                "rule_of_40": (rev_growth or 0) * 100 + (ebitda_margins or 0) * 100,
            }
        except Exception:
            results[ticker] = {k: None for k in [
                "price", "market_cap", "tev", "pct_52w_hi",
                "ntm_ev_ebitda", "ltm_ev_ebitda", "pe_ntm", "pe_ltm",
                "peg", "ntm_rev_growth", "cagr_3y", "gross_margin",
                "ebitda_margin", "rule_of_40",
            ]}
    return results
