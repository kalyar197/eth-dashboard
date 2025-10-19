# app.py

import sentry_sdk
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
import time
from data import eth_btc_ratio, btc_price, gold_price, rsi, bollinger_bands
from data import vwap, adx  # PHASE 4: Added VWAP, ADX
from data.indexer import index_to_baseline
from config import CACHE_DURATION, RATE_LIMIT_DELAY

# Initialize Sentry SDK for error monitoring
sentry_sdk.init(
    dsn="https://51a1e702949ccbd441d980a082211e9f@o4510197158510592.ingest.us.sentry.io/4510197228044288",
    # Add data like request headers and IP for users,
    # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
    send_default_pii=True,
)

app = Flask(__name__)
CORS(app)

# Cache configuration
cache = {}

# Rate limiting
last_api_call = {}

# A dictionary mapping dataset names to their data-fetching modules
DATA_PLUGINS = {
    'eth_btc': eth_btc_ratio,
    'btc': btc_price,
    'gold': gold_price,
    'rsi': rsi,
    'bollinger_bands': bollinger_bands,
    'vwap': vwap,    # Phase 4
    'adx': adx       # Phase 4
}

def get_cache_key(dataset_name, days):
    """Generate a cache key for the dataset and days combination"""
    return f"{dataset_name}_{days}"

def is_cache_valid(cache_key):
    """Check if cached data exists and is still valid"""
    if cache_key not in cache:
        return False
    
    cached_time = cache[cache_key]['timestamp']
    return (time.time() - cached_time) < CACHE_DURATION

def rate_limit_check(dataset_name):
    """Check if we can make an API call for this dataset"""
    current_time = time.time()
    if dataset_name in last_api_call:
        time_since_last = current_time - last_api_call[dataset_name]
        if time_since_last < RATE_LIMIT_DELAY:
            time.sleep(RATE_LIMIT_DELAY - time_since_last)
    
    last_api_call[dataset_name] = time.time()

@app.route('/api/datasets')
def get_datasets_metadata():
    """
    Returns metadata for all available datasets
    """
    metadata = {}
    for name, module in DATA_PLUGINS.items():
        if hasattr(module, 'get_metadata'):
            metadata[name] = module.get_metadata()
        else:
            # Fallback for modules without metadata
            metadata[name] = {'label': name.upper(), 'color': '#888888'}
    return jsonify(metadata)

@app.route('/api/data')
def get_data():
    """
    A single, flexible endpoint to fetch data for any dataset.
    Query parameters:
    - dataset: The name of the dataset to fetch (e.g., 'eth_btc', 'btc', 'gold', 'rsi', 'vwap', 'adx')
    - days: The number of days of data to retrieve (e.g., '365', 'max')
    """
    dataset_name = request.args.get('dataset')
    days = request.args.get('days', '365')

    if not dataset_name or dataset_name not in DATA_PLUGINS:
        return jsonify({'error': 'Invalid or missing dataset parameter'}), 400

    # Check cache first
    cache_key = get_cache_key(dataset_name, days)
    
    if is_cache_valid(cache_key):
        print(f"Serving {dataset_name} from cache")
        return jsonify(cache[cache_key]['data'])

    try:
        # Apply rate limiting before making API call
        rate_limit_check(dataset_name)
        
        # Dynamically call the get_data function from the appropriate module
        data_module = DATA_PLUGINS[dataset_name]
        data = data_module.get_data(days)
        
        # Store in cache
        cache[cache_key] = {
            'data': data,
            'timestamp': time.time()
        }
        
        print(f"Fetched fresh data for {dataset_name}")
        return jsonify(data)
        
    except Exception as e:
        # If we have cached data (even if expired), return it on error
        if cache_key in cache:
            print(f"Error fetching {dataset_name}, returning stale cache: {str(e)}")
            return jsonify(cache[cache_key]['data'])
        
        return jsonify({'error': f'Server error processing {dataset_name}: {str(e)}'}), 500

@app.route('/api/indexed-data')
def get_indexed_data():
    """
    Returns indexed data for a dataset, normalized to baseline 100 at start.
    Query parameters:
    - dataset: The name of the dataset to fetch (e.g., 'eth_btc', 'btc', 'gold', 'rsi', 'vwap', 'adx')
    - days: The number of days of data to retrieve (e.g., '365', 'max')
    - baseline: The baseline value (default: 100)
    """
    dataset_name = request.args.get('dataset')
    days = request.args.get('days', '365')
    baseline = int(request.args.get('baseline', '100'))

    if not dataset_name or dataset_name not in DATA_PLUGINS:
        return jsonify({'error': 'Invalid or missing dataset parameter'}), 400

    # Check cache first
    cache_key = f"indexed_{dataset_name}_{days}_{baseline}"

    if is_cache_valid(cache_key):
        print(f"Serving indexed {dataset_name} from cache")
        return jsonify(cache[cache_key]['data'])

    try:
        # Apply rate limiting before making API call
        rate_limit_check(dataset_name)

        # Get raw data from the plugin
        data_module = DATA_PLUGINS[dataset_name]
        raw_data_response = data_module.get_data(days)

        # Extract data and metadata
        raw_data = raw_data_response.get('data', [])
        metadata = raw_data_response.get('metadata', {})

        # Apply indexing transformation
        indexed_data = index_to_baseline(raw_data, baseline=baseline)

        # Modify metadata for indexed version
        indexed_metadata = metadata.copy()
        indexed_metadata['yAxisId'] = 'indexed'
        indexed_metadata['yAxisLabel'] = f'Indexed (Base {baseline})'
        indexed_metadata['unit'] = ''  # Remove $ or % units
        indexed_metadata['label'] = metadata.get('label', dataset_name) + ' (Indexed)'

        # Remove fixed domains (like RSI's 0-100) for indexed data
        if 'yDomain' in indexed_metadata:
            del indexed_metadata['yDomain']

        # Remove reference lines (they don't make sense in indexed context)
        if 'referenceLines' in indexed_metadata:
            del indexed_metadata['referenceLines']

        result = {
            'metadata': indexed_metadata,
            'data': indexed_data
        }

        # Store in cache
        cache[cache_key] = {
            'data': result,
            'timestamp': time.time()
        }

        print(f"Fetched and indexed data for {dataset_name}")
        return jsonify(result)

    except Exception as e:
        # If we have cached data (even if expired), return it on error
        if cache_key in cache:
            print(f"Error fetching indexed {dataset_name}, returning stale cache: {str(e)}")
            return jsonify(cache[cache_key]['data'])

        return jsonify({'error': f'Server error processing indexed {dataset_name}: {str(e)}'}), 500

