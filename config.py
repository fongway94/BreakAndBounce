import os
from dotenv import load_dotenv

load_dotenv()

# ==================== TRADING MODE ====================
# Options: "backtest", "paper", "live"
TRADING_MODE = "paper"

# ==================== SYMBOLS ====================
SYMBOLS = [
    # US Tech Stocks
    "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "AMD",
    # Other Popular Stocks
    "JPM", "V", "MA", "NFLX", "DIS",
    # US Indices
    "US100", "US500", "SPX",
    # European Indices
    "DE40", "UK100", "FR40",
    # Asian Indices
    "HKHSI",
]

# ==================== TIME SETTINGS ====================
TRADING_WINDOW_MINUTES = 150
MARKET_OPEN_TIME = "09:30"

# ==================== TELEGRAM ====================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ==================== MOOMOO / openD ====================
MOOMOO_HOST = "127.0.0.1"
MOOMOO_PORT = 11111
MOOMOO_TRADING_PASSWORD = os.getenv("MOOMOO_TRADING_PASSWORD", "")

# ==================== RISK MANAGEMENT ====================
MAX_DAILY_LOSS = 500
RISK_PER_TRADE = 0.01

# ==================== LOGGING ====================
LOG_FILE = "logs/trade_log.csv"
