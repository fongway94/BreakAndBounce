import pandas as pd
from datetime import datetime
import os
import warnings

warnings.filterwarnings("ignore", category=FutureWarning, module="pandas")


class TradeLogger:
    def __init__(self, log_file="logs/trade_log.csv"):
        self.log_file = log_file

        # Create logs directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        if not os.path.exists(log_file):
            pd.DataFrame(columns=[
                "timestamp", "symbol", "action", "price", "quantity",
                "mode", "pnl", "notes"
            ]).to_csv(log_file, index=False)

    def log_trade(self, symbol, action, price, quantity, mode, pnl=0, notes=""):
        new_row = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "symbol": symbol,
            "action": action,
            "price": price,
            "quantity": quantity,
            "mode": mode,
            "pnl": pnl,
            "notes": notes
        }

        df = pd.read_csv(self.log_file)
        new_df = pd.DataFrame([new_row], columns=df.columns)
        df = pd.concat([df, new_df], ignore_index=True)
        df.to_csv(self.log_file, index=False)
        print(f"[LOG] Trade logged: {action} {symbol}")

    def get_trade_history(self):
        return pd.read_csv(self.log_file)
