from moomoo import *
from dotenv import load_dotenv
import os

load_dotenv()

def test_unlock():
    host = "127.0.0.1"
    port = 11111
    password = os.getenv("MOOMOO_TRADING_PASSWORD", "")
    
    print("=== Testing Unlock Trade ===")
    print(f"Password loaded: {'Yes' if password else 'No (empty)'}")
    
    try:
        trd_ctx = OpenSecTradeContext(
            filter_trdmarket=TrdMarket.US,
            host=host,
            port=port,
            security_firm=SecurityFirm.FUTUINC
        )
        print("OpenSecTradeContext created successfully")
        
        if not password:
            print("ERROR: No trading password found in .env")
            trd_ctx.close()
            return
        
        ret, data = trd_ctx.unlock_trade(password)
        
        if ret == RET_OK:
            print("✅ Unlock successful!")
        else:
            print(f"❌ Unlock failed: {data}")
        
        trd_ctx.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_unlock()
