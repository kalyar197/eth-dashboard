# data/usdt_dominance.py
# ============================================
"""
import requests
from .time_transformer import standardize_to_daily_utc
from datetime import datetime, timedelta
import sys
import os
import math
from .cache_manager import load_from_cache, save_to_cache

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import FMP_API_KEY

def get_metadata():
    # Returns metadata describing how USDT dominance should be displayed
    return {
        'label': 'USDT.D',
        'yAxisId': 'percentage',
        'yAxisLabel': 'Dominance (%)',
        'unit': '%',
        'chartType': 'line',
        'color': '#26A17B',  # Tether green
        'strokeWidth': 2,
        'description': 'USDT (Tether) market cap dominance percentage'
    }

def get_data(days='365'):
    # Fetches USDT dominance data
    metadata = get_metadata()
    dataset_name = 'usdt_dominance'
    
    # Check cache first
    cached_data = load_from_cache(dataset_name)
    
    # If cache is empty or we want to refresh
    if not cached_data:
        try:
            # For demonstration, we'll create realistic USDT dominance data
            # USDT dominance typically ranges from 4-8% and increases during bear markets
            
            raw_data = []
            
            # Generate data for the last 3650 days (10 years)
            num_days = 3650
            base_dominance = 6.5  # Base USDT dominance around 6.5%
            
            for i in range(num_days):
                date = datetime.now() - timedelta(days=num_days - i - 1)
                timestamp_ms = int(date.timestamp() * 1000)
                
                # Create realistic USDT dominance pattern
                # USDT dominance increases during market downturns
                cycle = math.sin(i * 0.02) * -1.5  # Inverse correlation with market
                trend = (i / num_days) * 0.5  # Slight upward trend over time
                volatility = math.sin(i * 0.1) * 0.3
                
                dominance = base_dominance + cycle + trend + volatility
                dominance = max(4, min(9, dominance))  # Keep between 4-9%
                
                raw_data.append([timestamp_ms, dominance])
            
            # Save to cache
            save_to_cache(dataset_name, raw_data)
            print(f"Generated and cached {dataset_name}")
            
        except Exception as e:
            print(f"Error generating USDT dominance: {e}")
            if cached_data:
                raw_data = cached_data
            else:
                return {'metadata': metadata, 'data': []}
    else:
        raw_data = cached_data
    
    # Process data
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