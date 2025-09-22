# data/btc_dominance.py
# REAL DATA from CoinStats API - NO ESTIMATES

import requests
from .time_transformer import standardize_to_daily_utc
from datetime import datetime, timedelta
import sys
import os
from .cache_manager import load_from_cache, save_to_cache

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import COINSTATS_API_KEY

def get_metadata():
    """Returns metadata describing how BTC dominance should be displayed"""
    return {
        'label': 'BTC.D',
        'yAxisId': 'percentage',
        'yAxisLabel': 'Dominance (%)',
        'unit': '%',
        'chartType': 'line',
        'color': '#F7931A',  # Bitcoin orange
        'strokeWidth': 2,
        'description': 'Bitcoin market cap dominance - REAL DATA from CoinStats'
    }

def get_data(days='365'):
    """Fetches REAL Bitcoin dominance data from CoinStats API."""
    metadata = get_metadata()
    dataset_name = 'btc_dominance_coinstats'
    
    try:
        print("Fetching REAL BTC dominance from CoinStats API...")
        
        # CoinStats API endpoint for dominance data
        # Note: The exact endpoint depends on your CoinStats API plan
        # Common endpoints include:
        # - /v1/charts/dominance
        # - /v1/coins/bitcoin/charts with dominance parameter
        # - /v1/markets/charts with dominance metrics
        
        headers = {
            'X-API-KEY': COINSTATS_API_KEY,
            'Accept': 'application/json'
        }
        
        # Calculate period parameter based on days
        if days == 'max':
            period = 'all'
        elif int(days) <= 1:
            period = '24h'
        elif int(days) <= 7:
            period = '7d'
        elif int(days) <= 30:
            period = '1m'
        elif int(days) <= 90:
            period = '3m'
        elif int(days) <= 365:
            period = '1y'
        else:
            period = 'all'
        
        # CoinStats dominance endpoint
        # Update this URL based on your API documentation
        url = f'https://api.coinstats.app/public/v1/charts/dominance'
        
        params = {
            'coin': 'bitcoin',  # or 'btc' depending on API
            'period': period
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        if response.status_code != 200:
            # Try alternative endpoint structure
            url = f'https://openapiv1.coinstats.app/coins/bitcoin/charts'
            params = {
                'period': period,
                'type': 'dominance'
            }
            response = requests.get(url, headers=headers, params=params, timeout=30)
        
        response.raise_for_status()
        data = response.json()
        
        # Parse the response based on CoinStats format
        # CoinStats typically returns data in format:
        # { "chart": [[timestamp, value], [timestamp, value], ...] }
        # or
        # { "dominance": [[timestamp, value], ...] }
        
        dominance_data = []
        
        if 'chart' in data:
            chart_data = data['chart']
        elif 'dominance' in data:
            chart_data = data['dominance']
        elif 'data' in data and isinstance(data['data'], list):
            chart_data = data['data']
        else:
            raise ValueError(f"Unexpected CoinStats API response format: {data.keys()}")
        
        # Process the data points
        for point in chart_data:
            if isinstance(point, list) and len(point) >= 2:
                timestamp = point[0]
                dominance_value = point[1]
                
                # CoinStats may return timestamp in seconds or milliseconds
                # Convert to milliseconds if needed
                if timestamp < 1000000000000:  # If in seconds
                    timestamp = timestamp * 1000
                
                dominance_data.append([timestamp, dominance_value])
            elif isinstance(point, dict):
                # Alternative format: {"timestamp": ..., "dominance": ...}
                timestamp = point.get('timestamp', point.get('time', point.get('date')))
                dominance_value = point.get('dominance', point.get('value', point.get('percentage')))
                
                if timestamp and dominance_value is not None:
                    if timestamp < 1000000000000:  # If in seconds
                        timestamp = timestamp * 1000
                    dominance_data.append([timestamp, dominance_value])
        
        if not dominance_data:
            raise ValueError("No dominance data returned from CoinStats API")
        
        # Sort by timestamp
        dominance_data.sort(key=lambda x: x[0])
        
        # Save to cache
        save_to_cache(dataset_name, dominance_data)
        print(f"Successfully fetched {len(dominance_data)} REAL BTC dominance data points")
        print(f"Dominance range: {min(d[1] for d in dominance_data):.2f}% - {max(d[1] for d in dominance_data):.2f}%")
        
        raw_data = dominance_data
        
    except Exception as e:
        print(f"Error fetching BTC dominance from CoinStats: {e}")
        print("Attempting to load from cache...")
        
        raw_data = load_from_cache(dataset_name)
        if not raw_data:
            print("No cached REAL data available")
            return {
                'metadata': metadata, 
                'data': [],
                'error': f'Failed to fetch real data from CoinStats: {str(e)}'
            }
    
    # Process and standardize data
    if raw_data:
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
    
    return {'metadata': metadata, 'data': []}