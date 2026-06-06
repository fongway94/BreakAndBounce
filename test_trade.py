from config import USE_REAL_PAPER_TRADING, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from broker_moomoo import MoomooBroker
from logger import TradeLogger
from notifier import TelegramNotifier

def test_paper_trade():
    print("=== Testing Paper Trade ===")
    
    # Initialize components
    broker = MoomooBroker(use_real_paper=USE_REAL_PAPER_TRADING)
    
    # === ADD THESE TWO LINES HERE ===
    print("use_real_paper =", broker.use_real_paper)
    print("trade_ctx =", broker.trade_ctx)
    # =================================
    
    logger = TradeLogger()
    notifier = TelegramNotifier(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
    
    # Connect to Moomoo
    if not broker.connect():
        print("Failed to connect to Moomoo")
        return
    
    # Test trade details
    symbol = "AAPL"
    side = "buy"
    quantity = 10
    price = 150.0
    
    print(f"Placing test order: {side.upper()} {quantity} {symbol}")
    
    # Place order
    order = broker.place_order(
        symbol=symbol,
        side=side,
        quantity=quantity,
        price=price,
        paper=True
    )
    
    print(f"Order result: {order}")
    
    # Log the trade
    logger.log_trade(
        symbol=symbol,
        action=side,
        price=price,
        quantity=quantity,
        mode="paper",
        notes=f"TEST TRADE - Real Paper: {USE_REAL_PAPER_TRADING}"
    )
    
    # Send Telegram notification
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
