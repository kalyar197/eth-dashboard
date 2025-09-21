# data/gold_price.py

import requests
from .time_transformer import standardize_to_daily_utc
from datetime import datetime, timedelta
import sys
import os
from .cache_manager import load_from_cache, save_to_cache

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import FMP_API_KEY

def get_metadata():
    """Returns metadata describing how gold data should be displayed"""
    return {
        'label': 'Gold (XAU/USD)',
        'yAxisId': 'price_usd',
        'yAxisLabel': 'Price per Oz (USD)',
        'unit': '$',
        'chartType': 'line',
        'color': '#FFD700',
        'strokeWidth': 2,
        'description': 'Gold spot price per troy ounce in USD'
    }

def get_data(days='365'):
    """Fetches gold price data, using a local cache to minimize API calls."""
    metadata = get_metadata()
    dataset_name = 'gold_price'
    
    # Try different gold tickers
    tickers_to_try = [
        ('XAUUSD', 'forex'),  # Spot gold
        ('PAXGUSD', 'crypto'),  # PAX Gold as fallback
    ]
    
    raw_data = []
    successfully_fetched = False
    
    for ticker, market_type in tickers_to_try:
        if successfully_fetched:
            break
            
        try:
            # Construct URL based on market type
            url = f'https://financialmodelingprep.com/api/v3/historical-price-full/{ticker}?apikey={FMP_API_KEY}'
            
            print(f"Trying to fetch gold data from: {ticker}")
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'historical' in data and len(data['historical']) > 0:
                    print(f"Successfully fetched gold data using {ticker}")
                    
                    # Update label if using PAXG
                    if ticker == 'PAXGUSD':
                        metadata['label'] = 'Gold (PAXG/USD)'
                    
                    historical_data = data['historical']
                    raw_data = []
                    
                    # Process all the data
                    for item in historical_data:
                        date = datetime.strptime(item['date'], '%Y-%m-%d')
                        price = float(item['close'])
                        raw_data.append([int(date.timestamp() * 1000), price])
                    
                    # Save to cache
                    save_to_cache(dataset_name, raw_data)
                    print(f"Successfully updated cache for {dataset_name}")
                    successfully_fetched = True
                    break
        
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
            continue
    
    # If we couldn't fetch from any source, try the cache
    if not successfully_fetched:
        print(f"Could not fetch gold data from any source. Loading from cache.")
        raw_data = load_from_cache(dataset_name)
        if not raw_data:
            return {'metadata': metadata, 'data': []}
    
    # Sort and process the data
    raw_data.sort(key=lambda x: x[0])
    standardized_data = standardize_to_daily_utc(raw_data)
    
    # Trim to requested days
    if days != 'max':
        cutoff_date = datetime.now() - timedelta(days=int(days))
        cutoff_ms = int(cutoff_date.timestamp() * 1000)
        standardized_data = [d for d in standardized_data if d[0] >= cutoff_ms]
    
    return {
        'metadata': metadata,
        'data': standardized_data
    }