# data/rsi.py
"""
RSI calculator compatible with OHLCV data structure
Extracts closing prices from 6-element OHLCV data
"""

from datetime import datetime, timedelta
import sys
import os
from .cache_manager import load_from_cache, save_to_cache
from .time_transformer import extract_component

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import RSI_PERIOD
from . import eth_price

def get_metadata():
    """Returns metadata describing how RSI should be displayed"""
    return {
        'label': f'RSI ({RSI_PERIOD})',
        'yAxisId': 'indicator',
        'yAxisLabel': 'RSI Value',
        'unit': '',
        'chartType': 'line',
        'color': '#FF9500',
        'strokeWidth': 2,
        'description': f'{RSI_PERIOD}-period Relative Strength Index for ETH',
        'yDomain': [0, 100],  # RSI is always 0-100
        'referenceLines': [
            {'value': 30, 'label': 'Oversold', 'color': '#4CAF50', 'strokeDasharray': '5,5'},
            {'value': 70, 'label': 'Overbought', 'color': '#F44336', 'strokeDasharray': '5,5'}
        ]
    }

def calculate_rsi(prices, period=RSI_PERIOD):
    """Calculates the Relative Strength Index (RSI)"""
    if len(prices) < period:
        return []

    gains = []
    losses = []
    
    for i in range(1, period + 1):
        change = prices[i] - prices[i-1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))

    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    
    rsi_values = []
    
    if avg_loss == 0:
        rs = float('inf')
    else:
        rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    rsi_values.append(rsi)

    for i in range(period + 1, len(prices)):
        change = prices[i] - prices[i-1]
        gain = change if change > 0 else 0
        loss = abs(change) if change < 0 else 0
        
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period

        if avg_loss == 0:
            rs = float('inf')
        else:
            rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        rsi_values.append(rsi)
        
    return rsi_values

def get_data(days='365'):
    """Fetches ETH OHLCV data and calculates RSI from closing prices"""
    metadata = get_metadata()
    dataset_name = 'rsi'
    
    try:
        # Request extra days for RSI calculation
        if days == 'max':
            request_days = 'max'
        else:
            request_days = str(int(days) + RSI_PERIOD + 10)  # Extra buffer for RSI calculation
        
        # Get ETH OHLCV data from the eth_price module
        eth_data = eth_price.get_data(request_days)
        
        if not eth_data or not eth_data.get('data') or len(eth_data['data']) == 0:
            print("No ETH data available for RSI calculation")
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
        
        # Check if we have OHLCV structure or simple price structure
        if ohlcv_data and len(ohlcv_data[0]) == 6:
            # Extract closing prices from OHLCV data
            print("Extracting closing prices from OHLCV data for RSI calculation")
            price_data = extract_component(ohlcv_data, 'close')
        elif ohlcv_data and len(ohlcv_data[0]) == 2:
            # Simple price data (backward compatibility)
            print("Using simple price data for RSI calculation")
            price_data = ohlcv_data
        else:
            print(f"Unexpected data structure: {len(ohlcv_data[0]) if ohlcv_data else 0} elements")
            return {'metadata': metadata, 'data': []}
        
        if len(price_data) < RSI_PERIOD:
            print(f"Insufficient data for RSI calculation (need at least {RSI_PERIOD} data points)")
            return {'metadata': metadata, 'data': []}
        
        timestamps = [item[0] for item in price_data]
        closing_prices = [item[1] for item in price_data]

        # Calculate RSI
        rsi_values = calculate_rsi(closing_prices, RSI_PERIOD)
        
        # Combine timestamps with RSI values
        rsi_data = []
        for i in range(len(rsi_values)):
            rsi_data.append([timestamps[i + RSI_PERIOD], rsi_values[i]])
        
        # Save complete RSI data to cache
        save_to_cache(dataset_name, rsi_data)
        print(f"Successfully calculated and cached {dataset_name}")
        print(f"RSI calculated from {len(closing_prices)} price points")
        
        # Trim to requested days if not 'max'
        if days != 'max':
            final_cutoff = datetime.now() - timedelta(days=int(days))
            final_cutoff_ms = int(final_cutoff.timestamp() * 1000)
            rsi_data = [d for d in rsi_data if d[0] >= final_cutoff_ms]
        
        return {
            'metadata': metadata,
            'data': rsi_data
        }
        
    except Exception as e:
        print(f"Error calculating RSI: {e}. Loading from cache.")
        cached_data = load_from_cache(dataset_name)
        if cached_data:
            # Filter cached data to requested days
            if days != 'max':
                cutoff_date = datetime.now() - timedelta(days=int(days))
                cutoff_ms = int(cutoff_date.timestamp() * 1000)
                cached_data = [d for d in cached_data if d[0] >= cutoff_ms]
            return {'metadata': metadata, 'data': cached_data}
        return {'metadata': metadata, 'data': []}