from moomoo import *
import pandas as pd
import time
from config import MOOMOO_TRADING_PASSWORD, USE_REAL_PAPER_TRADING

class MoomooBroker:
    def __init__(self, host="127.0.0.1", port=11111, use_real_paper=False):
        self.host = host
        self.port = port
        self.use_real_paper = use_real_paper
        self.quote_ctx = None
        self.trade_ctx = None
        self.connected = False
        self.unlocked = False
        self.password = MOOMOO_TRADING_PASSWORD
        self.acc_id = None

    def connect(self):
        try:
            self.quote_ctx = OpenQuoteContext(host=self.host, port=self.port)
            
            self.trade_ctx = OpenSecTradeContext(
                filter_trdmarket=TrdMarket.US,
                host=self.host,
                port=self.port,
                security_firm=SecurityFirm.FUTUINC
            )
            
            # Get account list
            ret, data = self.trade_ctx.get_acc_list()
            if ret == RET_OK and not data.empty:
                self.acc_id = data['acc_id'][0]
                print(f"Using account ID: {self.acc_id}")
            else:
                print(f"Failed to get account list: {data}")
                return False
            
            self.connected = True
            print("Connected to Moomoo openD successfully")
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False

    def unlock_trade(self):
        if not self.trade_ctx or not self.password:
            return False
        try:
            ret, data = self.trade_ctx.unlock_trade(self.password)
            if ret == RET_OK:
                self.unlocked = True
                print("Trade unlocked successfully")
                return True
            else:
                print(f"Unlock failed: {data}")
                return False
        except Exception as e:
            print(f"Unlock error: {e}")
            return False

    def disconnect(self):
        if self.quote_ctx:
            self.quote_ctx.close()
        if self.trade_ctx:
            self.trade_ctx.close()
        self.connected = False
        self.unlocked = False

    def place_order(self, symbol, side, quantity, price=None):
        if not self.trade_ctx or not self.acc_id:
            return {"status": "error", "message": "No trade context or account ID"}
        
        if self.use_real_paper and not self.unlocked:
            self.unlock_trade()
        
        trd_env = TrdEnv.SIMULATE if self.use_real_paper else TrdEnv.REAL
        code = f"US.{symbol}" if not symbol.startswith("US.") else symbol
        
        # Use small positive price for market orders
        effective_price = 0.0001 if price is None or price <= 0 else price
        
        print(f"[REAL PAPER ORDER] {side.upper()} {quantity} {code} @ {effective_price}")
        
        try:
            ret, data = self.trade_ctx.place_order(
                acc_id=self.acc_id,
                price=effective_price,
                qty=quantity,
                code=code,
                trd_side=TrdSide.BUY if side.lower() == "buy" else TrdSide.SELL,
                order_type=OrderType.MARKET,
                trd_env=trd_env,
                trd_market=TrdMarket.US          # ← Added this line
            )
            if ret == RET_OK:
                print(f"Order placed successfully: {data}")
                return {"status": "success", "order_id": str(data)}
            else:
                print(f"Order failed: {data}")
                return {"status": "failed", "error": data}
        except Exception as e:
            print(f"Order error: {e}")
            return {"status": "error", "message": str(e)}

    def get_historical_data(self, symbol, start_date, end_date, freq="1"):
        if not self.connected:
            if not self.connect():
                return pd.DataFrame()
        
        code = f"US.{symbol}" if not symbol.startswith("US.") else symbol
        
        ktype_map = {
            "1": "K_1M", "5": "K_5M", "15": "K_15M",
            "30": "K_30M", "60": "K_60M", "1D": "K_DAY", "D": "K_DAY"
        }
        ktype = ktype_map.get(str(freq), "K_15M")
        
        try:
            ret, data, page_req_key = self.quote_ctx.request_history_kline(
                code=code, start=start_date, end=end_date, ktype=ktype, max_count=1000
            )
            if ret == RET_OK:
                df = data
                df['time_key'] = pd.to_datetime(df['time_key'])
                return df
            else:
                print(f"Error getting data for {code}: {data}")
                return pd.DataFrame()
        except Exception as e:
            print(f"Error: {e}")
            return pd.DataFrame()

    def get_account_info(self):
        return {"cash": 50000, "equity": 52000}

    def _get_possible_codes(self, symbol):
        """Return list of possible Futu codes to try"""
        symbol = symbol.upper()
        
        if symbol in ["AAPL", "TSLA", "NVDA", "MSFT", "GOOGL", "AMZN", "META", "AMD"]:
            return [f"US.{symbol}"]
        
        # US Indices - try multiple formats
        if symbol in ["US100", "IXIC"]:
            return ["US.NASDAQ", "US.IX.NASDAQ100", "US.US100", "US.IX.NASDAQ"]
        
        if symbol in ["US500", "SPX"]:
            return ["US.SP", "US.IX.SPX", "US.US500", "US.IX.SP"]
        
        # European Indices
        if symbol == "DE40":
            return ["DE.DAX", "DE.IX.DAX", "DE.IX.DAX30"]
        
        if symbol == "UK100":
            return ["UK.FTSE", "UK.IX.FTSE"]
        
        if symbol == "FR40":
            return ["FR.CAC", "FR.IX.CAC"]
        
        # Hong Kong
        if symbol == "HKHSI":
            return ["HK.HS", "HK.IX.HS"]
        
        return [f"US.{symbol}"]
        
