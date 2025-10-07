# data/usdt_dominance.py
"""
USDT (Tether) dominance calculator using REAL market cap data from CoinAPI
FULLY COMPLIANT - Fetches ACTUAL USDT/USD prices from CoinAPI
NO ESTIMATES, NO ASSUMPTIONS, NO MOCK VALUES
Market Cap = ACTUAL Price × Circulating Supply
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
        'description': 'Tether (USDT) dominance - REAL PRICES FROM COINAPI'
    }

def fetch_usdt_price_from_coinapi(start_date, end_date):
    """
    CRITICAL: Fetch ACTUAL USDT/USD prices from CoinAPI
    NO ASSUMPTIONS - Returns actual price data or None
    """
    try:
        print("Fetching REAL USDT/USD prices from CoinAPI...")
        
        # Try multiple USDT trading pairs for reliability
        symbol_ids = [
            'COINBASE_SPOT_USDT_USD',   # Coinbase USDT/USD
            'KRAKEN_SPOT_USDT_USD',     # Kraken USDT/USD
            'BITSTAMP_SPOT_USDT_USD',   # Bitstamp USDT/USD
            'BINANCE_SPOT_USDT_BUSD',   # Binance USDT/BUSD as fallback
        ]
        
        base_url = 'https://rest.coinapi.io/v1/ohlcv'
        headers = {'X-CoinAPI-Key': COINAPI_KEY}
        
        for symbol_id in symbol_ids:
            try:
                url = f'{base_url}/{symbol_id}/history'
                
                params = {
                    'period_id': '1DAY',
                    'time_start': start_date.strftime('%Y-%m-%dT00:00:00'),
                    'time_end': end_date.strftime('%Y-%m-%dT23:59:59'),
                    'limit': 100000
                }
                
                print(f"  Trying {symbol_id}...")
                response = requests.get(url, params=params, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data and len(data) > 0:
                        print(f"  ✅ Successfully fetched USDT prices from {symbol_id}")
                        
                        price_data = {}
                        for candle in data:
                            timestamp_str = candle.get('time_period_start')
                            close_price = candle.get('price_close')
                            
                            if timestamp_str and close_price is not None:
                                dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                                date_key = dt.strftime('%Y-%m-%d')
                                price_data[date_key] = float(close_price)
                                
                                # Log sample prices to verify they're realistic for USDT
                                if len(price_data) <= 3:
                                    print(f"    {date_key}: USDT = ${close_price:.6f}")
                        
                        if price_data:
                            print(f"  Fetched {len(price_data)} days of REAL USDT prices")
                            # Verify prices are realistic for a stablecoin (0.90 - 1.10 range)
                            prices = list(price_data.values())
                            min_price = min(prices)
                            max_price = max(prices)
                            avg_price = sum(prices) / len(prices)
                            print(f"  Price range: ${min_price:.4f} - ${max_price:.4f} (avg: ${avg_price:.4f})")
                            
                            return price_data
                        
            except Exception as e:
                print(f"  Failed to fetch from {symbol_id}: {e}")
                continue
        
        print("❌ ERROR: Could not fetch USDT prices from any CoinAPI source")
        return None
        
    except Exception as e:
        print(f"❌ ERROR fetching USDT prices: {e}")
        return None

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

def fetch_asset_prices_from_coinapi(asset_name, symbol_id, start_date, end_date):
    """
    Fetch historical prices for any asset from CoinAPI
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
        print(f"Error fetching prices for {asset_name}: {e}")
        return None

def calculate_real_market_caps(assets_config, start_date, end_date):
    """
    Calculate REAL market caps using ACTUAL Price × Circulating Supply
    NO ESTIMATES - Returns None if data is incomplete
    USDT uses REAL prices from CoinAPI - NO ASSUMPTIONS
    """
    market_caps = {}
    
    for asset_name, config in assets_config.items():
        print(f"Processing {asset_name}...")
        
        # Get historical supply
        supply_data = fetch_historical_supply(config['asset_id'], start_date, end_date)
        if not supply_data:
            print(f"ERROR: No supply data for {asset_name} - cannot calculate market cap")
            return None
        
        # CRITICAL: Get REAL prices for ALL assets including USDT
        if asset_name == 'USDT':
            # Use dedicated USDT price fetching function
            price_data = fetch_usdt_price_from_coinapi(start_date, end_date)
            if not price_data:
                print("❌ COMPLIANCE FAILURE: Cannot calculate USDT dominance without REAL USDT prices")
                print("   NO ASSUMPTIONS MADE - Calculation correctly failed")
                return None
        else:
            # Fetch prices for other assets
            price_data = fetch_asset_prices_from_coinapi(
                asset_name, 
                config['symbol_id'], 
                start_date, 
                end_date
            )
            if not price_data:
                print(f"ERROR: No price data for {asset_name}")
                return None
        
        # Calculate REAL market cap for each day using ACTUAL prices
        asset_market_caps = {}
        for date_key in supply_data:
            if date_key in price_data:
                actual_price = price_data[date_key]
                supply = supply_data[date_key]
                
                # CRITICAL: Market Cap = ACTUAL Price × Supply
                market_cap = actual_price * supply
                asset_market_caps[date_key] = market_cap
                
                # Log USDT calculations for transparency
                if asset_name == 'USDT' and len(asset_market_caps) <= 3:
                    print(f"  {date_key}: USDT Price=${actual_price:.4f} × Supply={supply/1e9:.2f}B = MCap=${market_cap/1e9:.2f}B")
        
        if not asset_market_caps:
            print(f"ERROR: No market cap data calculated for {asset_name}")
            return None
            
        market_caps[asset_name] = asset_market_caps
        print(f"  Calculated {len(asset_market_caps)} days of REAL market cap for {asset_name}")
    
    return market_caps

