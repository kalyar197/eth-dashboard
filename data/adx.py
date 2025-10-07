# data/adx.py
"""
ADX (Average Directional Index) calculator
Uses OHLCV data structure: high, low, close
ADX measures trend strength (not direction)
ADX > 25 = Strong trend, ADX < 20 = Weak/no trend
"""

from datetime import datetime, timedelta
import sys
import os
from .cache_manager import load_from_cache, save_to_cache

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from . import eth_price

# ADX standard period
ADX_PERIOD = 14

def get_metadata():
    """Returns metadata describing how ADX should be displayed"""
    return {
        'label': f'ADX ({ADX_PERIOD})',
        'yAxisId': 'indicator',
        'yAxisLabel': 'ADX',
        'unit': '',
        'chartType': 'line',
        'color': '#673AB7',  # Deep Purple
        'strokeWidth': 2,
        'description': f'{ADX_PERIOD}-period Average Directional Index - measures trend strength',
        'yDomain': [0, 100],
        'referenceLines': [
            {'value': 25, 'label': 'Strong Trend', 'color': '#4CAF50', 'strokeDasharray': '5,5'},
            {'value': 20, 'label': 'Weak Trend', 'color': '#FFC107', 'strokeDasharray': '5,5'}
        ]
    }

def calculate_true_range(ohlcv_data):
    """Calculate True Range (same as ATR)"""
    if len(ohlcv_data) < 2:
        return []
    
    true_ranges = []
    
    # First period
    first_high = ohlcv_data[0][2]
    first_low = ohlcv_data[0][3]
    true_ranges.append(first_high - first_low)
    
    # Subsequent periods
    for i in range(1, len(ohlcv_data)):
        high = ohlcv_data[i][2]
        low = ohlcv_data[i][3]
        prev_close = ohlcv_data[i-1][4]
        
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        true_ranges.append(tr)
    
    return true_ranges

def calculate_directional_movement(ohlcv_data):
    """
    Calculate +DM and -DM (Directional Movement)
    +DM = current high - previous high (if positive and > -DM, else 0)
    -DM = previous low - current low (if positive and > +DM, else 0)
    """
    if len(ohlcv_data) < 2:
        return [], []
    
    plus_dm = []
    minus_dm = []
    
    # First value is 0
    plus_dm.append(0)
    minus_dm.append(0)
    
    for i in range(1, len(ohlcv_data)):
        high = ohlcv_data[i][2]
        low = ohlcv_data[i][3]
        prev_high = ohlcv_data[i-1][2]
        prev_low = ohlcv_data[i-1][3]
        
        up_move = high - prev_high
        down_move = prev_low - low
        
        if up_move > down_move and up_move > 0:
            plus_dm.append(up_move)
        else:
            plus_dm.append(0)
        
        if down_move > up_move and down_move > 0:
            minus_dm.append(down_move)
        else:
            minus_dm.append(0)
    
    return plus_dm, minus_dm

def calculate_smoothed_average(values, period):
    """Calculate Wilder's smoothed average"""
    if len(values) < period:
        return []
    
    smoothed = []
    
    # First value is simple average
    first_avg = sum(values[:period]) / period
    smoothed.append(first_avg)
    
    # Subsequent values use Wilder's smoothing
    current = first_avg
    for i in range(period, len(values)):
        current = (current * (period - 1) + values[i]) / period
        smoothed.append(current)
    
    return smoothed

def calculate_adx(ohlcv_data, period=ADX_PERIOD):
    """
    Calculate ADX (Average Directional Index)
    
    Steps:
    1. Calculate True Range, +DM, -DM
    2. Smooth them over period
    3. Calculate +DI and -DI
    4. Calculate DX
    5. Smooth DX to get ADX
    """
    if len(ohlcv_data) < period * 2:
        return []
    
    # Step 1: Calculate TR, +DM, -DM
    tr = calculate_true_range(ohlcv_data)
    plus_dm, minus_dm = calculate_directional_movement(ohlcv_data)
    
    # Step 2: Smooth TR, +DM, -DM
    smoothed_tr = calculate_smoothed_average(tr, period)
    smoothed_plus_dm = calculate_smoothed_average(plus_dm, period)
    smoothed_minus_dm = calculate_smoothed_average(minus_dm, period)
    
    if not smoothed_tr or not smoothed_plus_dm or not smoothed_minus_dm:
        return []
    
    # Step 3: Calculate +DI and -DI
    plus_di = []
    minus_di = []
    
    for i in range(len(smoothed_tr)):
        if smoothed_tr[i] > 0:
            plus_di.append((smoothed_plus_dm[i] / smoothed_tr[i]) * 100)
            minus_di.append((smoothed_minus_dm[i] / smoothed_tr[i]) * 100)
        else:
            plus_di.append(0)
            minus_di.append(0)
    
    # Step 4: Calculate DX
    dx = []
    for i in range(len(plus_di)):
        di_sum = plus_di[i] + minus_di[i]
        if di_sum > 0:
            di_diff = abs(plus_di[i] - minus_di[i])
            dx_value = (di_diff / di_sum) * 100
            dx.append(dx_value)
        else:
            dx.append(0)
    
    # Step 5: Smooth DX to get ADX
    adx = calculate_smoothed_average(dx, period)
    
    return adx

