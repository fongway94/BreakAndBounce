"""
Diagnostic Script - Why is the 5-minute reversal being rejected?
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

"""
Improved Diagnostic Script - Uses full dataset properly
"""

from broker_moomoo import MoomooBroker
from strategy import (
    get_previous_day_range,
    has_recent_breakout,
    check_reversal_entry,
    align_timeframes
)
from config import USE_REAL_PAPER_TRADING
from datetime import datetime, timedelta

SYMBOL = "TSLA"
DAYS = 90

def diagnose():
    print(f"\n{'='*80}")
    print(f"IMPROVED DIAGNOSTIC — {SYMBOL} | Last {DAYS} days")
    print(f"{'='*80}\n")

    broker = MoomooBroker(use_real_paper=USE_REAL_PAPER_TRADING)
    if not broker.connect():
        print("Failed to connect")
        return

    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=DAYS)).strftime("%Y-%m-%d")

    # Fetch full data (no per-day slicing yet)
    df_daily = broker.get_historical_data(SYMBOL, start_date, end_date, freq="1D")
    df_15m = broker.get_historical_data(SYMBOL, start_date, end_date, freq="15")
    df_5m = broker.get_historical_data(SYMBOL, start_date, end_date, freq="5")

    if df_daily.empty or df_15m.empty or df_5m.empty:
        print("Insufficient data")
        return

    print(f"Daily candles: {len(df_daily)} | 15m: {len(df_15m)} | 5m: {len(df_5m)}\n")

    trading_days = df_daily['time_key'].dt.date.unique()
    breakout_count = 0
    reversal_count = 0

    for i, day in enumerate(trading_days):
        if i < 1:
            continue  # Need at least 1 previous day for the box

        # Get daily data up to current day
        day_daily = df_daily[df_daily['time_key'].dt.date <= day]

        prev_high, prev_low = get_previous_day_range(day_daily)
        if prev_high is None:
            continue

        # Get 15m and 5m data for this day
        day_15m = df_15m[df_15m['time_key'].dt.date == day]
        day_5m = df_5m[df_5m['time_key'].dt.date == day]

        if len(day_15m) < 5 or len(day_5m) < 10:
            continue

        direction = has_recent_breakout(day_15m, prev_high, prev_low)
        if direction is None:
            continue

        breakout_count += 1
        level = prev_high if direction == "bullish" else prev_low

        # Align and check reversal
        _, _, aligned_5m = align_timeframes(day_daily, day_15m, day_5m)
        if aligned_5m is None:
            continue

        reversal = check_reversal_entry(aligned_5m, direction, level)
        if reversal:
            reversal_count += 1
            print(f"[{day}] VALID SETUP → {reversal['pattern'].upper()} | {direction}")

    print(f"\n{'='*80}")
    print(f"Days with 15m breakout : {breakout_count}")
    print(f"Days with valid reversal: {reversal_count}")
    print(f"{'='*80}\n")

    broker.disconnect()


if __name__ == "__main__":
    diagnose()
