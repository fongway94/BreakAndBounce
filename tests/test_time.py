import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from strategy import get_us_eastern_time, is_within_trading_window
from datetime import time

def test_time():
    current = get_us_eastern_time().time()
    market_open = time(9, 30)
    
    print(f"Current US Eastern Time: {current}")
    print(f"Market Open Time: {market_open}")
    print(f"Within 150-min window: {is_within_trading_window(current, market_open)}")

if __name__ == "__main__":
    test_time()
