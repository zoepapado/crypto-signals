import pandas as pd
from core.signals import compute_signals, simple_risk_flag

def test_signal_output_keys():
    idx = pd.date_range("2024-01-01", periods=60, freq="D")
    df = pd.DataFrame({"price": range(1,61)}, index=idx)
    ind_df, snap = compute_signals(df)
    for k in ["signal","reason","price","RSI14","SMA20","SMA50","MACD","MACD_SIGNAL","MACD_HIST"]:
        assert k in snap

def test_risk_flag():
    assert simple_risk_flag(3e9, 1e8) == "Low"
    assert simple_risk_flag(1e9, 1e8) == "Medium"
    assert simple_risk_flag(4e8, 1e8) == "High"
    assert simple_risk_flag(3e9, 1e6) == "High"
