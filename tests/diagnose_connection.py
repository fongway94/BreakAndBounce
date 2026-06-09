import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import USE_REAL_PAPER_TRADING
from moomoo import *

def diagnose():
    print("=== Moomoo OpenD Connection Diagnosis ===")
    print(f"USE_REAL_PAPER_TRADING = {USE_REAL_PAPER_TRADING}")
    
    host = "127.0.0.1"
    port = 11111
    
    print(f"\nTrying to connect to OpenD at {host}:{port}...")
    
    try:
        quote_ctx = OpenQuoteContext(host=host, port=port)
        print("✓ OpenQuoteContext connected successfully")
        quote_ctx.close()
    except Exception as e:
        print(f"✗ OpenQuoteContext failed: {e}")
        return
    
    print("\nTrying to create OpenUSTradeContext...")
    try:
        trade_ctx = OpenSecTradeContext(filter_trdmarket=TrdMarket.US, host=host, port=port, security_firm=SecurityFirm.FUTUINC)
        print("✓ OpenUSTradeContext created successfully")
        trade_ctx.close()
    except AttributeError as e:
        print(f"✗ OpenUSTradeContext not available: {e}")
    except Exception as e:
        print(f"✗ OpenUSTradeContext failed with error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    diagnose()
