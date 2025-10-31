# app.py

import sentry_sdk
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
import time
# Data plugins
from data import eth_price, btc_price, gold_price, rsi, macd_histogram, volume, dxy, adx, atr, sma, parabolic_sar
from data import markov_regime
from data.normalizers import zscore
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
# Note: OVERLAY_PLUGINS will be merged into this dictionary below
DATA_PLUGINS = {
    'eth': eth_price,
    'btc': btc_price,
    'gold': gold_price
}

# Oscillator plugins (require asset parameter)
OSCILLATOR_PLUGINS = {
    'rsi': rsi,
    'macd_histogram': macd_histogram,
    'volume': volume,
    'dxy': dxy,
    'adx': adx,
    'atr': atr
}

# Overlay plugins (Moving Averages & Parabolic SAR - callable via /api/data)
# These overlay on price charts rather than displaying in separate oscillator chart
OVERLAY_PLUGINS = {
    'sma_7_btc': lambda days: sma.get_data(days, 'btc', 7),
    'sma_21_btc': lambda days: sma.get_data(days, 'btc', 21),
    'sma_60_btc': lambda days: sma.get_data(days, 'btc', 60),
    'sma_7_eth': lambda days: sma.get_data(days, 'eth', 7),
    'sma_21_eth': lambda days: sma.get_data(days, 'eth', 21),
    'sma_60_eth': lambda days: sma.get_data(days, 'eth', 60),
    'sma_7_gold': lambda days: sma.get_data(days, 'gold', 7),
    'sma_21_gold': lambda days: sma.get_data(days, 'gold', 21),
    'sma_60_gold': lambda days: sma.get_data(days, 'gold', 60),
    'psar_btc': lambda days: parabolic_sar.get_data(days, 'btc'),
    'psar_eth': lambda days: parabolic_sar.get_data(days, 'eth'),
    'psar_gold': lambda days: parabolic_sar.get_data(days, 'gold'),
}

# Merge overlay plugins into DATA_PLUGINS so they're accessible via /api/data
DATA_PLUGINS.update(OVERLAY_PLUGINS)

# Normalizer function (using only zscore - Regression Divergence)
NORMALIZERS = {
    'zscore': zscore
}

def align_timestamps(normalized_oscillators):
    """
    Align multiple normalized oscillator datasets to common timestamps.

    Args:
        normalized_oscillators: Dict of {oscillator_name: [[timestamp, value], ...]}

    Returns:
        Tuple of (common_timestamps, aligned_values)
        where aligned_values is Dict of {oscillator_name: [values aligned to common timestamps]}
    """
    if not normalized_oscillators:
        return [], {}

    # Find common timestamps (intersection)
    timestamp_sets = [set(item[0] for item in data) for data in normalized_oscillators.values()]
    common_timestamps = sorted(set.intersection(*timestamp_sets))

    if not common_timestamps:
        print("[Composite] No common timestamps found across oscillators")
        return [], {}

    # Create lookup dictionaries for each oscillator
    aligned = {}
    for name, data in normalized_oscillators.items():
        lookup = {item[0]: item[1] for item in data}
        aligned[name] = [lookup[ts] for ts in common_timestamps]

    print(f"[Composite] Aligned {len(normalized_oscillators)} oscillators to {len(common_timestamps)} common timestamps")

    return common_timestamps, aligned

