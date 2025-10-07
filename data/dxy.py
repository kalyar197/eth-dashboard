# data/dxy.py
"""
DXY Dollar Index fetcher using Federal Reserve Economic Data (FRED) API
Falls back to FMP if FRED unavailable
Returns simple 2-component structure [timestamp, value]
NO COINAPI REFERENCES - Uses FRED/FMP exclusively
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
    """Returns metadata describing how DXY data should be displayed"""
    return {
        'label': 'DXY (Dollar Index)',
        'yAxisId': 'indicator',
        'yAxisLabel': 'DXY Index',
        'unit': '',
        'chartType': 'line',
        'color': '#85BB65',  # Dollar bill green
        'strokeWidth': 2,
        'description': 'US Dollar Index (DXY) from FRED',
        'data_structure': 'simple',  # DXY is always a single value
        'components': ['timestamp', 'value']
    }

def fetch_dxy_from_fred(start_date, end_date):
    """
    Fetch DXY Dollar Index from Federal Reserve Economic Data (FRED)
    Series ID: DTWEXBGS or DTWEXM (Trade Weighted U.S. Dollar Index)
    """
    print("=" * 60)
    print("Fetching DXY from FRED API (Primary Source)")
    print("=" * 60)
    
    # FRED series IDs for Dollar Index
    series_ids = [
        ('DTWEXBGS', 'Trade Weighted U.S. Dollar Index: Broad, Goods and Services'),
        ('DTWEXM', 'Trade Weighted U.S. Dollar Index: Major Currencies'),
        ('DEXUSEU', 'U.S. / Euro Foreign Exchange Rate')  # Fallback
    ]
    
    base_url = 'https://api.stlouisfed.org/fred/series/observations'
    
    for series_id, description in series_ids:
        try:
            print(f"\nTrying FRED series: {series_id}")
            print(f"  Description: {description}")
            
            params = {
                'series_id': series_id,
                'api_key': FRED_API_KEY,
                'observation_start': start_date.strftime('%Y-%m-%d'),
                'observation_end': end_date.strftime('%Y-%m-%d'),
                'file_type': 'json',
                'frequency': 'd',  # Daily frequency
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
                        print(f"  No valid data points for {series_id}")
                        continue
                    
                    print(f"  ✅ Successfully fetched {len(valid_observations)} data points from FRED")
                    
                    # Convert to our format
                    raw_data = []
                    for obs in valid_observations:
                        date_str = obs['date']
                        value = float(obs['value'])
                        
                        # Parse date and convert to milliseconds
                        dt = datetime.strptime(date_str, '%Y-%m-%d')
                        timestamp_ms = int(dt.timestamp() * 1000)
                        
                        raw_data.append([timestamp_ms, value])
                    
                    # Sort by timestamp
                    raw_data.sort(key=lambda x: x[0])
                    
                    # Log sample data
                    if raw_data:
                        recent = raw_data[-1]
                        dt_recent = datetime.fromtimestamp(recent[0] / 1000)
                        print(f"  📊 Most recent: {dt_recent.date()} = {recent[1]:.2f}")
                        print(f"  📊 Data range: {len(raw_data)} daily points")
                    
                    return raw_data
                    
            elif response.status_code == 400:
                error_data = response.json()
                if 'error_message' in error_data:
                    if 'api_key' in error_data['error_message'].lower():
                        print(f"  ❌ FRED API key issue: {error_data['error_message']}")
                    else:
                        print(f"  ❌ FRED error: {error_data['error_message']}")
                else:
                    print(f"  ❌ Bad request to FRED API")
            elif response.status_code == 429:
                print(f"  ❌ FRED rate limit exceeded")
            else:
                print(f"  ❌ HTTP {response.status_code} from FRED")
                
        except Exception as e:
            print(f"  ❌ Error fetching from FRED: {e}")
            continue
    
    print("\n⚠️  Could not fetch DXY from FRED")
    return None

def fetch_dxy_from_fmp(start_date, end_date):
    """
    Fallback: Fetch DXY from Financial Modeling Prep
    """
    print("\n" + "=" * 60)
    print("Fetching DXY from FMP API (Fallback)")
    print("=" * 60)
    
    try:
        # FMP endpoint for DXY
        url = f'https://financialmodelingprep.com/api/v3/historical-price-full/DX-Y.NYB'
        params = {'apikey': FMP_API_KEY}
        
        print(f"URL: {url}")
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'historical' in data:
                historical_data = data['historical']
                
                if historical_data:
                    print(f"  ✅ Successfully fetched {len(historical_data)} data points from FMP")
                    
                    # Convert to our format
                    raw_data = []
                    for item in historical_data:
                        date_str = item['date']
                        close_value = float(item.get('close', item.get('price', 0)))
                        
                        if close_value > 0:  # Valid data
                            dt = datetime.strptime(date_str, '%Y-%m-%d')
                            timestamp_ms = int(dt.timestamp() * 1000)
                            raw_data.append([timestamp_ms, close_value])
                    
                    # Sort by timestamp
                    raw_data.sort(key=lambda x: x[0])
                    
                    if raw_data:
                        recent = raw_data[-1]
                        dt_recent = datetime.fromtimestamp(recent[0] / 1000)
                        print(f"  📊 Most recent: {dt_recent.date()} = {recent[1]:.2f}")
                    
                    return raw_data
        
        elif response.status_code == 401:
            print(f"  ❌ FMP authentication failed")
        else:
            print(f"  ❌ HTTP {response.status_code} from FMP")
            
    except Exception as e:
        print(f"  ❌ Error fetching from FMP: {e}")
    
    return None

def get_data(days='365'):
    """
    Fetches DXY Dollar Index data
    Prioritizes FRED API, falls back to FMP if needed
    Returns simple 2-component structure [timestamp, value]
    All data is standardized to daily UTC boundaries
    """
    metadata = get_metadata()
    dataset_name = 'dxy_dollar_index'
    
    try:
        # Calculate date range
        if days == 'max':
            start_date = datetime.now() - timedelta(days=365 * 5)  # 5 years max
        else:
            try:
                days_int = int(days)
                start_date = datetime.now() - timedelta(days=days_int + 30)  # Extra buffer
            except ValueError:
                start_date = datetime.now() - timedelta(days=365)
        
        end_date = datetime.now()
        
        # Try FRED first (primary source)
        raw_data = None
        
        if FRED_API_KEY and FRED_API_KEY != 'YOUR_FRED_API_KEY_HERE':
            raw_data = fetch_dxy_from_fred(start_date, end_date)
        else:
            print("⚠️  FRED API key not configured, skipping FRED")
        
        # Fall back to FMP if FRED fails
        if not raw_data:
            print("\nTrying FMP as fallback...")
            raw_data = fetch_dxy_from_fmp(start_date, end_date)
        
        # Try cache if both APIs fail
        if not raw_data:
            print("\nLoading DXY data from cache...")
            cached_data = load_from_cache(dataset_name)
            
            if cached_data:
                raw_data = cached_data
                print(f"  Loaded {len(raw_data)} cached data points")
            else:
                print("  No cached data available")
                return {
                    'metadata': metadata,
                    'data': [],
                    'error': 'Could not fetch DXY data from FRED or FMP, and no cache available'
                }
        else:
            # Save fresh data to cache
            save_to_cache(dataset_name, raw_data)
            print(f"\n  Cached {len(raw_data)} data points for future use")
        
        # Standardize data to daily UTC boundaries
        print("\nStandardizing to Daily UTC boundaries...")
        standardized_data = standardize_to_daily_utc(raw_data)
        print(f"  Standardized to {len(standardized_data)} daily data points")
        
        # Trim to requested days
        if days != 'max':
            try:
                days_int = int(days)
                cutoff_date = datetime.now() - timedelta(days=days_int)
                cutoff_ms = int(cutoff_date.timestamp() * 1000)
                standardized_data = [d for d in standardized_data if d[0] >= cutoff_ms]
                print(f"  Trimmed to {len(standardized_data)} data points (last {days} days)")
            except ValueError:
                print(f"  Invalid days parameter: {days}, returning all data")
        
        # Verify alignment to UTC
        if standardized_data:
            # Check alignment
            misaligned = 0
            for point in standardized_data:
                dt = datetime.fromtimestamp(point[0] / 1000)
                if dt.hour != 0 or dt.minute != 0 or dt.second != 0:
                    misaligned += 1
            
            if misaligned == 0:
                print(f"  ✅ All {len(standardized_data)} data points aligned to 00:00:00 UTC")
            else:
                print(f"  ⚠️  Warning: {misaligned} points not aligned to UTC")
        
        # Log final structure
        print(f"\nFinal output: {len(standardized_data)} data points")
        print(f"Structure: simple (2 components: [timestamp, value])")
        
        if standardized_data:
            # Show sample of recent data
            recent_sample = standardized_data[-5:]
            print("\nRecent DXY values:")
            for point in recent_sample:
                dt = datetime.fromtimestamp(point[0] / 1000)
                print(f"  {dt.date()}: {point[1]:.2f}")
        
        print("=" * 60)
        
        return {
            'metadata': metadata,
            'data': standardized_data,
            'structure': 'simple'
        }
        
    except Exception as e:
        print(f"❌ Error in get_data: {e}")
        import traceback
        traceback.print_exc()
        
        # Try cache as last resort
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

def verify_no_coinapi():
    """Verify this module has no CoinAPI references"""
    import inspect
    source = inspect.getsource(sys.modules[__name__])
    
    forbidden_terms = ['COINAPI', 'coinapi', 'CoinAPI']
    
    for term in forbidden_terms:
        if term in source:
            # Check if it's just in this verification function or comments
            lines = source.split('\n')
            for i, line in enumerate(lines):
                if term in line and 'verify_no_coinapi' not in line and 'NO COINAPI' not in line:
                    print(f"❌ WARNING: {term} reference found on line {i}")
                    return False
    
    print("✅ No CoinAPI references in dxy.py")
    return True

# Self-verification on module load
if __name__ != "__main__":
    verify_no_coinapi()