# core/signals.py
import pandas as pd
from datetime import datetime
from .indicators import sma, rsi, macd
from .settings import RISK_THRESH

def compute_signals(df: pd.DataFrame):
    out = df.copy()
    out["SMA20"] = sma(out["price"], 20)
    out["SMA50"] = sma(out["price"], 50)
    out["RSI14"] = rsi(out["price"], 14)
    out["MACD"], out["MACD_SIGNAL"], out["MACD_HIST"] = macd(out["price"], 12, 26, 9)

    latest = out.iloc[-1]
    if latest["RSI14"] < 30 and latest["price"] > latest["SMA20"] and latest["SMA20"] > latest["SMA50"]:
        signal = "BUY"
        reason = "RSI<30 (oversold) + price>SMA20 & SMA20>SMA50 (uptrend)"
    elif (latest["RSI14"] > 70) or (latest["price"] < latest["SMA20"] and latest["MACD"] < latest["MACD_SIGNAL"]):
        signal = "SELL"
        reason = "RSI>70 (overbought) or price<SMA20 with bearish MACD crossover"
    else:
        signal = "HOLD"
        reason = "Neutral: no strong edge between momentum and mean reversion"

    snapshot = {
        "signal": signal,
        "reason": reason,
        "price": float(latest["price"]),
        "RSI14": float(latest["RSI14"]),
        "SMA20": float(latest["SMA20"]),
        "SMA50": float(latest["SMA50"]),
        "MACD": float(latest["MACD"]),
        "MACD_SIGNAL": float(latest["MACD_SIGNAL"]),
        "MACD_HIST": float(latest["MACD_HIST"]),
    }
    return out, snapshot

def simple_risk_flag(mcap: float, vol24: float) -> str:
    if mcap == 0:
        return "Unknown"
    if (mcap < RISK_THRESH.high_risk_cap) or (vol24 < RISK_THRESH.low_vol24):
        return "High"
    if mcap < RISK_THRESH.low_cap:
        return "Medium"
    return "Low"

def historical_buy_example(df: pd.DataFrame):
    d = df.copy()
    d["SMA20"] = sma(d["price"], 20)
    d["SMA50"] = sma(d["price"], 50)
    d["RSI14"] = rsi(d["price"], 14)

    d = d.iloc[:-1]  # exclude current bar
    mask = (d["RSI14"] < 30) & (d["price"] > d["SMA20"]) & (d["SMA20"] > d["SMA50"])
    if not mask.any():
        return None

    last_idx = d[mask].index.max()
    if last_idx is None:
        return None

    entry = float(d.loc[last_idx, "price"])

    def fwd(days):
        cut = d.loc[d.index >= (last_idx + pd.Timedelta(days=days))]
        if cut.empty:
            return None
        end = float(cut.iloc[0]["price"])
        return round((end / entry - 1.0) * 100.0, 2)

    return {
        "signal_time": last_idx.strftime("%Y-%m-%d"),
        "entry_price": entry,
        "fwd_7d_pct": fwd(7),
        "fwd_30d_pct": fwd(30),
    }