def get_data(days='365'):
    """Fetches ETH OHLCV data and calculates ADX"""
    metadata = get_metadata()
    dataset_name = 'adx'
    
    try:
        # Request extra days for ADX calculation
        if days == 'max':
            request_days = 'max'
        else:
            request_days = str(int(days) + ADX_PERIOD * 3 + 10)
        
        # Get ETH OHLCV data
        eth_data = eth_price.get_data(request_days)
        
        if not eth_data or not eth_data.get('data') or len(eth_data['data']) == 0:
            print("No ETH data available for ADX calculation")
            cached_data = load_from_cache(dataset_name)
            if cached_data:
                if days != 'max':
                    cutoff_date = datetime.now() - timedelta(days=int(days))
                    cutoff_ms = int(cutoff_date.timestamp() * 1000)
                    cached_data = [d for d in cached_data if d[0] >= cutoff_ms]
                return {'metadata': metadata, 'data': cached_data}
            return {'metadata': metadata, 'data': []}
        
        ohlcv_data = eth_data['data']
        
        # Verify we have OHLCV structure
        if ohlcv_data and len(ohlcv_data[0]) != 6:
            print(f"ERROR: ADX requires OHLCV data (6 components), got {len(ohlcv_data[0])}")
            return {'metadata': metadata, 'data': []}
        
        if len(ohlcv_data) < ADX_PERIOD * 2:
            print(f"Insufficient data for ADX calculation (need at least {ADX_PERIOD * 2} points)")
            return {'metadata': metadata, 'data': []}
        
        print(f"Calculating ADX from {len(ohlcv_data)} OHLCV data points")
        
        # Calculate ADX
        adx_values = calculate_adx(ohlcv_data, ADX_PERIOD)
        
        if not adx_values:
            print("Insufficient data for ADX calculation")
            return {'metadata': metadata, 'data': []}
        
        # Align timestamps with ADX values
        # ADX starts after: period (TR smoothing) + period (DX smoothing) - 1
        adx_start_index = ADX_PERIOD * 2 - 2
        adx_data = []
        
        for i in range(len(adx_values)):
            timestamp = ohlcv_data[i + adx_start_index][0]
            adx_data.append([timestamp, adx_values[i]])
        
        # Save to cache
        save_to_cache(dataset_name, adx_data)
        print(f"Successfully calculated and cached {dataset_name}")
        
        # Show sample ADX values
        print(f"Sample ADX values:")
        for i in range(min(3, len(adx_data))):
            dt = datetime.fromtimestamp(adx_data[i][0] / 1000)
            adx_val = adx_data[i][1]
            trend_strength = "Strong" if adx_val > 25 else "Weak" if adx_val < 20 else "Moderate"
            print(f"  {dt.date()}: ADX = {adx_val:.2f} ({trend_strength} trend)")
        
        # Trim to requested days
        if days != 'max':
            cutoff_date = datetime.now() - timedelta(days=int(days))
            cutoff_ms = int(cutoff_date.timestamp() * 1000)
            adx_data = [d for d in adx_data if d[0] >= cutoff_ms]
        
        return {
            'metadata': metadata,
            'data': adx_data
        }
        
    except Exception as e:
        print(f"Error calculating ADX: {e}. Loading from cache.")
        import traceback
        traceback.print_exc()
        
        cached_data = load_from_cache(dataset_name)
        if cached_data:
            if days != 'max':
                cutoff_date = datetime.now() - timedelta(days=int(days))
                cutoff_ms = int(cutoff_date.timestamp() * 1000)
                cached_data = [d for d in cached_data if d[0] >= cutoff_ms]
            return {'metadata': metadata, 'data': cached_data}
        return {'metadata': metadata, 'data': []}
