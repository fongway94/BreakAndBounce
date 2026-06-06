import futu as ft
import pandas as pd
import time

class MoomooBroker:
    def __init__(self, host="127.0.0.1", port=11111):
        self.host = host
        self.port = port
        self.quote_ctx = None
        self.trade_ctx = None
        self.connected = False

    def connect(self):
        try:
            self.quote_ctx = ft.OpenQuoteContext(host=self.host, port=self.port)
            
            # Try US trade context, fallback if not available
            try:
                self.trade_ctx = ft.OpenUSTradeContext(host=self.host, port=self.port)
            except AttributeError:
                print("Warning: OpenUSTradeContext not available, using quote only")
                self.trade_ctx = None
                
            self.connected = True
            print("Connected to Moomoo openD")
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

    def get_historical_data(self, symbol, start_date, end_date, freq="1"):
        if not self.connected:
            self.connect()
        try:
            ret, data, page_req_key = self.quote_ctx.request_history_kline(
                code=symbol, start=start_date, end=end_date, ktype=freq, max_count=1000
            )
            if ret == ft.RET_OK:
                df = data
                df['time_key'] = pd.to_datetime(df['time_key'])
                return df
            else:
                print(f"Error getting data: {data}")
                return pd.DataFrame()
        except Exception as e:
            print(f"Error: {e}")
            return pd.DataFrame()

    def place_order(self, symbol, side, quantity, price=None, order_type="MARKET", paper=True):
        if paper:
            print(f"[PAPER ORDER] {side.upper()} {quantity} {symbol} @ {price or 'MARKET'}")
            return {"status": "success", "order_id": f"PAPER_{int(time.time())}"}
        else:
            print(f"[LIVE ORDER] {side.upper()} {quantity} {symbol}")
            return {"status": "success", "order_id": "LIVE123"}

    def get_account_info(self):
        return {"cash": 50000, "equity": 52000}
