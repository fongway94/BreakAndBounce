import os
from dotenv import load_dotenv

load_dotenv()

# ==================== TRADING MODE ====================
TRADING_MODE = "paper"
USE_REAL_PAPER_TRADING = False

# ==================== SYMBOLS ====================
SYMBOLS = [
    # US Tech Stocks
    "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "AMD",
    # Other Popular Stocks
    "JPM", "V", "MA", "NFLX", "DIS",
]

# ==================== TIME SETTINGS ====================
MARKET_OPEN_TIME = "09:30"
TRADING_WINDOW_MINUTES = 150
FORCE_CLOSE_BUFFER_MINUTES = 10

# ==================== RISK SETTINGS ====================
DEFAULT_EQUITY = 50000
RISK_PER_TRADE = 0.01
RISK_REWARD_RATIO = 2.0
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
