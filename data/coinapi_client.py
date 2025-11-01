# data/coinapi_client.py
"""
CoinAPI Client Helper Module

Provides unified interface for fetching cryptocurrency options and derivatives data
from CoinAPI.io (Startup tier: $79/month, 1000 requests/day).

Supports:
- Implied volatility across multiple exchanges (Deribit, Binance, OKX)
- Options Greeks (Delta, Gamma, Vega, Theta)
- Open interest for put/call ratio calculation
- Historical data batching with rate limit management
"""

import requests
import time
from datetime import datetime, timedelta, timezone
import json

# Rate limiting state
_REQUEST_COUNT = 0
_REQUEST_RESET_TIME = None
_LAST_REQUEST_TIME = None
_MIN_REQUEST_INTERVAL = 0.1  # 100ms between requests


def get_api_key():
    """Get CoinAPI key from config"""
    try:
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from config import COINAPI_KEY
        return COINAPI_KEY
    except ImportError:
        print("[CoinAPI] Warning: COINAPI_KEY not found in config.py")
        return None


def rate_limit_check():
    """
    Enforce rate limiting: 1000 requests/day with 100ms minimum interval.
    """
    global _REQUEST_COUNT, _REQUEST_RESET_TIME, _LAST_REQUEST_TIME

    current_time = time.time()

    # Reset counter at midnight UTC
    if _REQUEST_RESET_TIME is None or current_time >= _REQUEST_RESET_TIME:
        _REQUEST_COUNT = 0
        # Set next reset to midnight UTC
        now_utc = datetime.now(tz=timezone.utc)
        next_midnight = (now_utc + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        _REQUEST_RESET_TIME = next_midnight.timestamp()
        print(f"[CoinAPI] Rate limit counter reset. Next reset at {next_midnight}")

    # Check daily limit
    if _REQUEST_COUNT >= 1000:
        wait_time = _REQUEST_RESET_TIME - current_time
        print(f"[CoinAPI] Daily rate limit reached (1000 requests). Reset in {wait_time/3600:.1f} hours")
        raise Exception(f"CoinAPI daily rate limit exceeded. Resets in {wait_time/3600:.1f} hours")

    # Enforce minimum interval between requests
    if _LAST_REQUEST_TIME is not None:
        elapsed = current_time - _LAST_REQUEST_TIME
        if elapsed < _MIN_REQUEST_INTERVAL:
            time.sleep(_MIN_REQUEST_INTERVAL - elapsed)

    _REQUEST_COUNT += 1
    _LAST_REQUEST_TIME = time.time()

    print(f"[CoinAPI] Request {_REQUEST_COUNT}/1000 today")


def make_request(endpoint, params=None):
    """
    Make authenticated request to CoinAPI with rate limiting.

    Args:
        endpoint (str): API endpoint path (e.g., '/v1/metrics/exchange')
        params (dict): Query parameters

    Returns:
        dict: JSON response data
    """
    api_key = get_api_key()
    if not api_key:
        raise Exception("CoinAPI key not configured")

    # Rate limit check
    rate_limit_check()

    base_url = 'https://rest.coinapi.io'
    url = f"{base_url}{endpoint}"

    headers = {
        'X-CoinAPI-Key': api_key,
        'Accept': 'application/json'
    }

    try:
        print(f"[CoinAPI] GET {endpoint}")
        response = requests.get(url, headers=headers, params=params, timeout=30)

        # Handle rate limit headers from CoinAPI
        if 'X-RateLimit-Remaining' in response.headers:
            remaining = response.headers['X-RateLimit-Remaining']
            print(f"[CoinAPI] Remaining requests: {remaining}")

        response.raise_for_status()
        return response.json()

    except requests.exceptions.HTTPError as e:
        if response.status_code == 429:
            print(f"[CoinAPI] Rate limit exceeded: {e}")
            raise Exception("CoinAPI rate limit exceeded")
        elif response.status_code == 401:
            print(f"[CoinAPI] Authentication failed: {e}")
            raise Exception("CoinAPI authentication failed - check API key")
        else:
            print(f"[CoinAPI] HTTP error: {e}")
            raise

    except Exception as e:
        print(f"[CoinAPI] Request failed: {e}")
        raise


def fetch_options_symbols(currency='BTC', exchange='DERIBIT'):
    """
    Fetch list of available options symbols for a currency.

    Args:
        currency (str): Currency code (BTC, ETH)
        exchange (str): Exchange name (DERIBIT, BINANCE, OKX)

    Returns:
        list: List of symbol IDs
    """
    try:
        endpoint = '/v1/symbols'
        params = {
            'filter_symbol_id': f'{exchange}_OPT_{currency}',
            'filter_asset_type': 'OPTION'
        }

        data = make_request(endpoint, params)
        symbols = [s['symbol_id'] for s in data if s.get('symbol_type') == 'OPTION']

        print(f"[CoinAPI] Found {len(symbols)} options symbols for {currency} on {exchange}")
        return symbols

    except Exception as e:
        print(f"[CoinAPI] Failed to fetch symbols: {e}")
        return []


def fetch_ohlcv_history(symbol_id, period='1DAY', time_start=None, time_end=None, limit=100):
    """
    Fetch historical OHLCV data for a symbol.

    Args:
        symbol_id (str): Symbol identifier (e.g., 'DERIBIT_OPT_BTC_USD_30DEC22_20000_C')
        period (str): Time period (1DAY, 1HRS, etc.)
        time_start (datetime): Start time
        time_end (datetime): End time
        limit (int): Max number of records

    Returns:
        list: OHLCV data points
    """
    try:
        endpoint = f'/v1/ohlcv/{symbol_id}/history'
        params = {'period_id': period, 'limit': limit}

        if time_start:
            params['time_start'] = time_start.isoformat()
        if time_end:
            params['time_end'] = time_end.isoformat()

        data = make_request(endpoint, params)
        print(f"[CoinAPI] Fetched {len(data)} OHLCV records for {symbol_id}")

        return data

    except Exception as e:
        print(f"[CoinAPI] Failed to fetch OHLCV: {e}")
        return []


def fetch_current_quotes(symbol_ids):
    """
    Fetch current quotes for multiple symbols.

    Args:
        symbol_ids (list): List of symbol IDs

    Returns:
        dict: Map of symbol_id -> quote data
    """
    try:
        # CoinAPI has a bulk quotes endpoint
        endpoint = '/v1/quotes/current'
        params = {'filter_symbol_id': ','.join(symbol_ids[:10])}  # Limit to 10 at a time

        data = make_request(endpoint, params)

        quotes = {}
        for quote in data:
            symbol_id = quote.get('symbol_id')
            if symbol_id:
                quotes[symbol_id] = quote

        print(f"[CoinAPI] Fetched quotes for {len(quotes)} symbols")
        return quotes

    except Exception as e:
        print(f"[CoinAPI] Failed to fetch quotes: {e}")
        return {}


def fetch_options_greeks(currency='BTC', exchange='DERIBIT', expiry_days_target=30):
    """
    Fetch options Greeks for approximate expiry.

    Note: CoinAPI may not directly provide Greeks in Startup tier.
    This function prepares the structure for when available.

    Args:
        currency (str): Currency code
        exchange (str): Exchange name
        expiry_days_target (int): Target days to expiry

    Returns:
        dict: Map of strike -> {delta, gamma, vega, theta, iv}
    """
    print(f"[CoinAPI] Greeks fetching may not be available in Startup tier")
    print(f"[CoinAPI] Attempting to fetch current options quotes for {currency}")

    try:
        # Fetch symbols
        symbols = fetch_options_symbols(currency, exchange)

        if not symbols:
            return {}

        # Filter by approximate expiry (would need symbol parsing)
        # This is a simplified version
        filtered_symbols = symbols[:20]  # Limit for rate limiting

        quotes = fetch_current_quotes(filtered_symbols)

        # Extract Greeks if available in quote data
        greeks_data = {}
        for symbol_id, quote in quotes.items():
            # Greeks may be in 'ask_greeks', 'bid_greeks' fields if available
            greeks_data[symbol_id] = quote

        return greeks_data

    except Exception as e:
        print(f"[CoinAPI] Failed to fetch Greeks: {e}")
        return {}


def batch_historical_fetch(symbol_id, days=1095, period='1DAY'):
    """
    Fetch historical data in batches to manage rate limits.

    For 3 years of daily data, we need ~1095 data points.
    CoinAPI limits to 100 records per request, so we need ~11 requests.

    Args:
        symbol_id (str): Symbol identifier
        days (int): Number of days to fetch
        period (str): Time period

    Returns:
        list: All OHLCV data points
    """
    all_data = []
    batch_size = 100  # CoinAPI limit per request

    end_time = datetime.now(tz=timezone.utc)
    start_time = end_time - timedelta(days=days)

    print(f"[CoinAPI] Batching historical fetch: {start_time.date()} to {end_time.date()}")

    current_start = start_time
    batch_count = 0

    while current_start < end_time:
        batch_count += 1
        batch_end = min(current_start + timedelta(days=batch_size), end_time)

        print(f"[CoinAPI] Batch {batch_count}: {current_start.date()} to {batch_end.date()}")

        batch_data = fetch_ohlcv_history(
            symbol_id=symbol_id,
            period=period,
            time_start=current_start,
            time_end=batch_end,
            limit=batch_size
        )

        all_data.extend(batch_data)
        current_start = batch_end

        # Rate limiting between batches
        time.sleep(0.2)

    print(f"[CoinAPI] Batched fetch complete: {len(all_data)} total records")
    return all_data


def get_exchange_priority():
    """
    Return prioritized list of exchanges for options data.
    """
    return ['DERIBIT', 'BINANCE', 'OKX']


# Test function
if __name__ == '__main__':
    print("Testing CoinAPI Client...")
    print("=" * 60)

    # Test API key
    api_key = get_api_key()
    if api_key:
        print(f"[OK] API key loaded: {api_key[:10]}...")
    else:
        print("[ERROR] No API key found")
        exit(1)

    # Test fetching symbols
    print("\nFetching BTC options symbols from Deribit...")
    symbols = fetch_options_symbols('BTC', 'DERIBIT')

    if symbols:
        print(f"[OK] Found {len(symbols)} symbols")
        print(f"Sample: {symbols[0] if symbols else 'None'}")
    else:
        print("[WARNING] No symbols found")

    print("\n" + "=" * 60)
    print("CoinAPI client test complete")
