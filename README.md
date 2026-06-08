# Break & Bounce Trading Bot

Automated trading system based on the "Break & Bounce" strategy from [ProRealAlgos](https://www.youtube.com/watch?v=xTTDH5iRhJc).

## Strategy (Exact Video Rules)
1. **Daily**: Box yesterday's high to low
2. **15-min**: Wait for candle CLOSE above box high (bullish) or below box low (bearish)
3. **5-min**: Wait for reversal candle AT the breakout level
   - Bullish breakout → Hammer or Bullish Engulfing
   - Bearish breakout → Inverted Hammer or Bearish Engulfing
4. **Entry**: Hammer/Inverted Hammer at candle close; Engulfing at prev candle high/low
5. **Stop Loss**: Based on reversal candle (slightly below/above)
6. **Take Profit**: 1:2 risk-reward (configurable)
7. **Time Filter**: Only ENTER in first 150 minutes (9:30–12:00 ET). Force CLOSE near market close (16:00 ET).

## Features
- Exact 3-step strategy (Daily box → 15m breakout → 5m reversal)
- Mechanical Stop Loss & Take Profit (1:2 R:R, configurable)
- Cash balance check before every order (no margin)
- Force close near market close (16:00 ET, not end of entry window)
- Paper trading mode via Moomoo OpenAPI v10.7
- Telegram notifications
- Streamlit dashboard with trade log
- Fractional shares (2 decimal places)

## Setup Instructions

1. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```

2. Create `.env` file (copy from `env.example`):
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   TELEGRAM_CHAT_ID=your_chat_id_here
   MOOMOO_TRADING_PASSWORD=your_trading_password_here
   ```

3. Edit `config.py` (set mode and symbols).

4. Make sure Moomoo openD is running on `127.0.0.1:11111`.

5. Run tests:
   ```bash
   python test_system.py
   python test_trade.py
   ```

6. Run dashboard:
   ```bash
   streamlit run dashboard.py
   ```

7. Run bot:
   ```bash
   python main.py
   ```

## Diagnostic Tools
- `python diagnose_connection.py` — Test openD connection
- `python diagnose_trading.py` — Test trading context
- `python check_accounts.py` — List available accounts
- `python test_unlock.py` — Test trade unlock with password
- `python test_time.py` — Verify US Eastern time & trading window

## Important
- Start in **paper** mode.
- `USE_REAL_PAPER_TRADING = True` in config (required for paper trading).
- Uses `from moomoo import *` (Moomoo OpenAPI v10.7).
- Cash only, no margin. Orders auto-reduced to fit cash buying power.
