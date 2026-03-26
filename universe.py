import pandas as pd
import os

UNIVERSE_PATH = os.path.join(os.path.dirname(__file__), "expanded_services_universe_us_uk.xlsx")

def load_universe() -> pd.DataFrame:
    df = pd.read_excel(UNIVERSE_PATH)
    return df

def get_sectors() -> list:
    df = load_universe()
    return sorted(df["sector"].unique().tolist())

def get_tickers_for_sector(sector: str) -> list:
    df = load_universe()
    return df[df["sector"] == sector]["ticker"].tolist()

def get_all_tickers() -> list:
    df = load_universe()
    return df["ticker"].tolist()

def get_ticker_metadata() -> dict:
    df = load_universe()
    meta = {}
    for _, row in df.iterrows():
        meta[row["ticker"]] = {
            "name": row["name"],
            "sector": row["sector"],
            "sub_sector": row["sub_sector"],
            "country": row["listing_country"],
            "exchange": row["exchange"],
        }
    return meta
