# data/eth_price.py

import requests
from .time_transformer import standardize_to_daily_utc
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import ALPHA_VANTAGE_API_KEY

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
    """Fetches Ethereum price data and returns it with metadata"""
    metadata = get_metadata()
    
    try:
        url = 'https://www.alphavantage.co/query'
        params = {
            'function': 'DIGITAL_CURRENCY_DAILY',
            'symbol': 'ETH',
            'market': 'USD',
            'apikey': ALPHA_VANTAGE_API_KEY
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if 'Error Message' in data:
            print(f"Alpha Vantage API error: {data['Error Message']}")
            return {'metadata': metadata, 'data': []}
        
        if 'Note' in data:
            print(f"Alpha Vantage API limit reached: {data['Note']}")
            return {'metadata': metadata, 'data': []}
        
        if 'Time Series (Digital Currency Daily)' not in data:
            print("Unexpected response format from Alpha Vantage")
            return {'metadata': metadata, 'data': []}
        
        time_series = data['Time Series (Digital Currency Daily)']
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
            
            # Handle different field names
            if '4a. close (USD)' in values:
                price = float(values['4a. close (USD)'])
            elif '4. close' in values:
                price = float(values['4. close'])
            else:
                print(f"Available keys: {list(values.keys())}")
                continue
            
            raw_data.append([timestamp_ms, price])
        
        raw_data.sort(key=lambda x: x[0])
        standardized_data = standardize_to_daily_utc(raw_data)
        
        return {
            'metadata': metadata,
            'data': standardized_data
        }
        
    except Exception as e:
        print(f"Error fetching ETH data: {e}")
        return {'metadata': metadata, 'data': []}