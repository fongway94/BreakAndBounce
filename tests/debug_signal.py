"""
Debug Signal Checker for Break & Bounce Strategy

This script helps validate whether the strategy is detecting setups correctly.
It shows:
- Daily box (previous day high/low)
- 15-minute breakout status
- 5-minute reversal candle check
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from broker_moomoo import MoomooBroker
from strategy import (
    get_previous_day_range,
    has_recent_breakout,
    check_reversal_entry,
    align_timeframes,
    get_us_eastern_time
)
from config import USE_REAL_PAPER_TRADING
from datetime import datetime, timedelta
import pandas as pd

def debug_symbol(broker, symbol):
    print(f"\n{'='*60}")
    print(f"DEBUG SIGNAL CHECKER — {symbol}")
    print(f"{'='*60}\n")

    # Fetch last 10 days of data
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")

    df_daily = broker.get_historical_data(symbol, start_date, end_date, freq="1D")
    df_15m = broker.get_historical_data(symbol, start_date, end_date, freq="15")
    df_5m = broker.get_historical_data(symbol, start_date, end_date, freq="5")

    print(f"Daily candles: {len(df_daily)}  |  15m: {len(df_15m)}  |  5m: {len(df_5m)}")

    if df_daily.empty or df_15m.empty or df_5m.empty:
        print("  → Insufficient data. Skipping.\n")
        return

    # Step 1: Daily Box
    prev_high, prev_low = get_previous_day_range(df_daily)
    if prev_high is None or prev_low is None:
        print("  → Could not determine daily box.\n")
        return

    print(f"  Daily Box       : High={prev_high:.2f}  Low={prev_low:.2f}")

    # Align timeframes
    df_daily, df_15m, df_5m = align_timeframes(df_daily, df_15m, df_5m)
    if df_daily is None:
        print("  → Could not align timeframes.\n")
        return

    # Step 2: 15-minute Breakout
    direction = has_recent_breakout(df_15m, prev_high, prev_low, lookback=5)
    if not direction:
        print("  → No 15-minute breakout detected.\n")
        return

    level = prev_high if direction == "bullish" else prev_low
    print(f"  15m Breakout    : {direction.upper()} at {level:.2f}")

    # Step 3: 5-minute Reversal
    reversal = check_reversal_entry(df_5m, direction, level)

    if reversal:
        print(f"  5m Reversal     : {reversal['pattern'].upper()}")
        print(f"  Suggested Entry : {reversal['entry']:.2f}")
        print(f"  Stop Loss Ref   : {reversal['sl_ref']:.2f}")
        print(f"\n  >>> POTENTIAL TRADE SETUP FOUND <<<\n")
    else:
        print("  → No valid 5-minute reversal candle.\n")


if __name__ == "__main__":
    from config import SYMBOLS

    print(f"Checking all {len(SYMBOLS)} symbols in your config...\n")

    broker = MoomooBroker(use_real_paper=USE_REAL_PAPER_TRADING)

    if not broker.connect():
        print("Failed to connect to Moomoo openD")
    else:
        for symbol in SYMBOLS:
            debug_symbol(broker, symbol)

        broker.disconnect()
        print("\nAll symbols checked.")
