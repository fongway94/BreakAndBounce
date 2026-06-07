import futu as ft
import pandas as pd
import time

class MoomooBroker:
    def __init__(self, host="127.0.0.1", port=11111, use_real_paper=False):
        self.host = host
        self.port = port
        self.use_real_paper = use_real_paper
        self.quote_ctx = None
        self.trade_ctx = None
        self.connected = False
        self.unlocked = False

    def connect(self):
        try:
            self.quote_ctx = ft.OpenQuoteContext(host=self.host, port=self.port)
            self.trade_ctx = ft.OpenSecTradeContext(host=self.host, port=self.port)
            
            self.connected = True
            print("Connected to Moomoo openD successfully")
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False

    def unlock_trade(self, password=""):
        """Unlock trading (required in v10.7)"""
        if not self.trade_ctx:
            return False
        try:
            ret, data = self.trade_ctx.unlock_trade(password=password)
            if ret == ft.RET_OK:
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

    def place_order(self, symbol, side, quantity, price=None, order_type="MARKET", paper=True):
        if not self.trade_ctx:
            print("[PAPER ORDER] Simulated (no trade context)")
            return {"status": "success", "order_id": f"PAPER_{int(time.time())}"}
        
        # Unlock if not already unlocked
        if self.use_real_paper and not self.unlocked:
            if not self.unlock_trade():
                return {"status": "error", "message": "Failed to unlock trade"}
        
        trd_env = ft.TrdEnv.SIMULATE if self.use_real_paper else ft.TrdEnv.REAL
        code = f"US.{symbol}" if not symbol.startswith("US.") else symbol
        
        print(f"[{'REAL PAPER' if self.use_real_paper else 'LIVE'} ORDER] {side.upper()} {quantity} {code}")
        
        try:
            ret, data = self.trade_ctx.place_order(
                price=price or 0,
                qty=quantity,
                code=code,
                trd_side=ft.TrdSide.BUY if side.lower() == "buy" else ft.TrdSide.SELL,
                order_type=ft.OrderType.NORMAL,
                trd_env=trd_env
            )
            if ret == ft.RET_OK:
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
            if ret == ft.RET_OK:
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
        
