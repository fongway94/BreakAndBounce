"""
Diagnostic Script - Why is the 5-minute reversal being rejected?
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

"""
Diagnostic Script - Break & Bounce Strategy
Shows why no setups are being found (especially breakout detection)
"""

from broker_moomoo import MoomooBroker
from strategy import (
    get_previous_day_range,
    has_recent_breakout,
    align_timeframes
)
from config import USE_REAL_PAPER_TRADING
from datetime import datetime, timedelta

SYMBOL = "TSLA"          # Change this to test different symbols
DAYS = 60

def diagnose():
    print(f"\n{'='*75}")
    print(f"DIAGNOSTIC — {SYMBOL} | Last {DAYS} days")
    print(f"{'='*75}\n")

    broker = MoomooBroker(use_real_paper=USE_REAL_PAPER_TRADING)
    if not broker.connect():
        print("Failed to connect")
        return

    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=DAYS)).strftime("%Y-%m-%d")

    df_daily = broker.get_historical_data(SYMBOL, start_date, end_date, freq="1D")
    df_15m = broker.get_historical_data(SYMBOL, start_date, end_date, freq="15")
    df_5m = broker.get_historical_data(SYMBOL, start_date, end_date, freq="5")

    if df_daily.empty or df_15m.empty:
        print("Insufficient data")
        return

    trading_days = df_daily['time_key'].dt.date.unique()
    print(f"Total trading days in period: {len(trading_days)}\n")

    breakout_days = 0
    skipped_days = 0

    for day in trading_days:
        day_daily = df_daily[df_daily['time_key'].dt.date == day]
        day_15m = df_15m[df_15m['time_key'].dt.date == day]

        if len(day_daily) < 2 or len(day_15m) < 5:
            skipped_days += 1
            continue

        prev_high, prev_low = get_previous_day_range(day_daily)
        if prev_high is None:
            continue

        direction = has_recent_breakout(day_15m, prev_high, prev_low, lookback=5)

        if direction:
            breakout_days += 1
            print(f"[{day}] Breakout detected → {direction.upper()} | "
                  f"Box: {prev_high:.2f} / {prev_low:.2f} | 15m candles: {len(day_15m)}")

    print(f"\n{'='*75}")
    print(f"Days with enough data     : {len(trading_days) - skipped_days}")
    print(f"Days skipped (low data)   : {skipped_days}")
    print(f"Days with 15m breakout    : {breakout_days}")
    print(f"{'='*75}\n")

    broker.disconnect()


if __name__ == "__main__":
    diagnose()
