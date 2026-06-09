import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

"""
Inspect one specific breakout day in detail
"""
"""
Inspect one specific breakout day - Only shows candles within first 2.5 hours
"""

from broker_moomoo import MoomooBroker
from strategy import get_previous_day_range, has_recent_breakout, align_timeframes
from config import USE_REAL_PAPER_TRADING
from datetime import datetime, timedelta, time as dt_time
import pandas as pd

SYMBOL = "TSLA"
TARGET_DATE = "2026-03-23"   # Change this to any breakout day

def inspect_day():
    print(f"\n{'='*85}")
    print(f"INSPECTING DAY: {TARGET_DATE} — {SYMBOL} (First 2.5 Hours Only)")
    print(f"{'='*85}\n")

    broker = MoomooBroker(use_real_paper=USE_REAL_PAPER_TRADING)
    if not broker.connect():
        print("Failed to connect")
        return

    end_date = (datetime.strptime(TARGET_DATE, "%Y-%m-%d") + timedelta(days=3)).strftime("%Y-%m-%d")
    start_date = (datetime.strptime(TARGET_DATE, "%Y-%m-%d") - timedelta(days=10)).strftime("%Y-%m-%d")

    df_daily = broker.get_historical_data(SYMBOL, start_date, end_date, freq="1D")
    df_15m = broker.get_historical_data(SYMBOL, start_date, end_date, freq="15")
    df_5m = broker.get_historical_data(SYMBOL, start_date, end_date, freq="5")

    target_day = pd.to_datetime(TARGET_DATE).date()

    day_daily = df_daily[df_daily['time_key'].dt.date <= target_day]
    prev_high, prev_low = get_previous_day_range(day_daily)

    if prev_high is None:
        print("Not enough daily data")
        return

    print(f"Daily Box (Previous Day): High = {prev_high:.2f} | Low = {prev_low:.2f}\n")

    day_15m = df_15m[df_15m['time_key'].dt.date == target_day]
    direction = has_recent_breakout(day_15m, prev_high, prev_low, lookback=5)

    print(f"15-minute Breakout: {direction}\n")

    if direction:
        level = prev_high if direction == "bullish" else prev_low
        print(f"Breakout Level: {level:.2f}\n")

        # Filter 5-minute candles to only first 2.5 hours (9:30 - 12:00)
        day_5m = df_5m[df_5m['time_key'].dt.date == target_day]
        start_time = dt_time(9, 30)
        end_time = dt_time(12, 0)

        filtered_5m = day_5m[(day_5m['time_key'].dt.time >= start_time) & 
                             (day_5m['time_key'].dt.time <= end_time)]

        _, _, aligned_5m = align_timeframes(day_daily, day_15m, filtered_5m)

        if aligned_5m is not None and len(aligned_5m) > 0:
            print(f"Five-Minute Candles (9:30 - 12:00 ET) — {len(aligned_5m)} candles:")
            print(aligned_5m[['time_key', 'open', 'high', 'low', 'close']].to_string(index=False))
        else:
            print("No 5-minute data within the first 2.5 hours")

    broker.disconnect()
    print(f"\n{'='*85}\n")


if __name__ == "__main__":
    inspect_day()
