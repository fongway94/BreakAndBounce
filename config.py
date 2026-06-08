import os
from dotenv import load_dotenv

load_dotenv()

# ==================== TRADING MODE ====================
TRADING_MODE = "paper"
USE_REAL_PAPER_TRADING = True        # Must be True for paper trading (was False = caused acc_id bug)

# ==================== SYMBOLS ====================
SYMBOLS = [
    # US Tech Stocks
    "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "AMD",
    # Other Popular Stocks
    "JPM", "V", "MA", "NFLX", "DIS",
]

# ==================== TIME SETTINGS (US Eastern) ====================
MARKET_OPEN_TIME = "09:30"
MARKET_CLOSE_TIME = "16:00"              # Force close near market close (per video)
TRADING_WINDOW_MINUTES = 150             # Only ENTER trades in first 2.5 hours
FORCE_CLOSE_BUFFER_MINUTES = 10          # Force close trades this many minutes before market close

# ==================== RISK SETTINGS ====================
DEFAULT_EQUITY = 50000
RISK_PER_TRADE = 0.01                    # 1% risk per trade
RISK_REWARD_RATIO = 2.0                  # 1:2 risk-reward (video uses 2:1 and 3:1)
MAX_DAILY_LOSS = 500

# ==================== TELEGRAM ====================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ==================== MOOMOO / openD ====================
MOOMOO_HOST = "127.0.0.1"
MOOMOO_PORT = 11111
MOOMOO_TRADING_PASSWORD = os.getenv("MOOMOO_TRADING_PASSWORD", "")

# ==================== LOGGING ====================
LOG_FILE = "logs/trade_log.csv"
