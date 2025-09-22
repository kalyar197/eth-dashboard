# data/usdt_dominance.py
# REAL DATA from CoinStats API if available - NO ESTIMATES

import requests
from .time_transformer import standardize_to_daily_utc
from datetime import datetime, timedelta
import sys
import os
from .cache_manager import load_from_cache, save_to_cache

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import COINSTATS_API_KEY

def get_metadata():
    """Returns metadata describing how USDT dominance should be displayed"""
    return {
        'label': 'USDT.D',
        'yAxisId': 'percentage',
        'yAxisLabel': 'Dominance (%)',
        'unit': '%',
        'chartType': 'line',
        'color': '#26A17B',  # Tether green
        'strokeWidth': 2,
        'description': 'Tether (USDT) dominance - REAL DATA from CoinStats (if available)'
    }

def get_data(days='365'):
    """Fetches REAL USDT dominance data from CoinStats API if available."""
    metadata = get_metadata()
    dataset_name = 'usdt_dominance_coinstats'
    
    try:
        print("Attempting to fetch REAL USDT dominance from CoinStats API...")
        
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
        
        # Try different possible coin identifiers for USDT
        coin_identifiers = ['tether', 'usdt', 'tether-usdt']
        
        dominance_data = []
        data_found = False
        
        for coin_id in coin_identifiers:
            if data_found:
                break
                
            try:
                # CoinStats dominance endpoint
                url = f'https://api.coinstats.app/public/v1/charts/dominance'
                
                params = {
                    'coin': coin_id,
                    'period': period
                }
                
                response = requests.get(url, headers=headers, params=params, timeout=30)
                
                if response.status_code != 200:
                    # Try alternative endpoint structure
                    url = f'https://openapiv1.coinstats.app/coins/{coin_id}/charts'
                    params = {
                        'period': period,
                        'type': 'dominance'
                    }
                    response = requests.get(url, headers=headers, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Parse the response
                    if 'chart' in data:
                        chart_data = data['chart']
                    elif 'dominance' in data:
                        chart_data = data['dominance']
                    elif 'data' in data and isinstance(data['data'], list):
                        chart_data = data['data']
                    else:
                        continue  # Try next identifier
                    
                    # Process the data points
                    for point in chart_data:
                        if isinstance(point, list) and len(point) >= 2:
                            timestamp = point[0]
                            dominance_value = point[1]
                            
                            # Convert to milliseconds if needed
                            if timestamp < 1000000000000:  # If in seconds
                                timestamp = timestamp * 1000
                            
                            dominance_data.append([timestamp, dominance_value])
                        elif isinstance(point, dict):
                            timestamp = point.get('timestamp', point.get('time', point.get('date')))
                            dominance_value = point.get('dominance', point.get('value', point.get('percentage')))
                            
                            if timestamp and dominance_value is not None:
                                if timestamp < 1000000000000:
                                    timestamp = timestamp * 1000
                                dominance_data.append([timestamp, dominance_value])
                    
                    if dominance_data:
                        data_found = True
                        print(f"Found USDT dominance data using identifier: {coin_id}")
                        
            except Exception as e:
                print(f"Failed with identifier {coin_id}: {e}")
                continue
        
        if not dominance_data:
            # CoinStats may not provide USDT dominance
            print("USDT dominance not available from CoinStats API")
            print("You may need to find an alternative API that provides USDT dominance")
            
            # Check cache
            raw_data = load_from_cache(dataset_name)
            if raw_data:
                print("Using cached USDT dominance data")
                dominance_data = raw_data
            else:
                # Return empty with clear message
                return {
                    'metadata': metadata,
                    'data': [],
                    'error': 'USDT dominance not available from CoinStats. Consider alternative APIs.'
                }
        
        # Sort by timestamp
        dominance_data.sort(key=lambda x: x[0])
        
        # Save to cache if we got new data
        if data_found:
            save_to_cache(dataset_name, dominance_data)
            print(f"Successfully fetched {len(dominance_data)} REAL USDT dominance data points")
            print(f"Dominance range: {min(d[1] for d in dominance_data):.2f}% - {max(d[1] for d in dominance_data):.2f}%")
        
        raw_data = dominance_data
        
    except Exception as e:
        print(f"Error fetching USDT dominance from CoinStats: {e}")
        print("Attempting to load from cache...")
        
        raw_data = load_from_cache(dataset_name)
        if not raw_data:
            print("No cached REAL data available for USDT")
            return {
                'metadata': metadata,
                'data': [],
                'error': f'USDT dominance not available: {str(e)}'
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