"""
Diagnostic Script - Why is the 5-minute reversal being rejected?
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

"""
Detailed Diagnostic - Why reversal is rejected on breakout days
"""

from broker_moomoo import MoomooBroker
from strategy import (
    get_previous_day_range,
    has_recent_breakout,
    check_reversal_entry,
    align_timeframes,
    has_preceding_move,
    is_hammer,
    is_inverted_hammer,
    is_engulfing
)
from config import USE_REAL_PAPER_TRADING
from datetime import datetime, timedelta

SYMBOL = "TSLA"
DAYS = 90

def diagnose():
    print(f"\n{'='*85}")
    print(f"DETAILED REVERSAL DIAGNOSTIC — {SYMBOL}")
    print(f"{'='*85}\n")

    broker = MoomooBroker(use_real_paper=USE_REAL_PAPER_TRADING)
    if not broker.connect():
        print("Failed to connect")
        return

    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=DAYS)).strftime("%Y-%m-%d")

    df_daily = broker.get_historical_data(SYMBOL, start_date, end_date, freq="1D")
    df_15m = broker.get_historical_data(SYMBOL, start_date, end_date, freq="15")
    df_5m = broker.get_historical_data(SYMBOL, start_date, end_date, freq="5")

    trading_days = df_daily['time_key'].dt.date.unique()
    breakout_days = []

    for i, day in enumerate(trading_days):
        if i < 1:
            continue

        day_daily = df_daily[df_daily['time_key'].dt.date <= day]
        prev_high, prev_low = get_previous_day_range(day_daily)
        if prev_high is None:
            continue

        day_15m = df_15m[df_15m['time_key'].dt.date == day]
        day_5m = df_5m[df_5m['time_key'].dt.date == day]

        if len(day_15m) < 5 or len(day_5m) < 10:
            continue

        direction = has_recent_breakout(day_15m, prev_high, prev_low)
        if direction is None:
            continue

        level = prev_high if direction == "bullish" else prev_low
        _, _, aligned_5m = align_timeframes(day_daily, day_15m, day_5m)

        if aligned_5m is None or len(aligned_5m) < 5:
            continue

        breakout_days.append(day)

        # Detailed reversal check
        current = aligned_5m.iloc[-1]
        tolerance = level * 0.0015
        near_level = (abs(current['low'] - level) < tolerance or
                      abs(current['high'] - level) < tolerance or
                      abs(current['close'] - level) < tolerance)

        preceding_ok = has_preceding_move(aligned_5m, direction)

        is_h = is_hammer(current) if direction == "bullish" else False
        is_inv = is_inverted_hammer(current) if direction == "bearish" else False
        is_eng = is_engulfing(aligned_5m.iloc[-2], current, direction) if len(aligned_5m) >= 2 else False

        print(f"[{day}] Breakout: {direction.upper()} | Near level: {near_level} | "
              f"Preceding move: {preceding_ok} | Hammer: {is_h} | Engulfing: {is_eng}")

    print(f"\n{'='*85}")
    print(f"Total days with 15m breakout : {len(breakout_days)}")
    print(f"{'='*85}\n")

    broker.disconnect()


if __name__ == "__main__":
    diagnose()
