# core/settings.py
from dataclasses import dataclass

VS_CURRENCY = "usd"

TOP10 = [
    {"id": "bitcoin",        "symbol": "BTC"},
    {"id": "ethereum",       "symbol": "ETH"},
    {"id": "solana",         "symbol": "SOL"},
    {"id": "binancecoin",    "symbol": "BNB"},
    {"id": "ripple",         "symbol": "XRP"},
    {"id": "cardano",        "symbol": "ADA"},
    {"id": "dogecoin",       "symbol": "DOGE"},
    {"id": "tron",           "symbol": "TRX"},
    {"id": "polkadot",       "symbol": "DOT"},
    {"id": "litecoin",       "symbol": "LTC"},
]
TOP5 = TOP10[:5]

DEFAULT_DAYS = 240
CACHE_TTL_SEC = 60 * 60  # 1 hour

@dataclass(frozen=True)
class RiskThresholds:
    low_cap: float = 2e9     # < $2B = Medium
    high_risk_cap: float = 5e8  # < $500M = High
    low_vol24: float = 5e7   # < $50M 24h volume = High

RISK_THRESH = RiskThresholds()
