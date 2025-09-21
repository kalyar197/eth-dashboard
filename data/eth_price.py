# data/eth_price.py

import requests
from .time_transformer import standardize_to_daily_utc
from datetime import datetime, timedelta
import sys
import os
from .cache_manager import load_from_cache, save_to_cache

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import FMP_API_KEY

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
    """Fetches Ethereum price data, using a local cache to minimize API calls."""
    metadata = get_metadata()
    dataset_name = 'eth_price' # Unique name for this dataset's cache file

    try:
        # The FMP API provides full history, so the simplest strategy is to always fetch fresh data
        # and update our complete local cache. This ensures data is always current.
        url = f'https://financialmodelingprep.com/api/v3/historical-price-full/ETHUSD?apikey={FMP_API_KEY}'
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if 'Error Message' in data:
            print(f"FMP API error: {data['Error Message']}")
            raise ConnectionError("API Error")

        if 'historical' not in data:
            print("Unexpected response format from FMP API")
            raise ValueError("Unexpected API format")
        
        # Process the fresh data from the API
        historical_data = data['historical']
        raw_data = []
        for item in historical_data:
            date = datetime.strptime(item['date'], '%Y-%m-%d')
            price = float(item['close'])
            raw_data.append([int(date.timestamp() * 1000), price])
        
        # Save the complete, fresh dataset to our local cache
        save_to_cache(dataset_name, raw_data)
        print(f"Successfully fetched fresh data for {dataset_name} and updated cache.")

    except Exception as e:
        print(f"API fetch failed for {dataset_name}: {e}. Attempting to serve from cache.")
        # If API fails for any reason, load data from our local cache instead
        raw_data = load_from_cache(dataset_name)
        if not raw_data:
             # If API fails AND cache is empty, return nothing
            return {'metadata': metadata, 'data': []}

    # IMPORTANT: The rest of the function operates on `raw_data`,
    # which is now sourced from either the API or the cache.
    # The time_transformer and filtering logic doesn't need to change.
    
    # Sort by timestamp (oldest first)
    raw_data.sort(key=lambda x: x[0])
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