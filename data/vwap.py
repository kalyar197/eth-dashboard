# data/vwap.py
"""
Volume Weighted Average Price (VWAP) calculator
Uses OHLCV data structure: high, low, close, volume
VWAP = Cumulative(Typical Price × Volume) / Cumulative(Volume)
Typical Price = (High + Low + Close) / 3
"""

from datetime import datetime, timedelta
import sys
import os
from .cache_manager import load_from_cache, save_to_cache

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from . import btc_price

def get_metadata():
    """Returns metadata describing how VWAP should be displayed"""
    return {
        'label': 'VWAP',
        'yAxisId': 'price_usd',
        'yAxisLabel': 'Price (USD)',
        'unit': '$',
        'chartType': 'line',
        'color': '#00BCD4',  # Cyan
        'strokeWidth': 2,
        'description': 'Volume Weighted Average Price - shows true average price weighted by volume'
    }

def calculate_vwap(ohlcv_data):
    """
    Calculate Volume Weighted Average Price
    VWAP = Cumulative(Typical Price × Volume) / Cumulative(Volume)
    
    Args:
        ohlcv_data: List of [timestamp, open, high, low, close, volume]
    
    Returns:
        List of [timestamp, vwap_value]
    """
    if len(ohlcv_data) < 1:
        return []
    
    vwap_values = []
    cumulative_tp_volume = 0  # Cumulative (Typical Price × Volume)
    cumulative_volume = 0      # Cumulative Volume
    
    for point in ohlcv_data:
        timestamp = point[0]
        high = point[2]
        low = point[3]
        close = point[4]
        volume = point[5]
        
        # Calculate Typical Price
        typical_price = (high + low + close) / 3
        
        # Update cumulatives
        cumulative_tp_volume += typical_price * volume
        cumulative_volume += volume
        
        # Calculate VWAP
        if cumulative_volume > 0:
            vwap = cumulative_tp_volume / cumulative_volume
            vwap_values.append([timestamp, vwap])
        else:
            # If no volume, use typical price
            vwap_values.append([timestamp, typical_price])
    
    return vwap_values

def get_data(days='365'):
    """Fetches BTC OHLCV data and calculates VWAP"""
    metadata = get_metadata()
    dataset_name = 'vwap'
    
    try:
        # Get BTC OHLCV data
        if days == 'max':
            request_days = 'max'
        else:
            request_days = str(int(days) + 10)  # Extra buffer

        btc_data = btc_price.get_data(request_days)

        if not btc_data or not btc_data.get('data') or len(btc_data['data']) == 0:
            print("No BTC data available for VWAP calculation")
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
        
        ohlcv_data = btc_data['data']
        
        # Verify we have OHLCV structure (6 elements)
        if ohlcv_data and len(ohlcv_data[0]) != 6:
            print(f"ERROR: VWAP requires OHLCV data (6 components), got {len(ohlcv_data[0])}")
            return {'metadata': metadata, 'data': []}
        
        print(f"Calculating VWAP from {len(ohlcv_data)} OHLCV data points")
        
        # Calculate VWAP
        vwap_data = calculate_vwap(ohlcv_data)
        
        if not vwap_data:
            print("Insufficient data for VWAP calculation")
            return {'metadata': metadata, 'data': []}
        
        # Save complete VWAP data to cache
        save_to_cache(dataset_name, vwap_data)
        print(f"Successfully calculated and cached {dataset_name}")
        
        # Show sample VWAP values
        print(f"Sample VWAP values:")
        for i in range(min(3, len(vwap_data))):
            dt = datetime.fromtimestamp(vwap_data[i][0] / 1000)
            print(f"  {dt.date()}: VWAP = ${vwap_data[i][1]:.2f}")
        
        # Trim to requested days if not 'max'
        if days != 'max':
            cutoff_date = datetime.now() - timedelta(days=int(days))
            cutoff_ms = int(cutoff_date.timestamp() * 1000)
            vwap_data = [d for d in vwap_data if d[0] >= cutoff_ms]
        
        return {
            'metadata': metadata,
            'data': vwap_data
        }
        
    except Exception as e:
        print(f"Error calculating VWAP: {e}. Loading from cache.")
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
