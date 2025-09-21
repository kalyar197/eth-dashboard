# data/gold_price.py

import requests
from .time_transformer import standardize_to_daily_utc
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import ALPHA_VANTAGE_API_KEY

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
    Fetches gold price data using Alpha Vantage's FX_DAILY
    XAU (Gold Ounce) to USD gives the actual gold spot price
    No fallbacks - returns empty if not available
    """
    metadata = get_metadata()
    
    try:
        url = 'https://www.alphavantage.co/query'
        
        # Get daily forex data for XAU/USD (Gold to USD)
        params = {
            'function': 'FX_DAILY',
            'from_symbol': 'XAU',  # Gold (troy ounce)
            'to_symbol': 'USD',
            'apikey': ALPHA_VANTAGE_API_KEY
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Check for API errors
        if 'Error Message' in data:
            print(f"Gold price not available: {data['Error Message']}")
            return {'metadata': metadata, 'data': []}
        
        if 'Note' in data:
            print(f"Alpha Vantage API limit reached: {data['Note']}")
            return {'metadata': metadata, 'data': []}
        
        if 'Time Series FX (Daily)' not in data:
            print("Gold (XAU/USD) data not available from Alpha Vantage")
            return {'metadata': metadata, 'data': []}
        
        # Parse the time series data
        time_series = data['Time Series FX (Daily)']
        raw_data = []
        
        if days == 'max':
            days_limit = 3650
        else:
            days_limit = int(days)
        
        cutoff_date = datetime.now() - timedelta(days=days_limit)
        
        for date_str, values in time_series.items():
            date = datetime.strptime(date_str, '%Y-%m-%d')
            
            if date < cutoff_date:
                continue
            
            timestamp_ms = int(date.timestamp() * 1000)
            
            # XAU/USD gives direct gold price per troy ounce
            price = float(values['4. close'])
            raw_data.append([timestamp_ms, price])
        
        raw_data.sort(key=lambda x: x[0])
        standardized_data = standardize_to_daily_utc(raw_data)
        
        return {
            'metadata': metadata,
            'data': standardized_data
        }
        
    except Exception as e:
        print(f"Error fetching gold price data: {e}")
        return {'metadata': metadata, 'data': []}