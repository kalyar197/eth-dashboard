# app.py

import sentry_sdk
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
import time
# Data plugins will be imported as they are added during the rebuild
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
# Empty during rebuild - plugins will be added as trading system is developed
DATA_PLUGINS = {}

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
        'message': 'BTC Trading System - Core Infrastructure (Rebuild Mode)',
        'endpoint': '/api/data?dataset=<name>&days=<number>',
        'available_datasets': list(DATA_PLUGINS.keys()),
        'cache_duration': f'{CACHE_DURATION} seconds',
        'cached_items': len(cache),
        'api_key_status': api_status,
        'config_endpoint': '/api/config',
        'clear_cache_endpoint': '/api/clear-cache',
        'rebuild_status': 'Core infrastructure only - plugins will be added incrementally'
    })

if __name__ == '__main__':
    from config import FMP_API_KEY, COINAPI_KEY

    print("="*60)
    print("BTC Trading System - Core Infrastructure")
    print("="*60)
    print(f"Server URL: http://127.0.0.1:5000")
    print(f"Status: REBUILD MODE - Core infrastructure only")
    print(f"Available datasets: {list(DATA_PLUGINS.keys()) if DATA_PLUGINS else 'None (rebuild in progress)'}")
    print(f"Cache duration: {CACHE_DURATION} seconds")
    print(f"Rate limit: {RATE_LIMIT_DELAY} seconds between API calls")

    print("\nAPI Key Status:")
    if FMP_API_KEY and FMP_API_KEY != 'YOUR_FMP_API_KEY':
        print(f"  FMP: [OK] Configured")
    else:
        print(f"  FMP: [X] Not configured")

    if COINAPI_KEY and COINAPI_KEY != 'YOUR_COINAPI_KEY_HERE':
        print(f"  CoinAPI: [OK] Configured")
    else:
        print(f"  CoinAPI: [X] Not configured")

    print("\n[REBUILD] Trading System Features:")
    print("  - Core infrastructure preserved")
    print("  - Frontend design and styling intact")
    print("  - Data plugins will be added one-by-one")
    print("  - Chart system ready for 12+ normalized indicators")

    print("="*60)
    print("Dependencies: pip install Flask requests Flask-Cors numpy")
    print("="*60)

    app.run(debug=True, port=5000)