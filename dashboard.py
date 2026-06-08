import streamlit as st
import pandas as pd
from datetime import datetime
import time as time_module
import plotly.express as px
from config import TRADING_MODE, SYMBOLS, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, MAX_DAILY_LOSS, USE_REAL_PAPER_TRADING
from logger import TradeLogger
from notifier import TelegramNotifier
from broker_moomoo import MoomooBroker

st.set_page_config(page_title="Break & Bounce Bot", layout="wide")
st.title("🚀 Break & Bounce Trading Bot")

st.sidebar.header("🖥️ System Status")
st.sidebar.metric("Current Mode", TRADING_MODE.upper())
st.sidebar.metric("Symbols Tracked", len(SYMBOLS))
st.sidebar.metric("Current Time", datetime.now().strftime("%H:%M:%S"))
st.sidebar.metric("Daily Loss Limit", f"${MAX_DAILY_LOSS}")

st.sidebar.header("⚙️ Controls")
if st.sidebar.button("Refresh"):
    st.rerun()

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("📈 Performance")
    logger = TradeLogger()
    history = logger.get_trade_history()          # ← Fixed here
    if not history.empty:
        total_trades = len(history)
        st.metric("Total Trades", total_trades)
    else:
        st.info("No trades yet")

with col2:
    st.subheader("📊 Live Status")
    st.write(f"**Mode:** {TRADING_MODE}")
    st.write(f"**Trading Window:** First 150 minutes")

with col3:
    st.subheader("📱 Alerts")
    if st.button("Send Test Telegram"):
        notifier = TelegramNotifier(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
        notifier.notify_status("Test from dashboard")
        st.success("Test sent!")

# ==================== CURRENT POSITIONS SECTION ====================
st.subheader("📍 Current Account Positions (Live from Moomoo)")

try:
    broker = MoomooBroker(use_real_paper=USE_REAL_PAPER_TRADING)
    if broker.connect():
        positions = broker.get_open_positions_summary()
        if positions:
            pos_df = pd.DataFrame(positions)
            pos_df = pos_df[["symbol", "qty", "cost_price", "nominal_price", "unrealized_pl", "market_val"]]
            st.dataframe(pos_df, use_container_width=True)

            total_value = sum(p["market_val"] for p in positions)
            total_pl = sum(p["unrealized_pl"] for p in positions)
            st.metric("Total Position Value", f"${total_value:,.2f}")
            st.metric("Total Unrealized P&L", f"${total_pl:,.2f}", delta=f"{total_pl:,.2f}")
        else:
            st.info("No open positions in the account.")
        broker.disconnect()
    else:
        st.warning("Could not connect to Moomoo openD to fetch positions.")
except Exception as e:
    st.error(f"Error fetching positions: {e}")
    st.info("Make sure openD is running and credentials are set.")

st.subheader("📜 Recent Trade Log")
if not history.empty:
    st.dataframe(history.tail(15), use_container_width=True)
else:
    st.write("No trades logged yet.")

st.caption("Dashboard v2.0")
