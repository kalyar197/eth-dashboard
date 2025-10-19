# data/eth_btc_ratio.py
"""
ETH/BTC Ratio data fetcher using CoinAPI
Fetches direct ETH/BTC trading pair data from Binance
Returns simple [timestamp, ratio] data structure using closing prices
"""

import requests
from .time_transformer import standardize_to_daily_utc, extract_component
from datetime import datetime, timedelta
import sys
import os
from .cache_manager import load_from_cache, save_to_cache

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import COINAPI_KEY

def get_metadata():
    """Returns metadata describing how this data should be displayed"""
    return {
        'label': 'ETH/BTC Ratio',
        'yAxisId': 'ratio',
        'yAxisLabel': 'ETH/BTC',
        'unit': '',
        'chartType': 'line',
        'color': '#627EEA',  # Ethereum's brand color
        'strokeWidth': 2,
        'description': 'Ethereum to Bitcoin price ratio from direct trading pair'
    }

def get_data(days='365'):
    """
    Fetches ETH/BTC ratio using CoinAPI's direct ETH/BTC trading pair.
    Returns simple [timestamp, ratio] data structure using closing prices.
    """
    metadata = get_metadata()
    dataset_name = 'eth_btc_ratio'

    try:
        print("Fetching ETH/BTC ratio data from CoinAPI...")
        print("Using direct BINANCE_SPOT_ETH_BTC trading pair")

        # CoinAPI OHLCV History endpoint configuration
        base_url = 'https://rest.coinapi.io/v1/ohlcv'
        symbol_id = 'BINANCE_SPOT_ETH_BTC'  # Direct ETH/BTC pair

        # Calculate date range
        if days == 'max':
            # Get max available data (e.g., 5 years)
            start_date = datetime.now() - timedelta(days=365 * 5)
        else:
            start_date = datetime.now() - timedelta(days=int(days) + 10)  # Extra buffer

        end_date = datetime.now()

        # Format dates for CoinAPI (ISO 8601)
        time_start = start_date.strftime('%Y-%m-%dT00:00:00')
        time_end = end_date.strftime('%Y-%m-%dT23:59:59')

        # Construct the API URL
        url = f'{base_url}/{symbol_id}/history'

        # API parameters
        params = {
            'period_id': '1DAY',  # Daily candles
            'time_start': time_start,
            'time_end': time_end,
            'limit': 100000  # Max limit to get all available data
        }

        # Headers with API key
        headers = {
            'X-CoinAPI-Key': COINAPI_KEY
        }

        # Make the API request
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()

        if not data:
            raise ValueError("No data returned from CoinAPI")

        # Process the OHLCV data - we'll extract closing prices
        raw_data = []
        for candle in data:
            timestamp_str = candle.get('time_period_start')

            # Extract all components
            open_price = candle.get('price_open')
            high_price = candle.get('price_high')
            low_price = candle.get('price_low')
            close_price = candle.get('price_close')
            volume_traded = candle.get('volume_traded')

            # Validate all components exist
            if (timestamp_str and
                open_price is not None and
                high_price is not None and
                low_price is not None and
                close_price is not None and
                volume_traded is not None):

                # Parse the ISO timestamp
                dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                timestamp_ms = int(dt.timestamp() * 1000)

                # Store all 6 components temporarily
                raw_data.append([
                    timestamp_ms,
                    float(open_price),
                    float(high_price),
                    float(low_price),
                    float(close_price),
                    float(volume_traded)
                ])
            else:
                print(f"Warning: Incomplete OHLCV data for {timestamp_str}, skipping...")

        if not raw_data:
            raise ValueError("No valid data extracted from CoinAPI response")

        # Sort by timestamp (oldest first)
        raw_data.sort(key=lambda x: x[0])

        # Standardize to daily UTC format
        standardized_data = standardize_to_daily_utc(raw_data)

        # Extract only closing prices for ratio display
        ratio_data = extract_component(standardized_data, 'close')

        # Trim to the exact requested number of days
        if days != 'max':
            cutoff_date = datetime.now() - timedelta(days=int(days))
            cutoff_ms = int(cutoff_date.timestamp() * 1000)
            ratio_data = [d for d in ratio_data if d[0] >= cutoff_ms]

        # Save to cache
        save_to_cache(dataset_name, ratio_data)
        print(f"Successfully fetched {len(ratio_data)} ETH/BTC ratio data points")
        print(f"Sample ratio: {ratio_data[0][1]:.6f} BTC per ETH (timestamp: {ratio_data[0][0]})")

        return {
            'metadata': metadata,
            'data': ratio_data
        }

    except requests.exceptions.RequestException as e:
        print(f"API request failed for ETH/BTC ratio: {e}")
        # Load from cache if API fails
        cached_data = load_from_cache(dataset_name)
        if cached_data:
            return {'metadata': metadata, 'data': cached_data}
        return {'metadata': metadata, 'data': []}

    except Exception as e:
        print(f"Error fetching ETH/BTC ratio from CoinAPI: {e}")
        # Load from cache if any error occurs
        cached_data = load_from_cache(dataset_name)
        if cached_data:
            return {'metadata': metadata, 'data': cached_data}
        return {'metadata': metadata, 'data': []}
