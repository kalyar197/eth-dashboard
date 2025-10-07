# data/dxy.py
"""
US Dollar Index alternative using FRED Trade-Weighted Index
CRITICAL LIMITATION: FRED does NOT have the actual ICE DXY (proprietary data)
FRED indices are based on 2006=100, currently ~120
Actual ICE DXY is currently ~98

This module uses FRED's Trade-Weighted Index as the best free alternative
User should be aware this is NOT the same as the ICE DXY
"""

import requests
from .time_transformer import standardize_to_daily_utc
from datetime import datetime, timedelta
import sys
import os
from .cache_manager import load_from_cache, save_to_cache

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import FRED_API_KEY, FMP_API_KEY

def get_metadata():
    """Returns metadata describing how this index should be displayed"""
    return {
        'label': 'USD Index (FRED)',
        'yAxisId': 'indicator',
        'yAxisLabel': 'Index Value',
        'unit': '',
        'chartType': 'line',
        'color': '#85BB65',  # Dollar bill green
        'strokeWidth': 2,
        'description': 'FRED Trade-Weighted USD Index (2006=100). NOTE: This is NOT the ICE DXY.',
        'data_structure': 'simple',
        'components': ['timestamp', 'value'],
        'warning': 'FRED does not provide the actual ICE DXY. This is a trade-weighted alternative.'
    }

