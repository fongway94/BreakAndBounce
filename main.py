"""
Break & Bounce Trading Bot — Main Orchestrator

Aligned with ProRealAlgos video:
  - Enters trades ONLY in first 150 minutes after market open (9:30–12:00 ET)
  - Force-closes open trades near market close (16:00 ET), NOT at end of entry window
  - Mechanical SL/TP based on reversal candle
  - Daily loss limit protection
"""

from config import (
    TRADING_MODE, SYMBOLS, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID,
    MAX_DAILY_LOSS, RISK_PER_TRADE, USE_REAL_PAPER_TRADING,
    MARKET_OPEN_TIME, MARKET_CLOSE_TIME, FORCE_CLOSE_BUFFER_MINUTES,
    DEFAULT_EQUITY, RISK_REWARD_RATIO
)
from broker_moomoo import MoomooBroker
from strategy import (
    generate_signal, calculate_position_size, check_daily_loss_limit,
    is_near_market_close, get_us_eastern_time
)
from logger import TradeLogger
from notifier import TelegramNotifier
import time
from datetime import datetime, date, timedelta, time as dt_time


class TradingBot:
    def __init__(self):
        self.mode = TRADING_MODE
        self.use_real_paper = USE_REAL_PAPER_TRADING
        self.broker = MoomooBroker(use_real_paper=self.use_real_paper)
        self.logger = TradeLogger()
        self.notifier = TelegramNotifier(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
        self.market_open = dt_time.fromisoformat(MARKET_OPEN_TIME)
        self.market_close = dt_time.fromisoformat(MARKET_CLOSE_TIME)
        self.daily_pnl = 0
        self.trades_today = 0
        self.is_running = False
        self.open_trades = []
        self.last_position_sync = None

    def start(self):
        print(f"=== Break & Bounce Bot Started | Mode: {self.mode.upper()} ===")
        print(f"    Paper Trading: {self.use_real_paper}")
        print(f"    Symbols: {len(SYMBOLS)}")
        print(f"    Entry Window: {MARKET_OPEN_TIME}–{self._entry_window_end()} ET")
        print(f"    Force Close: {MARKET_CLOSE_TIME} ET (buffer={FORCE_CLOSE_BUFFER_MINUTES} min)")

        if not self.broker.connect():
            print("Failed to connect to Moomoo openD")
            return False

        self.is_running = True
        self.notifier.notify_status(
            f"Bot started in {self.mode} mode (Paper: {self.use_real_paper})"
        )

        while self.is_running:
            self.run_cycle()
            time.sleep(60)

    def _entry_window_end(self):
        """Calculate end of entry window as HH:MM string."""
        total_min = self.market_open.hour * 60 + self.market_open.minute + 150
        return f"{total_min // 60:02d}:{total_min % 60:02d}"

    def sync_open_trades_from_positions(self):
        """
        Sync self.open_trades with the actual positions from the broker API.
        This ensures the in-memory list always reflects reality.
        Called at the start of every cycle.
        """
        try:
            real_positions = self.broker.get_open_positions_summary()
            if not real_positions:
                if self.open_trades:
                    print("  [SYNC] No open positions in account — clearing in-memory trades")
                    self.open_trades = []
                return

            # Rebuild open_trades based on real positions
            new_open_trades = []
            for pos in real_positions:
                # Try to preserve existing metadata if available
                existing = next((t for t in self.open_trades if t['symbol'] == pos['symbol']), None)
                if existing:
                    new_open_trades.append(existing)
                else:
                    # New position detected (e.g. from previous session or manual trade)
                    new_open_trades.append({
                        "symbol": pos['symbol'],
                        "signal": "buy" if pos['position_side'] == "LONG" else "sell",
                        "entry": pos['cost_price'],
                        "quantity": pos['qty'],
                        "stop_loss": 0,
                        "take_profit": 0,
                        "pattern": "synced_from_account",
                    })

            if len(new_open_trades) != len(self.open_trades):
                print(f"  [SYNC] Synced {len(new_open_trades)} open positions from account")

            self.open_trades = new_open_trades

        except Exception as e:
            print(f"  [SYNC] Error syncing positions: {e}")

    def run_cycle(self):
        """Main trading cycle — runs every 60 seconds."""
        # Reset daily stats on new day
        current_date = date.today()
        if hasattr(self, 'last_date') and self.last_date != current_date:
            self.daily_pnl = 0
            self.trades_today = 0
        self.last_date = current_date

        # === NEW: Sync open_trades from real account positions (prevents stale memory state) ===
        self.sync_open_trades_from_positions()

        # Check daily loss limit
        if check_daily_loss_limit(self.daily_pnl, MAX_DAILY_LOSS):
            print("Daily loss limit reached. Stopping trading for today.")
            self.notifier.notify_status("Daily loss limit reached — trading paused")
            self.is_running = False
            return

        # Force-close open trades near market close (per video: "by the time the market closes")
        self.force_close_trades()

        # Dynamic date range (last 15 days)
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=15)).strftime("%Y-%m-%d")

        et_now = get_us_eastern_time()
        print(f"\n[{et_now.strftime('%H:%M:%S')} ET] Running cycle...")

        for symbol in SYMBOLS:
            try:
                # === NEW: Authoritative duplicate prevention using Moomoo position API ===
                # This prevents the 5-minute signal duplication bug mentioned in the issue.
                if self.broker.has_open_position(symbol):
                    print(f"  Skipping {symbol} (already have open position in account)")
                    continue

                # Also keep the in-memory check as a fast secondary filter
                if any(trade['symbol'] == symbol for trade in self.open_trades):
                    print(f"  Skipping {symbol} (trade already tracked in memory)")
                    continue

                print(f"  Fetching data for {symbol}...")

                df_daily = self.broker.get_historical_data(symbol, start_date, end_date, freq="1D")
                df_15m = self.broker.get_historical_data(symbol, start_date, end_date, freq="15")
                df_5m = self.broker.get_historical_data(symbol, start_date, end_date, freq="5")

                print(f"    Daily: {len(df_daily)} rows | 15m: {len(df_15m)} rows | 5m: {len(df_5m)} rows")

                if df_daily.empty or df_15m.empty or df_5m.empty:
                    print(f"    Skipping {symbol} (insufficient data)")
                    continue

                result = generate_signal(df_daily, df_15m, df_5m, self.market_open)

                if result and isinstance(result, dict):
                    signal = result["signal"]
                    entry_price = result["entry"]
                    stop_loss = result["stop_loss"]
                    take_profit = result["take_profit"]
                    pattern = result.get("pattern", "unknown")

                    print(f"  >>> SIGNAL: {signal.upper()} on {symbol}")
                    print(f"      Pattern: {pattern} | Entry: {entry_price} | SL: {stop_loss} | TP: {take_profit}")

                    if self.mode in ["paper", "live"]:
                        account = self.broker.get_account_info()
                        equity = account.get("equity", DEFAULT_EQUITY)
                        quantity = calculate_position_size(
                            equity, RISK_PER_TRADE, entry_price, stop_loss
                        )

                        print(f"      Quantity: {quantity} (equity=${equity}, risk={RISK_PER_TRADE*100}%)")

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
                            notes=f"Pattern:{pattern} SL:{stop_loss} TP:{take_profit}"
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
                            "signal": signal,
                            "entry": entry_price,
                            "quantity": quantity,
                            "stop_loss": stop_loss,
                            "take_profit": take_profit,
                            "pattern": pattern,
                        })
                        self.trades_today += 1

            except Exception as e:
                print(f"  Error processing {symbol}: {e}")
                continue

    def force_close_trades(self):
        """
        Force-close any open trades near market close.

        Video: "if we are still in position by the time the market closes,
                we want to manually close the trade."

        This triggers FORCE_CLOSE_BUFFER_MINUTES before market close (default: 10 min).
        """
        if not self.open_trades:
            return

        current_time = get_us_eastern_time().time()

        if is_near_market_close(current_time, self.market_close, FORCE_CLOSE_BUFFER_MINUTES):
            print(f"\n[FORCE CLOSE] Near market close — closing {len(self.open_trades)} open trade(s)")

            for trade in self.open_trades[:]:
                print(f"  Force closing {trade['symbol']} ({trade['pattern']})")

                self.broker.place_order(
                    symbol=trade['symbol'],
                    side="sell" if trade.get("signal", "buy") == "buy" else "buy",
                    quantity=trade['quantity'],
                )

                self.logger.log_trade(
                    trade['symbol'], "force_close",
                    price=trade['entry'],
                    quantity=trade['quantity'],
                    mode=self.mode,
                    notes=f"Force closed near market close (pattern: {trade['pattern']})"
                )

                self.notifier.notify_trade(
                    trade['symbol'], "force_close",
                    price=trade['entry'],
                    quantity=trade['quantity'],
                    mode=self.mode
                )

                self.open_trades.remove(trade)

            print("  All open trades force closed.")

    def stop(self):
        self.is_running = False
        self.broker.disconnect()
        self.notifier.notify_status("Bot stopped")


if __name__ == "__main__":
    bot = TradingBot()
    bot.start()