def calculate_composite_average(common_timestamps, aligned_values, weights=None):
    """
    Calculate equally-weighted (or custom-weighted) average of aligned oscillator values.

    Args:
        common_timestamps: List of timestamps
        aligned_values: Dict of {oscillator_name: [values]}
        weights: Dict of {oscillator_name: weight} or None for equal weights

    Returns:
        List of [timestamp, composite_value] pairs
    """
    if not common_timestamps or not aligned_values:
        return []

    # Determine weights
    oscillator_names = list(aligned_values.keys())
    if weights is None:
        # Equal weights
        n = len(oscillator_names)
        weights = {name: 1.0 / n for name in oscillator_names}
        print(f"[Composite] Using equal weights: {weights}")
    else:
        # Normalize weights to sum to 1
        total = sum(weights.values())
        weights = {name: w / total for name, w in weights.items()}
        print(f"[Composite] Using custom weights: {weights}")

    # Calculate weighted average for each timestamp
    composite_data = []
    for i, timestamp in enumerate(common_timestamps):
        weighted_sum = 0.0
        for name, values in aligned_values.items():
            weight = weights.get(name, 0.0)
            value = values[i]
            weighted_sum += weight * value

        composite_data.append([timestamp, weighted_sum])

    print(f"[Composite] Generated {len(composite_data)} composite points")

    return composite_data

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

        # Dynamically call the get_data function from the appropriate module or callable
        data_plugin = DATA_PLUGINS[dataset_name]

        # Check if it's a callable (lambda) or a module with get_data method
        if callable(data_plugin) and not hasattr(data_plugin, 'get_data'):
            # It's a lambda function - call it directly
            data = data_plugin(days)
        else:
            # It's a module - call its get_data method
            data = data_plugin.get_data(days)
        
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

