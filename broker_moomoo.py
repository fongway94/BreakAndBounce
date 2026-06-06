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
        
        possible_codes = self._get_possible_codes(symbol)
        
        ktype_map = {
            "1": "K_1M", "5": "K_5M", "15": "K_15M",
            "30": "K_30M", "60": "K_60M", "1D": "K_DAY", "D": "K_DAY"
        }
        ktype = ktype_map.get(str(freq), "K_15M")
        
        for code in possible_codes:
            try:
                ret, data, page_req_key = self.quote_ctx.request_history_kline(
                    code=code, start=start_date, end=end_date, ktype=ktype, max_count=1000
                )
                if ret == ft.RET_OK:
                    df = data
                    df['time_key'] = pd.to_datetime(df['time_key'])
                    print(f"Successfully fetched data using code: {code}")
                    return df
                else:
                    print(f"Tried {code} - failed: {data}")
            except Exception as e:
                print(f"Error with {code}: {e}")
                continue
        
        print(f"All formats failed for {symbol}")
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
