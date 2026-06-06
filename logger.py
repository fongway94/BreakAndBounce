import pandas as pd
from datetime import datetime
import os

class TradeLogger:
    def __init__(self, log_file="logs/trade_log.csv"):
        self.log_file = log_file
        if not os.path.exists(log_file):
            pd.DataFrame(columns=["timestamp", "symbol", "action", "price", "quantity", "mode", "pnl", "notes"]).to_csv(log_file, index=False)

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
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv(self.log_file, index=False)
        print(f"[LOG] Trade logged: {action} {symbol}")