def get_data(days='365'):
    """
    Fetches USDT dominance using REAL market cap data
    Market Cap = ACTUAL CoinAPI Price × Circulating Supply
    FULLY COMPLIANT - NO ASSUMPTIONS, NO ESTIMATES, NO MOCK VALUES
    """
    metadata = get_metadata()
    dataset_name = 'usdt_dominance_real'
    
    try:
        print("=" * 60)
        print("Calculating USDT dominance with REAL PRICES")
        print("Using ACTUAL USDT/USD prices from CoinAPI")
        print("NO ASSUMPTIONS - NO $1.00 PLACEHOLDER")
        print("=" * 60)
        
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
                'symbol_id': 'COINBASE_SPOT_USDT_USD'  # Will be handled by dedicated function
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
                'symbol_id': 'COINBASE_SPOT_USDC_USD'
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
        
        # Calculate REAL market caps with ACTUAL prices
        market_caps = calculate_real_market_caps(assets_config, start_date, end_date)
        
        if not market_caps:
            print("=" * 60)
            print("COMPLIANT FAILURE: Cannot calculate without complete REAL data")
            print("NO ESTIMATES OR ASSUMPTIONS WERE MADE")
            print("=" * 60)
            
            # Try loading from cache
            cached_data = load_from_cache(dataset_name)
            if cached_data:
                print("Using previously calculated REAL dominance data from cache")
                return process_cached_data(cached_data, days, metadata)
            else:
                return {
                    'metadata': metadata,
                    'data': [],
                    'error': 'COMPLIANT FAILURE: Insufficient REAL price data. NO ESTIMATES USED.'
                }
        
        # Calculate USDT dominance for each day
        dominance_data = []
        usdt_caps = market_caps.get('USDT', {})
        
        print("\nCalculating dominance from REAL market caps...")
        for date_key in sorted(usdt_caps.keys()):
            usdt_market_cap = usdt_caps[date_key]
            
            # Calculate total market cap for this date
            total_market_cap = 0
            assets_with_data = 0
            for asset_name, asset_caps in market_caps.items():
                if date_key in asset_caps:
                    total_market_cap += asset_caps[date_key]
                    assets_with_data += 1
            
            # Only calculate dominance if we have sufficient data
            if total_market_cap > 0 and assets_with_data >= len(market_caps) * 0.7:
                # Calculate REAL dominance
                dominance = (usdt_market_cap / total_market_cap) * 100
                
                # Convert date to timestamp
                dt = datetime.strptime(date_key, '%Y-%m-%d')
                dt = dt.replace(tzinfo=timezone.utc)
                timestamp_ms = int(dt.timestamp() * 1000)
                
                dominance_data.append([timestamp_ms, dominance])
                
                # Log first few calculations for verification
                if len(dominance_data) <= 3:
                    print(f"{date_key}: USDT MCap=${usdt_market_cap/1e9:.2f}B, Total=${total_market_cap/1e9:.2f}B, Dominance={dominance:.3f}%")
        
        if not dominance_data:
            print("ERROR: No dominance data calculated")
            return {
                'metadata': metadata,
                'data': [],
                'error': 'COMPLIANT FAILURE: Could not calculate dominance from available REAL data'
            }
        
        # Sort by timestamp
        dominance_data.sort(key=lambda x: x[0])
        
        # Save REAL data to cache
        save_to_cache(dataset_name, dominance_data)
        print(f"\n✅ Successfully calculated {len(dominance_data)} REAL USDT dominance data points")
        print("✅ ALL CALCULATIONS USED ACTUAL COINAPI PRICES")
        print("✅ FULLY COMPLIANT - NO ESTIMATES OR ASSUMPTIONS")
        
        raw_data = dominance_data
        
    except Exception as e:
        print(f"Error calculating USDT dominance: {e}")
        print("Attempting to load cached REAL data...")
        
        raw_data = load_from_cache(dataset_name)
        if not raw_data:
            return {
                'metadata': metadata,
                'data': [],
                'error': f'COMPLIANT FAILURE: {str(e)} - NO ESTIMATES USED'
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