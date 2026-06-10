import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

"""
Improved Break & Bounce Backtest - Focused on March 2026 (NFLX)
This matches the exact period shown in the video.
"""

from broker_moomoo import MoomooBroker
from strategy import generate_signal, calculate_take_profit
from config import USE_REAL_PAPER_TRADING
from datetime import datetime, timedelta, time as dt_time
import pandas as pd

SYMBOL = "NFLX"
START_DATE = "2026-03-04"     # Start of March 2026
END_DATE = "2026-03-05"       # Covers the examples shown in the video
RISK_REWARD = 2.0

def run_backtest():
    print(f"\n{'='*80}")
    print(f"BACKTEST — Break & Bounce Strategy (NFLX)")
    print(f"Period: {START_DATE} to {END_DATE} (Matches Video Example)")
    print(f"{'='*80}\n")

    broker = MoomooBroker(use_real_paper=USE_REAL_PAPER_TRADING)
    if not broker.connect():
        print("Failed to connect to Moomoo openD")
        return

    df_daily = broker.get_historical_data(SYMBOL, START_DATE, END_DATE, freq="1D")
    df_15m = broker.get_historical_data(SYMBOL, START_DATE, END_DATE, freq="15")
    df_5m = broker.get_historical_data(SYMBOL, START_DATE, END_DATE, freq="5")

    if df_daily.empty or df_15m.empty or df_5m.empty:
        print("Insufficient data")
        return

    print(f"Data loaded: {len(df_daily)} daily | {len(df_15m)} 15m | {len(df_5m)} 5m\n")

    trading_days = df_daily['time_key'].dt.date.unique()
    trades = []
    market_open = dt_time(9, 30)

    for i, day in enumerate(trading_days):
        if i < 1:
            continue

        # Fixed: Use full daily data up to current day
        day_daily = df_daily[df_daily['time_key'].dt.date <= day]
        day_15m = df_15m[df_15m['time_key'].dt.date == day]
        day_5m = df_5m[df_5m['time_key'].dt.date == day]

        if len(day_daily) < 2 or len(day_15m) < 5 or len(day_5m) < 10:
            continue

        signal = generate_signal(day_daily, day_15m, day_5m, market_open)

        if signal:
            entry = signal["entry"]
            stop_loss = signal["stop_loss"]
            take_profit = calculate_take_profit(entry, signal["signal"], stop_loss, RISK_REWARD)
            direction = signal["signal"]

            # Simulate outcome
            future_5m = df_5m[df_5m['time_key'].dt.date >= day]
            outcome = "open"

            for idx in range(len(future_5m)):
                candle = future_5m.iloc[idx]
                if direction == "buy":
                    if candle['low'] <= stop_loss:
                        outcome = "loss"
                        break
                    if candle['high'] >= take_profit:
                        outcome = "win"
                        break
                else:
                    if candle['high'] >= stop_loss:
                        outcome = "loss"
                        break
                    if candle['low'] <= take_profit:
                        outcome = "win"
                        break

            trades.append({
                "date": day,
                "direction": direction,
                "entry": entry,
                "outcome": outcome
            })

    broker.disconnect()

    # Results
    total = len(trades)
    wins = sum(1 for t in trades if t["outcome"] == "win")
    losses = sum(1 for t in trades if t["outcome"] == "loss")
    opens = sum(1 for t in trades if t["outcome"] == "open")
    win_rate = (wins / total * 100) if total > 0 else 0

    print(f"\n{'='*80}")
    print(f"BACKTEST RESULTS — NFLX (March 2026)")
    print(f"{'='*80}")
    print(f"Total Trades Detected : {total}")
    print(f"Wins (TP Hit)         : {wins}")
    print(f"Losses (SL Hit)       : {losses}")
    print(f"Still Open            : {opens}")
    print(f"Win Rate              : {win_rate:.1f}%")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    run_backtest()
