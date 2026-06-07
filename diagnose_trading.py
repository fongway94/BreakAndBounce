from moomoo import *
import os
from dotenv import load_dotenv

load_dotenv()

def test_another_stock(symbol="TSLA"):
    host = "127.0.0.1"
    port = 11111
    
    print(f"=== Testing Order for {symbol} ===")
    
    try:
        trd_ctx = OpenSecTradeContext(
            filter_trdmarket=TrdMarket.US,
            host=host,
            port=port,
            security_firm=SecurityFirm.FUTUINC
        )
        
        ret, data = trd_ctx.get_acc_list()
        if ret == RET_OK and not data.empty:
            acc_id = data['acc_id'][0]
            print(f"Using acc_id: {acc_id}")
            
            print(f"\nPlacing order for {symbol}...")
            ret_order, data_order = trd_ctx.place_order(
                acc_id=acc_id,
                price=0.01,                    # Small positive price
                qty=1,
                code=f"US.{symbol}",
                trd_side=TrdSide.BUY,
                order_type=OrderType.MARKET,
                trd_env=TrdEnv.SIMULATE
            )
            if ret_order == RET_OK:
                print(f"✅ Order placed successfully for {symbol}!")
                print(f"   Order data: {data_order}")
            else:
                print(f"❌ Order failed for {symbol}: {data_order}")
        else:
            print(f"Failed to get account list: {data}")
        
        trd_ctx.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Change the symbol below to test different stocks
    test_another_stock("TSLA")   # ← Change this to test other stocks (e.g. "NVDA", "MSFT", "GOOGL")
