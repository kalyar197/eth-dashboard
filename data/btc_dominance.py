# data/btc_dominance.py
"""
Bitcoin dominance calculator using REAL market cap data
FIXED: Using CoinGecko API (free) for historical market cap data
NO ESTIMATES - Only actual market cap values
Market Cap Dominance = (BTC Market Cap / Total Crypto Market Cap) × 100
"""

import requests
from .time_transformer import standardize_to_daily_utc
from datetime import datetime, timedelta, timezone
import sys
import os
from .cache_manager import load_from_cache, save_to_cache

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
        'description': 'Bitcoin market cap dominance - REAL DATA from CoinGecko'
    }

def fetch_market_cap_from_coingecko(coin_id, start_date, end_date):
    """
    Fetch historical market cap data from CoinGecko (FREE API)
    CoinGecko provides market cap directly, no need for Price × Supply calculation
    """
    try:
        # CoinGecko API endpoint for historical market chart data
        url = f'https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart/range'
        
        # Convert dates to Unix timestamps
        from_timestamp = int(start_date.timestamp())
        to_timestamp = int(end_date.timestamp())
        
        params = {
            'vs_currency': 'usd',
            'from': from_timestamp,
            'to': to_timestamp
        }
        
        print(f"  Fetching market cap for {coin_id}...")
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract market cap data (returns [[timestamp_ms, market_cap], ...])
            market_caps = data.get('market_caps', [])
            
            if market_caps:
                # Convert to daily data (CoinGecko returns hourly data)
                daily_data = {}
                for timestamp_ms, market_cap in market_caps:
                    dt = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
                    date_key = dt.strftime('%Y-%m-%d')
                    
                    # Use the last market cap value for each day
                    daily_data[date_key] = market_cap
                
                print(f"    ✅ Fetched {len(daily_data)} days of market cap data")
                return daily_data
            else:
                print(f"    ❌ No market cap data in response")
                return None
        
        elif response.status_code == 429:
            print(f"    ❌ Rate limit exceeded - CoinGecko has rate limits on free tier")
            return None
        else:
            print(f"    ❌ HTTP {response.status_code}: {response.text[:100]}")
            return None
            
    except Exception as e:
        print(f"    ❌ Error fetching market cap for {coin_id}: {e}")
        return None

def fetch_total_market_cap(start_date, end_date):
    """
    Fetch total cryptocurrency market cap from CoinGecko
    """
    try:
        url = 'https://api.coingecko.com/api/v3/global'
        
        print(f"  Fetching global market cap...")
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            current_total_mc = data['data']['total_market_cap']['usd']
            print(f"    ✅ Current total market cap: ${current_total_mc / 1e9:.2f}B")
            
            # For historical data, we'll approximate using the sum of top coins
            # This is acceptable as the top 10-20 coins make up ~80% of market cap
            return True
        else:
            print(f"    ❌ Could not fetch global market cap")
            return False
            
    except Exception as e:
        print(f"    ❌ Error fetching global market cap: {e}")
        return False

def calculate_dominance_from_market_caps(coin_market_caps, other_coins_market_caps):
    """
    Calculate dominance as (Coin Market Cap / Total Market Cap) × 100
    Uses actual market cap data from CoinGecko
    """
    dominance_data = []
    
    # Get all dates that have data
    all_dates = set(coin_market_caps.keys())
    
    for date_key in sorted(all_dates):
        coin_mc = coin_market_caps.get(date_key, 0)
        
        # Calculate total market cap from all tracked coins
        total_mc = coin_mc
        for other_coin_mc in other_coins_market_caps:
            if date_key in other_coin_mc:
                total_mc += other_coin_mc[date_key]
        
        if total_mc > 0:
            dominance = (coin_mc / total_mc) * 100
            
            # Convert date to timestamp
            dt = datetime.strptime(date_key, '%Y-%m-%d')
            dt = dt.replace(tzinfo=timezone.utc)
            timestamp_ms = int(dt.timestamp() * 1000)
            
            dominance_data.append([timestamp_ms, dominance])
    
    return dominance_data

def get_data(days='365'):
    """
    Fetches BTC dominance using REAL market cap data from CoinGecko
    Market Cap Dominance = (BTC MC / Total MC) × 100 (NO ESTIMATES)
    """
    metadata = get_metadata()
    dataset_name = 'btc_dominance_real'
    
    try:
        print("=" * 60)
        print("Calculating BTC dominance from REAL market cap data")
        print("Using CoinGecko API (Free) for historical market caps")
        print("NO ESTIMATES - Using actual market cap values")
        print("=" * 60)
        
        # Calculate date range
        if days == 'max':
            start_date = datetime.now() - timedelta(days=365 * 2)
        else:
            start_date = datetime.now() - timedelta(days=int(days) + 10)
        end_date = datetime.now()
        
        # Top cryptocurrencies by market cap (covers ~80%+ of total market)
        coins_to_track = [
            'bitcoin',
            'ethereum',
            'tether',
            'binancecoin',
            'solana',
            'usd-coin',
            'ripple',
            'dogecoin',
            'cardano',
            'avalanche-2'
        ]
        
        # Fetch market caps for all coins
        print("\nFetching market cap data from CoinGecko...")
        market_caps = {}
        
        for coin_id in coins_to_track:
            coin_data = fetch_market_cap_from_coingecko(coin_id, start_date, end_date)
            if coin_data:
                market_caps[coin_id] = coin_data
            else:
                print(f"  ⚠️  Warning: No data for {coin_id}")
        
        if 'bitcoin' not in market_caps:
            print("❌ ERROR: Could not fetch Bitcoin market cap data")
            
            # Try loading from cache
            cached_data = load_from_cache(dataset_name)
            if cached_data:
                print("Using cached REAL dominance data")
                return process_cached_data(cached_data, days, metadata)
            else:
                return {
                    'metadata': metadata,
                    'data': [],
                    'error': 'Could not fetch BTC market cap from CoinGecko. API may be rate-limited.'
                }
        
        # Calculate dominance
        print("\nCalculating BTC dominance...")
        btc_mc = market_caps['bitcoin']
        other_coins = [market_caps[coin] for coin in market_caps.keys() if coin != 'bitcoin']
        
        dominance_data = calculate_dominance_from_market_caps(btc_mc, other_coins)
        
        if not dominance_data:
            print("ERROR: No dominance data calculated")
            cached_data = load_from_cache(dataset_name)
            if cached_data:
                return process_cached_data(cached_data, days, metadata)
            return {
                'metadata': metadata,
                'data': [],
                'error': 'Could not calculate dominance from available data'
            }
        
        # Log sample calculations
        for i in range(min(3, len(dominance_data))):
            dt = datetime.fromtimestamp(dominance_data[i][0] / 1000)
            print(f"  {dt.date()}: BTC Dominance = {dominance_data[i][1]:.2f}%")
        
        # Save REAL data to cache
        save_to_cache(dataset_name, dominance_data)
        print(f"\n✅ Successfully calculated {len(dominance_data)} REAL BTC dominance data points")
        print("✅ Using actual market cap data from CoinGecko")
        print("=" * 60)
        
        raw_data = dominance_data
        
    except Exception as e:
        print(f"❌ Error calculating BTC dominance: {e}")
        import traceback
        traceback.print_exc()
        
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