# data/eth_price.py
"""
Ethereum price data fetcher using CoinAPI
Fetches daily OHLCV data and uses closing price
"""

import requests
from .time_transformer import standardize_to_daily_utc
from datetime import datetime, timedelta
import sys
import os
from .cache_manager import load_from_cache, save_to_cache

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import COINAPI_KEY

def get_metadata():
    """Returns metadata describing how this data should be displayed"""
    return {
        'label': 'Ethereum (ETH)',
        'yAxisId': 'price_usd',
        'yAxisLabel': 'Price (USD)',
        'unit': '$',
        'chartType': 'line',
        'color': '#627EEA',  # Ethereum's brand color
        'strokeWidth': 2,
        'description': 'Ethereum daily closing price in USD'
    }

def get_data(days='365'):
    """
    Fetches Ethereum price data using CoinAPI's OHLCV history endpoint.
    Returns daily closing prices processed through time_transformer.
    """
    metadata = get_metadata()
    dataset_name = 'eth_price'

    try:
        print("Fetching ETH price data from CoinAPI...")
        
        # CoinAPI OHLCV History endpoint configuration
        base_url = 'https://rest.coinapi.io/v1/ohlcv'
        symbol_id = 'BINANCE_SPOT_ETH_USDT'  # High-volume reliable symbol
        
        # Calculate date range
        if days == 'max':
            # Get max available data (e.g., 5 years)
            start_date = datetime.now() - timedelta(days=365 * 5)
        else:
            start_date = datetime.now() - timedelta(days=int(days) + 10)  # Extra buffer
        
        end_date = datetime.now()
        
        # Format dates for CoinAPI (ISO 8601)
        time_start = start_date.strftime('%Y-%m-%dT00:00:00')
        time_end = end_date.strftime('%Y-%m-%dT23:59:59')
        
        # Construct the API URL
        url = f'{base_url}/{symbol_id}/history'
        
        # API parameters
        params = {
            'period_id': '1DAY',  # Daily candles
            'time_start': time_start,
            'time_end': time_end,
            'limit': 100000  # Max limit to get all available data
        }
        
        # Headers with API key
        headers = {
            'X-CoinAPI-Key': COINAPI_KEY
        }
        
        # Make the API request
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if not data:
            raise ValueError("No data returned from CoinAPI")
        
        # Process the OHLCV data
        raw_data = []
        for candle in data:
            # CoinAPI returns time_period_start as the timestamp
            # and price_close as the closing price
            timestamp_str = candle.get('time_period_start')
            close_price = candle.get('price_close')
            
            if timestamp_str and close_price is not None:
                # Parse the ISO timestamp
                dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                timestamp_ms = int(dt.timestamp() * 1000)
                raw_data.append([timestamp_ms, float(close_price)])
        
        if not raw_data:
            raise ValueError("No valid price data extracted from CoinAPI response")
        
        # Sort by timestamp (oldest first)
        raw_data.sort(key=lambda x: x[0])
        
        # Save the complete dataset to cache
        save_to_cache(dataset_name, raw_data)
        print(f"Successfully fetched {len(raw_data)} ETH price data points from CoinAPI")
        
    except requests.exceptions.RequestException as e:
        print(f"API request failed for ETH price: {e}")
        # Load from cache if API fails
        raw_data = load_from_cache(dataset_name)
        if not raw_data:
            return {'metadata': metadata, 'data': []}
            
    except Exception as e:
        print(f"Error fetching ETH price from CoinAPI: {e}")
        # Load from cache if any error occurs
        raw_data = load_from_cache(dataset_name)
        if not raw_data:
            return {'metadata': metadata, 'data': []}
    
    # Standardize the data to daily UTC format
    standardized_data = standardize_to_daily_utc(raw_data)
    
    # Trim to the exact requested number of days
    if days != 'max':
        cutoff_date = datetime.now() - timedelta(days=int(days))
        cutoff_ms = int(cutoff_date.timestamp() * 1000)
        standardized_data = [d for d in standardized_data if d[0] >= cutoff_ms]
    
    return {
        'metadata': metadata,
        'data': standardized_data
    }