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

"""
Diagnostic Script - Check data availability per day
"""

from broker_moomoo import MoomooBroker
from strategy import get_previous_day_range, has_recent_breakout
from config import USE_REAL_PAPER_TRADING
from datetime import datetime, timedelta

SYMBOL = "TSLA"
DAYS = 60

def diagnose():
    print(f"\n{'='*75}")
    print(f"DATA AVAILABILITY DIAGNOSTIC — {SYMBOL}")
    print(f"{'='*75}\n")

    broker = MoomooBroker(use_real_paper=USE_REAL_PAPER_TRADING)
    if not broker.connect():
        print("Failed to connect")
        return

    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=DAYS)).strftime("%Y-%m-%d")

    df_daily = broker.get_historical_data(SYMBOL, start_date, end_date, freq="1D")
    df_15m = broker.get_historical_data(SYMBOL, start_date, end_date, freq="15")

    if df_daily.empty or df_15m.empty:
        print("Insufficient data")
        return

    trading_days = df_daily['time_key'].dt.date.unique()
    print(f"Total trading days: {len(trading_days)}\n")

    low_data_days = 0
    good_data_days = 0

    for day in trading_days:
        day_daily = df_daily[df_daily['time_key'].dt.date == day]
        day_15m = df_15m[df_15m['time_key'].dt.date == day]

        candle_count = len(day_15m)

        if len(day_daily) < 2 or candle_count < 5:
            low_data_days += 1
            print(f"[{day}] 15m candles: {candle_count:2}  ← LOW DATA")
        else:
            good_data_days += 1
            if candle_count < 20:   # Only print if not full day
                print(f"[{day}] 15m candles: {candle_count:2}")

    print(f"\n{'='*75}")
    print(f"Days with good data   : {good_data_days}")
    print(f"Days with low data    : {low_data_days}")
    print(f"{'='*75}\n")

    broker.disconnect()


if __name__ == "__main__":
    diagnose()
