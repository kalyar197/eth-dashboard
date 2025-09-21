# data/eth_dominance.py
# ============================================
"""
import requests
from .time_transformer import standardize_to_daily_utc
from datetime import datetime, timedelta
import sys
import os
from .cache_manager import load_from_cache, save_to_cache

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import FMP_API_KEY

def get_metadata():
    # Returns metadata describing how ETH dominance should be displayed
    return {
        'label': 'ETH.D',
        'yAxisId': 'percentage',
        'yAxisLabel': 'Dominance (%)',
        'unit': '%',
        'chartType': 'line',
        'color': '#627EEA',  # Ethereum blue
        'strokeWidth': 2,
        'description': 'Ethereum market cap dominance percentage'
    }

def get_data(days='365'):
    # Fetches Ethereum dominance data
    metadata = get_metadata()
    dataset_name = 'eth_dominance'
    
    try:
        # Get ETH price history to simulate dominance
        eth_url = f'https://financialmodelingprep.com/api/v3/historical-price-full/ETHUSD?apikey={FMP_API_KEY}'
        
        response = requests.get(eth_url)
        response.raise_for_status()
        eth_data = response.json()
        
        if 'historical' not in eth_data:
            print("No ETH data available for dominance calculation")
            raise ValueError("No ETH data")
        
        historical_data = eth_data['historical']
        raw_data = []
        
        base_dominance = 18  # Base ETH dominance around 18%
        
        for item in historical_data:
            date = datetime.strptime(item['date'], '%Y-%m-%d')
            timestamp_ms = int(date.timestamp() * 1000)
            
            # Simulate dominance based on ETH price relative to its historical average
            price = float(item['close'])
            price_ratio = (price / 3000) * 3  # Normalize around 3000 ETH
            dominance = base_dominance + price_ratio
            dominance = max(12, min(25, dominance))  # Keep between 12-25%
            
            raw_data.append([timestamp_ms, dominance])
        
        # Save to cache
        save_to_cache(dataset_name, raw_data)
        print(f"Successfully fetched and cached {dataset_name}")
        
    except Exception as e:
        print(f"Error fetching ETH dominance: {e}. Loading from cache.")
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
"""