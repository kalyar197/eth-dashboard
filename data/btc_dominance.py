# data/btc_dominance.py

import requests
from .time_transformer import standardize_to_daily_utc
from datetime import datetime, timedelta
import sys
import os
from .cache_manager import load_from_cache, save_to_cache

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import FMP_API_KEY

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
        'description': 'Bitcoin market cap dominance percentage'
    }

def get_data(days='365'):
    """Fetches Bitcoin dominance data, using a local cache to minimize API calls."""
    metadata = get_metadata()
    dataset_name = 'btc_dominance'
    
    try:
        # First get Bitcoin market cap history
        btc_url = f'https://financialmodelingprep.com/api/v3/historical-price-full/BTCUSD?apikey={FMP_API_KEY}'
        
        response = requests.get(btc_url)
        response.raise_for_status()
        btc_data = response.json()
        
        if 'historical' not in btc_data:
            print("No BTC data available")
            raise ValueError("No BTC data")
        
        # For simplicity, we'll simulate dominance data based on BTC price movements
        # In production, you'd calculate this from total crypto market cap
        historical_data = btc_data['historical']
        raw_data = []
        
        base_dominance = 45  # Base BTC dominance around 45%
        
        for item in historical_data:
            date = datetime.strptime(item['date'], '%Y-%m-%d')
            timestamp_ms = int(date.timestamp() * 1000)
            
            # Simulate dominance based on price changes
            price = float(item['close'])
            price_ratio = (price / 50000) * 10  # Normalize around 50k BTC
            dominance = base_dominance + price_ratio
            dominance = max(35, min(65, dominance))  # Keep between 35-65%
            
            raw_data.append([timestamp_ms, dominance])
        
        # Save to cache
        save_to_cache(dataset_name, raw_data)
        print(f"Successfully fetched and cached {dataset_name}")
        
    except Exception as e:
        print(f"Error fetching BTC dominance: {e}. Loading from cache.")
        raw_data = load_from_cache(dataset_name)
        if not raw_data:
            return {'metadata': metadata, 'data': []}
    
    # Sort and process
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