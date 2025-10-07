# data/usdt_dominance.py
"""
USDT (Tether) dominance calculator using REAL market cap data
FIXED: Using CoinGecko API (free) for historical market cap data
NO ESTIMATES, NO ASSUMPTIONS - Only actual market cap values
"""

import requests
from .time_transformer import standardize_to_daily_utc
from datetime import datetime, timedelta, timezone
import sys
import os
from .cache_manager import load_from_cache, save_to_cache

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
        'description': 'Tether (USDT) dominance - REAL DATA from CoinGecko'
    }

def fetch_market_cap_from_coingecko(coin_id, start_date, end_date):
    """Fetch historical market cap data from CoinGecko (FREE API)"""
    try:
        url = f'https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart/range'
        from_timestamp = int(start_date.timestamp())
        to_timestamp = int(end_date.timestamp())
        
        params = {
            'vs_currency': 'usd',
            'from': from_timestamp,
            'to': to_timestamp
        }
        
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            market_caps = data.get('market_caps', [])
            
            if market_caps:
                # Convert to daily data
                daily_data = {}
                for timestamp_ms, market_cap in market_caps:
                    dt = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
                    date_key = dt.strftime('%Y-%m-%d')
                    daily_data[date_key] = market_cap
                
                return daily_data
        
        return None
    except Exception as e:
        return None

def calculate_dominance_from_market_caps(coin_market_caps, other_coins_market_caps):
    """Calculate dominance as (Coin Market Cap / Total Market Cap) × 100"""
    dominance_data = []
    all_dates = set(coin_market_caps.keys())
    
    for date_key in sorted(all_dates):
        coin_mc = coin_market_caps.get(date_key, 0)
        total_mc = coin_mc
        
        for other_coin_mc in other_coins_market_caps:
            if date_key in other_coin_mc:
                total_mc += other_coin_mc[date_key]
        
        if total_mc > 0:
            dominance = (coin_mc / total_mc) * 100
            dt = datetime.strptime(date_key, '%Y-%m-%d')
            dt = dt.replace(tzinfo=timezone.utc)
            timestamp_ms = int(dt.timestamp() * 1000)
            dominance_data.append([timestamp_ms, dominance])
    
    return dominance_data

def get_data(days='365'):
    """Fetches USDT dominance using REAL market cap data from CoinGecko"""
    metadata = get_metadata()
    dataset_name = 'usdt_dominance_real'
    
    try:
        print("=" * 60)
        print("Calculating USDT dominance with REAL market cap data")
        print("Using CoinGecko API (Free) for historical market caps")
        print("NO ASSUMPTIONS - NO ESTIMATES")
        print("=" * 60)
        
        # Calculate date range
        if days == 'max':
            start_date = datetime.now() - timedelta(days=365 * 2)
        else:
            start_date = datetime.now() - timedelta(days=int(days) + 10)
        end_date = datetime.now()
        
        # Top cryptocurrencies
        coins_to_track = [
            'bitcoin',
            'ethereum',
            'tether',  # USDT
            'binancecoin',
            'solana',
            'usd-coin',
            'ripple',
            'dogecoin',
            'cardano',
            'avalanche-2'
        ]
        
        # Fetch market caps
        market_caps = {}
        for coin_id in coins_to_track:
            coin_data = fetch_market_cap_from_coingecko(coin_id, start_date, end_date)
            if coin_data:
                market_caps[coin_id] = coin_data
        
        if 'tether' not in market_caps:
            print("❌ Could not fetch USDT market cap data")
            cached_data = load_from_cache(dataset_name)
            if cached_data:
                print("Using cached REAL dominance data")
                return process_cached_data(cached_data, days, metadata)
            return {
                'metadata': metadata,
                'data': [],
                'error': 'Could not fetch USDT market cap from CoinGecko'
            }
        
        # Calculate dominance
        print("Calculating USDT dominance...")
        usdt_mc = market_caps['tether']
        other_coins = [market_caps[coin] for coin in market_caps.keys() if coin != 'tether']
        dominance_data = calculate_dominance_from_market_caps(usdt_mc, other_coins)
        
        if not dominance_data:
            print("ERROR: No dominance data calculated")
            cached_data = load_from_cache(dataset_name)
            if cached_data:
                return process_cached_data(cached_data, days, metadata)
            return {'metadata': metadata, 'data': [], 'error': 'Could not calculate dominance'}
        
        # Log sample
        for i in range(min(3, len(dominance_data))):
            dt = datetime.fromtimestamp(dominance_data[i][0] / 1000)
            print(f"  {dt.date()}: USDT Dominance = {dominance_data[i][1]:.2f}%")
        
        # Save to cache
        save_to_cache(dataset_name, dominance_data)
        print(f"\n✅ Successfully calculated {len(dominance_data)} REAL USDT dominance data points")
        print("✅ Using actual market cap data from CoinGecko")
        print("=" * 60)
        
        raw_data = dominance_data
        
    except Exception as e:
        print(f"❌ Error calculating USDT dominance: {e}")
        raw_data = load_from_cache(dataset_name)
        if not raw_data:
            return {'metadata': metadata, 'data': [], 'error': str(e)}
    
    return process_cached_data(raw_data, days, metadata)

def process_cached_data(raw_data, days, metadata):
    """Process and filter cached or calculated data"""
    if raw_data:
        standardized_data = standardize_to_daily_utc(raw_data)
        
        if days != 'max':
            cutoff_date = datetime.now() - timedelta(days=int(days))
            cutoff_ms = int(cutoff_date.timestamp() * 1000)
            standardized_data = [d for d in standardized_data if d[0] >= cutoff_ms]
        
        return {'metadata': metadata, 'data': standardized_data}
    
    return {'metadata': metadata, 'data': []}