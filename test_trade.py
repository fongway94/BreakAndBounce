from config import USE_REAL_PAPER_TRADING, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, RISK_PER_TRADE
from broker_moomoo import MoomooBroker
from logger import TradeLogger
from notifier import TelegramNotifier
from strategy import calculate_position_size

def test_paper_trade():
    print("=== Testing Real Paper Trade ===")
    
    broker = MoomooBroker(use_real_paper=USE_REAL_PAPER_TRADING)
    logger = TradeLogger()
    notifier = TelegramNotifier(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
    
    if not broker.connect():
        print("Failed to connect to Moomoo")
        return
    
    # Test parameters
    symbol = "AAPL"
    side = "buy"
    entry_price = 150.0          # Current market price
    stop_loss = 145.0
    take_profit = 160.0
    
    account = broker.get_account_info()
    equity = account.get("equity", 50000)
    quantity = calculate_position_size(equity, RISK_PER_TRADE, entry_price, stop_loss)
    
    print(f"Symbol: {symbol}")
    print(f"Side: {side.upper()}")
    print(f"Entry Price: {entry_price}")
    print(f"Quantity: {quantity}")
    print(f"Stop Loss: {stop_loss}")
    print(f"Take Profit: {take_profit}")
    
    # Place order using the same parameters that worked in diagnostic
    order = broker.place_order(
        symbol=symbol,
        side=side,
        quantity=quantity,
        price=0.0001                    # Small positive price (required by API)
    )
    
    print(f"Order result: {order}")
    
    # Log the trade
    logger.log_trade(
        symbol=symbol,
        action=side,
        price=entry_price,
        quantity=quantity,
        mode="paper",
        notes=f"SL:{stop_loss} TP:{take_profit}"
    )
    
    # Send Telegram notification
    notifier.notify_trade(
        symbol=symbol,
        action=side,
        price=entry_price,
        quantity=quantity,
        mode="paper"
    )
    
    print("Test completed!")
    broker.disconnect()

if __name__ == "__main__":
    test_paper_trade()
