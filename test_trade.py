from config import USE_REAL_PAPER_TRADING, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from broker_moomoo import MoomooBroker
from logger import TradeLogger
from notifier import TelegramNotifier

def test_paper_trade():
    print("=== Testing Real Paper Trade ===")
    
    broker = MoomooBroker(use_real_paper=USE_REAL_PAPER_TRADING)
    logger = TradeLogger()
    notifier = TelegramNotifier(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
    
    if not broker.connect():
        print("Failed to connect to Moomoo")
        return
    
    symbol = "AAPL"
    side = "buy"
    quantity = 10
    price = 150.0
    
    print(f"Placing real paper order: {side.upper()} {quantity} {symbol}")
    
    order = broker.place_order(
        symbol=symbol,
        side=side,
        quantity=quantity,
        price=price
    )
    
    print(f"Order result: {order}")
    
    logger.log_trade(
        symbol=symbol,
        action=side,
        price=price,
        quantity=quantity,
        mode="paper",
        notes=f"REAL PAPER TRADE - {USE_REAL_PAPER_TRADING}"
    )
    
    notifier.notify_trade(
        symbol=symbol,
        action=side,
        price=price,
        quantity=quantity,
        mode="paper"
    )
    
    print("Test completed!")
    broker.disconnect()

if __name__ == "__main__":
    test_paper_trade()
