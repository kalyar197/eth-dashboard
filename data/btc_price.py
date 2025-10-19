# data/btc_price.py
"""
Bitcoin OHLCV data fetcher using CoinAPI
Returns FULL OHLCV data structure: [timestamp, open, high, low, close, volume]
NO DATA DISCARDING - All 6 components preserved
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
        'label': 'Bitcoin (BTC)',
        'yAxisId': 'price_usd',
        'yAxisLabel': 'Price (USD)',
        'unit': '$',
        'chartType': 'line',
        'color': '#F7931A',  # Bitcoin orange
        'strokeWidth': 2,
        'description': 'Bitcoin OHLCV data - Full 6-component structure',
        'data_structure': 'OHLCV',
        'components': ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    }

def get_data(days='365'):
    """
    Fetches Bitcoin FULL OHLCV data using CoinAPI's history endpoint.
    Returns 6-component data: [timestamp, open, high, low, close, volume]
    NO DATA LOSS - All OHLCV components preserved for technical indicators.
    """
    metadata = get_metadata()
    dataset_name = 'btc_ohlcv'

    try:
        print("Fetching BTC FULL OHLCV data from CoinAPI...")
        print("Structure: [timestamp, open, high, low, close, volume]")
        
        # CoinAPI OHLCV History endpoint configuration
        base_url = 'https://rest.coinapi.io/v1/ohlcv'
        symbol_id = 'BINANCE_SPOT_BTC_USDT'  # High-volume reliable symbol
        
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
        
        # Process the FULL OHLCV data - ALL 6 COMPONENTS
        raw_data = []
        for candle in data:
            # Extract ALL OHLCV components
            timestamp_str = candle.get('time_period_start')
            
            # CRITICAL: Extract all 6 components
            open_price = candle.get('price_open')
            high_price = candle.get('price_high')
            low_price = candle.get('price_low')
            close_price = candle.get('price_close')
            volume_traded = candle.get('volume_traded')
            
            # Validate all components exist
            if (timestamp_str and 
                open_price is not None and 
                high_price is not None and 
                low_price is not None and 
                close_price is not None and 
                volume_traded is not None):
                
                # Parse the ISO timestamp
                dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                timestamp_ms = int(dt.timestamp() * 1000)
                
                # CRITICAL: Store all 6 components
                raw_data.append([
                    timestamp_ms,
                    float(open_price),
                    float(high_price),
                    float(low_price),
                    float(close_price),
                    float(volume_traded)
                ])
            else:
                print(f"Warning: Incomplete OHLCV data for {timestamp_str}, skipping...")
        
        if not raw_data:
            raise ValueError("No valid OHLCV data extracted from CoinAPI response")
        
        # Sort by timestamp (oldest first)
        raw_data.sort(key=lambda x: x[0])
        
        # Save the complete OHLCV dataset to cache
        save_to_cache(dataset_name, raw_data)
        print(f"Successfully fetched {len(raw_data)} FULL OHLCV data points from CoinAPI")
        print(f"Sample data structure: timestamp={raw_data[0][0]}, O=${raw_data[0][1]:.2f}, H=${raw_data[0][2]:.2f}, L=${raw_data[0][3]:.2f}, C=${raw_data[0][4]:.2f}, V={raw_data[0][5]:.2f}")
        
    except requests.exceptions.RequestException as e:
        print(f"API request failed for BTC OHLCV: {e}")
        # Load from cache if API fails
        raw_data = load_from_cache(dataset_name)
        if not raw_data:
            return {'metadata': metadata, 'data': []}
            
    except Exception as e:
        print(f"Error fetching BTC OHLCV from CoinAPI: {e}")
        # Load from cache if any error occurs
        raw_data = load_from_cache(dataset_name)
        if not raw_data:
            return {'metadata': metadata, 'data': []}
    
    # Standardize the OHLCV data to daily UTC format
    # time_transformer handles 6-element structure
    standardized_data = standardize_to_daily_utc(raw_data)
    
    # Trim to the exact requested number of days
    if days != 'max':
        cutoff_date = datetime.now() - timedelta(days=int(days))
        cutoff_ms = int(cutoff_date.timestamp() * 1000)
        standardized_data = [d for d in standardized_data if d[0] >= cutoff_ms]
    
    # Log structure verification
    if standardized_data:
        print(f"Returning {len(standardized_data)} OHLCV records with 6 components each")
        print(f"First record has {len(standardized_data[0])} elements (should be 6)")
    
    return {
        'metadata': metadata,
        'data': standardized_data,
        'structure': 'OHLCV'  # Explicit structure indicator
    }
