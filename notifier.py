import telegram
from telegram import Bot
import asyncio

class TelegramNotifier:
    def __init__(self, token, chat_id):
        self.bot = Bot(token=token)
        self.chat_id = chat_id

    async def send_message(self, message):
        try:
            await self.bot.send_message(chat_id=self.chat_id, text=message)
            print(f"[TELEGRAM] Sent: {message[:60]}...")
        except Exception as e:
            print(f"Telegram error: {e}")

    def notify_trade(self, symbol, action, price, quantity, mode):
        message = (f"🚨 TRADE EXECUTED\nSymbol: {symbol}\nAction: {action.upper()}\n"
                   f"Price: {price}\nQuantity: {quantity}\nMode: {mode}")
        asyncio.run(self.send_message(message))

    def notify_status(self, status):
        asyncio.run(self.send_message(f"📊 System Status: {status}"))