# data/bollinger_bands.py
"""
Bollinger Bands calculator compatible with OHLCV data structure
Extracts closing prices from 6-element OHLCV data
"""

import numpy as np
from datetime import datetime, timedelta
import sys
import os
from .cache_manager import load_from_cache, save_to_cache
from .time_transformer import extract_component

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import FMP_API_KEY
from . import eth_price

def get_metadata():
    """Returns metadata describing how Bollinger Bands should be displayed"""
    return {
        'label': 'Bollinger Bands',
        'yAxisId': 'price_usd',
        'yAxisLabel': 'Price (USD)',
        'unit': '$',
        'chartType': 'band',  # Special type for bands
        'color': '#9C27B0',  # Purple for middle band
        'upperBandColor': '#4CAF50',  # Green for upper band
        'lowerBandColor': '#F44336',  # Red for lower band
        'strokeWidth': 1,
        'description': '20-day Bollinger Bands for ETH',
        'fillOpacity': 0.1
    }

def calculate_bollinger_bands(prices, period=20, num_std=2):
    """Calculate Bollinger Bands
    Returns: (middle_band, upper_band, lower_band)
    """
    if len(prices) < period:
        return [], [], []
    
    middle_band = []
    upper_band = []
    lower_band = []
    
    for i in range(period - 1, len(prices)):
        # Calculate SMA for middle band
        window = prices[i - period + 1:i + 1]
        sma = np.mean(window)
        
        # Calculate standard deviation
        std = np.std(window)
        
        # Calculate bands
        middle_band.append(sma)
        upper_band.append(sma + (std * num_std))
        lower_band.append(sma - (std * num_std))
    
    return middle_band, upper_band, lower_band

def get_data(days='365'):
    """Fetches ETH OHLCV data and calculates Bollinger Bands from closing prices"""
    metadata = get_metadata()
    dataset_name = 'bollinger_bands'
    
    try:
        # Get ETH OHLCV data
        if days == 'max':
            request_days = 'max'
        else:
            request_days = str(int(days) + 30)  # Extra days for calculation
        
        eth_data = eth_price.get_data(request_days)
        
        if not eth_data or not eth_data.get('data') or len(eth_data['data']) == 0:
            print("No ETH data available for Bollinger Bands calculation")
            # Try loading from cache
            cached_data = load_from_cache(dataset_name)
            if cached_data:
                # Filter cached data to requested days
                if days != 'max':
                    cutoff_date = datetime.now() - timedelta(days=int(days))
                    cutoff_ms = int(cutoff_date.timestamp() * 1000)
                    # Filter all three bands
                    if 'middle' in cached_data:
                        cached_data['middle'] = [d for d in cached_data['middle'] if d[0] >= cutoff_ms]
                        cached_data['upper'] = [d for d in cached_data['upper'] if d[0] >= cutoff_ms]
                        cached_data['lower'] = [d for d in cached_data['lower'] if d[0] >= cutoff_ms]
                return {'metadata': metadata, 'data': cached_data}
            return {'metadata': metadata, 'data': {'middle': [], 'upper': [], 'lower': []}}
        
        ohlcv_data = eth_data['data']
        
        # Check if we have OHLCV structure or simple price structure
        if ohlcv_data and len(ohlcv_data[0]) == 6:
            # Extract closing prices from OHLCV data
            print("Extracting closing prices from OHLCV data for Bollinger Bands calculation")
            price_data = extract_component(ohlcv_data, 'close')
        elif ohlcv_data and len(ohlcv_data[0]) == 2:
            # Simple price data (backward compatibility)
            print("Using simple price data for Bollinger Bands calculation")
            price_data = ohlcv_data
        else:
            print(f"Unexpected data structure: {len(ohlcv_data[0]) if ohlcv_data else 0} elements")
            return {'metadata': metadata, 'data': {'middle': [], 'upper': [], 'lower': []}}
        
        # Extract timestamps and prices
        timestamps = [item[0] for item in price_data]
        prices = [item[1] for item in price_data]
        
        # Calculate Bollinger Bands
        period = 20
        middle, upper, lower = calculate_bollinger_bands(prices, period)
        
        if not middle:
            print(f"Insufficient data for Bollinger Bands (need at least {period} points)")
            return {'metadata': metadata, 'data': {'middle': [], 'upper': [], 'lower': []}}
        
        # Align timestamps with band data
        band_timestamps = timestamps[period - 1:]
        
        # Create data structure for bands
        middle_data = [[band_timestamps[i], middle[i]] for i in range(len(middle))]
        upper_data = [[band_timestamps[i], upper[i]] for i in range(len(upper))]
        lower_data = [[band_timestamps[i], lower[i]] for i in range(len(lower))]
        
        # Save complete bands data to cache
        bands_data = {
            'middle': middle_data,
            'upper': upper_data,
            'lower': lower_data
        }
        save_to_cache(dataset_name, bands_data)
        print(f"Successfully calculated and cached {dataset_name}")
        print(f"Bollinger Bands calculated from {len(prices)} price points")
        
        # Trim to requested days if not 'max'
        if days != 'max':
            cutoff_date = datetime.now() - timedelta(days=int(days))
            cutoff_ms = int(cutoff_date.timestamp() * 1000)
            
            middle_data = [d for d in middle_data if d[0] >= cutoff_ms]
            upper_data = [d for d in upper_data if d[0] >= cutoff_ms]
            lower_data = [d for d in lower_data if d[0] >= cutoff_ms]
        
        # Return special format for bands
        return {
            'metadata': metadata,
            'data': {
                'middle': middle_data,
                'upper': upper_data,
                'lower': lower_data
            }
        }
        
    except Exception as e:
        print(f"Error calculating Bollinger Bands: {e}. Loading from cache.")
        cached_data = load_from_cache(dataset_name)
        if cached_data:
            # Filter cached data to requested days
            if days != 'max':
                cutoff_date = datetime.now() - timedelta(days=int(days))
                cutoff_ms = int(cutoff_date.timestamp() * 1000)
                # Filter all three bands
                if 'middle' in cached_data:
                    cached_data['middle'] = [d for d in cached_data['middle'] if d[0] >= cutoff_ms]
                    cached_data['upper'] = [d for d in cached_data['upper'] if d[0] >= cutoff_ms]
                    cached_data['lower'] = [d for d in cached_data['lower'] if d[0] >= cutoff_ms]
            return {'metadata': metadata, 'data': cached_data}
        return {'metadata': metadata, 'data': {'middle': [], 'upper': [], 'lower': []}}