@app.route('/api/clear-cache')
def clear_cache():
    """Clear the cache manually if needed"""
    global cache
    cache = {}
    return jsonify({'message': 'Cache cleared successfully'})

@app.route('/api/config')
def get_config():
    """Show current configuration (without revealing API keys)"""
    from config import API_PROVIDER, DEFAULT_DAYS, RSI_PERIOD, FMP_API_KEY, COINAPI_KEY

    return jsonify({
        'api_provider': API_PROVIDER,
        'cache_duration': f'{CACHE_DURATION} seconds',
        'rate_limit_delay': f'{RATE_LIMIT_DELAY} seconds',
        'default_days': DEFAULT_DAYS,
        'rsi_period': RSI_PERIOD,
        'api_keys_configured': {
            'fmp': bool(FMP_API_KEY and FMP_API_KEY != 'YOUR_FMP_API_KEY'),
            'coinapi': bool(COINAPI_KEY and COINAPI_KEY != 'YOUR_COINAPI_KEY_HERE')
        }
    })

@app.route('/')
def home():
    """
    Serve the main HTML page
    """
    return send_from_directory('.', 'index.html')

@app.route('/js/<path:filename>')
def serve_js(filename):
    """
    Serve JavaScript files from the static/js directory
    """
    return send_from_directory('static/js', filename)

@app.route('/favicon.ico')
def favicon():
    """Return a simple 204 No Content response for favicon requests"""
    return '', 204

@app.route('/api/status')
def api_status():
    """
    API status endpoint to verify server is running
    """
    from config import FMP_API_KEY, COINAPI_KEY

    # Check API key status
    api_status = {
        'FMP': "[OK]" if (FMP_API_KEY and FMP_API_KEY != 'YOUR_FMP_API_KEY') else "[NOT CONFIGURED]",
        'CoinAPI': "[OK]" if (COINAPI_KEY and COINAPI_KEY != 'YOUR_COINAPI_KEY_HERE') else "[NOT CONFIGURED]"
    }

    return jsonify({
        'status': 'running',
        'message': 'Advanced Financial Charting API Server',
        'endpoint': '/api/data?dataset=<name>&days=<number>',
        'available_datasets': list(DATA_PLUGINS.keys()),
        'cache_duration': f'{CACHE_DURATION} seconds',
        'cached_items': len(cache),
        'api_key_status': api_status,
        'config_endpoint': '/api/config',
        'clear_cache_endpoint': '/api/clear-cache',
        'phase4_indicators': ['vwap', 'adx']
    })

if __name__ == '__main__':
    from config import FMP_API_KEY, COINAPI_KEY

    print("="*60)
    print("Starting Advanced Financial Charting Server")
    print("="*60)
    print(f"Server URL: http://127.0.0.1:5000")
    print(f"Available datasets: {list(DATA_PLUGINS.keys())}")
    print(f"Cache duration: {CACHE_DURATION} seconds")
    print(f"Rate limit: {RATE_LIMIT_DELAY} seconds between API calls")

    print("\nAPI Key Status:")
    if FMP_API_KEY and FMP_API_KEY != 'YOUR_FMP_API_KEY':
        print(f"  FMP: [OK] Configured (for Gold)")
    else:
        print(f"  FMP: [X] Not configured")

    if COINAPI_KEY and COINAPI_KEY != 'YOUR_COINAPI_KEY_HERE':
        print(f"  CoinAPI: [OK] Configured (for Crypto)")
    else:
        print(f"  CoinAPI: [X] Not configured")

    print("\n[NEW] PHASE 4 INDICATORS:")
    print("  - VWAP (Volume Weighted Average Price)")
    print("  - ADX (Average Directional Index)")

    print("="*60)
    print("[OK] CRITICAL FIXES APPLIED:")
    print("  - Gold Price: Fixed FMP endpoint (using ZGUSD symbol)")
    print("  - Sentry SDK: Integrated for error monitoring")
    print("="*60)
    print("Make sure to install: pip install Flask requests Flask-Cors numpy")
    print("="*60)

    app.run(debug=True, port=5000)