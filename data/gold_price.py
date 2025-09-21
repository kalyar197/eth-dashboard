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
    Uses the commodity endpoint for GCUSD (Gold futures)
    """
    metadata = get_metadata()
    
    try:
        url = 'https://financialmodelingprep.com/api/v3/historical-price-full/commodity/GCUSD'
        
        # Calculate limit
        if days == 'max':
            limit = 3650
        else:
            limit = int(days)
        
        params = {
            'apikey': FMP_API_KEY
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Check for API errors
        if 'Error Message' in data:
            print(f"FMP API error for gold: {data['Error Message']}")
            return {'metadata': metadata, 'data': []}
        
        if 'historical' not in data:
            print("Gold data not available from FMP API")
            print(f"Response keys: {list(data.keys())}")
            return {'metadata': metadata, 'data': []}
        
        # Parse the historical data
        historical_data = data['historical']
        raw_data = []
        
        # Limit the data to requested days
        for i, item in enumerate(historical_data):
            if i >= limit:
                break
            
            date_str = item['date']
            date = datetime.strptime(date_str, '%Y-%m-%d')
            timestamp_ms = int(date.timestamp() * 1000)
            
            price = float(item['close'])
            raw_data.append([timestamp_ms, price])
        
        # Sort by timestamp (FMP returns newest first, we need oldest first)
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
        print(f"Error fetching gold price data from FMP: {e}")
        return {'metadata': metadata, 'data': []}