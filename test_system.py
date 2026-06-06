from strategy import generate_signal, calculate_position_size, check_daily_loss_limit, is_hammer, is_engulfing
from broker_moomoo import MoomooBroker
from logger import TradeLogger
from notifier import TelegramNotifier
from config import TRADING_MODE, SYMBOLS, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
import pandas as pd
from datetime import datetime, time
import traceback

def test_strategy_logic():
    print("=== Testing Strategy Logic ===")
    dates = pd.date_range('2025-01-01', periods=50, freq='D')
    daily_data = pd.DataFrame({
        'time_key': dates,
        'open': [100 + i*0.5 for i in range(50)],
        'high': [102 + i*0.5 for i in range(50)],
        'low': [98 + i*0.5 for i in range(50)],
        'close': [101 + i*0.5 for i in range(50)]
    })
    m15_dates = pd.date_range('2025-01-01', periods=100, freq='15min')
    m15_data = pd.DataFrame({
        'time_key': m15_dates,
        'open': [100 + i*0.1 for i in range(100)],
        'high': [102 + i*0.1 for i in range(100)],
        'low': [98 + i*0.1 for i in range(100)],
        'close': [101 + i*0.1 for i in range(100)]
    })
    m5_dates = pd.date_range('2025-01-01', periods=200, freq='5min')
    m5_data = pd.DataFrame({
        'time_key': m5_dates,
        'open': [100 + i*0.05 for i in range(200)],
        'high': [102 + i*0.05 for i in range(200)],
        'low': [98 + i*0.05 for i in range(200)],
        'close': [101 + i*0.05 for i in range(200)]
    })
    test_candle = {'open': 100, 'high': 102, 'low': 95, 'close': 100.5}
    assert is_hammer(test_candle) == True
    print("✓ Hammer detection working")
    signal = generate_signal(daily_data, m15_data, m5_data, time(9, 30))
    print(f"✓ Signal generation test completed")
    print("Strategy logic tests passed!\n")

def test_risk_management():
    print("=== Testing Risk Management ===")
    size = calculate_position_size(50000, 0.01, 100, 95)
    assert size > 0
    print(f"✓ Position size calculated: {size}")
    loss_check = check_daily_loss_limit(-600, 500)
    assert loss_check == True
    print("✓ Daily loss limit working")
    print("Risk management tests passed!\n")

def run_full_test():
    print("Starting full system test...\n")
    try:
        test_strategy_logic()
        test_risk_management()
        print("=" * 50)
        print("✅ ALL TESTS PASSED")
        print("=" * 50)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    run_full_test()