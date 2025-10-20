# core/data.py
import requests
import pandas as pd
from datetime import datetime
from streamlit.runtime.caching import cache_data  # safe import even if Streamlit not running
from .settings import VS_CURRENCY, CACHE_TTL_SEC

@cache_data(ttl=CACHE_TTL_SEC)
def fetch_market_chart(coin_id: str, days: int, vs: str = VS_CURRENCY) -> pd.DataFrame:
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {"vs_currency": vs, "days": days, "interval": "hourly" if days <= 30 else "daily"}
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()

    def _to_df(key):
        arr = data.get(key, [])
        df = pd.DataFrame(arr, columns=["ts", key])
        df["time"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
        df = df.drop(columns=["ts"]).set_index("time")
        return df

    p = _to_df("prices").rename(columns={"prices": "price"})
    m = _to_df("market_caps").rename(columns={"market_caps": "market_cap"})
    v = _to_df("total_volumes").rename(columns={"total_volumes": "volume"})
    return p.join([m, v], how="outer").sort_index().dropna()

@cache_data(ttl=CACHE_TTL_SEC)
def fetch_markets_snapshot(coin_ids, vs: str = VS_CURRENCY):
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {"vs_currency": vs, "ids": ",".join(coin_ids)}
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    arr = r.json()
    out = {}
    for item in arr:
        out[item["id"]] = {
            "market_cap": float(item.get("market_cap") or 0),
            "total_volume": float(item.get("total_volume") or 0)
        }
    return out
