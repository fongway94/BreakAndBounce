"""
Improved Simplified Backtest for Break & Bounce Strategy

Includes:
- First 2.5 hours time window
- Better trade simulation
- Force close at 16:00 ET (as per video)
- Multiple symbols testing
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from broker_moomoo import MoomooBroker
from strategy import generate_signal, calculate_take_profit
from config import USE_REAL_PAPER_TRADING, SYMBOLS
from datetime import datetime, timedelta, time as dt_time
import pandas as pd

DAYS = 60
RISK_REWARD = 2.0
MARKET_CLOSE = dt_time(16, 0)


def simulate_trade_outcome(df_5m, entry_price, stop_loss, take_profit, direction):
    """
    Simulates trade outcome.
    - Stops at first TP or SL hit
    - Force closes at 16:00 ET if still open
    """
    for idx in range(len(df_5m)):
        candle = df_5m.iloc[idx]
        candle_time = candle['time_key'].time()

        # Force close at market end
        if candle_time >= MARKET_CLOSE:
            return "force_close"

        if direction == "buy":
            if candle['low'] <= stop_loss:
                return "loss"
            if candle['high'] >= take_profit:
                return "win"
        else:  # sell
            if candle['high'] >= stop_loss:
                return "loss"
            if candle['low'] <= take_profit:
                return "win"

    return "open"


def run_backtest():
    print(f"\n{'='*80}")
    print(f"IMPROVED BACKTEST — Break & Bounce Strategy (with Force Close)")
    print(f"Symbols: {len(SYMBOLS)} | Period: Last {DAYS} days")
    print(f"Time Window: 9:30–12:00 ET | Force Close: 16:00 ET")
    print(f"{'='*80}\n")

    broker = MoomooBroker(use_real_paper=USE_REAL_PAPER_TRADING)

    if not broker.connect():
        print("Failed to connect to Moomoo openD")
        return

    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=DAYS)).strftime("%Y-%m-%d")

    all_trades = []
    market_open = dt_time(9, 30)

    for symbol in SYMBOLS:
        print(f"Testing {symbol}...")

        df_daily = broker.get_historical_data(symbol, start_date, end_date, freq="1D")
        df_15m = broker.get_historical_data(symbol, start_date, end_date, freq="15")
        df_5m = broker.get_historical_data(symbol, start_date, end_date, freq="5")

        if df_daily.empty or df_15m.empty or df_5m.empty:
            print(f"  → Insufficient data for {symbol}")
            continue

        trading_days = df_daily['time_key'].dt.date.unique()

        for day in trading_days:
            day_daily = df_daily[df_daily['time_key'].dt.date == day]
            day_15m = df_15m[df_15m['time_key'].dt.date == day]
            day_5m = df_5m[df_5m['time_key'].dt.date == day]

            if len(day_daily) < 2 or len(day_15m) < 10 or len(day_5m) < 20:
                continue

            signal = generate_signal(day_daily, day_15m, day_5m, market_open)

            if signal:
                entry = signal["entry"]
                stop_loss = signal["stop_loss"]
                take_profit = calculate_take_profit(entry, signal["signal"], stop_loss, RISK_REWARD)
                direction = signal["signal"]

                future_5m = df_5m[df_5m['time_key'].dt.date >= day]
                outcome = simulate_trade_outcome(future_5m, entry, stop_loss, take_profit, direction)

                all_trades.append({
                    "symbol": symbol,
                    "date": day,
                    "direction": direction,
                    "entry": entry,
                    "stop_loss": stop_loss,
                    "take_profit": take_profit,
                    "pattern": signal.get("pattern", "unknown"),
                    "outcome": outcome
                })

    broker.disconnect()

    # ==================== RESULTS ====================
    print(f"\n{'='*80}")
    print("BACKTEST RESULTS")
    print(f"{'='*80}\n")

    if not all_trades:
        print("No valid setups found.")
        return

    total = len(all_trades)
    wins = sum(1 for t in all_trades if t["outcome"] == "win")
    losses = sum(1 for t in all_trades if t["outcome"] == "loss")
    force_close = sum(1 for t in all_trades if t["outcome"] == "force_close")
    opens = sum(1 for t in all_trades if t["outcome"] == "open")

    win_rate = (wins / total * 100) if total > 0 else 0

    print(f"Total Trades Detected     : {total}")
    print(f"Wins (TP Hit)             : {wins}")
    print(f"Losses (SL Hit)           : {losses}")
    print(f"Force Closed at 16:00     : {force_close}")
    print(f"Still Open                : {opens}")
    print(f"Win Rate (excluding force close) : {win_rate:.1f}%")
    print(f"\n{'='*80}")

    # Sample trades
    print("\nSample Trades:")
    for trade in all_trades[:10]:
        print(f"  {trade['date']} | {trade['symbol']:6} | {trade['direction'].upper():4} | "
              f"Entry: {trade['entry']:.2f} | Outcome: {trade['outcome'].upper()}")

    if len(all_trades) > 10:
        print(f"  ... and {len(all_trades) - 10} more trades")


if __name__ == "__main__":
    run_backtest()