@app.route('/api/oscillator-data')
def get_oscillator_data():
    """
    Fetch oscillator data with optional composite mode and regime detection.

    Query parameters:
    - asset: 'btc' | 'eth' | 'gold'
    - datasets: comma-separated list (e.g., 'rsi,macd,volume,dxy')
    - days: '7' | '30' | '180' | '1095'
    - normalizer: 'zscore' (Regression Divergence - only normalizer available)
    - mode: 'individual' | 'composite' (default: 'individual')
    - noise_level: 14 | 30 | 50 | 100 | 200 (window size for composite Z-score, default: 50)

    When mode='composite':
    - Returns composite Z-score oscillator (weighted avg of all specified oscillators)
    - Returns Markov regime data for background shading
    - noise_level controls oscillator sensitivity
    """
    asset = request.args.get('asset')
    datasets_param = request.args.get('datasets', '')
    days = request.args.get('days', '30')
    normalizer_name = request.args.get('normalizer', 'zscore')
    mode = request.args.get('mode', 'individual')
    noise_level = int(request.args.get('noise_level', '50'))

    if not asset or asset not in DATA_PLUGINS:
        return jsonify({'error': 'Invalid or missing asset parameter'}), 400

    if not datasets_param:
        return jsonify({'error': 'Missing datasets parameter'}), 400

    # Parse dataset names
    dataset_names = [d.strip() for d in datasets_param.split(',') if d.strip()]

    if not dataset_names:
        return jsonify({'error': 'No valid datasets specified'}), 400

    # Validate normalizer (only used in individual mode)
    if mode == 'individual' and normalizer_name not in NORMALIZERS:
        return jsonify({'error': f'Invalid normalizer: {normalizer_name}'}), 400

    # Validate noise level
    valid_noise_levels = [14, 30, 50, 100, 200]
    if noise_level not in valid_noise_levels:
        return jsonify({'error': f'Invalid noise_level. Must be one of: {valid_noise_levels}'}), 400

    # Generate cache key (include mode and noise_level)
    cache_key = f"oscillator_{mode}_{asset}_{datasets_param}_{days}_{normalizer_name}_{noise_level}"

    # Check cache
    if is_cache_valid(cache_key):
        print(f"Serving oscillator data from cache: {cache_key}")
        return jsonify(cache[cache_key]['data'])

    try:
        # Handle composite mode
        if mode == 'composite':
            print(f"[Composite Mode] Generating composite oscillator for {asset} with window={noise_level}")
            print(f"[Composite Mode] Oscillators: {dataset_names}")

            # Apply rate limiting
            rate_limit_check(f"composite_{asset}")

            # Step 1: Fetch asset price data (OHLCV) for normalization
            # Request extra days to ensure enough history for rolling window
            if days == 'max':
                price_days = 'max'
            else:
                price_days = str(int(days) + noise_level + 10)

            asset_module = DATA_PLUGINS[asset]
            asset_result = asset_module.get_data(price_days)
            asset_ohlcv_data = asset_result['data']

            if not asset_ohlcv_data:
                raise ValueError(f"No {asset.upper()} price data available")

            print(f"[Composite Mode] Fetched {len(asset_ohlcv_data)} price points for {asset.upper()}")

            # Step 2: Normalize each oscillator using regression-based normalizer
            normalized_oscillators = {}
            oscillator_metadata = {}  # Store metadata for breakdown chart

            for oscillator_name in dataset_names:
                if oscillator_name not in OSCILLATOR_PLUGINS:
                    print(f"[Composite Mode] Warning: Unknown oscillator '{oscillator_name}', skipping...")
                    continue

                try:
                    # Apply rate limiting
                    rate_limit_check(f"{oscillator_name}_{asset}")

                    # Fetch raw oscillator data
                    oscillator_module = OSCILLATOR_PLUGINS[oscillator_name]

                    # Request extra days to ensure enough history for rolling window
                    # Add noise_level + 10 extra days as buffer
                    if days == 'max':
                        extra_days = 'max'
                    else:
                        extra_days = str(int(days) + noise_level + 10)

                    # DXY doesn't need asset parameter
                    if oscillator_name == 'dxy':
                        oscillator_result = oscillator_module.get_data(extra_days)
                    else:
                        oscillator_result = oscillator_module.get_data(extra_days, asset)

                    raw_oscillator_data = oscillator_result['data']

                    if not raw_oscillator_data:
                        print(f"[Composite Mode] Warning: No data for {oscillator_name}, skipping...")
                        continue

                    print(f"[Composite Mode] Fetched {len(raw_oscillator_data)} points for {oscillator_name}")

                    # Normalize using Rolling OLS Regression Divergence
                    normalized_data = zscore.normalize(
                        dataset_data=raw_oscillator_data,
                        asset_price_data=asset_ohlcv_data,
                        window=noise_level
                    )

                    if not normalized_data:
                        print(f"[Composite Mode] Warning: Normalization failed for {oscillator_name}, skipping...")
                        continue

                    # Store normalized data
                    normalized_oscillators[oscillator_name] = normalized_data

                    # Capture metadata for breakdown chart
                    metadata = oscillator_result['metadata'].copy()
                    metadata['normalizer'] = 'Rolling OLS Regression Divergence'
                    metadata['window'] = noise_level
                    oscillator_metadata[oscillator_name] = metadata

                    print(f"[Composite Mode] Normalized {oscillator_name}: {len(normalized_data)} points")

                except Exception as e:
                    print(f"[Composite Mode] Error processing {oscillator_name}: {e}")
                    import traceback
                    traceback.print_exc()
                    # Continue with other oscillators

            if not normalized_oscillators:
                raise ValueError("No oscillators could be normalized successfully")

            # Step 3: Align all normalized oscillators to common timestamps
            common_timestamps, aligned_values = align_timestamps(normalized_oscillators)

            if not common_timestamps:
                raise ValueError("No common timestamps found across normalized oscillators")

            # Step 4: Calculate equally-weighted composite average
            composite_data = calculate_composite_average(
                common_timestamps=common_timestamps,
                aligned_values=aligned_values,
                weights=None  # Equal weights
            )

            # Step 4.5: Trim composite data to requested number of days
            if composite_data and days != 'max':
                cutoff_timestamp = composite_data[-1][0] - (int(days) * 24 * 60 * 60 * 1000)
                composite_data = [d for d in composite_data if d[0] >= cutoff_timestamp]
                print(f"[Composite Mode] Trimmed to {len(composite_data)} points for {days} days")

            # Step 5: Get Markov regime data
            regime_result = markov_regime.get_data(days=days, asset=asset)

            # Step 5.5: Build breakdown data (individual normalized oscillators)
            breakdown_data = {}

            for oscillator_name, normalized_data in normalized_oscillators.items():
                # Trim each oscillator's data to requested number of days
                trimmed_data = normalized_data
                if normalized_data and days != 'max':
                    cutoff_timestamp = normalized_data[-1][0] - (int(days) * 24 * 60 * 60 * 1000)
                    trimmed_data = [d for d in normalized_data if d[0] >= cutoff_timestamp]

                breakdown_data[oscillator_name] = {
                    'data': trimmed_data,
                    'metadata': oscillator_metadata[oscillator_name]
                }

            print(f"[Composite Mode] Generated breakdown data for {len(breakdown_data)} oscillators")

            # Step 6: Build result
            result = {
                'mode': 'composite',
                'asset': asset,
                'noise_level': noise_level,
                'composite': {
                    'data': composite_data,
                    'metadata': {
                        'label': 'Composite Regression Divergence',
                        'yAxisId': 'zscore',
                        'yAxisLabel': 'Standard Deviations',
                        'unit': 'σ',
                        'color': '#00D9FF',
                        'chartType': 'line',
                        'window': noise_level,
                        'components': list(normalized_oscillators.keys()),
                        'weights': {name: 1.0/len(normalized_oscillators) for name in normalized_oscillators.keys()},
                        'normalizer': 'Rolling OLS Regression Divergence'
                    }
                },
                'regime': {
                    'data': regime_result['data'],
                    'metadata': regime_result['metadata']
                },
                'breakdown': breakdown_data
            }

            print(f"[Composite Mode] Generated {len(composite_data)} composite points")
            print(f"[Composite Mode] Generated {len(regime_result['data'])} regime points")

            # Store in cache
            cache[cache_key] = {
                'data': result,
                'timestamp': time.time()
            }

            return jsonify(result)

        # Handle individual mode (existing logic)
        else:
            # Fetch asset price data (needed for normalization)
            asset_module = DATA_PLUGINS[asset]
            asset_result = asset_module.get_data(days)
            asset_ohlcv_data = asset_result['data']

            if not asset_ohlcv_data:
                raise ValueError(f"No {asset.upper()} price data available")

            # Fetch oscillator datasets
            result = {
                'mode': 'individual',
                'asset': asset,
                'normalizer': normalizer_name,
                'datasets': {}
            }

            normalizer_module = NORMALIZERS[normalizer_name]

            for dataset_name in dataset_names:
                if dataset_name not in OSCILLATOR_PLUGINS:
                    print(f"Warning: Unknown oscillator dataset '{dataset_name}', skipping...")
                    continue

                try:
                    # Apply rate limiting
                    rate_limit_check(f"{dataset_name}_{asset}")

                    # Fetch raw oscillator data
                    oscillator_module = OSCILLATOR_PLUGINS[dataset_name]

                    # DXY doesn't need asset parameter
                    if dataset_name == 'dxy':
                        oscillator_result = oscillator_module.get_data(days)
                    else:
                        oscillator_result = oscillator_module.get_data(days, asset)

                    raw_data = oscillator_result['data']

                    if not raw_data:
                        print(f"Warning: No data for {dataset_name}, skipping...")
                        continue

                    # Apply normalization
                    normalized_data = normalizer_module.normalize(raw_data, asset_ohlcv_data)

                    # Get metadata
                    metadata = oscillator_result['metadata']

                    result['datasets'][dataset_name] = {
                        'data': normalized_data,
                        'metadata': metadata
                    }

                    print(f"Fetched and normalized {dataset_name} for {asset}: {len(normalized_data)} points")

                except Exception as e:
                    print(f"Error fetching oscillator {dataset_name}: {e}")
                    # Continue with other datasets

            # Store in cache
            cache[cache_key] = {
                'data': result,
                'timestamp': time.time()
            }

            return jsonify(result)

    except Exception as e:
        print(f"Error processing oscillator data: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Server error processing oscillator data: {str(e)}'}), 500

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