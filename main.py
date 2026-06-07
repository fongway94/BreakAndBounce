from config import TRADING_MODE, SYMBOLS, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, MAX_DAILY_LOSS, RISK_PER_TRADE, USE_REAL_PAPER_TRADING
from broker_moomoo import MoomooBroker
from strategy import generate_signal, calculate_position_size, check_daily_loss_limit, is_near_end_of_window, get_us_eastern_time
from logger import TradeLogger
from notifier import TelegramNotifier
import time
from datetime import datetime, date

class TradingBot:
    def __init__(self):
        self.mode = TRADING_MODE
        self.use_real_paper = USE_REAL_PAPER_TRADING
        self.broker = MoomooBroker(use_real_paper=self.use_real_paper)
        self.logger = TradeLogger()
        self.notifier = TelegramNotifier(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
        self.market_open = datetime.strptime("09:30", "%H:%M").time()
        self.daily_pnl = 0
        self.trades_today = 0
        self.is_running = False
        self.open_trades = []

    def start(self):
        print(f"=== Break & Bounce Bot Started | Mode: {self.mode.upper()} ===")
        if not self.broker.connect():
            print("Failed to connect to Moomoo openD")
            return False
        self.is_running = True
        self.notifier.notify_status(f"Bot started in {self.mode} mode (Real Paper: {self.use_real_paper})")
        while self.is_running:
            self.run_cycle()
            time.sleep(60)

    def run_cycle(self):
        current_date = date.today()
        if hasattr(self, 'last_date') and self.last_date != current_date:
            self.daily_pnl = 0
            self.trades_today = 0
        self.last_date = current_date

        if check_daily_loss_limit(self.daily_pnl, MAX_DAILY_LOSS):
            print("Daily loss limit reached. Stopping trading for today.")
            self.notifier.notify_status("Daily loss limit reached - trading paused")
            self.is_running = False
            return

        self.force_close_trades()

        for symbol in SYMBOLS:
            try:
                df_daily = self.broker.get_historical_data(symbol, "2025-01-01", "2026-06-06", freq="1")
                df_15m = self.broker.get_historical_data(symbol, "2025-01-01", "2026-06-06", freq="15")
                df_5m = self.broker.get_historical_data(symbol, "2025-01-01", "2026-06-06", freq="5")

                if df_daily.empty or df_15m.empty or df_5m.empty:
                    continue

                result = generate_signal(df_daily, df_15m, df_5m, self.market_open)

                if result and isinstance(result, dict):
                    signal = result["signal"]
                    entry_price = result["entry"]
                    stop_loss = result["stop_loss"]
                    take_profit = result["take_profit"]

                    print(f"[{datetime.now()}] SIGNAL: {signal.upper()} on {symbol} | Entry: {entry_price} | SL: {stop_loss} | TP: {take_profit}")

                    if self.mode in ["paper", "live"]:
                        account = self.broker.get_account_info()
                        equity = account.get("equity", 50000)

                        # Calculate quantity based on equity and risk
                        quantity = calculate_position_size(equity, RISK_PER_TRADE, entry_price, stop_loss)

                        order = self.broker.place_order(
                            symbol=symbol,
                            side=signal,
                            quantity=quantity,
                            price=entry_price
                        )

                        self.logger.log_trade(
                            symbol=symbol,
                            action=signal,
                            price=entry_price,
                            quantity=quantity,
                            mode=self.mode,
                            notes=f"SL:{stop_loss} TP:{take_profit}"
                        )

                        self.notifier.notify_trade(
                            symbol=symbol,
                            action=signal,
                            price=entry_price,
                            quantity=quantity,
                            mode=self.mode
                        )

                        self.open_trades.append({
                            "symbol": symbol,
                            "entry": entry_price,
                            "quantity": quantity,
                            "stop_loss": stop_loss,
                            "take_profit": take_profit
                        })
                        self.trades_today += 1

            except Exception as e:
                print(f"Error processing {symbol}: {e}")
                continue

    def force_close_trades(self):
        if not self.open_trades:
            return
        current_time = get_us_eastern_time().time()
        if is_near_end_of_window(current_time, self.market_open):
            for trade in self.open_trades[:]:
                print(f"[FORCE CLOSE] Closing trade on {trade['symbol']} at market price")
                self.logger.log_trade(
                    trade['symbol'], "force_close", price=trade['entry'],
                    quantity=trade['quantity'], mode=self.mode,
                    notes="Force closed at end of trading window"
                )
                self.notifier.notify_trade(
                    trade['symbol'], "force_close", price=trade['entry'],
                    quantity=trade['quantity'], mode=self.mode
                )
                self.open_trades.remove(trade)
            print("All open trades force closed due to end of trading window.")

    def stop(self):
        self.is_running = False
        self.broker.disconnect()
        self.notifier.notify_status("Bot stopped")


if __name__ == "__main__":
    bot = TradingBot()
    bot.start()
