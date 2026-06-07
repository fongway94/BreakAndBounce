from moomoo import *
import os
from dotenv import load_dotenv

load_dotenv()

def diagnose_v4():
    host = "127.0.0.1"
    port = 11111
    
    print("=== Diagnostic v4: Omit price parameter ===")
    
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
            
            # Try without passing price
            print("\nTrying place_order without price parameter...")
            ret_order, data_order = trd_ctx.place_order(
                acc_id=acc_id,
                qty=1,
                code="US.AAPL",
                trd_side=TrdSide.BUY,
                order_type=OrderType.MARKET,
                trd_env=TrdEnv.SIMULATE
                # price parameter is omitted
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
    diagnose_v4()
