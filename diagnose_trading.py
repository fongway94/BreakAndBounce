from moomoo import *
import os
from dotenv import load_dotenv

load_dotenv()

def diagnose_v2():
    host = "127.0.0.1"
    port = 11111
    
    print("=== Diagnostic v2: Skip Unlock ===")
    
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
            
            # Try placing order WITHOUT unlock
            print("\nTrying place_order directly (no unlock)...")
            ret_order, data_order = trd_ctx.place_order(
                acc_id=acc_id,
                price=0,
                qty=1,
                code="US.AAPL",
                trd_side=TrdSide.BUY,
                order_type=OrderType.NORMAL,
                trd_env=TrdEnv.SIMULATE
            )
            if ret_order == RET_OK:
                print(f"✅ Order placed successfully: {data_order}")
            else:
                print(f"❌ Order failed: {data_order}")
        else:
            print(f"Failed to get account list: {data}")
        
        trd_ctx.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    diagnose_v2()
