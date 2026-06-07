def unlock_trade(self, password=""):
    """Unlock trading with password (required for real paper trading)"""
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

def place_order(self, symbol, side, quantity, price=None, order_type="MARKET", paper=True, password=""):
    if not self.trade_ctx:
        return {"status": "error", "message": "No trade context available"}
    
    # Unlock if not already unlocked
    if not self.unlocked:
        if not self.unlock_trade(password=password):
            return {"status": "error", "message": "Failed to unlock trade"}
    
    trd_env = ft.TrdEnv.SIMULATE if self.use_real_paper else ft.TrdEnv.REAL
    code = f"US.{symbol}" if not symbol.startswith("US.") else symbol
    
    print(f"[REAL PAPER ORDER] {side.upper()} {quantity} {code}")
    
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
        
