from moomoo import *

def check_accounts():
    host = "127.0.0.1"
    port = 11111
    
    print("=== Checking Available Trading Accounts ===")
    
    try:
        trd_ctx = OpenSecTradeContext(
            filter_trdmarket=TrdMarket.US,
            host=host,
            port=port,
            security_firm=SecurityFirm.FUTUINC
        )
        
        ret, data = trd_ctx.get_acc_list()
        
        if ret == RET_OK:
            print("\n✅ Successfully retrieved account list:")
            print(data)
            
            if not data.empty:
                print("\nAccount IDs available:")
                print(data['acc_id'].values.tolist())
                
                print("\nFirst account ID:")
                print(data['acc_id'][0])
            else:
                print("\nNo accounts found for US market.")
        else:
            print(f"\n❌ get_acc_list error: {data}")
        
        trd_ctx.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_accounts()
