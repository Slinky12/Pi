from __future__ import annotations
from datetime import datetime, timezone
from typing import Dict, List, Optional

import pandas as pd
import streamlit as st

try:
    import yfinance as yf
except Exception:
    yf = None


def _fmt_price(x: Optional[float]) -> str:
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return "—"
    return f"${x:,.2f}"


def _fmt_change_abs(x: Optional[float]) -> str:
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return "—"
    sign = "+" if x >= 0 else ""
    return f"{sign}{x:,.2f}"


def _fmt_change_pct(x: Optional[float]) -> str:
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return "—"
    sign = "+" if x >= 0 else ""
    return f"{sign}{x*100:,.2f}%"


@st.cache_data(ttl=300, show_spinner=False)
def get_quotes(tickers: List[str], ttl_seconds: int = 300) -> Dict[str, Dict]:
    """
    Returns: {TICKER: {price, change_abs, change_pct, asof}}
    Uses yfinance if available and internet works.
    """
    if yf is None:
        return {}

    out: Dict[str, Dict] = {}
    # Use yf.download for efficiency
    try:
        data = yf.download(
            tickers=tickers,
            period="2d",
            interval="1m",
            group_by="ticker",
            auto_adjust=False,
            threads=True,
            progress=False,
        )
    except Exception:
        return {}

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    for t in tickers:
        try:
            # download output differs for single vs multi ticker
            if len(tickers) == 1:
                close = data["Close"].dropna()
            else:
                close = data[t]["Close"].dropna()

            if close.empty:
                continue
            price = float(close.iloc[-1])

            # Previous close from earlier day (approx)
            prev = float(close.iloc[0])
            change_abs = price - prev
            change_pct = (change_abs / prev) if prev else None

            out[t] = {
                "price": _fmt_price(price),
                "change_abs": _fmt_change_abs(change_abs),
                "change_pct": _fmt_change_pct(change_pct),
                "asof": now,
            }
        except Exception:
            continue
    return out


@st.cache_data(ttl=300, show_spinner=False)
def get_sparklines(tickers: List[str], ttl_seconds: int = 300) -> Dict[str, pd.Series]:
    """
    Returns tiny series for last ~1 day minute closes.
    """
    if yf is None:
        return {}

    out: Dict[str, pd.Series] = {}
    try:
        data = yf.download(
            tickers=tickers,
            period="1d",
            interval="5m",
            group_by="ticker",
            auto_adjust=False,
            threads=True,
            progress=False,
        )
    except Exception:
        return {}

    for t in tickers:
        try:
            if len(tickers) == 1:
                close = data["Close"].dropna()
            else:
                close = data[t]["Close"].dropna()
            if close.empty:
                continue
            out[t] = close
        except Exception:
            continue
    return out
