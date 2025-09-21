# data/rsi.py

import requests
from .time_transformer import standardize_to_daily_utc
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import ALPHA_VANTAGE_API_KEY, RSI_PERIOD

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
    """Fetches ETH price, calculates RSI, and returns with metadata"""
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
            print(f"Alpha Vantage API error for RSI: {data['Error Message']}")
            return {'metadata': metadata, 'data': []}
        
        if 'Note' in data:
            print(f"Alpha Vantage API limit reached for RSI: {data['Note']}")
            return {'metadata': metadata, 'data': []}
        
        if 'Time Series (Digital Currency Daily)' not in data:
            print("Unexpected response format from Alpha Vantage for RSI")
            return {'metadata': metadata, 'data': []}
        
        time_series = data['Time Series (Digital Currency Daily)']
        raw_data = []
        
        if days == 'max':
            days_limit = 3650
        else:
            days_limit = int(days) + 50
        
        cutoff_date = datetime.now() - timedelta(days=days_limit)
        
        for date_str, values in time_series.items():
            date = datetime.strptime(date_str, '%Y-%m-%d')
            
            if date < cutoff_date:
                continue
                
            timestamp_ms = int(date.timestamp() * 1000)
            
            if '4a. close (USD)' in values:
                price = float(values['4a. close (USD)'])
            elif '4. close' in values:
                price = float(values['4. close'])
            else:
                continue
                
            raw_data.append([timestamp_ms, price])
        
        raw_data.sort(key=lambda x: x[0])
        standardized_price_data = standardize_to_daily_utc(raw_data)
        
        if not standardized_price_data:
            return {'metadata': metadata, 'data': []}
            
        timestamps = [item[0] for item in standardized_price_data]
        closing_prices = [item[1] for item in standardized_price_data]

        rsi_values = calculate_rsi(closing_prices, RSI_PERIOD)
        
        rsi_data = []
        for i in range(len(rsi_values)):
            rsi_data.append([timestamps[i + RSI_PERIOD], rsi_values[i]])
        
        if days != 'max':
            final_cutoff = datetime.now() - timedelta(days=int(days))
            final_cutoff_ms = int(final_cutoff.timestamp() * 1000)
            rsi_data = [d for d in rsi_data if d[0] >= final_cutoff_ms]
            
        return {
            'metadata': metadata,
            'data': rsi_data
        }
        
    except Exception as e:
        print(f"Error getting RSI data: {e}")
        return {'metadata': metadata, 'data': []}