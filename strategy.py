import pandas as pd
import numpy as np
from datetime import datetime, time

def is_valid_candle(candle):
    return candle['high'] >= max(candle['open'], candle['close']) and \
           candle['low'] <= min(candle['open'], candle['close'])

def is_hammer(candle):
    if not is_valid_candle(candle):
        return False
    body = abs(candle['close'] - candle['open'])
    if body == 0:
        return False
    lower_wick = min(candle['open'], candle['close']) - candle['low']
    upper_wick = candle['high'] - max(candle['open'], candle['close'])
    if lower_wick > 2 * body and upper_wick < body * 0.5:
        return True
    if upper_wick > 2 * body and lower_wick < body * 0.5:
        return True
    return False

def is_engulfing(prev_candle, current_candle, direction):
    if not is_valid_candle(prev_candle) or not is_valid_candle(current_candle):
        return False
    prev_body = abs(prev_candle['close'] - prev_candle['open'])
    curr_body = abs(current_candle['close'] - current_candle['open'])
    if curr_body < prev_body * 0.8:
        return False
    if direction == "bullish":
        return (prev_candle['close'] < prev_candle['open'] and
                current_candle['close'] > current_candle['open'] and
                current_candle['close'] >= prev_candle['open'] and
                current_candle['open'] <= prev_candle['close'])
    elif direction == "bearish":
        return (prev_candle['close'] > prev_candle['open'] and
                current_candle['close'] < current_candle['open'] and
                current_candle['close'] <= prev_candle['open'] and
                current_candle['open'] >= prev_candle['close'])
    return False

def get_previous_day_range(df_daily):
    if len(df_daily) < 2:
        return None, None
    prev_day = df_daily.iloc[-2]
    return prev_day['high'], prev_day['low']

def align_timeframes(df_daily, df_15m, df_5m):
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
    if len(df_15m) < lookback:
        return None
    recent = df_15m.tail(lookback)
    for _, candle in recent.iterrows():
        if candle['close'] > prev_high:
            return "bullish"
        elif candle['close'] < prev_low:
            return "bearish"
    return None

def check_reversal_entry(df_5m, direction, level):
    if len(df_5m) < 3:
        return False
    current = df_5m.iloc[-1]
    previous = df_5m.iloc[-2]
    tolerance = level * 0.0015
    near_level = (abs(current['low'] - level) < tolerance or 
                  abs(current['high'] - level) < tolerance or
                  abs(current['close'] - level) < tolerance)
    if not near_level:
        return False
    if direction == "bullish":
        if is_hammer(current) or is_engulfing(previous, current, "bullish"):
            return True
    elif direction == "bearish":
        if is_hammer(current) or is_engulfing(previous, current, "bearish"):
            return True
    return False

def is_within_trading_window(current_time, market_open_time):
    minutes_since_open = (current_time.hour * 60 + current_time.minute) - (market_open_time.hour * 60 + market_open_time.minute)
    return 0 <= minutes_since_open <= 150

def is_near_end_of_window(current_time, market_open_time, buffer_minutes=10):
    minutes_since_open = (current_time.hour * 60 + current_time.minute) - (market_open_time.hour * 60 + market_open_time.minute)
    return minutes_since_open >= (150 - buffer_minutes)

def calculate_position_size(account_equity, risk_percent, entry_price, stop_loss_price, min_lot=1):
    """Calculate position size based on risk percentage"""
    if entry_price == stop_loss_price:
        return min_lot
    risk_per_share = abs(entry_price - stop_loss_price)
    risk_amount = account_equity * risk_percent
    if risk_per_share <= 0:
        return min_lot
    size = risk_amount / risk_per_share
    return max(min_lot, round(size))

def check_daily_loss_limit(daily_pnl, max_daily_loss):
    """Check if daily loss limit has been hit"""
    return daily_pnl <= -max_daily_loss

def calculate_mechanical_stop_loss(entry_price, direction, daily_high, daily_low, reversal_low=None, reversal_high=None):
    box_height = daily_high - daily_low
    if direction == "buy":
        if reversal_low:
            stop = min(daily_low, reversal_low) - (box_height * 0.1)
        else:
            stop = daily_low - (box_height * 0.1)
        return round(stop, 2)
    else:
        if reversal_high:
            stop = max(daily_high, reversal_high) + (box_height * 0.1)
        else:
            stop = daily_high + (box_height * 0.1)
        return round(stop, 2)

def calculate_mechanical_take_profit(entry_price, direction, stop_loss, risk_reward=2.0):
    risk = abs(entry_price - stop_loss)
    if direction == "buy":
        return round(entry_price + (risk * risk_reward), 2)
    else:
        return round(entry_price - (risk * risk_reward), 2)

def generate_signal(df_daily, df_15m, df_5m, market_open_time):
    current_time = datetime.now().time()
    if not is_within_trading_window(current_time, market_open_time):
        return None
    
    df_daily, df_15m, df_5m = align_timeframes(df_daily, df_15m, df_5m)
    if df_daily is None or df_15m is None or df_5m is None:
        return None
    
    prev_high, prev_low = get_previous_day_range(df_daily)
    if prev_high is None or prev_low is None:
        return None
    
    direction = has_recent_breakout(df_15m, prev_high, prev_low)
    if direction is None:
        return None
    
    level = prev_high if direction == "bullish" else prev_low
    
    if check_reversal_entry(df_5m, direction, level):
        current_price = df_5m.iloc[-1]['close']
        stop_loss = calculate_mechanical_stop_loss(
            current_price, direction, prev_high, prev_low,
            reversal_low=df_5m.iloc[-1]['low'],
            reversal_high=df_5m.iloc[-1]['high']
        )
        take_profit = calculate_mechanical_take_profit(current_price, direction, stop_loss, risk_reward=2.0)
        
        return {
            "signal": "buy" if direction == "bullish" else "sell",
            "entry": round(current_price, 2),
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "risk_reward": 2.0
        }
    return None
