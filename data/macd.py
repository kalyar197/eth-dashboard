# data/macd.py
"""
MACD (Moving Average Convergence Divergence) calculator
Uses OHLCV data structure to extract closing prices
MACD = 12-period EMA - 26-period EMA
Signal = 9-period EMA of MACD
Histogram = MACD - Signal
"""

from datetime import datetime, timedelta
import sys
import os
from .cache_manager import load_from_cache, save_to_cache
from .time_transformer import extract_component

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from . import btc_price

# MACD standard parameters
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

def get_metadata():
    """Returns metadata describing how MACD should be displayed"""
    return {
        'label': 'MACD',
        'yAxisId': 'indicator',
        'yAxisLabel': 'MACD',
        'unit': '',
        'chartType': 'line',
        'color': '#FF5722',  # Deep Orange
        'strokeWidth': 2,
        'description': f'MACD ({MACD_FAST},{MACD_SLOW},{MACD_SIGNAL}) - trend following momentum indicator',
        'additionalLines': [
            {'name': 'signal', 'color': '#FFC107', 'strokeWidth': 1.5},
            {'name': 'histogram', 'color': '#9E9E9E', 'strokeWidth': 1, 'chartType': 'bar'}
        ]
    }

def calculate_ema(prices, period):
    """
    Calculate Exponential Moving Average
    EMA = Price(t) × k + EMA(y) × (1 - k)
    where k = 2 / (period + 1)
    """
    if len(prices) < period:
        return []
    
    ema_values = []
    k = 2 / (period + 1)
    
    # First EMA is SMA
    first_ema = sum(prices[:period]) / period
    ema_values.append(first_ema)
    
    # Calculate remaining EMAs
    for i in range(period, len(prices)):
        ema = prices[i] * k + ema_values[-1] * (1 - k)
        ema_values.append(ema)
    
    return ema_values

def calculate_macd(closing_prices):
    """
    Calculate MACD, Signal, and Histogram
    
    Returns:
        tuple: (macd_line, signal_line, histogram)
    """
    if len(closing_prices) < MACD_SLOW:
        return [], [], []
    
    # Calculate 12-period EMA
    ema_fast = calculate_ema(closing_prices, MACD_FAST)
    
    # Calculate 26-period EMA
    ema_slow = calculate_ema(closing_prices, MACD_SLOW)
    
    if not ema_fast or not ema_slow:
        return [], [], []
    
    # Calculate MACD line (12 EMA - 26 EMA)
    # Align the EMAs (slow starts later)
    alignment_offset = MACD_SLOW - MACD_FAST
    macd_line = []
    for i in range(len(ema_slow)):
        macd_value = ema_fast[i + alignment_offset] - ema_slow[i]
        macd_line.append(macd_value)
    
    if len(macd_line) < MACD_SIGNAL:
        return macd_line, [], []
    
    # Calculate Signal line (9-period EMA of MACD)
    signal_line = calculate_ema(macd_line, MACD_SIGNAL)
    
    # Calculate Histogram (MACD - Signal)
    histogram = []
    signal_offset = len(macd_line) - len(signal_line)
    for i in range(len(signal_line)):
        hist_value = macd_line[i + signal_offset] - signal_line[i]
        histogram.append(hist_value)
    
    return macd_line, signal_line, histogram

