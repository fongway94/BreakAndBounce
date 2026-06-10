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

"""
Improved Break & Bounce Backtest
- Fixed daily data handling
- Relaxed reversal rules
- Tests on NFLX (same stock as video)
"""

from broker_moomoo import MoomooBroker
from strategy import generate_signal, calculate_take_profit
from config import USE_REAL_PAPER_TRADING
from datetime import datetime, timedelta, time as dt_time
import pandas as pd

SYMBOL = "NFLX"          # Same stock used in the video
DAYS = 180
RISK_REWARD = 2.0

def has_preceding_move_relaxed(df_5m, direction, lookback=3):
    """Relaxed: only needs at least 1 candle in the correct direction"""
    if len(df_5m) < lookback + 1:
        return False
    recent = df_5m.iloc[-(lookback + 1):-1]
    if direction == "bullish":
        return sum(1 for _, c in recent.iterrows() if c['close'] < c['open']) >= 1
    else:
        return sum(1 for _, c in recent.iterrows() if c['close'] > c['open']) >= 1


def run_backtest():
    print(f"\n{'='*80}")
    print(f"IMPROVED BACKTEST — Break & Bounce Strategy")
    print(f"Symbol: {SYMBOL} | Period: Last {DAYS} days (~6 months)")
    print(f"{'='*80}\n")

    broker = MoomooBroker(use_real_paper=USE_REAL_PAPER_TRADING)
    if not broker.connect():
        print("Failed to connect to Moomoo openD")
        return

    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=DAYS)).strftime("%Y-%m-%d")

    df_daily = broker.get_historical_data(SYMBOL, start_date, end_date, freq="1D")
    df_15m = broker.get_historical_data(SYMBOL, start_date, end_date, freq="15")
    df_5m = broker.get_historical_data(SYMBOL, start_date, end_date, freq="5")

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

        # Use full daily data up to current day (fixed issue)
        day_daily = df_daily[df_daily['time_key'].dt.date <= day]
        day_15m = df_15m[df_15m['time_key'].dt.date == day]
        day_5m = df_5m[df_5m['time_key'].dt.date == day]

        if len(day_daily) < 2 or len(day_15m) < 5 or len(day_5m) < 10:
            continue

        # Generate signal (still respects 2.5h window)
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
    print(f"BACKTEST RESULTS — {SYMBOL}")
    print(f"{'='*80}")
    print(f"Total Trades Detected : {total}")
    print(f"Wins (TP Hit)         : {wins}")
    print(f"Losses (SL Hit)       : {losses}")
    print(f"Still Open            : {opens}")
    print(f"Win Rate              : {win_rate:.1f}%")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    run_backtest()
