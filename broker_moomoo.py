from moomoo import *
import pandas as pd
import time
from config import MOOMOO_TRADING_PASSWORD, USE_REAL_PAPER_TRADING, DEFAULT_EQUITY


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
            self.quote_ctx = OpenQuoteContext(host=self.host, port=self.port)

            self.trade_ctx = OpenSecTradeContext(
                filter_trdmarket=TrdMarket.US,
                host=self.host,
                port=self.port,
                security_firm=SecurityFirm.FUTUINC
            )

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

    # ==================== CASH BALANCE CHECK (Feature 2) ====================

    def get_cash_balance(self):
        """
        Get account funds from Moomoo API.

        Uses: accinfo_query() — Moomoo OpenAPI v10.7
        Returns dict with cash info, or None on failure.

        Key fields (per API doc):
          us_cash             — USD Cash available
          usd_net_cash_power  — USD Cash Buying Power (cash only, no margin)
          total_assets        — Total Net Assets
          available_funds     — Available funds
          frozen_cash         — Funds on Hold
        """
        if not self.trade_ctx or not self.acc_id:
            print("Warning: No trade context for cash balance query")
            return None

        trd_env = TrdEnv.SIMULATE if self.use_real_paper else TrdEnv.REAL

        try:
            ret, data = self.trade_ctx.accinfo_query(
                trd_env=trd_env,
                acc_id=self.acc_id,
                refresh_cache=True
            )

            if ret == RET_OK and not data.empty:
                row = data.iloc[0]
                result = {
                    "total_assets": float(row.get("total_assets", 0)),
                    "us_cash": float(row.get("us_cash", 0)),
                    "usd_net_cash_power": float(row.get("usd_net_cash_power", 0)),
                    "available_funds": float(row.get("available_funds", 0)),
                    "frozen_cash": float(row.get("frozen_cash", 0)),
                }
                print(f"  [CASH] Total Assets: ${result['total_assets']:.2f} | "
                      f"USD Cash: ${result['us_cash']:.2f} | "
                      f"Cash Buying Power: ${result['usd_net_cash_power']:.2f}")
                return result
            else:
                print(f"  [CASH] accinfo_query failed: {data}")
                return None

        except Exception as e:
            print(f"  [CASH] Error querying funds: {e}")
            return None

    def check_cash_before_order(self, symbol, quantity, price):
        """
        Check if the order value fits within USD Cash Buying Power.
        Adjusts quantity DOWN if not enough cash. Never uses margin.

        Returns: (allowed_quantity, cash_info)
          - allowed_quantity: may be reduced from original quantity
          - cash_info: the raw fund data from API
        """
        cash_info = self.get_cash_balance()

        if cash_info is None:
            # Cannot verify — reject order
            print(f"  [CASH CHECK] Cannot verify cash balance. Order REJECTED.")
            return 0, None

        order_value = price * quantity
        cash_power = cash_info["usd_net_cash_power"]

        if order_value <= cash_power:
            # Enough cash — order is fine
            print(f"  [CASH CHECK] ✅ Order ${order_value:.2f} <= Cash Power ${cash_power:.2f} — OK")
            return quantity, cash_info
        else:
            # Not enough cash — reduce quantity to fit
            if cash_power <= 0 or price <= 0:
                print(f"  [CASH CHECK] ❌ No cash buying power. Order REJECTED.")
                return 0, cash_info

            max_quantity = cash_power / price
            max_quantity = int(max_quantity * 100) / 100  # Floor to 2 decimal places (never round up)

            # Safety check: ensure rounded quantity still fits within cash
            if max_quantity * price > cash_power:
                max_quantity = int(max_quantity * 100 - 1) / 100  # reduce by 0.01

            if max_quantity < 0.01:
                print(f"  [CASH CHECK] ❌ Not enough cash even for 0.01 shares. Order REJECTED.")
                return 0, cash_info

            print(f"  [CASH CHECK] ⚠️ Order ${order_value:.2f} > Cash Power ${cash_power:.2f}")
            print(f"  [CASH CHECK] Reducing quantity: {quantity} → {max_quantity} (cash only, no margin)")
            return max_quantity, cash_info

    # ==================== PLACE ORDER ====================

    def place_order(self, symbol, side, quantity, price=None):
        """
        Place a market order with cash balance check.

        Flow:
          1. Check cash balance via accinfo_query()
          2. If not enough cash → reduce quantity (never use margin)
          3. If still not enough for 0.01 shares → reject
          4. Place order

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

        # Cash balance check (only for BUY orders)
        if side.lower() == "buy":
            allowed_qty, cash_info = self.check_cash_before_order(symbol, quantity, effective_price)

            if allowed_qty <= 0:
                return {"status": "rejected", "message": "Insufficient cash balance (no margin)"}

            if allowed_qty < quantity:
                print(f"  [ORDER] Quantity adjusted: {quantity} → {allowed_qty} due to cash limit")
                quantity = allowed_qty

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

    # ==================== HISTORICAL DATA ====================

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

    # ==================== ACCOUNT INFO ====================

    def get_account_info(self):
        """
        Get account info using accinfo_query().
        Falls back to defaults if API call fails.
        """
        cash_info = self.get_cash_balance()
        if cash_info:
            return {
                "cash": cash_info["us_cash"],
                "equity": cash_info["total_assets"],
                "cash_power": cash_info["usd_net_cash_power"],
                "available_funds": cash_info["available_funds"],
            }

        print("Warning: Using default equity values (could not fetch real data)")
        return {"cash": DEFAULT_EQUITY, "equity": DEFAULT_EQUITY, "cash_power": DEFAULT_EQUITY, "available_funds": DEFAULT_EQUITY}

    # ==================== POSITION CHECK (NEW - Prevents Duplicate Entries) ====================

    def get_positions(self, symbol=None):
        """
        Query current open positions using position_list_query() — Moomoo OpenAPI v10.7.

        This is the source of truth to prevent duplicate trades.
        Returns DataFrame with position details (code, qty, position_side, etc.).
        """
        if not self.trade_ctx or not self.acc_id:
            print("Warning: No trade context for position query")
            return pd.DataFrame()

        trd_env = TrdEnv.SIMULATE if self.use_real_paper else TrdEnv.REAL

        try:
            code_filter = f"US.{symbol}" if symbol else ""
            ret, data = self.trade_ctx.position_list_query(
                code=code_filter,
                trd_env=trd_env,
                acc_id=self.acc_id,
                refresh_cache=True
            )

            if ret == RET_OK:
                return data
            else:
                print(f"  [POSITION] position_list_query failed: {data}")
                return pd.DataFrame()

        except Exception as e:
            print(f"  [POSITION] Error querying positions: {e}")
            return pd.DataFrame()

    def has_open_position(self, symbol):
        """
        Check if the account already holds a position in the given symbol.
        Uses the official position_list_query API as the authoritative source.
        """
        positions = self.get_positions(symbol)
        if positions.empty:
            return False

        symbol_code = f"US.{symbol}" if not symbol.startswith("US.") else symbol
        matching = positions[positions['code'] == symbol_code]

        if not matching.empty:
            qty = float(matching.iloc[0].get('qty', 0))
            return qty > 0.0
        return False

    def get_open_positions_summary(self):
        """
        Return a clean list of current open positions (authoritative from API).
        Used for syncing open_trades and for dashboard display.
        """
        positions = self.get_positions()
        if positions.empty:
            return []

        summary = []
        for _, row in positions.iterrows():
            if float(row.get('qty', 0)) > 0:
                summary.append({
                    "symbol": str(row.get('code', '')).replace("US.", ""),
                    "qty": float(row.get('qty', 0)),
                    "can_sell_qty": float(row.get('can_sell_qty', 0)),
                    "cost_price": float(row.get('cost_price', 0)),
                    "market_val": float(row.get('market_val', 0)),
                    "unrealized_pl": float(row.get('unrealized_pl', 0)),
                    "position_side": str(row.get('position_side', '')),
                    "nominal_price": float(row.get('nominal_price', 0)),
                })
        print(f"  [POSITION] Found {len(summary)} open positions from account")
        return summary

    def get_symbols_with_positions(self):
        """
        Returns a SET of symbols that currently have open positions.
        This makes only ONE API call per cycle instead of one per symbol.
        This is the key optimization for staying under Moomoo rate limits.
        """
        positions = self.get_positions()  # No symbol filter → gets ALL positions at once
        if positions.empty:
            return set()

        symbols = set()
        for _, row in positions.iterrows():
            if float(row.get('qty', 0)) > 0:
                symbol = str(row.get('code', '')).replace("US.", "")
                symbols.add(symbol)

        if symbols:
            print(f"  [POSITION] Cached positions for symbols: {symbols}")
        return symbols
