import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

"""
Inspect one specific breakout day in detail
"""

from broker_moomoo import MoomooBroker
from strategy import get_previous_day_range, has_recent_breakout, align_timeframes
from config import USE_REAL_PAPER_TRADING
from datetime import datetime, timedelta
import pandas as pd

SYMBOL = "TSLA"
TARGET_DATE = "2026-03-18"   # Change this to any breakout day from the diagnostic

def inspect_day():
    print(f"\n{'='*80}")
    print(f"INSPECTING DAY: {TARGET_DATE} — {SYMBOL}")
    print(f"{'='*80}\n")

    broker = MoomooBroker(use_real_paper=USE_REAL_PAPER_TRADING)
    if not broker.connect():
        print("Failed to connect")
        return

    # Fetch more data to have context
    end_date = (datetime.strptime(TARGET_DATE, "%Y-%m-%d") + timedelta(days=5)).strftime("%Y-%m-%d")
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

        day_5m = df_5m[df_5m['time_key'].dt.date == target_day]
        _, _, aligned_5m = align_timeframes(day_daily, day_15m, day_5m)

        if aligned_5m is not None and len(aligned_5m) > 0:
            print("Last 10 Five-Minute Candles:")
            print(aligned_5m[['time_key', 'open', 'high', 'low', 'close']].tail(10).to_string(index=False))
        else:
            print("No 5-minute data aligned")

    broker.disconnect()
    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    inspect_day()
