"""
Diagnostic Script - Why is the 5-minute reversal being rejected?
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

SYMBOL = "TSLA"          # Change this to test different symbols
DAYS = 60

def diagnose_reversal():
    print(f"\n{'='*70}")
    print(f"REVERSAL DIAGNOSTIC — {SYMBOL}")
    print(f"{'='*70}\n")

    broker = MoomooBroker(use_real_paper=USE_REAL_PAPER_TRADING)
    if not broker.connect():
        print("Failed to connect")
        return

    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=DAYS)).strftime("%Y-%m-%d")

    df_daily = broker.get_historical_data(SYMBOL, start_date, end_date, freq="1D")
    df_15m = broker.get_historical_data(SYMBOL, start_date, end_date, freq="15")
    df_5m = broker.get_historical_data(SYMBOL, start_date, end_date, freq="5")

    if df_daily.empty or df_15m.empty or df_5m.empty:
        print("Insufficient data")
        return

    trading_days = df_daily['time_key'].dt.date.unique()
    print(f"Checking {len(trading_days)} trading days...\n")

    found_potential = 0

    for day in trading_days:
        day_daily = df_daily[df_daily['time_key'].dt.date == day]
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

        # Align timeframes
        _, _, aligned_5m = align_timeframes(day_daily, day_15m, day_5m)
        if aligned_5m is None or len(aligned_5m) < 5:
            continue

        found_potential += 1

        # Check reversal
        reversal = check_reversal_entry(aligned_5m, direction, level)

        if reversal:
            print(f"[{day}] VALID SETUP FOUND → {reversal['pattern']}")
        else:
            # Diagnose why it failed
            current = aligned_5m.iloc[-1]
            tolerance = level * 0.0015
            near_level = (abs(current['low'] - level) < tolerance or
                          abs(current['high'] - level) < tolerance or
                          abs(current['close'] - level) < tolerance)

            preceding_ok = has_preceding_move(aligned_5m, direction)

            print(f"[{day}] No reversal | Near level: {near_level} | Preceding move: {preceding_ok}")

    print(f"\nTotal days with breakout: {found_potential}")
    broker.disconnect()


if __name__ == "__main__":
    diagnose_reversal()
