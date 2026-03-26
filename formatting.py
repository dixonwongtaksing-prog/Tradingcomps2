import pandas as pd
import numpy as np


def fmt_multiple(val):
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return ""
    return f"{val:.1f}x"


def fmt_pct(val):
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return ""
    return f"{val * 100:.0f}%"


def fmt_currency(val):
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return ""
    if abs(val) >= 1000:
        return f"${val/1000:.1f}B"
    return f"${val:.0f}M"


def fmt_r40(val):
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return ""
    return f"{val:.0f}"


def fmt_peg(val):
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return ""
    return f"{val:.2f}x"


def apply_display_formats(df: pd.DataFrame) -> pd.DataFrame:
    display = df.copy()

    currency_cols = ["Mkt Cap ($M)", "TEV ($M)"]
    multiple_cols = ["NTM EV/EBITDA", "NTM P/E", "LTM EV/EBITDA", "LTM P/E"]
    pct_cols = ["% 52W Hi", "NTM Rev Gr%", "3Y CAGR", "Gross Mgn", "EBITDA Mgn"]
    r40_cols = ["Rule of 40"]
    peg_cols = ["PEG"]

    for col in currency_cols:
        if col in display.columns:
            display[col] = display[col].apply(fmt_currency)

    for col in multiple_cols:
        if col in display.columns:
            display[col] = display[col].apply(fmt_multiple)

    for col in pct_cols:
        if col in display.columns:
            display[col] = display[col].apply(fmt_pct)

    for col in r40_cols:
        if col in display.columns:
            display[col] = display[col].apply(fmt_r40)

    for col in peg_cols:
        if col in display.columns:
            display[col] = display[col].apply(fmt_peg)

    return display
