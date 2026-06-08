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
        self.acc_id = None
        self.connected = False

    def connect(self):
        """Connect to openD and initialize both quote and trade contexts."""
        try:
            # Quote context (for historical data)
            self.quote_ctx = OpenQuoteContext(host=self.host, port=self.port)

            # Trade context (for placing orders)
            self.trade_ctx = OpenSecTradeContext(
                filter_trdmarket=TrdMarket.US,
                host=self.host,
                port=self.port,
                security_firm=SecurityFirm.FUTUINC
            )

            # Get account ID once
            ret, data = self.trade_ctx.get_acc_list()
            if ret == RET_OK and not data.empty:
                self.acc_id = data['acc_id'][0]
                print(f"Using account ID: {self.acc_id}")
            else:
                print(f"Warning: Could not get account list: {data}")

            self.connected = True
            print("Connected to Moomoo openD successfully")
            return True

        except Exception as e:
            print(f"Connection failed: {e}")
            return False

    def disconnect(self):
        """Close all connections."""
        if self.quote_ctx:
            self.quote_ctx.close()
        if self.trade_ctx:
            self.trade_ctx.close()
        self.connected = False
        print("Disconnected from Moomoo openD")

    def place_order(self, symbol, side, quantity, price=None):
        """
        Place a market order. Reuses the trade context created in connect().

        Args:
            symbol:    e.g. "AAPL"
            side:      "buy" or "sell"
            quantity:  float (supports fractional shares, 2 decimal places)
            price:     None for market order (uses 0.0001 as API requires)
        """
        if not self.trade_ctx or not self.acc_id:
            return {"status": "error", "message": "No trade context or account ID. Call connect() first."}

        trd_env = TrdEnv.SIMULATE if self.use_real_paper else TrdEnv.REAL
        code = f"US.{symbol}" if not symbol.startswith("US.") else symbol
        effective_price = 0.0001 if price is None or price <= 0 else price

        print(f"[ORDER] {side.upper()} {quantity} {code} @ {effective_price} (env={trd_env})")

        try:
            ret, data = self.trade_ctx.place_order(
                acc_id=self.acc_id,
                price=effective_price,
                qty=quantity,
                code=code,
                trd_side=TrdSide.BUY if side.lower() == "buy" else TrdSide.SELL,
                order_type=OrderType.MARKET,
                trd_env=trd_env
            )

            if ret == RET_OK:
                print(f"Order placed successfully: {data}")
                return {"status": "success", "order_id": str(data)}
            else:
                print(f"Order failed: {data}")
                return {"status": "failed", "error": str(data)}

        except Exception as e:
            print(f"Order error: {e}")
            return {"status": "error", "message": str(e)}

    def get_historical_data(self, symbol, start_date, end_date, freq="1"):
        """
        Get historical candle data from Moomoo.

        Args:
            symbol:     e.g. "AAPL" (auto-prefixed with "US.")
            start_date: "YYYY-MM-DD"
            end_date:   "YYYY-MM-DD"
            freq:       "1", "5", "15", "30", "60", "1D"
        """
        if not self.connected:
            if not self.connect():
                return pd.DataFrame()

        code = f"US.{symbol}" if not symbol.startswith("US.") else symbol

        ktype_map = {
            "1": KLType.K_1M,
            "5": KLType.K_5M,
            "15": KLType.K_15M,
            "30": KLType.K_30M,
            "60": KLType.K_60M,
            "1D": KLType.K_DAY,
            "D": KLType.K_DAY,
        }
        ktype = ktype_map.get(str(freq), KLType.K_15M)

        try:
            ret, data, page_req_key = self.quote_ctx.request_history_kline(
                code=code,
                start=start_date,
                end=end_date,
                ktype=ktype,
                max_count=1000
            )

            if ret == RET_OK:
                df = data.copy()
                df['time_key'] = pd.to_datetime(df['time_key'])
                return df
            else:
                print(f"Error getting data for {code}: {data}")
                return pd.DataFrame()

        except Exception as e:
            print(f"Data fetch error: {e}")
            return pd.DataFrame()

    def get_account_info(self):
        """
        Get real account info from Moomoo.
        Falls back to defaults if API call fails.
        """
        from config import DEFAULT_EQUITY
        try:
            if self.trade_ctx and self.acc_id:
                ret, data = self.trade_ctx.accinfo_get_funds()
                if ret == RET_OK and not data.empty:
                    row = data.iloc[0]
                    return {
                        "cash": float(row.get('cash', DEFAULT_EQUITY)),
                        "equity": float(row.get('total_assets', DEFAULT_EQUITY)),
                    }
        except Exception as e:
            print(f"Warning: Could not fetch real account info: {e}")

        return {"cash": DEFAULT_EQUITY, "equity": DEFAULT_EQUITY}

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

   

