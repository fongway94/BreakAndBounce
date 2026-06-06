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

    def _format_code(self, symbol):
        """Convert ticker to Futu format"""
        symbol = symbol.upper()
        
        # US Stocks
        if symbol in ["AAPL", "TSLA", "NVDA", "MSFT", "GOOGL", "AMZN", "META", "AMD"]:
            return f"US.{symbol}"
        
        # US Indices (most common working formats)
        if symbol in ["US100", "IXIC"]:
            return "US.NASDAQ"                    # Try this first
            # return "US.IX.NASDAQ100"            # Alternative
        
        if symbol in ["US500", "SPX"]:
            return "US.SP"                        # Try this first
            # return "US.IX.SPX"                  # Alternative
        
        # European Indices
        if symbol == "DE40":
            return "DE.DAX"                       # Try this first
            # return "DE.IX.DAX"                  # Alternative
        
        if symbol == "UK100":
            return "UK.FTSE"                      # Try this first
            # return "UK.IX.FTSE"                 # Alternative
        
        if symbol == "FR40":
            return "FR.CAC"                       # Try this first
            # return "FR.IX.CAC"                  # Alternative
        
        # Hong Kong
        if symbol == "HKHSI":
            return "HK.HS"                        # Try this first
            # return "HK.IX.HS"                   # Alternative
        
        # Default
        return f"US.{symbol}"

    def connect(self):
        try:
            self.quote_ctx = ft.OpenQuoteContext(host=self.host, port=self.port)
            try:
                self.trade_ctx = ft.OpenUSTradeContext(host=self.host, port=self.port)
            except AttributeError:
                self.trade_ctx = None
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

    def get_historical_data(self, symbol, start_date, end_date, freq="1"):
        if not self.connected:
            if not self.connect():
                return pd.DataFrame()
        
        code = self._format_code(symbol)
        
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
            print(f"Error fetching {code}: {e}")
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
