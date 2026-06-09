"""
Simplified Backtest for Break & Bounce Strategy

This script validates whether the current strategy would have triggered signals
on historical data while respecting the first 2.5 hours time window.

It also simulates trade outcomes to calculate Win Rate.
"""

from broker_moomoo import MoomooBroker
from strategy import (
    generate_signal,
    calculate_take_profit,
    calculate_stop_loss,
    get_us_eastern_time
)
from config import USE_REAL_PAPER_TRADING
from datetime import datetime, timedelta, time as dt_time
import pandas as pd

SYMBOL = "AAPL"
DAYS = 60
RISK_REWARD = 2.0


def simulate_trade_outcome(df_5m, entry_price, stop_loss, take_profit, direction):
    """
    Simulate what happened after entry using historical 5-minute data.
    Returns: "win", "loss", or "open"
    """
    for idx in range(len(df_5m)):
        candle = df_5m.iloc[idx]

        if direction == "buy":
            # Check if SL hit first
            if candle['low'] <= stop_loss:
                return "loss"
            # Check if TP hit
            if candle['high'] >= take_profit:
                return "win"
        else:  # sell
            if candle['high'] >= stop_loss:
                return "loss"
            if candle['low'] <= take_profit:
                return "win"

    return "open"  # Trade still open at end of data


def run_backtest():
    print(f"\n{'='*70}")
    print(f"SIMPLIFIED BACKTEST — Break & Bounce Strategy")
    print(f"Symbol: {SYMBOL} | Period: Last {DAYS} days")
    print(f"Time Window: First 2.5 hours only (as per video)")
    print(f"{'='*70}\n")

    broker = MoomooBroker(use_real_paper=USE_REAL_PAPER_TRADING)

    if not broker.connect():
        print("Failed to connect to Moomoo openD")
        return

    # Fetch data
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=DAYS)).strftime("%Y-%m-%d")

    print(f"Fetching data from {start_date} to {end_date}...\n")

    df_daily = broker.get_historical_data(SYMBOL, start_date, end_date, freq="1D")
    df_15m = broker.get_historical_data(SYMBOL, start_date, end_date, freq="15")
    df_5m = broker.get_historical_data(SYMBOL, start_date, end_date, freq="5")

    if df_daily.empty or df_15m.empty or df_5m.empty:
        print("Insufficient data.")
        broker.disconnect()
        return

    print(f"Data loaded: {len(df_daily)} daily | {len(df_15m)} 15m | {len(df_5m)} 5m candles\n")

    # Get unique trading days
    trading_days = df_daily['time_key'].dt.date.unique()
    print(f"Number of trading days: {len(trading_days)}\n")

    trades = []
    market_open = dt_time(9, 30)

    for day in trading_days:
        # Filter data for this day only (for signal generation)
        day_str = day.strftime("%Y-%m-%d")

        day_daily = df_daily[df_daily['time_key'].dt.date == day]
        day_15m = df_15m[df_15m['time_key'].dt.date == day]
        day_5m = df_5m[df_5m['time_key'].dt.date == day]

        if len(day_daily) < 2 or len(day_15m) < 10 or len(day_5m) < 20:
            continue

        # Generate signal (this already checks the 2.5-hour window)
        signal = generate_signal(day_daily, day_15m, day_5m, market_open)

        if signal:
            entry = signal["entry"]
            stop_loss = signal["stop_loss"]
            take_profit = calculate_take_profit(entry, signal["signal"], stop_loss, RISK_REWARD)
            direction = signal["signal"]

            # Simulate outcome using future 5-minute candles
            future_5m = df_5m[df_5m['time_key'].dt.date >= day]
            outcome = simulate_trade_outcome(future_5m, entry, stop_loss, take_profit, direction)

            trades.append({
                "date": day,
                "direction": direction,
                "entry": entry,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "pattern": signal.get("pattern", "unknown"),
                "outcome": outcome
            })

    broker.disconnect()

    # Results
    print(f"\n{'='*70}")
    print("BACKTEST RESULTS")
    print(f"{'='*70}\n")

    if not trades:
        print("No valid setups found in the period.")
        return

    total_trades = len(trades)
    wins = sum(1 for t in trades if t["outcome"] == "win")
    losses = sum(1 for t in trades if t["outcome"] == "loss")
    open_trades = sum(1 for t in trades if t["outcome"] == "open")

    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0

    print(f"Total Trades Detected : {total_trades}")
    print(f"Wins (TP Hit)         : {wins}")
    print(f"Losses (SL Hit)       : {losses}")
    print(f"Still Open            : {open_trades}")
    print(f"Win Rate              : {win_rate:.1f}%")
    print(f"\n{'='*70}")

    # Show some example trades
    print("\nSample Trades:")
    for trade in trades[:5]:
        print(f"  {trade['date']} | {trade['direction'].upper():4} | "
              f"Entry: {trade['entry']:.2f} | TP: {trade['take_profit']:.2f} | "
              f"Outcome: {trade['outcome'].upper()}")

    if len(trades) > 5:
        print(f"  ... and {len(trades) - 5} more trades")


if __name__ == "__main__":
    run_backtest()
