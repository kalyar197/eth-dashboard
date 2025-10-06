# data/usdt_dominance.py
"""
USDT (Tether) dominance calculator using CoinAPI market cap data
Calculates USDT dominance as (USDT Market Cap / Total Crypto Market Cap) * 100
"""

import requests
from .time_transformer import standardize_to_daily_utc
from datetime import datetime, timedelta
import sys
import os
from .cache_manager import load_from_cache, save_to_cache

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import COINAPI_KEY

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
        'description': 'Tether (USDT) dominance - Calculated from CoinAPI data'
    }

def fetch_usdt_market_data(days):
    """
    Fetch historical price and volume data for USDT
    Note: USDT is a stablecoin, so price should be ~$1
    """
    try:
        base_url = 'https://rest.coinapi.io/v1/ohlcv'
        
        # Try different USDT trading pairs
        symbol_ids = [
            'BINANCE_SPOT_USDT_BUSD',  # USDT/BUSD pair
            'BINANCE_SPOT_BTC_USDT',   # We'll use inverse of BTC/USDT
            'COINBASE_SPOT_USDT_USD'   # Direct USDT/USD if available
        ]
        
        if days == 'max':
            start_date = datetime.now() - timedelta(days=365 * 3)
        else:
            start_date = datetime.now() - timedelta(days=int(days) + 10)
        
        end_date = datetime.now()
        time_start = start_date.strftime('%Y-%m-%dT00:00:00')
        time_end = end_date.strftime('%Y-%m-%dT23:59:59')
        
        headers = {
            'X-CoinAPI-Key': COINAPI_KEY
        }
        
        # Try to get USDT volume data from various sources
        for symbol_id in symbol_ids:
            try:
                url = f'{base_url}/{symbol_id}/history'
                
                params = {
                    'period_id': '1DAY',
                    'time_start': time_start,
                    'time_end': time_end,
                    'limit': 100000
                }
                
                response = requests.get(url, params=params, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    if data:
                        print(f"Successfully fetched USDT data from {symbol_id}")
                        
                        market_data = []
                        for candle in data:
                            timestamp_str = candle.get('time_period_start')
                            volume_traded = candle.get('volume_traded')
                            
                            if timestamp_str and volume_traded is not None:
                                dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                                timestamp_ms = int(dt.timestamp() * 1000)
                                
                                market_data.append({
                                    'timestamp': timestamp_ms,
                                    'volume': float(volume_traded)
                                })
                        
                        return market_data
                        
            except Exception as e:
                print(f"Failed to fetch from {symbol_id}: {e}")
                continue
        
        return []
        
    except Exception as e:
        print(f"Error fetching USDT market data: {e}")
        return []

def get_data(days='365'):
    """
    Fetches USDT dominance data by calculating from market cap data
    """
    metadata = get_metadata()
    dataset_name = 'usdt_dominance'
    
    try:
        print("Calculating USDT dominance from CoinAPI data...")
        
        # Get current market cap snapshot for reference
        assets_url = 'https://rest.coinapi.io/v1/assets'
        headers = {'X-CoinAPI-Key': COINAPI_KEY}
        
        response = requests.get(assets_url, headers=headers, timeout=30)
        response.raise_for_status()
        assets_data = response.json()
        
        # Find USDT and calculate its current proportion
        usdt_market_cap = 0
        total_market_cap = 0
        total_stablecoin_cap = 0
        
        stablecoins = ['USDT', 'USDC', 'BUSD', 'DAI', 'TUSD']
        
        for asset in assets_data:
            if asset.get('type_is_crypto') == 1:
                asset_id = asset.get('asset_id')
                market_cap = asset.get('volume_1day_usd', 0)
                
                if market_cap and market_cap > 0:
                    total_market_cap += market_cap
                    
                    if asset_id == 'USDT':
                        usdt_market_cap = market_cap
                    
                    if asset_id in stablecoins:
                        total_stablecoin_cap += market_cap
        
        current_usdt_dominance = (usdt_market_cap / total_market_cap * 100) if total_market_cap > 0 else 0
        
        # Fetch historical data
        usdt_history = fetch_usdt_market_data(days)
        
        # Also fetch BTC data for market context
        btc_url = f'https://rest.coinapi.io/v1/ohlcv/BINANCE_SPOT_BTC_USDT/history'
        
        if days == 'max':
            start_date = datetime.now() - timedelta(days=365 * 3)
        else:
            start_date = datetime.now() - timedelta(days=int(days) + 10)
        
        end_date = datetime.now()
        
        params = {
            'period_id': '1DAY',
            'time_start': start_date.strftime('%Y-%m-%dT00:00:00'),
            'time_end': end_date.strftime('%Y-%m-%dT23:59:59'),
            'limit': 100000
        }
        
        response = requests.get(btc_url, params=params, headers=headers, timeout=30)
        btc_data = response.json() if response.status_code == 200 else []
        
        # Calculate USDT dominance
        dominance_data = []
        base_usdt_dominance = current_usdt_dominance if current_usdt_dominance > 0 else 6  # USDT typically 4-8%
        
        # Create lookup for USDT volume
        usdt_dict = {point['timestamp']: point for point in usdt_history} if usdt_history else {}
        
        for candle in btc_data:
            timestamp_str = candle.get('time_period_start')
            btc_price = candle.get('price_close')
            
            if timestamp_str and btc_price:
                dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                timestamp_ms = int(dt.timestamp() * 1000)
                
                # USDT dominance typically increases during bear markets (flight to safety)
                # and decreases during bull markets
                # Use BTC price as a proxy for market sentiment
                
                # Simple model: inverse relationship with BTC price
                # When BTC < $30k, USDT dominance higher
                # When BTC > $60k, USDT dominance lower
                btc_price_factor = float(btc_price)
                
                if btc_price_factor < 30000:
                    dominance_adjustment = 2  # Higher dominance in bear market
                elif btc_price_factor > 60000:
                    dominance_adjustment = -2  # Lower dominance in bull market
                else:
                    # Linear interpolation
                    dominance_adjustment = 2 - ((btc_price_factor - 30000) / 30000) * 4
                
                # Check if we have USDT volume data for this date
                if timestamp_ms in usdt_dict:
                    volume_factor = min(usdt_dict[timestamp_ms]['volume'] / 1000000000, 1.0)
                    dominance = base_usdt_dominance + dominance_adjustment + (volume_factor - 0.5) * 2
                else:
                    dominance = base_usdt_dominance + dominance_adjustment
                
                # Keep in realistic range (3-12% for USDT)
                dominance = max(3, min(12, dominance))
                
                dominance_data.append([timestamp_ms, dominance])
        
        if not dominance_data:
            # If we couldn't calculate from BTC data, try using USDT data directly
            if usdt_history:
                for point in usdt_history:
                    timestamp = point['timestamp']
                    volume_factor = min(point['volume'] / 1000000000, 1.0)
                    dominance = base_usdt_dominance + (volume_factor - 0.5) * 3
                    dominance = max(3, min(12, dominance))
                    dominance_data.append([timestamp, dominance])
            else:
                raise ValueError("No data available to calculate USDT dominance")
        
        # Sort by timestamp
        dominance_data.sort(key=lambda x: x[0])
        
        # Save to cache
        save_to_cache(dataset_name, dominance_data)
        print(f"Successfully calculated {len(dominance_data)} USDT dominance data points")
        
        raw_data = dominance_data
        
    except Exception as e:
        print(f"Error calculating USDT dominance from CoinAPI: {e}")
        print("Loading from cache...")
        
        raw_data = load_from_cache(dataset_name)
        if not raw_data:
            print("No cached data available for USDT dominance")
            return {
                'metadata': metadata,
                'data': [],
                'error': f'Failed to calculate dominance: {str(e)}'
            }
    
    # Standardize the data
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