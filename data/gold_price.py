# data/gold_price.py

import requests
from .time_transformer import standardize_to_daily_utc
from datetime import datetime, timedelta
import sys
import os

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
    """
    Fetches gold price data from FMP API
    Tries XAUUSD first, then PAXGUSD as fallback
    """
    metadata = get_metadata()
    
    # Try different gold tickers
    tickers_to_try = [
        ('XAUUSD', 'forex'),  # Spot gold
        ('PAXGUSD', 'crypto'),  # PAX Gold as fallback
    ]
    
    for ticker, market_type in tickers_to_try:
        try:
            # Construct URL based on market type
            if market_type == 'forex':
                url = f'https://financialmodelingprep.com/api/v3/historical-price-full/{ticker}?apikey={FMP_API_KEY}'
            else:
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
                    
                    # Calculate limit
                    if days == 'max':
                        limit = 3650
                    else:
                        limit = int(days)
                    
                    # Process the data
                    for i, item in enumerate(historical_data):
                        if i >= limit:
                            break
                        
                        date_str = item['date']
                        date = datetime.strptime(date_str, '%Y-%m-%d')
                        timestamp_ms = int(date.timestamp() * 1000)
                        
                        price = float(item['close'])
                        raw_data.append([timestamp_ms, price])
                    
                    # Sort by timestamp
                    raw_data.sort(key=lambda x: x[0])
                    standardized_data = standardize_to_daily_utc(raw_data)
                    
                    # Trim to exact requested days if not 'max'
                    if days != 'max':
                        cutoff_date = datetime.now() - timedelta(days=int(days))
                        cutoff_ms = int(cutoff_date.timestamp() * 1000)
                        standardized_data = [d for d in standardized_data if d[0] >= cutoff_ms]
                    
                    return {
                        'metadata': metadata,
                        'data': standardized_data
                    }
        
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
            continue
    
    print("Could not fetch gold data from any source")
    return {'metadata': metadata, 'data': []}