# data/atr.py
"""
Average True Range (ATR) calculator compatible with OHLCV data structure
Uses high, low, and close prices from 6-element OHLCV data
ATR = Moving average of True Range over period (typically 14 days)
True Range = max(high - low, |high - prev_close|, |low - prev_close|)
"""

from datetime import datetime, timedelta
import sys
import os
from .cache_manager import load_from_cache, save_to_cache

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import RSI_PERIOD  # We can use same period as RSI, or define ATR_PERIOD
from . import eth_price

# ATR typically uses 14-period moving average
ATR_PERIOD = 14

def get_metadata():
    """Returns metadata describing how ATR should be displayed"""
    return {
        'label': f'ATR ({ATR_PERIOD})',
        'yAxisId': 'indicator',
        'yAxisLabel': 'ATR Value',
        'unit': '$',
        'chartType': 'line',
        'color': '#9C27B0',  # Purple
        'strokeWidth': 2,
        'description': f'{ATR_PERIOD}-period Average True Range for ETH - measures volatility'
    }

def calculate_true_range(ohlcv_data):
    """
    Calculate True Range for each period
    TR = max(high - low, |high - prev_close|, |low - prev_close|)
    
    Args:
        ohlcv_data: List of [timestamp, open, high, low, close, volume]
    
    Returns:
        List of true range values
    """
    if len(ohlcv_data) < 2:
        return []
    
    true_ranges = []
    
    # First period: TR = high - low (no previous close)
    first_high = ohlcv_data[0][2]
    first_low = ohlcv_data[0][3]
    true_ranges.append(first_high - first_low)
    
    # Subsequent periods: TR = max of three calculations
    for i in range(1, len(ohlcv_data)):
        high = ohlcv_data[i][2]
        low = ohlcv_data[i][3]
        prev_close = ohlcv_data[i-1][4]
        
        # Calculate three values
        high_low = high - low
        high_prev_close = abs(high - prev_close)
        low_prev_close = abs(low - prev_close)
        
        # True Range is the maximum
        tr = max(high_low, high_prev_close, low_prev_close)
        true_ranges.append(tr)
    
    return true_ranges

def calculate_atr(true_ranges, period=ATR_PERIOD):
    """
    Calculate Average True Range using smoothed moving average
    First ATR = Simple average of first 'period' TRs
    Subsequent ATR = ((Previous ATR × (period - 1)) + Current TR) / period
    
    This is Wilder's smoothing method
    """
    if len(true_ranges) < period:
        return []
    
    atr_values = []
    
    # First ATR: Simple average of first 'period' true ranges
    first_atr = sum(true_ranges[:period]) / period
    atr_values.append(first_atr)
    
    # Subsequent ATRs: Wilder's smoothing
    current_atr = first_atr
    for i in range(period, len(true_ranges)):
        current_tr = true_ranges[i]
        current_atr = ((current_atr * (period - 1)) + current_tr) / period
        atr_values.append(current_atr)
    
    return atr_values

def get_data(days='365'):
    """Fetches ETH OHLCV data and calculates ATR from high, low, close prices"""
    metadata = get_metadata()
    dataset_name = 'atr'
    
    try:
        # Request extra days for ATR calculation
        if days == 'max':
            request_days = 'max'
        else:
            request_days = str(int(days) + ATR_PERIOD + 10)  # Extra buffer
        
        # Get ETH OHLCV data
        eth_data = eth_price.get_data(request_days)
        
        if not eth_data or not eth_data.get('data') or len(eth_data['data']) == 0:
            print("No ETH data available for ATR calculation")
            # Try loading from cache
            cached_data = load_from_cache(dataset_name)
            if cached_data:
                # Filter cached data to requested days
                if days != 'max':
                    cutoff_date = datetime.now() - timedelta(days=int(days))
                    cutoff_ms = int(cutoff_date.timestamp() * 1000)
                    cached_data = [d for d in cached_data if d[0] >= cutoff_ms]
                return {'metadata': metadata, 'data': cached_data}
            return {'metadata': metadata, 'data': []}
        
        ohlcv_data = eth_data['data']
        
        # Verify we have OHLCV structure (6 elements)
        if ohlcv_data and len(ohlcv_data[0]) != 6:
            print(f"ERROR: ATR requires OHLCV data (6 components), got {len(ohlcv_data[0])}")
            return {'metadata': metadata, 'data': []}
        
        if len(ohlcv_data) < ATR_PERIOD:
            print(f"Insufficient data for ATR calculation (need at least {ATR_PERIOD} data points)")
            return {'metadata': metadata, 'data': []}
        
        print(f"Calculating ATR from {len(ohlcv_data)} OHLCV data points")
        
        # Calculate True Range for each period
        true_ranges = calculate_true_range(ohlcv_data)
        
        # Calculate ATR
        atr_values = calculate_atr(true_ranges, ATR_PERIOD)
        
        if not atr_values:
            print(f"Insufficient data for ATR calculation")
            return {'metadata': metadata, 'data': []}
        
        # Combine timestamps with ATR values
        # ATR starts at index ATR_PERIOD (after we have enough data)
        # CRITICAL FIX: First ATR value corresponds to day 14 (index 13)
        atr_data = []
        for i in range(len(atr_values)):
            timestamp = ohlcv_data[i + ATR_PERIOD - 1][0]  # FIXED: -1 for correct alignment
            atr_data.append([timestamp, atr_values[i]])
        
        # Save complete ATR data to cache
        save_to_cache(dataset_name, atr_data)
        print(f"Successfully calculated and cached {dataset_name}")
        print(f"ATR calculated from {len(ohlcv_data)} OHLCV points")
        
        # Show sample ATR values
        print(f"Sample ATR values:")
        for i in range(min(3, len(atr_data))):
            dt = datetime.fromtimestamp(atr_data[i][0] / 1000)
            print(f"  {dt.date()}: ATR = ${atr_data[i][1]:.2f}")
        
        # Trim to requested days if not 'max'
        if days != 'max':
            cutoff_date = datetime.now() - timedelta(days=int(days))
            cutoff_ms = int(cutoff_date.timestamp() * 1000)
            atr_data = [d for d in atr_data if d[0] >= cutoff_ms]
        
        return {
            'metadata': metadata,
            'data': atr_data
        }
        
    except Exception as e:
        print(f"Error calculating ATR: {e}. Loading from cache.")
        import traceback
        traceback.print_exc()
        
        cached_data = load_from_cache(dataset_name)
        if cached_data:
            # Filter cached data to requested days
            if days != 'max':
                cutoff_date = datetime.now() - timedelta(days=int(days))
                cutoff_ms = int(cutoff_date.timestamp() * 1000)
                cached_data = [d for d in cached_data if d[0] >= cutoff_ms]
            return {'metadata': metadata, 'data': cached_data}
        return {'metadata': metadata, 'data': []}