import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

"""
Improved Break & Bounce Backtest - Focused on March 2026 (NFLX)
Matches the exact example shown in the video (March 30-31, 2026)
"""
"""
Break & Bounce Backtest - Exact Video Example Dates
Focus: March 30-31, 2026 (NFLX)
"""

from broker_moomoo import MoomooBroker
from strategy import (
    get_previous_day_range,
    has_recent_breakout,
    check_reversal_entry,
    align_timeframes
)
from config import USE_REAL_PAPER_TRADING
from datetime import datetime, timedelta, time as dt_time
import pandas as pd

SYMBOL = "NFLX"
START_DATE = "2026-03-25"      # A few days before
END_DATE = "2026-04-05"        # A few days after

def run_backtest():
    print(f"\n{'='*90}")
    print(f"BACKTEST — Break & Bounce (NFLX) | Exact Video Period")
    print(f"Date Range: {START_DATE} to {END_DATE}")
    print(f"{'='*90}\n")

    broker = MoomooBroker(use_real_paper=USE_REAL_PAPER_TRADING)
    if not broker.connect():
        print("Failed to connect")
        return

    df_daily = broker.get_historical_data(SYMBOL, START_DATE, END_DATE, freq="1D")
    df_15m = broker.get_historical_data(SYMBOL, START_DATE, END_DATE, freq="15")
    df_5m = broker.get_historical_data(SYMBOL, START_DATE, END_DATE, freq="5")

    trading_days = df_daily['time_key'].dt.date.unique()
    print(f"Total trading days in range: {len(trading_days)}\n")

    trades_found = 0
    market_open = dt_time(9, 30)

    for day in trading_days:
        day_daily = df_daily[df_daily['time_key'].dt.date <= day]
        day_15m = df_15m[df_15m['time_key'].dt.date == day]
        day_5m = df_5m[df_5m['time_key'].dt.date == day]

        if len(day_daily) < 2 or len(day_15m) < 5 or len(day_5m) < 10:
            continue

        prev_high, prev_low = get_previous_day_range(day_daily)
        if prev_high is None:
            continue

        direction = has_recent_breakout(day_15m, prev_high, prev_low)
        if direction is None:
            continue

        level = prev_high if direction == "bullish" else prev_low
        _, _, aligned_5m = align_timeframes(day_daily, day_15m, day_5m)

        if aligned_5m is None or len(aligned_5m) < 5:
            continue

        # Check for reversal
        reversal = check_reversal_entry(aligned_5m, direction, level)

        print(f"[{day}] 15m Breakout: {direction.upper()} | Level: {level:.2f} | "
              f"Reversal Detected: {bool(reversal)}")

        if reversal:
            trades_found += 1
            print(f"   >>> VALID SETUP FOUND: {reversal['pattern']}")

    print(f"\n{'='*90}")
    print(f"Total valid setups found: {trades_found}")
    print(f"{'='*90}\n")

    broker.disconnect()


if __name__ == "__main__":
    run_backtest()
