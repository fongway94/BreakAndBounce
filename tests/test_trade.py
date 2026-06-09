import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import USE_REAL_PAPER_TRADING, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, RISK_PER_TRADE
from broker_moomoo import MoomooBroker
from logger import TradeLogger
from notifier import TelegramNotifier
from strategy import calculate_position_size


def test_cash_balance():
    """Test that cash balance query works."""
    print("=== Testing Cash Balance Query ===")

    broker = MoomooBroker(use_real_paper=USE_REAL_PAPER_TRADING)

    if not broker.connect():
        print("Failed to connect to Moomoo")
        return

    cash_info = broker.get_cash_balance()

    if cash_info:
        print(f"  Total Assets:     ${cash_info['total_assets']:.2f}")
        print(f"  USD Cash:         ${cash_info['us_cash']:.2f}")
        print(f"  Cash Buying Power: ${cash_info['usd_net_cash_power']:.2f}")
        print(f"  Available Funds:  ${cash_info['available_funds']:.2f}")
        print(f"  Frozen Cash:      ${cash_info['frozen_cash']:.2f}")
        print("  ✅ Cash balance query working!")
    else:
        print("  ❌ Cash balance query failed")

    broker.disconnect()


def test_cash_check_before_order():
    """Test that cash check works before placing order."""
    print("\n=== Testing Cash Check Before Order ===")

    broker = MoomooBroker(use_real_paper=USE_REAL_PAPER_TRADING)

    if not broker.connect():
        print("Failed to connect to Moomoo")
        return

    symbol = "AAPL"
    entry_price = 150.0
    quantity = 100

    print(f"\n  Simulating: BUY {quantity} {symbol} @ ${entry_price}")
    print(f"  Order value: ${quantity * entry_price:.2f}")

    allowed_qty, cash_info = broker.check_cash_before_order(symbol, quantity, entry_price)

    if allowed_qty > 0:
        print(f"  ✅ Allowed quantity: {allowed_qty} shares")
    else:
        print(f"  ❌ Order would be rejected (insufficient cash)")

    broker.disconnect()


def test_paper_trade():
    """Full paper trade test with cash balance check."""
    print("\n=== Testing Full Paper Trade (with Cash Check) ===")

    broker = MoomooBroker(use_real_paper=USE_REAL_PAPER_TRADING)
    logger = TradeLogger()
    notifier = TelegramNotifier(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)

    if not broker.connect():
        print("Failed to connect to Moomoo")
        return

    # Test parameters
    symbol = "AAPL"
    side = "buy"
    entry_price = 150.0
    stop_loss = 145.0
    take_profit = 160.0

    account = broker.get_account_info()
    equity = account.get("equity", 50000)
    quantity = calculate_position_size(equity, RISK_PER_TRADE, entry_price, stop_loss)

    print(f"  Symbol: {symbol}")
    print(f"  Side: {side.upper()}")
    print(f"  Entry Price: {entry_price}")
    print(f"  Quantity (risk-based): {quantity}")
    print(f"  Stop Loss: {stop_loss}")
    print(f"  Take Profit: {take_profit}")
    print(f"  Order Value: ${quantity * entry_price:.2f}")

    # place_order now includes cash check internally
    order = broker.place_order(
        symbol=symbol,
        side=side,
        quantity=quantity,
        price=0.0001
    )

    print(f"  Order result: {order}")

    logger.log_trade(
        symbol=symbol,
        action=side,
        price=entry_price,
        quantity=quantity,
        mode="paper",
        notes=f"SL:{stop_loss} TP:{take_profit}"
    )

    notifier.notify_trade(
        symbol=symbol,
        action=side,
        price=entry_price,
        quantity=quantity,
        mode="paper"
    )

    print("  Test completed!")
    broker.disconnect()


if __name__ == "__main__":
    test_cash_balance()
    test_cash_check_before_order()
    test_paper_trade()
