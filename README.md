# Break & Bounce Trading Bot

Automated trading system based on the "Break & Bounce" strategy from ProRealAlgos.

## Features
- Exact 3-step strategy (Daily box → 15m breakout → 5m reversal)
- Mechanical Stop Loss & Take Profit (1:2 R:R)
- Force close at end of 150-minute window
- Paper trading mode
- Telegram notifications
- Streamlit dashboard with trade log

## Setup Instructions

1. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```

2. Create `.env` file with your Telegram credentials.

3. Edit `config.py` (set mode and symbols).

4. Make sure openD is running.

5. Run test:
   ```bash
   python test_system.py
   ```

6. Run dashboard:
   ```bash
   streamlit run dashboard.py
   ```

7. Run bot:
   ```bash
   python main.py
   ```

## Important
- Start in **paper** mode.
- Only trades in first 150 minutes after market open.
- Will force close trades at end of window.