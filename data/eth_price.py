# data/eth_price.py

import requests
from .time_transformer import standardize_to_daily_utc
from datetime import datetime, timedelta
import sys
import os

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
    """Fetches Ethereum price data from FMP API and returns it with metadata"""
    metadata = get_metadata()
    
    try:
        url = 'https://financialmodelingprep.com/api/v3/historical-price-full/ETHUSD'
        
        # Calculate limit with extra days for RSI calculation
        if days == 'max':
            limit = 3650
        else:
            limit = int(days) + 50  # Add extra days for RSI calculation
        
        params = {
            'apikey': FMP_API_KEY
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if 'Error Message' in data:
            print(f"FMP API error: {data['Error Message']}")
            return {'metadata': metadata, 'data': []}
        
        if 'historical' not in data:
            print("Unexpected response format from FMP API")
            print(f"Response keys: {list(data.keys())}")
            return {'metadata': metadata, 'data': []}
        
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
        print(f"Error fetching ETH data from FMP: {e}")
        return {'metadata': metadata, 'data': []}