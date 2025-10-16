# data/gold_price.py
"""
Gold price fetcher using Financial Modeling Prep (FMP) API
FIXED: Using correct FMP endpoint structure
Endpoint: /stable/historical-price-eod/full
Symbol: GCUSD (Gold Continuous Contract)
NO COINAPI REFERENCES
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
        'data_structure': 'unknown',
        'components': []
    }

def fetch_gold_from_fmp_stable_endpoint(days):
    """
    Fetch gold price from FMP using the CORRECT stable endpoint
    URL: https://financialmodelingprep.com/stable/historical-price-eod/full
    Symbol: GCUSD
    """
    print("=" * 60)
    print("Fetching Gold Price from FMP Stable Endpoint")
    print("FIXED: Using correct endpoint structure")
    print("=" * 60)
    
    try:
        # CORRECT FMP endpoint structure as specified
        base_url = 'https://financialmodelingprep.com/stable/historical-price-eod/full'
        
        params = {
            'symbol': 'GCUSD',  # Gold Continuous Contract
            'apikey': FMP_API_KEY
        }
        
        print(f"\nEndpoint: {base_url}")
        print(f"Symbol: GCUSD (Gold Continuous Contract)")
        print(f"Making request...")
        
        response = requests.get(base_url, params=params, timeout=30)
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check response structure
            if isinstance(data, dict):
                # Try different possible keys
                if 'historical' in data:
                    historical_data = data['historical']
                elif 'data' in data:
                    historical_data = data['data']
                else:
                    # Response might be the data directly
                    historical_data = [data] if 'date' in data else []
            elif isinstance(data, list):
                historical_data = data
            else:
                print(f"  [X] Unexpected response structure")
                print(f"  Response type: {type(data)}")
                return None, None
            
            if not historical_data or len(historical_data) == 0:
                print(f"  [X] Empty historical data")
                return None, None
            
            print(f"  [OK] Successfully fetched {len(historical_data)} data points")
            
            # Process data
            raw_data = []
            data_structure = None
            
            for item in historical_data[:min(len(historical_data), 2000)]:
                # Parse date
                if 'date' in item:
                    date_str = item['date']
                    try:
                        dt = datetime.strptime(date_str, '%Y-%m-%d')
                    except ValueError:
                        # Try alternative format
                        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                else:
                    continue
                
                timestamp_ms = int(dt.timestamp() * 1000)
                
                # Check data structure
                has_ohlcv = all(k in item for k in ['open', 'high', 'low', 'close', 'volume'])
                has_ohlc = all(k in item for k in ['open', 'high', 'low', 'close'])
                has_close = 'close' in item or 'price' in item
                
                if has_ohlcv:
                    if data_structure is None:
                        data_structure = 'OHLCV'
                        print("  [DATA] Full OHLCV data structure detected")
                    
                    raw_data.append([
                        timestamp_ms,
                        float(item['open']),
                        float(item['high']),
                        float(item['low']),
                        float(item['close']),
                        float(item.get('volume', 0))
                    ])
                    
                elif has_ohlc:
                    if data_structure is None:
                        data_structure = 'OHLCV'
                        print("  [DATA] OHLC data detected (volume set to 0)")
                    
                    raw_data.append([
                        timestamp_ms,
                        float(item['open']),
                        float(item['high']),
                        float(item['low']),
                        float(item['close']),
                        0.0
                    ])
                    
                elif has_close:
                    if data_structure is None:
                        data_structure = 'simple'
                        print("  [DATA] Simple price structure detected (close only)")
                    
                    close_price = float(item.get('close', item.get('price', 0)))
                    raw_data.append([timestamp_ms, close_price])
            
            if raw_data:
                # Sort by timestamp
                raw_data.sort(key=lambda x: x[0])
                
                # Log structure details
                print(f"\n  [OK] Gold Price Data Structure: {data_structure}")
                if data_structure == 'OHLCV':
                    print(f"     Components: [timestamp, open, high, low, close, volume]")
                    sample = raw_data[-1]
                    print(f"     Sample: O=${sample[1]:.2f}, H=${sample[2]:.2f}, L=${sample[3]:.2f}, C=${sample[4]:.2f}")
                else:
                    print(f"     Components: [timestamp, close]")
                    sample = raw_data[-1]
                    print(f"     Sample: Price=${sample[1]:.2f}")
                
                # Validate price range
                recent_prices = [d[4 if data_structure == 'OHLCV' else 1] for d in raw_data[-30:]]
                avg_price = sum(recent_prices) / len(recent_prices)
                
                if 1500 <= avg_price <= 3000:
                    print(f"\n  [OK] VALIDATION PASSED: Average price = ${avg_price:.2f}")
                    print(f"  [OK] This is in the expected gold price range")
                else:
                    print(f"\n  [WARNING]  WARNING: Average price = ${avg_price:.2f}")
                    print(f"  [WARNING]  Expected range: $1500-$3000")
                
                print(f"\n  [SUCCESS] SUCCESSFULLY FIXED: Gold data fetched from FMP stable endpoint")
                return raw_data, data_structure
                
        elif response.status_code == 401:
            print(f"  [X] Authentication failed - check FMP API key")
        elif response.status_code == 403:
            print(f"  [X] 403 Forbidden")
            print(f"  This may indicate:")
            print(f"    - Invalid API key")
            print(f"    - API key lacks permissions for this endpoint")
            print(f"    - Subscription tier doesn't include stable endpoints")
        elif response.status_code == 429:
            print(f"  [X] Rate limit exceeded")
        else:
            print(f"  [X] HTTP {response.status_code}: {response.reason}")
            
    except Exception as e:
        print(f"  [X] Error: {e}")
        import traceback
        traceback.print_exc()
    
    return None, None

def fetch_gold_from_fmp_fallback(days):
    """
    Fallback: Try alternative FMP endpoints
    """
    print("\n" + "=" * 60)
    print("Trying Fallback FMP Endpoints")
    print("=" * 60)
    
    endpoints_to_try = [
        {
            'name': 'V3 Historical Price Full',
            'url': 'https://financialmodelingprep.com/api/v3/historical-price-full/GCUSD',
            'params': {'apikey': FMP_API_KEY},
            'data_path': 'historical'
        },
        {
            'name': 'V3 Historical Chart',
            'url': 'https://financialmodelingprep.com/api/v3/historical-chart/1day/GCUSD',
            'params': {'apikey': FMP_API_KEY},
            'data_path': None
        }
    ]
    
    for endpoint in endpoints_to_try:
        try:
            print(f"\nTrying {endpoint['name']}...")
            print(f"URL: {endpoint['url']}")
            
            response = requests.get(endpoint['url'], params=endpoint['params'], timeout=30)
            print(f"Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract data
                if endpoint['data_path'] and endpoint['data_path'] in data:
                    historical_data = data[endpoint['data_path']]
                elif isinstance(data, list):
                    historical_data = data
                else:
                    print(f"  Unexpected format")
                    continue
                
                if historical_data and len(historical_data) > 0:
                    print(f"  [OK] Got {len(historical_data)} data points")
                    
                    # Process similar to stable endpoint
                    raw_data = []
                    for item in historical_data[:2000]:
                        if 'date' not in item:
                            continue
                        
                        date_str = item['date']
                        dt = datetime.strptime(date_str, '%Y-%m-%d')
                        timestamp_ms = int(dt.timestamp() * 1000)
                        
                        if all(k in item for k in ['open', 'high', 'low', 'close']):
                            raw_data.append([
                                timestamp_ms,
                                float(item['open']),
                                float(item['high']),
                                float(item['low']),
                                float(item['close']),
                                float(item.get('volume', 0))
                            ])
                        elif 'close' in item or 'price' in item:
                            close_price = float(item.get('close', item.get('price', 0)))
                            raw_data.append([timestamp_ms, close_price])
                    
                    if raw_data:
                        raw_data.sort(key=lambda x: x[0])
                        data_structure = 'OHLCV' if len(raw_data[0]) == 6 else 'simple'
                        return raw_data, data_structure
                        
        except Exception as e:
            print(f"  [X] Error: {e}")
            continue
    
    return None, None

def get_data(days='365'):
    """
    Fetches gold price data from FMP API
    FIXED: Using correct stable endpoint structure
    """
    metadata = get_metadata()
    dataset_name = 'gold_price_fmp_fixed'
    
    try:
        # Try stable endpoint first (correct endpoint)
        raw_data, data_structure = fetch_gold_from_fmp_stable_endpoint(days)
        
        # Try fallback endpoints if stable fails
        if not raw_data:
            print("\nStable endpoint failed, trying fallback endpoints...")
            raw_data, data_structure = fetch_gold_from_fmp_fallback(days)
        
        # Try cache if all APIs fail
        if not raw_data:
            print("\nAll FMP endpoints failed. Loading from cache...")
            cached_data = load_from_cache(dataset_name)
            
            if cached_data:
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
            print(f"\n  Cached {len(raw_data)} data points")
        
        # Update metadata
        metadata['data_structure'] = data_structure
        if data_structure == 'OHLCV':
            metadata['components'] = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        else:
            metadata['components'] = ['timestamp', 'close']
        
        # Standardize data
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
        
        # Final verification
        if standardized_data:
            recent_sample = standardized_data[-5:]
            print("\nRecent gold prices:")
            for point in recent_sample:
                dt = datetime.fromtimestamp(point[0] / 1000)
                price = point[4] if data_structure == 'OHLCV' else point[1]
                print(f"  {dt.date()}: ${price:.2f}")
        
        print("\n" + "=" * 60)
        print("[OK] GOLD PRICE FIX COMPLETE")
        print(f"[OK] Using FMP endpoint with correct structure")
        print(f"[OK] Data structure: {data_structure}")
        print(f"[OK] Total points: {len(standardized_data)}")
        print("=" * 60)
        
        return {
            'metadata': metadata,
            'data': standardized_data,
            'structure': data_structure
        }
        
    except Exception as e:
        print(f"[X] Error: {e}")
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

# Module verified: Uses only FMP API for gold price data