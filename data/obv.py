# data/obv.py
"""
On-Balance Volume (OBV) calculator compatible with OHLCV data structure
Extracts closing prices and volume from 6-element OHLCV data
OBV = Cumulative sum of volume (positive if close > prev_close, negative if close < prev_close)
"""

from datetime import datetime, timedelta
import sys
import os
from .cache_manager import load_from_cache, save_to_cache
from .time_transformer import extract_component

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from . import eth_price

def get_metadata():
    """Returns metadata describing how OBV should be displayed"""
    return {
        'label': 'OBV (On-Balance Volume)',
        'yAxisId': 'indicator',
        'yAxisLabel': 'OBV',
        'unit': '',
        'chartType': 'line',
        'color': '#2196F3',  # Blue
        'strokeWidth': 2,
        'description': 'On-Balance Volume indicator for ETH - measures buying/selling pressure'
    }

def calculate_obv(ohlcv_data):
    """
    Calculate On-Balance Volume (OBV)
    OBV = Previous OBV + Volume (if close > prev_close)
    OBV = Previous OBV - Volume (if close < prev_close)
    OBV = Previous OBV (if close == prev_close)
    
    Args:
        ohlcv_data: List of [timestamp, open, high, low, close, volume]
    
    Returns:
        List of [timestamp, obv_value]
    """
    if len(ohlcv_data) < 2:
        return []
    
    obv_values = []
    current_obv = 0  # Start OBV at 0
    
    # First data point - use volume as initial OBV
    current_obv = ohlcv_data[0][5]  # volume
    obv_values.append([ohlcv_data[0][0], current_obv])
    
    # Calculate OBV for subsequent points
    for i in range(1, len(ohlcv_data)):
        timestamp = ohlcv_data[i][0]
        close = ohlcv_data[i][4]
        volume = ohlcv_data[i][5]
        prev_close = ohlcv_data[i-1][4]
        
        # Update OBV based on price direction
        if close > prev_close:
            current_obv += volume
        elif close < prev_close:
            current_obv -= volume
        # If close == prev_close, OBV stays the same
        
        obv_values.append([timestamp, current_obv])
    
    return obv_values

def get_data(days='365'):
    """Fetches ETH OHLCV data and calculates OBV from volume and closing prices"""
    metadata = get_metadata()
    dataset_name = 'obv'
    
    try:
        # Get ETH OHLCV data
        if days == 'max':
            request_days = 'max'
        else:
            request_days = str(int(days) + 10)  # Extra buffer
        
        eth_data = eth_price.get_data(request_days)
        
        if not eth_data or not eth_data.get('data') or len(eth_data['data']) == 0:
            print("No ETH data available for OBV calculation")
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
            print(f"ERROR: OBV requires OHLCV data (6 components), got {len(ohlcv_data[0])}")
            return {'metadata': metadata, 'data': []}
        
        print(f"Calculating OBV from {len(ohlcv_data)} OHLCV data points")
        
        # Calculate OBV
        obv_data = calculate_obv(ohlcv_data)
        
        if not obv_data:
            print("Insufficient data for OBV calculation")
            return {'metadata': metadata, 'data': []}
        
        # Save complete OBV data to cache
        save_to_cache(dataset_name, obv_data)
        print(f"Successfully calculated and cached {dataset_name}")
        print(f"OBV calculated from {len(ohlcv_data)} price/volume points")
        
        # Show sample OBV values
        print(f"Sample OBV values:")
        for i in range(min(3, len(obv_data))):
            dt = datetime.fromtimestamp(obv_data[i][0] / 1000)
            print(f"  {dt.date()}: OBV = {obv_data[i][1]:,.0f}")
        
        # Trim to requested days if not 'max'
        if days != 'max':
            cutoff_date = datetime.now() - timedelta(days=int(days))
            cutoff_ms = int(cutoff_date.timestamp() * 1000)
            obv_data = [d for d in obv_data if d[0] >= cutoff_ms]
        
        return {
            'metadata': metadata,
            'data': obv_data
        }
        
    except Exception as e:
        print(f"Error calculating OBV: {e}. Loading from cache.")
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
