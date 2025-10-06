# data/eth_dominance.py
"""
Ethereum dominance calculator using REAL market cap data from CoinAPI
NO ESTIMATES - Only actual market cap values
"""

import requests
from .time_transformer import standardize_to_daily_utc
from datetime import datetime, timedelta, timezone
import sys
import os
from .cache_manager import load_from_cache, save_to_cache

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import COINAPI_KEY

def get_metadata():
    """Returns metadata describing how ETH dominance should be displayed"""
    return {
        'label': 'ETH.D',
        'yAxisId': 'percentage',
        'yAxisLabel': 'Dominance (%)',
        'unit': '%',
        'chartType': 'line',
        'color': '#627EEA',  # Ethereum blue
        'strokeWidth': 2,
        'description': 'Ethereum market cap dominance - REAL DATA from CoinAPI'
    }

def fetch_historical_supply(asset_id, start_date, end_date):
    """
    Fetch historical circulating supply data for an asset
    This is CRITICAL for accurate market cap calculation
    """
    try:
        url = f'https://rest.coinapi.io/v1/metrics/asset'
        
        headers = {
            'X-CoinAPI-Key': COINAPI_KEY
        }
        
        params = {
            'metric_id': 'SUPPLY_CIRCULATING',
            'asset_id': asset_id,
            'time_start': start_date.strftime('%Y-%m-%dT00:00:00'),
            'time_end': end_date.strftime('%Y-%m-%dT23:59:59'),
            'period_id': '1DAY',
            'limit': 100000
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            supply_data = {}
            for entry in data:
                timestamp_str = entry.get('time_period_start')
                supply_value = entry.get('value')
                
                if timestamp_str and supply_value is not None:
                    dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    date_key = dt.strftime('%Y-%m-%d')
                    supply_data[date_key] = float(supply_value)
            
            return supply_data
        else:
            print(f"Failed to fetch supply data for {asset_id}: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Error fetching supply for {asset_id}: {e}")
        return None

def fetch_historical_prices(symbol_id, start_date, end_date):
    """
    Fetch historical price data for an asset
    """
    try:
        base_url = 'https://rest.coinapi.io/v1/ohlcv'
        url = f'{base_url}/{symbol_id}/history'
        
        params = {
            'period_id': '1DAY',
            'time_start': start_date.strftime('%Y-%m-%dT00:00:00'),
            'time_end': end_date.strftime('%Y-%m-%dT23:59:59'),
            'limit': 100000
        }
        
        headers = {
            'X-CoinAPI-Key': COINAPI_KEY
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=30)
        
        if response.status_code != 200:
            return None
            
        data = response.json()
        price_data = {}
        
        for candle in data:
            timestamp_str = candle.get('time_period_start')
            close_price = candle.get('price_close')
            
            if timestamp_str and close_price is not None:
                dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                date_key = dt.strftime('%Y-%m-%d')
                price_data[date_key] = float(close_price)
        
        return price_data
        
    except Exception as e:
        print(f"Error fetching prices for {symbol_id}: {e}")
        return None

def calculate_real_market_caps(assets_config, start_date, end_date):
    """
    Calculate REAL market caps using Price × Circulating Supply
    NO ESTIMATES - Returns None if data is incomplete
    """
    market_caps = {}
    
    for asset_name, config in assets_config.items():
        print(f"Fetching real data for {asset_name}...")
        
        # Get historical prices
        price_data = fetch_historical_prices(config['symbol_id'], start_date, end_date)
        if not price_data:
            print(f"ERROR: No price data for {asset_name} - cannot calculate market cap")
            return None
        
        # Get historical supply
        supply_data = fetch_historical_supply(config['asset_id'], start_date, end_date)
        if not supply_data:
            print(f"ERROR: No supply data for {asset_name} - cannot calculate market cap")
            return None
        
        # Calculate REAL market cap for each day
        asset_market_caps = {}
        for date_key in price_data:
            if date_key in supply_data:
                price = price_data[date_key]
                supply = supply_data[date_key]
                market_cap = price * supply
                asset_market_caps[date_key] = market_cap
            else:
                print(f"Warning: Missing supply data for {asset_name} on {date_key}")
        
        market_caps[asset_name] = asset_market_caps
    
    return market_caps

def get_data(days='365'):
    """
    Fetches ETH dominance using REAL market cap data
    Market Cap = Price × Circulating Supply (NO ESTIMATES)
    """
    metadata = get_metadata()
    dataset_name = 'eth_dominance_real'
    
    try:
        print("Calculating ETH dominance from REAL market cap data...")
        print("NO ESTIMATES - Using actual Price × Circulating Supply")
        
        # Calculate date range
        if days == 'max':
            start_date = datetime.now() - timedelta(days=365 * 2)
        else:
            start_date = datetime.now() - timedelta(days=int(days) + 10)
        end_date = datetime.now()
        
        # Define assets to track for total market cap
        assets_config = {
            'BTC': {
                'asset_id': 'BTC',
                'symbol_id': 'BINANCE_SPOT_BTC_USDT'
            },
            'ETH': {
                'asset_id': 'ETH',
                'symbol_id': 'BINANCE_SPOT_ETH_USDT'
            },
            'USDT': {
                'asset_id': 'USDT',
                'symbol_id': 'BINANCE_SPOT_USDT_BUSD'
            },
            'BNB': {
                'asset_id': 'BNB',
                'symbol_id': 'BINANCE_SPOT_BNB_USDT'
            },
            'XRP': {
                'asset_id': 'XRP',
                'symbol_id': 'BINANCE_SPOT_XRP_USDT'
            },
            'USDC': {
                'asset_id': 'USDC',
                'symbol_id': 'BINANCE_SPOT_USDC_USDT'
            },
            'SOL': {
                'asset_id': 'SOL',
                'symbol_id': 'BINANCE_SPOT_SOL_USDT'
            },
            'ADA': {
                'asset_id': 'ADA',
                'symbol_id': 'BINANCE_SPOT_ADA_USDT'
            },
            'DOGE': {
                'asset_id': 'DOGE',
                'symbol_id': 'BINANCE_SPOT_DOGE_USDT'
            }
        }
        
        # Calculate REAL market caps
        market_caps = calculate_real_market_caps(assets_config, start_date, end_date)
        
        if not market_caps:
            print("ERROR: Cannot calculate dominance without complete market cap data")
            # Try loading from cache
            cached_data = load_from_cache(dataset_name)
            if cached_data:
                print("Using cached REAL dominance data")
                return process_cached_data(cached_data, days, metadata)
            else:
                return {
                    'metadata': metadata,
                    'data': [],
                    'error': 'Insufficient data for REAL market cap calculation. API may not provide historical supply data.'
                }
        
        # Calculate ETH dominance for each day
        dominance_data = []
        eth_caps = market_caps.get('ETH', {})
        
        for date_key in sorted(eth_caps.keys()):
            eth_market_cap = eth_caps[date_key]
            
            # Calculate total market cap for this date
            total_market_cap = 0
            for asset_name, asset_caps in market_caps.items():
                if date_key in asset_caps:
                    total_market_cap += asset_caps[date_key]
            
            if total_market_cap > 0:
                # Calculate REAL dominance
                dominance = (eth_market_cap / total_market_cap) * 100
                
                # Convert date to timestamp
                dt = datetime.strptime(date_key, '%Y-%m-%d')
                dt = dt.replace(tzinfo=timezone.utc)
                timestamp_ms = int(dt.timestamp() * 1000)
                
                dominance_data.append([timestamp_ms, dominance])
                
                # Log for verification
                print(f"{date_key}: ETH={eth_market_cap/1e9:.2f}B, Total={total_market_cap/1e9:.2f}B, Dominance={dominance:.2f}%")
        
        if not dominance_data:
            print("ERROR: No dominance data calculated")
            return {
                'metadata': metadata,
                'data': [],
                'error': 'Could not calculate dominance from available data'
            }
        
        # Sort by timestamp
        dominance_data.sort(key=lambda x: x[0])
        
        # Save REAL data to cache
        save_to_cache(dataset_name, dominance_data)
        print(f"Successfully calculated {len(dominance_data)} REAL ETH dominance data points")
        
        raw_data = dominance_data
        
    except Exception as e:
        print(f"Error calculating ETH dominance: {e}")
        print("Attempting to load cached REAL data...")
        
        raw_data = load_from_cache(dataset_name)
        if not raw_data:
            return {
                'metadata': metadata,
                'data': [],
                'error': f'Failed to calculate REAL dominance: {str(e)}'
            }
    
    # Standardize and return the data
    return process_cached_data(raw_data, days, metadata)

def process_cached_data(raw_data, days, metadata):
    """Process and filter cached or calculated data"""
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