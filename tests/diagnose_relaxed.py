"""
Relaxed Diagnostic Version - Testing less strict conditions
"""

from broker_moomoo import MoomooBroker
from strategy import (
    get_previous_day_range,
    has_recent_breakout,
    align_timeframes
)
from config import USE_REAL_PAPER_TRADING
from datetime import datetime, timedelta
import pandas as pd

SYMBOL = "TSLA"
DAYS = 90

def has_preceding_move_relaxed(df_5m, direction, lookback=3):
    """Relaxed version - only needs at least 1 candle in the correct direction"""
    if len(df_5m) < lookback + 1:
        return False

    recent = df_5m.iloc[-(lookback + 1):-1]

    if direction == "bullish":
        red_count = sum(1 for _, c in recent.iterrows() if c['close'] < c['open'])
        return red_count >= 1
    else:
        green_count = sum(1 for _, c in recent.iterrows() if c['close'] > c['open'])
        return green_count >= 1


def check_reversal_relaxed(df_5m, direction, level):
    """Relaxed reversal check with higher tolerance"""
    if len(df_5m) < 4:
        return False

    current = df_5m.iloc[-1]
    previous = df_5m.iloc[-2]

    # Increased tolerance from 0.15% to 0.4%
    tolerance = level * 0.004
    near_level = (abs(current['low'] - level) < tolerance or
                  abs(current['high'] - level) < tolerance or
                  abs(current['close'] - level) < tolerance)

    if not near_level:
        return False

    if not has_preceding_move_relaxed(df_5m, direction):
        return False

    # Basic pattern detection (simplified)
    body = abs(current['close'] - current['open'])
    if body == 0:
        return False

    lower_wick = min(current['open'], current['close']) - current['low']
    upper_wick = current['high'] - max(current['open'], current['close'])

    if direction == "bullish":
        if lower_wick > 2 * body:  # Hammer-like
            return {"pattern": "hammer_relaxed", "entry": current['close'], "sl_ref": current['low']}
    else:
        if upper_wick > 2 * body:  # Inverted Hammer-like
            return {"pattern": "inv_hammer_relaxed", "entry": current['close'], "sl_ref": current['high']}

    return False


def diagnose_relaxed():
    print(f"\n{'='*85}")
    print(f"RELAXED DIAGNOSTIC — {SYMBOL} (Higher tolerance + Relaxed preceding move)")
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
    valid_setups = 0

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

        reversal = check_reversal_relaxed(aligned_5m, direction, level)

        if reversal:
            valid_setups += 1
            print(f"[{day}] VALID SETUP FOUND → {reversal['pattern']}")

    print(f"\n{'='*85}")
    print(f"Total valid setups found with relaxed rules : {valid_setups}")
    print(f"{'='*85}\n")

    broker.disconnect()


if __name__ == "__main__":
    diagnose_relaxed()
