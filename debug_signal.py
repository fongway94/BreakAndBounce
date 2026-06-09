"""
Debug Signal Checker for Break & Bounce Strategy

This script helps validate whether the strategy is detecting setups correctly.
It shows:
- Daily box (previous day high/low)
- 15-minute breakout status
- 5-minute reversal candle check
"""

from broker_moomoo import MoomooBroker
from strategy import (
    get_previous_day_range,
    has_recent_breakout,
    check_reversal_entry,
    align_timeframes,
    get_us_eastern_time
)
from config import USE_REAL_PAPER_TRADING, SYMBOLS
from datetime import datetime, timedelta
import pandas as pd

def debug_symbol(symbol="AAPL"):
    print(f"\n{'='*60}")
    print(f"DEBUG SIGNAL CHECKER — {symbol}")
    print(f"Time: {get_us_eastern_time().strftime('%Y-%m-%d %H:%M:%S')} ET")
    print(f"{'='*60}\n")

    broker = MoomooBroker(use_real_paper=USE_REAL_PAPER_TRADING)

    if not broker.connect():
        print("Failed to connect to Moomoo openD")
        return

    # Fetch last 10 days of data
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")

    print(f"Fetching data from {start_date} to {end_date}...\n")

    df_daily = broker.get_historical_data(symbol, start_date, end_date, freq="1D")
    df_15m = broker.get_historical_data(symbol, start_date, end_date, freq="15")
    df_5m = broker.get_historical_data(symbol, start_date, end_date, freq="5")

    print(f"Daily candles: {len(df_daily)}")
    print(f"15m candles:   {len(df_15m)}")
    print(f"5m candles:    {len(df_5m)}\n")

    if df_daily.empty or df_15m.empty or df_5m.empty:
        print("Insufficient data. Cannot proceed.")
        broker.disconnect()
        return

    # Step 1: Daily Box
    prev_high, prev_low = get_previous_day_range(df_daily)
    if prev_high is None or prev_low is None:
        print("Could not determine daily box (need at least 2 daily candles).")
        broker.disconnect()
        return

    print(f"STEP 1 — DAILY BOX (Previous Day)")
    print(f"  Previous Day High : {prev_high:.2f}")
    print(f"  Previous Day Low  : {prev_low:.2f}\n")

    # Align timeframes
    df_daily, df_15m, df_5m = align_timeframes(df_daily, df_15m, df_5m)
    if df_daily is None:
        print("Could not align timeframes.")
        broker.disconnect()
        return

    # Step 2: 15-minute Breakout
    direction = has_recent_breakout(df_15m, prev_high, prev_low, lookback=5)
    print(f"STEP 2 — 15-MINUTE BREAKOUT CHECK")
    if direction:
        level = prev_high if direction == "bullish" else prev_low
        print(f"  Breakout Detected : {direction.upper()}")
        print(f"  Breakout Level    : {level:.2f}\n")
    else:
        print(f"  No confirmed 15-minute breakout in recent candles.\n")
        broker.disconnect()
        return

    # Step 3: 5-minute Reversal
    print(f"STEP 3 — 5-MINUTE REVERSAL CHECK")
    reversal = check_reversal_entry(df_5m, direction, level)

    if reversal:
        print(f"  Reversal Pattern Detected : {reversal['pattern'].upper()}")
        print(f"  Suggested Entry Price     : {reversal['entry']:.2f}")
        print(f"  Stop Loss Reference       : {reversal['sl_ref']:.2f}")
        print(f"\n  >>> POTENTIAL TRADE SETUP FOUND <<<")
    else:
        print(f"  No valid reversal candle found at the breakout level.\n")

    broker.disconnect()
    print(f"\n{'='*60}")
    print("Debug check completed.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    # You can change the symbol here
    debug_symbol("AAPL")
