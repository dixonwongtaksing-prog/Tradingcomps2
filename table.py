import streamlit as st
import pandas as pd
import numpy as np


COLUMN_GROUPS = {
    "Market Data": {
        "cols": ["Mkt Cap ($M)", "TEV ($M)", "% 52W Hi"],
        "header_color": "#dbeafe",
        "header_text": "#1e40af",
    },
    "NTM Multiples": {
        "cols": ["NTM EV/EBITDA", "NTM P/E"],
        "header_color": "#dcfce7",
        "header_text": "#166534",
    },
    "LTM Multiples": {
        "cols": ["LTM EV/EBITDA", "LTM P/E"],
        "header_color": "#e0e7ef",
        "header_text": "#374151",
    },
    "Growth Adjusted": {
        "cols": ["PEG"],
        "header_color": "#fce7f3",
        "header_text": "#9d174d",
    },
    "Growth & Margins": {
        "cols": ["NTM Rev Gr%", "3Y CAGR", "Gross Mgn", "EBITDA Mgn", "Rule of 40"],
        "header_color": "#fef9c3",
        "header_text": "#854d0e",
    },
}

PCT_COLS_HIGHLIGHT = ["% 52W Hi", "NTM Rev Gr%", "3Y CAGR", "Gross Mgn", "EBITDA Mgn"]
MULTIPLE_COLS = ["NTM EV/EBITDA", "NTM P/E", "LTM EV/EBITDA", "LTM P/E", "PEG"]
R40_COL = "Rule of 40"


def _color_pct(val_str: str) -> str:
    try:
        v = float(val_str.replace("%", "").replace("x", ""))
        if v >= 20:
            return "color: #15803d; font-weight: 600"
        elif v >= 10:
            return "color: #166534"
        elif v < 0:
            return "color: #dc2626"
        return ""
    except Exception:
        return ""


def _color_r40(val_str: str) -> str:
    try:
        v = float(val_str)
        if v >= 40:
            return "color: #15803d; font-weight: 600"
        elif v >= 20:
            return "color: #166534"
        elif v < 0:
            return "color: #dc2626"
        return ""
    except Exception:
        return ""


def style_table(df: pd.DataFrame) -> pd.io.formats.style.Styler:
    def style_cell(val, col):
        if col in PCT_COLS_HIGHLIGHT:
            return _color_pct(str(val))
        if col == R40_COL:
            return _color_r40(str(val))
        return ""

    styled = df.style

    for col in df.columns:
        if col in PCT_COLS_HIGHLIGHT or col == R40_COL:
            styled = styled.applymap(
                lambda v, c=col: style_cell(v, c),
                subset=[col]
            )

    styled = styled.set_properties(**{
        "font-size": "12px",
        "padding": "4px 8px",
        "white-space": "nowrap",
    })

    styled = styled.set_table_styles([
        {"selector": "thead th", "props": [
            ("font-size", "11px"),
            ("font-weight", "700"),
            ("text-align", "center"),
            ("border-bottom", "2px solid #e2e8f0"),
            ("padding", "6px 8px"),
        ]},
        {"selector": "tbody tr:nth-child(even)", "props": [
            ("background-color", "#f8fafc"),
        ]},
        {"selector": "tbody tr:hover", "props": [
            ("background-color", "#eff6ff"),
        ]},
        {"selector": "tbody td", "props": [
            ("text-align", "right"),
            ("border-bottom", "1px solid #f1f5f9"),
        ]},
        {"selector": "tbody td:first-child, tbody td:nth-child(2)", "props": [
            ("text-align", "left"),
        ]},
    ])

    return styled


def render_group_headers(display_cols: list) -> str:
    """Generate HTML for the multi-level column group headers."""
    fixed_cols = ["Company", "Ticker"]
    group_header_cells = f'<th colspan="{len(fixed_cols)}" style="background:#ffffff;border:none;"></th>'

    for group_name, group_info in COLUMN_GROUPS.items():
        visible = [c for c in group_info["cols"] if c in display_cols]
        if not visible:
            continue
        bg = group_info["header_color"]
        color = group_info["header_text"]
        group_header_cells += (
            f'<th colspan="{len(visible)}" style="'
            f'background:{bg};color:{color};font-size:11px;font-weight:700;'
            f'text-align:center;padding:5px 8px;border-left:2px solid #e2e8f0;'
            f'border-bottom:2px solid {color}40;letter-spacing:0.05em;">'
            f'{group_name.upper()}</th>'
        )

    return f"""
    <style>
    .comps-group-header {{ width: 100%; border-collapse: collapse; }}
    .comps-group-header th {{ border: none; }}
    </style>
    <table class="comps-group-header">
    <tr>{group_header_cells}</tr>
    </table>
    """


def render_stats_row(stats: dict, display_cols: list, label: str, key: str) -> dict:
    row = {"Company": label, "Ticker": ""}
    for col in display_cols:
        if col in stats and stats[col][key] is not None:
            val = stats[col][key]
            if "%" in col or col in ["NTM Rev Gr%", "3Y CAGR", "Gross Mgn", "EBITDA Mgn", "% 52W Hi"]:
                row[col] = f"{val * 100:.0f}%" if val <= 1.5 else f"{val:.0f}%"
            elif col in MULTIPLE_COLS:
                row[col] = f"{val:.1f}x"
            elif col == R40_COL:
                row[col] = f"{val:.0f}"
            elif col in ["Mkt Cap ($M)", "TEV ($M)"]:
                row[col] = ""
            else:
                row[col] = f"{val:.1f}"
        else:
            row[col] = ""
    return row
