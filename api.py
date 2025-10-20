# api.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from core.settings import TOP5, VS_CURRENCY, DEFAULT_DAYS
from core.data import fetch_market_chart, fetch_markets_snapshot
from core.signals import compute_signals, simple_risk_flag

app = FastAPI(title="Crypto Signals API", version="0.1.0")

class SignalItem(BaseModel):
    symbol: str
    coin_id: str
    signal: str
    reason: str
    price_usd: float
    rsi14: float
    sma20: float
    sma50: float
    risk: str
    market_cap: float | None
    volume_24h: float | None

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/signals", response_model=list[SignalItem])
def signals(days: int = DEFAULT_DAYS, vs: str = VS_CURRENCY):
    coin_ids = [c["id"] for c in TOP5]
    mkt = fetch_markets_snapshot(coin_ids, vs=vs)
    out = []
    for c in TOP5:
        cid, sym = c["id"], c["symbol"]
        try:
            df = fetch_market_chart(cid, days=days, vs=vs)
            _, snap = compute_signals(df)
            mc = float(mkt.get(cid, {}).get("market_cap") or 0)
            vol = float(mkt.get(cid, {}).get("total_volume") or 0)
            out.append(SignalItem(
                symbol=sym, coin_id=cid, signal=snap["signal"], reason=snap["reason"],
                price_usd=snap["price"], rsi14=snap["RSI14"], sma20=snap["SMA20"], sma50=snap["SMA50"],
                risk=simple_risk_flag(mc, vol),
                market_cap=None if mc == 0 else mc, volume_24h=None if vol == 0 else vol
            ))
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"{cid} failed: {e}")
    return out
