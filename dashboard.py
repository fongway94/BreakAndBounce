import streamlit as st
import pandas as pd
from datetime import datetime
import time as time_module
import plotly.express as px
from config import TRADING_MODE, SYMBOLS, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, MAX_DAILY_LOSS
from logger import TradeLogger
from notifier import TelegramNotifier

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
    history = logger.get_trade_history()
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

st.subheader("📜 Recent Trade Log")
if not history.empty:
    st.dataframe(history.tail(15), use_container_width=True)
else:
    st.write("No trades logged yet.")

st.caption("Dashboard v2.0")