def get_data(days='365'):
    """Fetches BTC OHLCV data and calculates MACD from closing prices"""
    metadata = get_metadata()
    dataset_name = 'macd'
    
    try:
        # Request extra days for MACD calculation
        if days == 'max':
            request_days = 'max'
        else:
            request_days = str(int(days) + MACD_SLOW + MACD_SIGNAL + 10)
        
        # Get BTC OHLCV data
        btc_data = btc_price.get_data(request_days)

        if not btc_data or not btc_data.get('data') or len(btc_data['data']) == 0:
            print("No BTC data available for MACD calculation")
            cached_data = load_from_cache(dataset_name)
            if cached_data:
                if days != 'max':
                    cutoff_date = datetime.now() - timedelta(days=int(days))
                    cutoff_ms = int(cutoff_date.timestamp() * 1000)
                    if 'macd' in cached_data:
                        cached_data['macd'] = [d for d in cached_data['macd'] if d[0] >= cutoff_ms]
                        cached_data['signal'] = [d for d in cached_data['signal'] if d[0] >= cutoff_ms]
                        cached_data['histogram'] = [d for d in cached_data['histogram'] if d[0] >= cutoff_ms]
                return {'metadata': metadata, 'data': cached_data}
            return {'metadata': metadata, 'data': {'macd': [], 'signal': [], 'histogram': []}}
        
        ohlcv_data = btc_data['data']
        
        # Check structure
        if ohlcv_data and len(ohlcv_data[0]) == 6:
            # Extract closing prices from OHLCV data
            print("Extracting closing prices from OHLCV data for MACD calculation")
            price_data = extract_component(ohlcv_data, 'close')
        elif ohlcv_data and len(ohlcv_data[0]) == 2:
            print("Using simple price data for MACD calculation")
            price_data = ohlcv_data
        else:
            print(f"Unexpected data structure: {len(ohlcv_data[0]) if ohlcv_data else 0} elements")
            return {'metadata': metadata, 'data': {'macd': [], 'signal': [], 'histogram': []}}
        
        if len(price_data) < MACD_SLOW + MACD_SIGNAL:
            print(f"Insufficient data for MACD calculation (need at least {MACD_SLOW + MACD_SIGNAL} points)")
            return {'metadata': metadata, 'data': {'macd': [], 'signal': [], 'histogram': []}}
        
        timestamps = [item[0] for item in price_data]
        closing_prices = [item[1] for item in price_data]
        
        print(f"Calculating MACD from {len(closing_prices)} price points")
        
        # Calculate MACD components
        macd_line, signal_line, histogram = calculate_macd(closing_prices)
        
        if not macd_line:
            print("Insufficient data for MACD calculation")
            return {'metadata': metadata, 'data': {'macd': [], 'signal': [], 'histogram': []}}
        
        # Align timestamps with MACD values
        macd_start_index = MACD_SLOW - 1
        macd_data = [[timestamps[i + macd_start_index], macd_line[i]] for i in range(len(macd_line))]
        
        signal_start_index = macd_start_index + MACD_SIGNAL - 1
        signal_data = [[timestamps[i + signal_start_index], signal_line[i]] for i in range(len(signal_line))]
        
        histogram_data = [[timestamps[i + signal_start_index], histogram[i]] for i in range(len(histogram))]
        
        # Save to cache
        macd_full_data = {
            'macd': macd_data,
            'signal': signal_data,
            'histogram': histogram_data
        }
        save_to_cache(dataset_name, macd_full_data)
        print(f"Successfully calculated and cached {dataset_name}")
        
        # Show samples
        if signal_data:
            dt = datetime.fromtimestamp(signal_data[-1][0] / 1000)
            print(f"Latest: {dt.date()} MACD={signal_data[-1][1]:.2f}")
        
        # Trim to requested days
        if days != 'max':
            cutoff_date = datetime.now() - timedelta(days=int(days))
            cutoff_ms = int(cutoff_date.timestamp() * 1000)
            
            macd_data = [d for d in macd_data if d[0] >= cutoff_ms]
            signal_data = [d for d in signal_data if d[0] >= cutoff_ms]
            histogram_data = [d for d in histogram_data if d[0] >= cutoff_ms]
        
        return {
            'metadata': metadata,
            'data': {
                'macd': macd_data,
                'signal': signal_data,
                'histogram': histogram_data
            }
        }
        
    except Exception as e:
        print(f"Error calculating MACD: {e}. Loading from cache.")
        import traceback
        traceback.print_exc()
        
        cached_data = load_from_cache(dataset_name)
        if cached_data:
            if days != 'max':
                cutoff_date = datetime.now() - timedelta(days=int(days))
                cutoff_ms = int(cutoff_date.timestamp() * 1000)
                if 'macd' in cached_data:
                    cached_data['macd'] = [d for d in cached_data['macd'] if d[0] >= cutoff_ms]
                    cached_data['signal'] = [d for d in cached_data['signal'] if d[0] >= cutoff_ms]
                    cached_data['histogram'] = [d for d in cached_data['histogram'] if d[0] >= cutoff_ms]
            return {'metadata': metadata, 'data': cached_data}
        return {'metadata': metadata, 'data': {'macd': [], 'signal': [], 'histogram': []}}
