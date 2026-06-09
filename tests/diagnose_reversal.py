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

"""
Diagnostic Script - Check daily + 15m data availability
"""

from broker_moomoo import MoomooBroker
from strategy import get_previous_day_range
from config import USE_REAL_PAPER_TRADING
from datetime import datetime, timedelta

SYMBOL = "TSLA"
DAYS = 60

def diagnose():
    print(f"\n{'='*80}")
    print(f"DATA AVAILABILITY DIAGNOSTIC — {SYMBOL}")
    print(f"{'='*80}\n")

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
    print(f"Total trading days in period: {len(trading_days)}\n")

    low_data_days = 0
    good_data_days = 0

    for day in trading_days:
        day_daily = df_daily[df_daily['time_key'].dt.date == day]
        day_15m = df_15m[df_15m['time_key'].dt.date == day]

        daily_count = len(day_daily)
        m15_count = len(day_15m)

        if daily_count < 2 or m15_count < 5:
            low_data_days += 1
            print(f"[{day}] Daily: {daily_count:2} | 15m: {m15_count:2}   ← LOW DATA")
        else:
            good_data_days += 1
            if daily_count < 3 or m15_count < 20:
                print(f"[{day}] Daily: {daily_count:2} | 15m: {m15_count:2}")

    print(f"\n{'='*80}")
    print(f"Days with good data   : {good_data_days}")
    print(f"Days with low data    : {low_data_days}")
    print(f"{'='*80}\n")

    broker.disconnect()


if __name__ == "__main__":
    diagnose()
