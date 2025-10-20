import pandas as pd
from core.indicators import sma, rsi, macd

def test_sma_len():
    s = pd.Series(range(1, 51))
    out = sma(s, 20)
    assert len(out) == 50
    assert out.iloc[19] == sum(range(1,21))/20

def test_rsi_bounds():
    s = pd.Series([1]*50)
    out = rsi(s, 14)
    assert (out >= 0).all() and (out <= 100).all()

def test_macd_shapes():
    s = pd.Series(range(1, 100))
    a, b, c = macd(s)
    assert len(a) == len(s) and len(b) == len(s) and len(c) == len(s)
