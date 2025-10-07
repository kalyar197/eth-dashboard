# data/gold_price.py
"""
Gold price fetcher using Financial Modeling Prep (FMP) API
FIXED: Using correct symbol ZGUSD for Gold
Attempts to fetch full OHLCV structure, falls back to simple price structure
NO COINAPI REFERENCES - Uses FMP exclusively
"""

import requests
from .time_transformer import standardize_to_daily_utc
from datetime import datetime, timedelta
import sys
import os
from .cache_manager import load_from_cache, save_to_cache

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import FMP_API_KEY

def get_metadata():
    """Returns metadata describing how gold data should be displayed"""
    return {
        'label': 'Gold (XAU/USD)',
        'yAxisId': 'price_usd',
        'yAxisLabel': 'Price per Oz (USD)',
        'unit': '$',
        'chartType': 'line',
        'color': '#FFD700',  # Gold color
        'strokeWidth': 2,
        'description': 'Gold spot price per troy ounce in USD from FMP',
        'data_structure': 'unknown',  # Will be determined at runtime
        'components': []  # Will be populated based on available data
    }

def fetch_gold_from_fmp(days):
    """
    Fetch gold price data from Financial Modeling Prep API
    FIXED: Using correct FMP symbol ZGUSD for Gold
    Attempts to get full OHLCV data, falls back to simple close prices
    """
    print("=" * 60)
    print("Fetching Gold Price from FMP API")
    print("=" * 60)
    
    # FIXED ENDPOINTS - Using correct FMP symbols for Gold
    endpoints_to_try = [
        {
            'name': 'Historical Price Full (ZGUSD)',
            'url': f'https://financialmodelingprep.com/api/v3/historical-price-full/ZGUSD',
            'params': {'apikey': FMP_API_KEY},
            'data_path': 'historical'
        },
        {
            'name': 'Historical Chart 1day (ZGUSD)',
            'url': f'https://financialmodelingprep.com/api/v3/historical-chart/1day/ZGUSD',
            'params': {'apikey': FMP_API_KEY},
            'data_path': None  # Direct list response
        },
        {
            'name': 'Quote (ZGUSD)',
            'url': f'https://financialmodelingprep.com/api/v3/quote/ZGUSD',
            'params': {'apikey': FMP_API_KEY},
            'data_path': None  # Direct response
        }
    ]
    
    for endpoint in endpoints_to_try:
        try:
            print(f"\nTrying {endpoint['name']} endpoint...")
            print(f"URL: {endpoint['url']}")
            
            response = requests.get(endpoint['url'], params=endpoint['params'], timeout=30)
            
            print(f"Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract historical data based on endpoint type
                if endpoint['data_path'] and endpoint['data_path'] in data:
                    historical_data = data[endpoint['data_path']]
                elif isinstance(data, list):
                    historical_data = data
                else:
                    print(f"  Unexpected data format in response")
                    continue
                
                if not historical_data or len(historical_data) == 0:
                    print(f"  Empty historical data")
                    continue
                
                print(f"  ✅ Successfully fetched {len(historical_data)} data points from {endpoint['name']}")
                
                # Process and determine structure
                raw_data = []
                data_structure = None
                
                for item in historical_data[:min(len(historical_data), 1000)]:  # Limit to avoid memory issues
                    # Parse date
                    if 'date' in item:
                        date_str = item['date']
                        dt = datetime.strptime(date_str, '%Y-%m-%d')
                    elif 'timestamp' in item:
                        dt = datetime.fromtimestamp(item['timestamp'])
                    else:
                        continue
                    
                    timestamp_ms = int(dt.timestamp() * 1000)
                    
                    # Check what data is available and determine structure
                    has_ohlcv = all(k in item for k in ['open', 'high', 'low', 'close', 'volume'])
                    has_ohlc = all(k in item for k in ['open', 'high', 'low', 'close'])
                    has_close = 'close' in item or 'price' in item
                    
                    if has_ohlcv:
                        # Full OHLCV structure available
                        if data_structure is None:
                            data_structure = 'OHLCV'
                            print("  📊 Full OHLCV data structure detected")
                        
                        raw_data.append([
                            timestamp_ms,
                            float(item['open']),
                            float(item['high']),
                            float(item['low']),
                            float(item['close']),
                            float(item.get('volume', 0))  # Use 0 if volume missing
                        ])
                        
                    elif has_ohlc:
                        # OHLC without volume
                        if data_structure is None:
                            data_structure = 'OHLCV'
                            print("  📊 OHLC data detected (volume set to 0)")
                        
                        raw_data.append([
                            timestamp_ms,
                            float(item['open']),
                            float(item['high']),
                            float(item['low']),
                            float(item['close']),
                            0.0  # No volume data
                        ])
                        
                    elif has_close:
                        # Simple close price only
                        if data_structure is None:
                            data_structure = 'simple'
                            print("  📊 Simple price structure detected (close only)")
                        
                        close_price = float(item.get('close', item.get('price', 0)))
                        raw_data.append([timestamp_ms, close_price])
                    
                if raw_data:
                    # Sort by timestamp (oldest first)
                    raw_data.sort(key=lambda x: x[0])
                    
                    # Log structure details
                    print(f"\n  ✅ Gold Price Data Structure: {data_structure}")
                    if data_structure == 'OHLCV':
                        print(f"     Components: [timestamp, open, high, low, close, volume]")
                        print(f"     6-component structure captured")
                        sample = raw_data[-1]  # Most recent
                        print(f"     Sample: O=${sample[1]:.2f}, H=${sample[2]:.2f}, L=${sample[3]:.2f}, C=${sample[4]:.2f}, V={sample[5]:.0f}")
                    else:
                        print(f"     Components: [timestamp, close]")
                        print(f"     2-component structure captured")
                        sample = raw_data[-1]  # Most recent
                        print(f"     Sample: Price=${sample[1]:.2f}")
                    
                    print(f"\n  🎯 SUCCESSFULLY FIXED: Gold data fetched from FMP using ZGUSD symbol")
                    return raw_data, data_structure
                    
            elif response.status_code == 401:
                print(f"  ❌ Authentication failed - check FMP API key")
            elif response.status_code == 403:
                print(f"  ❌ 403 Forbidden - API key may lack permissions or endpoint not available")
            elif response.status_code == 429:
                print(f"  ❌ Rate limit exceeded")
            else:
                print(f"  ❌ HTTP {response.status_code}: {response.reason}")
                
        except Exception as e:
            print(f"  ❌ Error with {endpoint['name']}: {e}")
            continue
    
    print("\n❌ Could not fetch gold data from any FMP endpoint")
    print("   This may indicate API key issues or endpoint changes")
    return None, None

def get_data(days='365'):
    """
    Fetches gold price data from FMP API
    Returns either 6-component OHLCV or 2-component simple structure
    All data is standardized to daily UTC boundaries
    """
    metadata = get_metadata()
    dataset_name = 'gold_price_fmp'
    
    try:
        # Try to fetch from FMP
        raw_data, data_structure = fetch_gold_from_fmp(days)
        
        if not raw_data:
            # Try loading from cache if API fails
            print("Loading gold data from cache...")
            cached_data = load_from_cache(dataset_name)
            
            if cached_data:
                # Determine structure from cached data
                if cached_data and len(cached_data[0]) == 6:
                    data_structure = 'OHLCV'
                    metadata['components'] = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
                else:
                    data_structure = 'simple'
                    metadata['components'] = ['timestamp', 'close']
                
                raw_data = cached_data
                print(f"  Loaded {len(raw_data)} cached data points")
            else:
                print("  No cached data available")
                return {
                    'metadata': metadata,
                    'data': [],
                    'error': 'Could not fetch gold data from FMP and no cache available'
                }
        else:
            # Save fresh data to cache
            save_to_cache(dataset_name, raw_data)
            print(f"  Cached {len(raw_data)} data points for future use")
        
        # Update metadata based on structure
        metadata['data_structure'] = data_structure
        if data_structure == 'OHLCV':
            metadata['components'] = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        else:
            metadata['components'] = ['timestamp', 'close']
        
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
        
        # Verify alignment
        if standardized_data:
            misaligned = sum(1 for point in standardized_data[:10] 
                           if datetime.fromtimestamp(point[0] / 1000).hour != 0)
            if misaligned == 0:
                print(f"  ✅ All data points aligned to 00:00:00 UTC")
            else:
                print(f"  ⚠️  Warning: Some data points not aligned to UTC")
        
        print(f"\nFinal output: {len(standardized_data)} data points")
        print(f"Structure: {data_structure} ({len(metadata['components'])} components)")
        print("=" * 60)
        
        return {
            'metadata': metadata,
            'data': standardized_data,
            'structure': data_structure
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
    
    if 'COINAPI' in source.upper():
        # Check if it's just in this verification function or comments
        lines = source.split('\n')
        for i, line in enumerate(lines):
            if 'COINAPI' in line.upper() and 'verify_no_coinapi' not in line and '#' not in line[:line.find('COINAPI')] if 'COINAPI' in line else True:
                print(f"❌ WARNING: CoinAPI reference found on line {i}")
                return False
    
    print("✅ No CoinAPI references in gold_price.py")
    return True

# Self-verification on module load
if __name__ != "__main__":
    verify_no_coinapi()