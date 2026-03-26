# Trading Comps — Services Universe (US & UK)

A Streamlit-powered trading comparables dashboard covering 349 public companies
across 10 sectors in the US and UK.

## Features

- Left sidebar with sector navigation (10 sectors from the universe)
- Trading comps table matching industry format:
  - Market Data: Mkt Cap, TEV, % 52W Hi
  - NTM Multiples: EV/EBITDA, P/E
  - LTM Multiples: EV/EBITDA, P/E
  - Growth Adjusted: PEG
  - Growth & Margins: NTM Rev Growth, 3Y CAGR, Gross Margin, EBITDA Margin, Rule of 40
- Mean and median rows highlighted at the top
- Charts tab with EV/EBITDA bar, P/E bar, growth vs margin scatter, market cap treemap
- Universe explorer with sub sector breakdown
- CSV download

## Local Setup

```bash
cd trading_comps
pip install -r requirements.txt
streamlit run app.py
```

## Deploy to Streamlit Community Cloud

1. Push this folder to a GitHub repository
2. Go to https://share.streamlit.io
3. Connect your GitHub account
4. Select the repo and set the main file path to `app.py`
5. Click Deploy

The data file `data/expanded_services_universe_us_uk.xlsx` must be committed to the repo.
Market data is fetched live from Yahoo Finance (yfinance) and cached for 1 hour.

## File Architecture

```
trading_comps/
├── app.py                         Main Streamlit entry point
├── requirements.txt
├── .streamlit/
│   └── config.toml                Light theme configuration
├── data/
│   ├── universe.py                Loads company universe from xlsx
│   ├── fetcher.py                 Fetches live market data via yfinance
│   └── expanded_services_universe_us_uk.xlsx
├── logic/
│   ├── multiples.py               Builds comps table and computes stats
│   └── formatting.py              Number formatting helpers
└── components/
    ├── table.py                   Table styling and column group headers
    └── charts.py                  Plotly chart components
```

## Notes

- yfinance NTM estimates are proxied via forward consensus data from Yahoo Finance
- For production use, replace the fetcher with a paid data provider (FactSet, Bloomberg, etc.)
- Data refreshes every hour via Streamlit's @st.cache_data(ttl=3600)
