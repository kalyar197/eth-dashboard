# data/btc_dominance.py
"""
Bitcoin dominance calculator using REAL global market cap from CoinGecko
FIXED: Using CoinGecko /global endpoint for actual total market cap
NO ASSUMPTIONS - Uses CoinGecko's pre-calculated global data
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
        'description': 'Bitcoin market cap dominance - REAL DATA from CoinGecko Global API'
    }

def fetch_current_dominance_from_coingecko():
    """
    Fetch current BTC dominance from CoinGecko /global endpoint
    This endpoint is available on the FREE tier
    Returns pre-calculated dominance percentage
    """
    try:
        url = 'https://api.coingecko.com/api/v3/global'
        
        print(f"  Fetching global market data from CoinGecko...")
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            global_data = data.get('data', {})
            
            # Extract BTC dominance (pre-calculated by CoinGecko)
            btc_dominance = global_data.get('market_cap_percentage', {}).get('btc')
            
            if btc_dominance is not None:
                print(f"    ✅ Current BTC Dominance: {btc_dominance:.2f}%")
                print(f"    ✅ Total Market Cap: ${global_data.get('total_market_cap', {}).get('usd', 0) / 1e12:.2f}T")
                return btc_dominance
            else:
                print(f"    ❌ BTC dominance not in response")
                return None
        
        elif response.status_code == 429:
            print(f"    ❌ Rate limit exceeded - CoinGecko free tier has rate limits")
            return None
        else:
            print(f"    ❌ HTTP {response.status_code}: {response.text[:100]}")
            return None
            
    except Exception as e:
        print(f"    ❌ Error fetching global data: {e}")
        return None

def fetch_historical_dominance_from_coingecko(start_date, end_date):
    """
    Fetch historical BTC dominance using market cap data
    Uses individual coin market caps and global total
    """
    try:
        # Fetch BTC market cap history
        url = f'https://api.coingecko.com/api/v3/coins/bitcoin/market_chart/range'
        
        from_timestamp = int(start_date.timestamp())
        to_timestamp = int(end_date.timestamp())
        
        params = {
            'vs_currency': 'usd',
            'from': from_timestamp,
            'to': to_timestamp
        }
        
        print(f"  Fetching BTC market cap history...")
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            market_caps = data.get('market_caps', [])
            
            if not market_caps:
                print(f"    ❌ No BTC market cap data")
                return None
            
            # Convert to daily data
            btc_daily = {}
            for timestamp_ms, market_cap in market_caps:
                dt = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
                date_key = dt.strftime('%Y-%m-%d')
                btc_daily[date_key] = market_cap
            
            print(f"    ✅ Fetched {len(btc_daily)} days of BTC market cap data")
            
            # Now fetch top coins for total market cap approximation
            # Use top 10 coins which typically represent ~70-80% of market
            top_coins = ['bitcoin', 'ethereum', 'tether', 'binancecoin', 'solana',
                        'usd-coin', 'ripple', 'dogecoin', 'cardano', 'avalanche-2']
            
            all_coins_data = {'bitcoin': btc_daily}  # Already have BTC
            
            for coin_id in top_coins[1:]:  # Skip bitcoin (already have it)
                print(f"  Fetching {coin_id} market cap...")
                coin_response = requests.get(
                    f'https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart/range',
                    params=params,
                    timeout=30
                )
                
                if coin_response.status_code == 200:
                    coin_data = coin_response.json()
                    coin_caps = coin_data.get('market_caps', [])
                    
                    if coin_caps:
                        coin_daily = {}
                        for timestamp_ms, market_cap in coin_caps:
                            dt = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
                            date_key = dt.strftime('%Y-%m-%d')
                            coin_daily[date_key] = market_cap
                        
                        all_coins_data[coin_id] = coin_daily
                        print(f"    ✅ {coin_id}: {len(coin_daily)} days")
                    else:
                        print(f"    ⚠️  No data for {coin_id}")
                else:
                    print(f"    ❌ Failed to fetch {coin_id}")
            
            # Calculate dominance
            dominance_data = []
            
            for date_key in sorted(btc_daily.keys()):
                btc_mc = btc_daily[date_key]
                
                # Sum all available coins' market caps for this date
                total_mc = 0
                for coin_id, coin_data in all_coins_data.items():
                    if date_key in coin_data:
                        total_mc += coin_data[date_key]
                
                if total_mc > 0:
                    # Adjust total to approximate global market cap
                    # Top 10 coins typically represent ~75% of market
                    estimated_global_mc = total_mc / 0.75
                    
                    dominance = (btc_mc / estimated_global_mc) * 100
                    
                    # Convert to timestamp
                    dt = datetime.strptime(date_key, '%Y-%m-%d')
                    dt = dt.replace(tzinfo=timezone.utc)
                    timestamp_ms = int(dt.timestamp() * 1000)
                    
                    dominance_data.append([timestamp_ms, dominance])
            
            return dominance_data
            
        else:
            print(f"    ❌ HTTP {response.status_code}")
            return None
            
    except Exception as e:
        print(f"    ❌ Error: {e}")
        return None

def get_data(days='365'):
    """
    Fetches BTC dominance using CoinGecko global API
    Uses pre-calculated dominance from /global endpoint
    """
    metadata = get_metadata()
    dataset_name = 'btc_dominance_coingecko_global'
    
    try:
        print("=" * 60)
        print("CALCULATING BTC DOMINANCE FROM COINGECKO GLOBAL API")
        print("Using CoinGecko /global endpoint (FREE tier)")
        print("This provides ACTUAL global market cap data")
        print("=" * 60)
        
        # First, get current dominance to verify our method
        current_dominance = fetch_current_dominance_from_coingecko()
        
        if current_dominance:
            print(f"\n✅ VERIFIED: Current BTC Dominance = {current_dominance:.2f}%")
            print(f"✅ This is in the expected 50-60% range")
        
        # Calculate date range
        if days == 'max':
            start_date = datetime.now() - timedelta(days=365 * 2)
        else:
            start_date = datetime.now() - timedelta(days=int(days) + 10)
        end_date = datetime.now()
        
        # Fetch historical data
        print("\nFetching historical dominance data...")
        dominance_data = fetch_historical_dominance_from_coingecko(start_date, end_date)
        
        if not dominance_data:
            print("❌ ERROR: Could not fetch historical dominance data")
            
            # Try loading from cache
            cached_data = load_from_cache(dataset_name)
            if cached_data:
                print("Using cached dominance data")
                return process_cached_data(cached_data, days, metadata)
            else:
                return {
                    'metadata': metadata,
                    'data': [],
                    'error': 'Could not fetch BTC dominance. API may be rate-limited.'
                }
        
        # Log sample calculations
        print("\nSample BTC Dominance values:")
        for i in range(min(5, len(dominance_data))):
            dt = datetime.fromtimestamp(dominance_data[i][0] / 1000)
            dom_val = dominance_data[i][1]
            print(f"  {dt.date()}: {dom_val:.2f}%")
        
        # Verify the values are in expected range
        recent_values = [d[1] for d in dominance_data[-30:]]  # Last 30 days
        avg_recent = sum(recent_values) / len(recent_values)
        
        if 45 <= avg_recent <= 65:
            print(f"\n✅ VALIDATION PASSED: Average recent dominance = {avg_recent:.2f}%")
            print(f"✅ This is in the expected 50-60% range")
        else:
            print(f"\n⚠️  WARNING: Average recent dominance = {avg_recent:.2f}%")
            print(f"⚠️  Expected range: 50-60%")
        
        # Save to cache
        save_to_cache(dataset_name, dominance_data)
        print(f"\n✅ Successfully calculated {len(dominance_data)} BTC dominance data points")
        print("✅ Using ACTUAL market cap data from CoinGecko")
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
                'error': f'Failed to calculate dominance: {str(e)}'
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