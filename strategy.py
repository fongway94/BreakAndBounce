"""
Break & Bounce Strategy — Aligned with ProRealAlgos video

Video Strategy Rules (exact):
  Step 1 (Daily):    Box yesterday's high to low. This is the blueprint.
  Step 2 (15-min):   Wait for a 15-min candle CLOSE above box high (bullish) or below box low (bearish).
  Step 3 (5-min):    After breakout, wait for reversal candle AT the breakout level:
                      - Bullish breakout → Hammer (lower wick) or Bullish Engulfing
                      - Bearish breakout → Inverted Hammer (upper wick) or Bearish Engulfing
  Entry:
    Hammer →           enter at break of hammer HIGH
    Inverted Hammer →  enter at break of inverted hammer LOW
    Bullish Engulfing → enter at HIGH of previous (smaller) candle
    Bearish Engulfing → enter at LOW of previous (smaller) candle
  Stop Loss:
    Slightly below the LOW of the reversal candle (longs)
    Slightly above the HIGH of the reversal candle (shorts)
  Take Profit:
    2× risk (configurable via RISK_REWARD_RATIO)
  Time Filter:
    Only ENTER in first 2.5 hours (150 min) after market open.
    Force CLOSE any open trades near market close (not at end of entry window).
  Preceding Move:
    Hammer must come after clear red (negative) movement.
    Inverted Hammer must come after clear green (positive) movement.
"""

import pandas as pd
import numpy as np
from datetime import datetime, time
import pytz
from config import RISK_REWARD_RATIO


# ==================== TIME HELPERS ====================

def get_us_eastern_time():
    """Get current time in US Eastern Time"""
    eastern = pytz.timezone("US/Eastern")
    return datetime.now(eastern)


def is_within_trading_window(current_time, market_open_time):
    """Check if we're within the first 150 minutes after market open (for ENTRY only)."""
    minutes_since_open = (current_time.hour * 60 + current_time.minute) - \
                         (market_open_time.hour * 60 + market_open_time.minute)
    return 0 <= minutes_since_open <= 150


def is_near_market_close(current_time, market_close_time, buffer_minutes=10):
    """Check if we're near market close — used to force-close open trades."""
    minutes_to_close = (market_close_time.hour * 60 + market_close_time.minute) - \
                       (current_time.hour * 60 + current_time.minute)
    return 0 <= minutes_to_close <= buffer_minutes


# ==================== CANDLE VALIDATION ====================

def is_valid_candle(candle):
    """Basic OHLC validation."""
    return (candle['high'] >= max(candle['open'], candle['close']) and
            candle['low'] <= min(candle['open'], candle['close']))


# ==================== PATTERN DETECTION ====================

def is_hammer(candle):
    """
    Detect Hammer candle (long LOWER wick) — used for BULLISH reversal only.

    Video: "The wick represents that the largest buyer took advantage of this liquidity."
    Must come after a clear red (negative) movement.
    """
    if not is_valid_candle(candle):
        return False
    body = abs(candle['close'] - candle['open'])
    if body == 0:
        return False
    lower_wick = min(candle['open'], candle['close']) - candle['low']
    upper_wick = candle['high'] - max(candle['open'], candle['close'])
    return lower_wick > 2 * body and upper_wick < body * 1.0


def is_inverted_hammer(candle):
    """
    Detect Inverted Hammer candle (long UPPER wick) — used for BEARISH reversal only.

    Video: "You would have the wick coming from the top."
    Must come after a clear green (positive) movement.
    """
    if not is_valid_candle(candle):
        return False
    body = abs(candle['close'] - candle['open'])
    if body == 0:
        return False
    lower_wick = min(candle['open'], candle['close']) - candle['low']
    upper_wick = candle['high'] - max(candle['open'], candle['close'])
    return upper_wick > 2 * body and lower_wick < body * 1.0


def is_engulfing(prev_candle, current_candle, direction):
    """
    Detect Engulfing pattern.

    Video: "This large candle here engulfs the previous smaller candle,
            meaning that the low of the candle is lower than the previous candle's low,
            and that the high of the candle is higher than the previous candle's high."
    """
    if not is_valid_candle(prev_candle) or not is_valid_candle(current_candle):
        return False
    prev_body = abs(prev_candle['close'] - prev_candle['open'])
    curr_body = abs(current_candle['close'] - current_candle['open'])
    if curr_body < prev_body * 0.8:
        return False
    if direction == "bullish":
        return (prev_candle['close'] < prev_candle['open'] and          # prev is red
                current_candle['close'] > current_candle['open'] and    # current is green
                current_candle['close'] >= prev_candle['open'] and
                current_candle['open'] <= prev_candle['close'])
    elif direction == "bearish":
        return (prev_candle['close'] > prev_candle['open'] and          # prev is green
                current_candle['close'] < current_candle['open'] and    # current is red
                current_candle['close'] <= prev_candle['open'] and
                current_candle['open'] >= prev_candle['close'])
    return False