def fetch_dxy_from_fred(start_date, end_date):
    """
    Fetch USD Trade-Weighted Index from FRED
    NOTE: This returns values around 120 (indexed to 100 in 2006)
    This is NOT the ICE DXY which is around 98
    """
    print("=" * 60)
    print("⚠️  CRITICAL LIMITATION NOTICE")
    print("=" * 60)
    print("FRED does NOT provide the actual ICE Dollar Index (DXY)")
    print("The ICE DXY is proprietary data not available on FRED")
    print("")
    print("Current values:")
    print("  - ICE DXY (proprietary): ~90-105 range")
    print("  - FRED Trade-Weighted Index: ~120 (2006=100 base)")
    print("")
    print("This module returns FRED's best alternative:")
    print("  - Broad Trade-Weighted US Dollar Index (DTWEXBGS)")
    print("  - Based on 2006=100")
    print("  - Currently around 120")
    print("=" * 60)
    
    # FRED series ID for Broad Trade-Weighted Index
    series_id = 'DTWEXBGS'
    
    try:
        print(f"\nFetching FRED series: {series_id}")
        
        base_url = 'https://api.stlouisfed.org/fred/series/observations'
        
        params = {
            'series_id': series_id,
            'api_key': FRED_API_KEY,
            'observation_start': start_date.strftime('%Y-%m-%d'),
            'observation_end': end_date.strftime('%Y-%m-%d'),
            'file_type': 'json',
            'frequency': 'd',
            'aggregation_method': 'avg'
        }
        
        response = requests.get(base_url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'observations' in data:
                observations = data['observations']
                
                # Filter out missing values
                valid_observations = [
                    obs for obs in observations 
                    if obs.get('value') not in ['.', '', None]
                ]
                
                if not valid_observations:
                    print(f"  No valid data points")
                    return None
                
                print(f"  ✅ Successfully fetched {len(valid_observations)} data points")
                
                # Convert to our format
                raw_data = []
                for obs in valid_observations:
                    date_str = obs['date']
                    value = float(obs['value'])
                    
                    dt = datetime.strptime(date_str, '%Y-%m-%d')
                    timestamp_ms = int(dt.timestamp() * 1000)
                    
                    raw_data.append([timestamp_ms, value])
                
                raw_data.sort(key=lambda x: x[0])
                
                # Show sample and range
                if raw_data:
                    recent = raw_data[-1]
                    dt_recent = datetime.fromtimestamp(recent[0] / 1000)
                    print(f"\n  📊 Most recent value: {dt_recent.date()} = {recent[1]:.2f}")
                    
                    recent_values = [d[1] for d in raw_data[-30:]]
                    avg_value = sum(recent_values) / len(recent_values)
                    print(f"  📊 30-day average: {avg_value:.2f}")
                    
                    print(f"\n  ℹ️  REMINDER: These values are around 120 (2006=100 base)")
                    print(f"  ℹ️  NOT comparable to ICE DXY (~98)")
                
                return raw_data
                
        elif response.status_code == 400:
            error_data = response.json()
            print(f"  ❌ FRED error: {error_data.get('error_message', 'Unknown error')}")
        elif response.status_code == 429:
            print(f"  ❌ FRED rate limit exceeded")
        else:
            print(f"  ❌ HTTP {response.status_code} from FRED")
            
    except Exception as e:
        print(f"  ❌ Error fetching from FRED: {e}")
    
    return None

def get_data(days='365'):
    """
    Fetches FRED Trade-Weighted USD Index
    IMPORTANT: This is NOT the ICE DXY
    Returns values around 120 (2006=100 base) vs ICE DXY ~98
    """
    metadata = get_metadata()
    dataset_name = 'fred_trade_weighted_usd'
    
    try:
        # Calculate date range
        if days == 'max':
            start_date = datetime.now() - timedelta(days=365 * 5)
        else:
            start_date = datetime.now() - timedelta(days=int(days) + 30)
        
        end_date = datetime.now()
        
        # Try FRED
        raw_data = None
        
        if FRED_API_KEY and FRED_API_KEY != 'YOUR_FRED_API_KEY_HERE':
            raw_data = fetch_dxy_from_fred(start_date, end_date)
        else:
            print("⚠️  FRED API key not configured")
        
        # Try cache if FRED fails
        if not raw_data:
            print("\nLoading data from cache...")
            cached_data = load_from_cache(dataset_name)
            
            if cached_data:
                raw_data = cached_data
                print(f"  Loaded {len(raw_data)} cached data points")
            else:
                print("  No cached data available")
                return {
                    'metadata': metadata,
                    'data': [],
                    'error': 'Could not fetch FRED data and no cache available'
                }
        else:
            # Save fresh data to cache
            save_to_cache(dataset_name, raw_data)
            print(f"\n  Cached {len(raw_data)} data points")
        
        # Standardize data
        print("\nStandardizing to Daily UTC boundaries...")
        standardized_data = standardize_to_daily_utc(raw_data)
        print(f"  Standardized to {len(standardized_data)} daily data points")
        
        # Trim to requested days
        if days != 'max':
            cutoff_date = datetime.now() - timedelta(days=int(days))
            cutoff_ms = int(cutoff_date.timestamp() * 1000)
            standardized_data = [d for d in standardized_data if d[0] >= cutoff_ms]
            print(f"  Trimmed to {len(standardized_data)} data points (last {days} days)")
        
        # Final summary
        if standardized_data:
            recent_sample = standardized_data[-5:]
            print("\nRecent values:")
            for point in recent_sample:
                dt = datetime.fromtimestamp(point[0] / 1000)
                print(f"  {dt.date()}: {point[1]:.2f}")
        
        print("\n" + "=" * 60)
        print("⚠️  IMPORTANT REMINDER")
        print("=" * 60)
        print("These values (~120) are from FRED's Trade-Weighted Index")
        print("This is NOT the ICE DXY (~98)")
        print("FRED does not provide the proprietary ICE DXY data")
        print("=" * 60)
        
        return {
            'metadata': metadata,
            'data': standardized_data,
            'structure': 'simple',
            'warning': 'This is FRED Trade-Weighted Index, NOT ICE DXY'
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
        # Try cache
        cached_data = load_from_cache(dataset_name)
        if cached_data:
            return {
                'metadata': metadata,
                'data': cached_data,
                'error': f'Using cached data due to error: {str(e)}'
            }
        
        return {
            'metadata': metadata,
            'data': [],
            'error': str(e)
        }