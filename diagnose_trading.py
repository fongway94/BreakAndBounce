from moomoo import *
import os
from dotenv import load_dotenv

load_dotenv()

def diagnose():
    host = "127.0.0.1"
    port = 11111
    password = os.getenv("MOOMOO_TRADING_PASSWORD", "")
    
    print("=" * 60)
    print("MOOMOO TRADING DIAGNOSTIC")
    print("=" * 60)
    
    print(f"\n[1] Password loaded: {'Yes' if password else 'No'}")
    print(f"    Password length: {len(password)}")
    
    try:
        print("\n[2] Creating OpenSecTradeContext...")
        trd_ctx = OpenSecTradeContext(
            filter_trdmarket=TrdMarket.US,
            host=host,
            port=port,
            security_firm=SecurityFirm.FUTUINC
        )
        print("    ✓ OpenSecTradeContext created successfully")
        
        # Get account list
        print("\n[3] Calling get_acc_list()...")
        ret, data = trd_ctx.get_acc_list()
        
        if ret == RET_OK:
            print("    ✓ get_acc_list() succeeded")
            print("\n    Full account data:")
            print(data)
            print("\n    Columns:", list(data.columns))
            
            if not data.empty:
                print("\n    Available acc_ids:", data['acc_id'].values.tolist())
                acc_id = data['acc_id'][0]
                print(f"    Using acc_id: {acc_id}")
                
                # Try to unlock
                print("\n[4] Attempting to unlock trade...")
                ret_unlock, data_unlock = trd_ctx.unlock_trade(password)
                if ret_unlock == RET_OK:
                    print("    ✓ Unlock successful")
                    
                    # Try a test order
                    print("\n[5] Attempting test order (buy 1 AAPL)...")
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
                        print("    ✓ Order placed successfully!")
                        print(f"    Order data: {data_order}")
                    else:
                        print(f"    ✗ Order failed: {data_order}")
                else:
                    print(f"    ✗ Unlock failed: {data_unlock}")
            else:
                print("    ✗ No accounts returned")
        else:
            print(f"    ✗ get_acc_list() failed: {data}")
        
        trd_ctx.close()
        print("\n[6] Connection closed")
        
    except Exception as e:
        print(f"\n✗ Error: {type(e).__name__}: {e}")
    
    print("\n" + "=" * 60)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    diagnose()
