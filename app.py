# app.py
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from datetime import datetime
from core.settings import TOP5, TOP10, VS_CURRENCY, DEFAULT_DAYS
from core.data import fetch_market_chart, fetch_markets_snapshot
from core.signals import compute_signals, simple_risk_flag, historical_buy_example

st.set_page_config(page_title="Daily Crypto Signal Dashboard — Beginner Friendly", page_icon="📈", layout="wide")

# --- Sidebar
st.sidebar.header("Settings")
beginner_mode = st.sidebar.checkbox("Beginner Mode", value=True)
days = st.sidebar.slider("History window (days)", 90, 730, DEFAULT_DAYS, step=10)
show_rsi = st.sidebar.checkbox("Show RSI panel", value=True)
show_macd = st.sidebar.checkbox("Show MACD panel", value=True)
if st.sidebar.button("🔄 Refresh"):
    fetch_market_chart.clear()
    fetch_markets_snapshot.clear()
    st.experimental_rerun()

coins_src = TOP5 if beginner_mode else TOP10
labels = [f'{c["symbol"]} ({c["id"]})' for c in coins_src]
id_by_label = {f'{c["symbol"]} ({c["id"]})': c["id"] for c in coins_src}
selected = st.sidebar.multiselect("Coins", labels, default=labels[:3])
if not selected:
    st.info("Select at least one coin in the sidebar to begin.")
    st.stop()

picked = [{"id": id_by_label[s], "symbol": s.split(" ")[0]} for s in selected]
coin_ids = [p["id"] for p in picked]

# --- Header
st.title("📈 Daily Crypto Signal Dashboard")
st.caption("Rules-based signals (RSI, SMA, MACD) with plain-English guidance. **Educational only — not financial advice.**")

if beginner_mode:
    with st.expander("📘 Beginner quick-start", expanded=True):
        st.markdown("""
- **BUY** = indicators suggest a possible opportunity. Not a guarantee.
- **HOLD** = neutral.
- **SELL** = risk may be higher right now.
- Beginners may prefer larger, more liquid coins (BTC/ETH).
- Avoid tiny coins with low volume; they’re easier to manipulate.
- Only risk what you can afford to lose; crypto is very volatile.
""")

# --- Risk snapshot
try:
    mkt = fetch_markets_snapshot(coin_ids, vs=VS_CURRENCY)
except Exception as e:
    mkt = {}
    st.warning(f"Could not fetch market caps/volumes ({e}).")

# --- Build signals table
rows, series_cache = [], {}
for p in picked:
    cid, sym = p["id"], p["symbol"]
    try:
        df = fetch_market_chart(cid, days=days, vs=VS_CURRENCY)
        series_cache[cid] = df
        ind_df, snap = compute_signals(df)

        mcap = mkt.get(cid, {}).get("market_cap", 0.0)
        vol24 = mkt.get(cid, {}).get("total_volume", 0.0)
        risk = simple_risk_flag(mcap, vol24)

        rows.append({
            "Symbol": sym,
            "Coin ID": cid,
            "Signal": snap["signal"],
            "Reason": snap["reason"],
            "Price (USD)": round(snap["price"], 4),
            "RSI(14)": round(snap["RSI14"], 2),
            "SMA20": round(snap["SMA20"], 2),
            "SMA50": round(snap["SMA50"], 2),
            "Risk": risk,
            "Mkt Cap ($)": None if not mcap else f"{mcap:,.0f}",
            "24h Vol ($)": None if not vol24 else f"{vol24:,.0f}",
            "Updated (UTC)": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        })
    except Exception as e:
        rows.append({
            "Symbol": sym, "Coin ID": cid, "Signal": "ERROR",
            "Reason": f"{e}", "Price (USD)": None, "RSI(14)": None,
            "SMA20": None, "SMA50": None, "Risk": "Unknown",
            "Mkt Cap ($)": None, "24h Vol ($)": None,
            "Updated (UTC)": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        })

# order & show
order = {"BUY": 0, "HOLD": 1, "SELL": 2, "ERROR": 3}
df_table = pd.DataFrame(rows)
df_table["__o"] = df_table["Signal"].map(lambda x: order.get(x, 9))
df_table = df_table.sort_values(["__o", "Symbol"]).drop(columns=["__o"])

st.subheader("Today’s Signals")
st.dataframe(df_table, use_container_width=True)

# --- CSV + JSON export
csv_bytes = df_table.to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Download CSV", data=csv_bytes, file_name="signals_today.csv", mime="text/csv")

json_payload = df_table.to_dict(orient="records")
st.download_button("⬇️ Download JSON", data=json.dumps(json_payload, ensure_ascii=False, indent=2).encode("utf-8"),
                   file_name="signals_today.json", mime="application/json")

with st.expander("ℹ️ Glossary & FAQs"):
    st.markdown("""
**RSI** — momentum from 0–100. Below 30 often called oversold; above 70 overbought.  
**SMA** — average price. SMA20>SMA50 = short-term uptrend bias.  
**MACD** — momentum crossover; MACD < Signal often means weakening momentum.

**Common mistakes**  
- Buying because of hype/shills.  
- Treating indicators as guarantees.  
- Ignoring small-cap / low-volume risk.  
- Going all-in instead of small, staged entries.
""")

st.markdown("---")
st.subheader("Charts & Historical Context")

for p in picked:
    cid, sym = p["id"], p["symbol"]
    if cid not in series_cache:
        continue
    df = series_cache[cid].copy()
    ind_df, snap = compute_signals(df)

    c1, c2 = st.columns([3, 2], gap="large")
    with c1:
        st.markdown(f"### {sym} — Price & SMA")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=ind_df.index, y=ind_df["price"], name="Price", mode="lines"))
        fig.add_trace(go.Scatter(x=ind_df.index, y=ind_df["SMA20"], name="SMA20", mode="lines"))
        fig.add_trace(go.Scatter(x=ind_df.index, y=ind_df["SMA50"], name="SMA50", mode="lines"))
        fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=340)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown(f"### {sym} — Snapshot")
        st.metric("Signal", snap["signal"])
        st.metric("Price (USD)", f'{snap["price"]:.2f}')
        st.metric("RSI(14)", f'{snap["RSI14"]:.1f}')
        st.metric("SMA20 vs SMA50", "Above" if snap["SMA20"] >= snap["SMA50"] else "Below")
        st.caption(f"Reason: {snap['reason']}")

        ex = historical_buy_example(df)
        with st.expander("🕓 Historical example (last BUY-like setup)"):
            if ex is None:
                st.write("No recent BUY-like setup found.")
            else:
                st.write(f"Signal date: **{ex['signal_time']}**, Entry: **${ex['entry_price']:.2f}**")
                st.write(f"Forward 7d: **{ex['fwd_7d_pct']}%**  |  30d: **{ex['fwd_30d_pct']}%**")
                st.caption("Past performance ≠ future results.")