# ==================== PRECEDING MOVE CHECK ====================

def has_preceding_move(df_5m, direction, lookback=3):
    """
    Check if there's a clear directional move BEFORE the current candle.

    Video (Hammer):   "This must come after a clear red negative movement."
    Video (Inv Hammer): "comes after a clear green positive movement."

    We check the candles BEFORE the last candle (i.e., df_5m[-lookback-1:-1]).
    """
    if len(df_5m) < lookback + 1:
        return False

    recent = df_5m.iloc[-(lookback + 1):-1]

    if direction == "bullish":
        # Need at least 1 red (negative) candle in the lookback
        red_count = sum(1 for _, c in recent.iterrows() if c['close'] < c['open'])
        return red_count >= 1
    elif direction == "bearish":
        # Need at least 1 green (positive) candle in the lookback
        green_count = sum(1 for _, c in recent.iterrows() if c['close'] > c['open'])
        return green_count >= 1
    return False


# ==================== DATA HELPERS ====================

def get_previous_day_range(df_daily):
    """Step 1: Get previous day's high and low (the 'box')."""
    if len(df_daily) < 2:
        return None, None
    prev_day = df_daily.iloc[-2]
    return prev_day['high'], prev_day['low']


def align_timeframes(df_daily, df_15m, df_5m):
    """
    Synchronize all three timeframes to the same point in time.
    Uses the latest 5-min candle as the reference.
    """
    if df_5m.empty:
        return None, None, None
    latest_time = df_5m['time_key'].iloc[-1]

    df_daily = df_daily[df_daily['time_key'] < latest_time].copy()
    if len(df_daily) < 2:
        return None, None, None

    df_15m = df_15m[df_15m['time_key'] <= latest_time].copy()
    df_5m = df_5m[df_5m['time_key'] <= latest_time].copy()
    return df_daily, df_15m, df_5m


def has_recent_breakout(df_15m, prev_high, prev_low, lookback=3):
    """
    Step 2: Check if a 15-min candle CLOSED outside the box in the recent lookback.
    Returns 'bullish' or 'bearish' or None.
    """
    if len(df_15m) < lookback:
        return None
    recent = df_15m.tail(lookback)
    for _, candle in recent.iterrows():
        if candle['close'] > prev_high:
            return "bullish"
        elif candle['close'] < prev_low:
            return "bearish"
    return None


# ==================== REVERSAL ENTRY ====================

def check_reversal_entry(df_5m, direction, level):
    """
    Step 3: Check for a reversal candle at the breakout level.

    Returns a dict with pattern, entry price, and stop-loss reference price,
    or False if no valid reversal found.

    Video rules (per direction):
      Bullish breakout → Hammer (enter at high) or Bullish Engulfing (enter at prev high)
      Bearish breakout → Inverted Hammer (enter at low) or Bearish Engulfing (enter at prev low)

    Stop Loss reference:
      Based on the REVERSAL candle, not the daily box.
      Hammer → SL at hammer low
      Engulfing → SL at engulfing candle low (bullish) or high (bearish)
    """
    if len(df_5m) < 4:
        return False

    current = df_5m.iloc[-1]
    previous = df_5m.iloc[-2]

    # Price must be near the breakout level (0.15% tolerance)
    tolerance = level * 0.0015
    near_level = (abs(current['low'] - level) < tolerance or
                  abs(current['high'] - level) < tolerance or
                  abs(current['close'] - level) < tolerance)

    if not near_level:
        return False

    # Must have preceding directional move into the level
    if not has_preceding_move(df_5m, direction):
        return False

    if direction == "bullish":
        # ---- Bullish breakout → Hammer or Bullish Engulfing ----

        if is_hammer(current):
            # Video: "enter at the break of this 5-minute hammer candle"
            # Video: "stop loss would be set at the low"
            return {
                "pattern": "hammer",
                "entry": current['high'],          # break of hammer high
                "sl_ref": current['low'],           # SL at hammer low
            }

        if is_engulfing(previous, current, "bullish"):
            # Video: "set my long entry here at the high of this red candle"
            # Video: "stop loss slightly below the low of the engulfing candle"
            return {
                "pattern": "bullish_engulfing",
                "entry": previous['high'],          # high of previous candle
                "sl_ref": current['low'],           # SL below engulfing candle low
            }

    elif direction == "bearish":
        # ---- Bearish breakout → Inverted Hammer or Bearish Engulfing ----

        if is_inverted_hammer(current):
            # Video: "entry would be at the break of the candle"
            # Video: "stop loss slightly above the high"
            return {
                "pattern": "inverted_hammer",
                "entry": current['low'],            # break of inverted hammer low
                "sl_ref": current['high'],          # SL above inverted hammer high
            }

        if is_engulfing(previous, current, "bearish"):
            # Video: "enter the short trade already at the low of the previous green candle"
            # Video: "stop loss slightly above the high"
            return {
                "pattern": "bearish_engulfing",
                "entry": previous['low'],           # low of previous candle
                "sl_ref": current['high'],          # SL above engulfing candle high
            }

    return False


