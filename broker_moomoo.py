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

    def connect(self):
        try:
            self.quote_ctx = ft.OpenQuoteContext(host=self.host, port=self.port)
            
            # Use modern OpenTradeContext
            self.trade_ctx = ft.OpenTradeContext(host=self.host, port=self.port)
            
            # Enable paper trading if needed
            if self.use_real_paper:
                self.trade_ctx.set_paper_trading(True)
                print("Paper trading mode enabled")
            
            self.connected = True
            print("Connected to Moomoo openD successfully")
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False

    def disconnect(self):
        if self.quote_ctx:
            self.quote_ctx.close()
        if self.trade_ctx:
            self.trade_ctx.close()
        self.connected = False

    def place_order(self, symbol, side, quantity, price=None, order_type="MARKET", paper=True):
        if self.use_real_paper and self.trade_ctx:
            print(f"[REAL PAPER ORDER] {side.upper()} {quantity} {symbol}")
            try:
                ret, data = self.trade_ctx.place_order(
                    price=price or 0,
                    qty=quantity,
                    code=symbol,
                    trd_side=ft.TrdSide.BUY if side.lower() == "buy" else ft.TrdSide.SELL,
                    order_type=ft.OrderType.NORMAL,
                    trd_env=ft.TrdEnv.SIMULATE if self.use_real_paper else ft.TrdEnv.REAL
                )
                if ret == ft.RET_OK:
                    print(f"Order placed successfully: {data}")
                    return {"status": "success", "order_id": str(data)}
                else:
                    print(f"Order failed: {data}")
                    return {"status": "failed", "error": data}
            except Exception as e:
                print(f"Real paper order error: {e}")
                return {"status": "error", "message": str(e)}
        else:
            # Simulated paper trading
            print(f"[PAPER ORDER] {side.upper()} {quantity} {symbol} @ {price or 'MARKET'}")
            return {"status": "success", "order_id": f"PAPER_{int(time.time())}"}

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
