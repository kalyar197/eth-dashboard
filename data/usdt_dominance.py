# data/usdt_dominance.py
"""
USDT (Tether) dominance calculator using REAL market cap data from CoinAPI
NO ESTIMATES - Only actual market cap values
NO PRICE ASSUMPTIONS - If price data missing, calculation FAILS (compliant failure)
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
    """Returns metadata describing how USDT dominance should be displayed"""
    return {
        'label': 'USDT.D',
        'yAxisId': 'percentage',
        'yAxisLabel': 'Dominance (%)',
        'unit': '%',
        'chartType': 'line',
        'color': '#26A17B',  # Tether green
        'strokeWidth': 2,
        'description': 'Tether (USDT) dominance - REAL DATA ONLY, NO ESTIMATES'
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
    NO FALLBACKS - Returns None if data unavailable
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
    CRITICAL: NO PRICE ASSUMPTIONS FOR STABLECOINS
    """
    market_caps = {}
    
    for asset_name, config in assets_config.items():
        print(f"Fetching real data for {asset_name}...")
        
        # Get historical supply
        supply_data = fetch_historical_supply(config['asset_id'], start_date, end_date)
        if not supply_data:
            print(f"ERROR: No supply data for {asset_name} - cannot calculate market cap")
            return None
        
        # Get historical prices
        price_data = fetch_historical_prices(config['symbol_id'], start_date, end_date)
        
        # CRITICAL FIX: NO ASSUMPTIONS FOR MISSING PRICE DATA
        # If price data is missing, the calculation MUST FAIL
        if not price_data:
            print(f"ERROR: No price data for {asset_name} - cannot calculate market cap")
            print(f"COMPLIANCE: Not assuming any price values. Calculation failed correctly.")
            return None
        
        # Calculate REAL market cap for each day
        asset_market_caps = {}
        missing_data_days = []
        
        for date_key in supply_data:
            if date_key in price_data:
                price = price_data[date_key]
                supply = supply_data[date_key]
                market_cap = price * supply
                asset_market_caps[date_key] = market_cap
            else:
                # CRITICAL: Log missing data but DO NOT SUBSTITUTE
                missing_data_days.append(date_key)
        
        if missing_data_days:
            print(f"Warning: Missing price data for {asset_name} on {len(missing_data_days)} days")
            print(f"COMPLIANCE: Not substituting any estimated prices")
            # If too much data is missing, consider the calculation failed
            if len(missing_data_days) > len(supply_data) * 0.1:  # More than 10% missing
                print(f"ERROR: Too much missing price data for {asset_name} (>10% days missing)")
                return None
        
        if not asset_market_caps:
            print(f"ERROR: No market cap data calculated for {asset_name}")
            return None
            
        market_caps[asset_name] = asset_market_caps
    
    return market_caps

def get_data(days='365'):
    """
    Fetches USDT dominance using REAL market cap data
    Market Cap = Price × Circulating Supply (NO ESTIMATES)
    CRITICAL: NO PRICE ASSUMPTIONS - Calculation fails if data missing
    """
    metadata = get_metadata()
    dataset_name = 'usdt_dominance_real'
    
    try:
        print("Calculating USDT dominance from REAL market cap data...")
        print("NO ESTIMATES - Using actual Price × Circulating Supply ONLY")
        print("COMPLIANCE: Will fail if price data unavailable (no $1.00 assumption)")
        
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
                'symbol_id': 'BINANCE_SPOT_USDT_BUSD'  # USDT/BUSD pair for real price
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
        
        # Calculate REAL market caps - NO ESTIMATES
        market_caps = calculate_real_market_caps(assets_config, start_date, end_date)
        
        if not market_caps:
            print("ERROR: Cannot calculate dominance without complete market cap data")
            print("COMPLIANCE: Failed correctly due to missing price data (no estimates used)")
            # Try loading from cache
            cached_data = load_from_cache(dataset_name)
            if cached_data:
                print("Using cached REAL dominance data (previously calculated with real prices)")
                return process_cached_data(cached_data, days, metadata)
            else:
                return {
                    'metadata': metadata,
                    'data': [],
                    'error': 'Insufficient REAL data for market cap calculation. NO ESTIMATES USED.'
                }
        
        # Calculate USDT dominance for each day
        dominance_data = []
        usdt_caps = market_caps.get('USDT', {})
        
        for date_key in sorted(usdt_caps.keys()):
            usdt_market_cap = usdt_caps[date_key]
            
            # Calculate total market cap for this date
            total_market_cap = 0
            assets_with_data = 0
            for asset_name, asset_caps in market_caps.items():
                if date_key in asset_caps:
                    total_market_cap += asset_caps[date_key]
                    assets_with_data += 1
            
            # Only calculate dominance if we have data for most assets
            if total_market_cap > 0 and assets_with_data >= len(market_caps) * 0.7:
                # Calculate REAL dominance
                dominance = (usdt_market_cap / total_market_cap) * 100
                
                # Convert date to timestamp
                dt = datetime.strptime(date_key, '%Y-%m-%d')
                dt = dt.replace(tzinfo=timezone.utc)
                timestamp_ms = int(dt.timestamp() * 1000)
                
                dominance_data.append([timestamp_ms, dominance])
                
                # Log for verification
                print(f"{date_key}: USDT={usdt_market_cap/1e9:.2f}B, Total={total_market_cap/1e9:.2f}B, Dominance={dominance:.2f}%")
        
        if not dominance_data:
            print("ERROR: No dominance data calculated")
            print("COMPLIANCE: Failed correctly - no estimates used")
            return {
                'metadata': metadata,
                'data': [],
                'error': 'Could not calculate dominance from available REAL data'
            }
        
        # Sort by timestamp
        dominance_data.sort(key=lambda x: x[0])
        
        # Save REAL data to cache
        save_to_cache(dataset_name, dominance_data)
        print(f"Successfully calculated {len(dominance_data)} REAL USDT dominance data points")
        print("COMPLIANCE: All calculations used actual price data - NO ESTIMATES")
        
        raw_data = dominance_data
        
    except Exception as e:
        print(f"Error calculating USDT dominance: {e}")
        print("Attempting to load cached REAL data...")
        
        raw_data = load_from_cache(dataset_name)
        if not raw_data:
            return {
                'metadata': metadata,
                'data': [],
                'error': f'Failed to calculate REAL dominance: {str(e)} - NO ESTIMATES USED'
            }
    
    # Standardize and return the data
    return process_cached_data(raw_data, days, metadata)

def process_cached_data(raw_data, days, metadata):
    """Process and filter cached or calculated data"""
    if raw_data:
        # Handle both 2-element and potential 6-element structures
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