# ==================== RISK MANAGEMENT ====================

def calculate_position_size(account_equity, risk_percent, entry_price, stop_loss_price, min_lot=0.01):
    """Position sizing with fractional shares (max 2 decimal places)."""
    if entry_price == stop_loss_price:
        return round(min_lot, 2)

    risk_per_share = abs(entry_price - stop_loss_price)
    risk_amount = account_equity * risk_percent

    if risk_per_share <= 0:
        return round(min_lot, 2)

    size = risk_amount / risk_per_share
    return round(max(min_lot, size), 2)


def check_daily_loss_limit(daily_pnl, max_daily_loss):
    """Check if daily loss limit has been hit."""
    return daily_pnl <= -max_daily_loss


def calculate_stop_loss(direction, sl_ref_price, buffer_percent=0.0005):
    """
    Calculate mechanical stop loss.

    Video: "slightly below the low" (longs) / "slightly above the high" (shorts)
    The sl_ref_price comes from the reversal candle (not the daily box).
    """
    if direction == "buy":
        buffer = sl_ref_price * buffer_percent
        return round(sl_ref_price - buffer, 2)
    else:
        buffer = sl_ref_price * buffer_percent
        return round(sl_ref_price + buffer, 2)


def calculate_take_profit(entry_price, direction, stop_loss, risk_reward=None):
    """
    Calculate take profit using risk-reward ratio.
    Default from config (RISK_REWARD_RATIO = 2.0).
    """
    if risk_reward is None:
        risk_reward = RISK_REWARD_RATIO
    risk = abs(entry_price - stop_loss)
    if direction == "buy":
        return round(entry_price + (risk * risk_reward), 2)
    else:
        return round(entry_price - (risk * risk_reward), 2)


# ==================== MAIN SIGNAL GENERATOR ====================

def generate_signal(df_daily, df_15m, df_5m, market_open_time):
    """
    Main function — returns dict with full trade setup or None.

    Aligned with video:
      1. Daily box (previous day high/low)
      2. 15-min confirmed breakout (candle close outside box)
      3. 5-min reversal candle at the level (pattern-specific entry & SL)
    """
    current_time = get_us_eastern_time().time()

    # Only enter in first 150 minutes
    if not is_within_trading_window(current_time, market_open_time):
        return None

    # Align timeframes
    df_daily, df_15m, df_5m = align_timeframes(df_daily, df_15m, df_5m)
    if df_daily is None or df_15m is None or df_5m is None:
        return None

    # Step 1: Previous day range (the box)
    prev_high, prev_low = get_previous_day_range(df_daily)
    if prev_high is None or prev_low is None:
        return None

    # Step 2: Confirmed breakout on 15-min
    direction = has_recent_breakout(df_15m, prev_high, prev_low)
    if direction is None:
        return None

    level = prev_high if direction == "bullish" else prev_low

    # Step 3: Reversal candle at the level
    reversal = check_reversal_entry(df_5m, direction, level)
    if not reversal:
        return None

    # Calculate SL & TP based on reversal candle
    signal_side = "buy" if direction == "bullish" else "sell"
    entry_price = reversal["entry"]
    stop_loss = calculate_stop_loss(signal_side, reversal["sl_ref"])
    take_profit = calculate_take_profit(entry_price, signal_side, stop_loss)

    return {
        "signal": signal_side,
        "entry": round(entry_price, 2),
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "risk_reward": RISK_REWARD_RATIO,
        "pattern": reversal["pattern"],
        "level": level,
    }
