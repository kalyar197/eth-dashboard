# data/dvol_index.py
"""
DVOL - Deribit Volatility Index

The DVOL index is Deribit's implied volatility index, constructed similarly
to the VIX. It uses the implied volatility smile of options with various
strike prices and expiration dates to output a single number representing
the 30-day annualized implied volatility.

DVOL is "forward-looking" - it measures the expected volatility of BTC/ETH
over the next 30 days as calculated through option activity.

API: Deribit public endpoint (no authentication required)
Endpoint: /public/get_volatility_index_data?currency=BTC&resolution=1D

Historical Data: Available since 2019 (6+ years of data)
"""

import requests
import time
from datetime import datetime, timedelta, timezone
from .incremental_data_manager import (
    load_historical_data,
    save_historical_data,
    merge_and_deduplicate,
    validate_data_structure
)


def get_metadata(asset='btc'):
    """Returns metadata describing how this data should be displayed"""
    asset_names = {
        'btc': 'Bitcoin',
        'eth': 'Ethereum'
    }
    asset_name = asset_names.get(asset, asset.upper())
    currency = asset.upper()

    return {
        'label': f'DVOL ({asset_name})',
        'oscillator': True,
        'yAxisId': 'oscillator',
        'yAxisLabel': 'DVOL (%)',
        'unit': '%',
        'chartType': 'line',
        'color': '#00D9FF',  # Cyan color
        'strokeWidth': 2,
        'description': f'Deribit Volatility Index for {asset_name} - 30-day implied volatility',
        'data_structure': 'simple',
        'components': ['timestamp', 'dvol_value']
    }


def fetch_dvol_from_deribit(currency='BTC', start_timestamp=None, end_timestamp=None):
    """
    Fetch DVOL data from Deribit API.

    Args:
        currency (str): 'BTC' or 'ETH'
        start_timestamp (int): Start timestamp in milliseconds
        end_timestamp (int): End timestamp in milliseconds

    Returns:
        list: [[timestamp_ms, dvol_value], ...]
    """
    base_url = 'https://www.deribit.com/api/v2'
    endpoint = '/public/get_volatility_index_data'

    params = {
        'currency': currency,
        'resolution': '1D'  # Daily resolution
    }

    if start_timestamp:
        params['start_timestamp'] = start_timestamp
    if end_timestamp:
        params['end_timestamp'] = end_timestamp

    try:
        print(f"[DVOL {currency}] Fetching DVOL data from Deribit...")
        response = requests.get(f"{base_url}{endpoint}", params=params, timeout=30)
        response.raise_for_status()

        data = response.json()

        # Handle different response formats from Deribit
        if isinstance(data, dict) and 'result' in data:
            if isinstance(data['result'], list):
                raw_data = data['result']
            elif 'data' in data['result']:
                raw_data = data['result']['data']
            else:
                print(f"[DVOL {currency}] Unexpected API response format (dict result)")
                return []
        elif isinstance(data, list):
            raw_data = data
        else:
            print(f"[DVOL {currency}] Unexpected API response format")
            return []

        # Convert to [[timestamp_ms, value], ...] format
        dvol_data = []
        for point in raw_data:
            # Handle both list format [timestamp, value] and dict format {'timestamp': ms, 'value': float}
            if isinstance(point, list) and len(point) >= 2:
                timestamp_ms = point[0]
                value = point[1]
            elif isinstance(point, dict):
                timestamp_ms = point.get('timestamp')
                value = point.get('value')
            else:
                continue

            if timestamp_ms is not None and value is not None:
                # Convert to daily UTC timestamp (midnight)
                dt = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
                daily_ts = int(dt.replace(hour=0, minute=0, second=0, microsecond=0).timestamp() * 1000)

                dvol_data.append([daily_ts, value])

        print(f"[DVOL {currency}] Fetched {len(dvol_data)} data points from Deribit")
        return dvol_data

    except requests.exceptions.RequestException as e:
        print(f"[DVOL {currency}] Deribit API request failed: {e}")
        return []
    except Exception as e:
        print(f"[DVOL {currency}] Error parsing Deribit response: {e}")
        return []


def batch_fetch_dvol(currency='BTC', days=1095):
    """
    Fetch DVOL data in batches to handle large historical ranges.

    Deribit API may have limits on how much data can be fetched in one request.
    This function batches requests into 90-day chunks.

    Args:
        currency (str): 'BTC' or 'ETH'
        days (int): Number of days to fetch

    Returns:
        list: Combined DVOL data
    """
    all_data = []
    batch_days = 365  # Fetch 1 year at a time

    end_date = datetime.now(tz=timezone.utc)
    start_date = end_date - timedelta(days=days)

    print(f"[DVOL {currency}] Batch fetching: {start_date.date()} to {end_date.date()}")

    current_start = start_date
    batch_count = 0

    while current_start < end_date:
        batch_count += 1
        batch_end = min(current_start + timedelta(days=batch_days), end_date)

        start_ts = int(current_start.timestamp() * 1000)
        end_ts = int(batch_end.timestamp() * 1000)

        print(f"[DVOL {currency}] Batch {batch_count}: {current_start.date()} to {batch_end.date()}")

        batch_data = fetch_dvol_from_deribit(
            currency=currency,
            start_timestamp=start_ts,
            end_timestamp=end_ts
        )

        all_data.extend(batch_data)
        current_start = batch_end

        # Rate limiting between batches
        if current_start < end_date:
            time.sleep(0.5)

    print(f"[DVOL {currency}] Total fetched: {len(all_data)} data points")
    return all_data


def get_data(days='365', asset='btc'):
    """
    Fetches DVOL data using incremental fetching strategy.

    Strategy:
    1. Load historical DVOL data from disk
    2. Fetch fresh DVOL data from Deribit API
    3. Merge with historical data
    4. Save to historical_data/dvol_{asset}.json
    5. Return filtered by requested days

    Args:
        days (str): Number of days to return ('7', '30', '180', '1095', 'max')
        asset (str): Asset name ('btc', 'eth')

    Returns:
        dict: {
            'metadata': metadata dict,
            'data': [[timestamp, dvol_value], ...],
            'structure': 'simple'
        }
    """
    metadata = get_metadata(asset)
    dataset_name = f'dvol_{asset}'

    # Map asset to currency code
    currency = 'BTC' if asset == 'btc' else 'ETH' if asset == 'eth' else 'BTC'

    try:
        requested_days = int(days) if days != 'max' else 1095

        # Fetch extra days to ensure full coverage
        fetch_days = requested_days + 10

        # Load existing historical DVOL data
        historical_data = load_historical_data(dataset_name)

        # Fetch fresh DVOL data from Deribit
        print(f"[DVOL {currency}] Fetching DVOL data for {fetch_days} days...")
        fresh_dvol_data = batch_fetch_dvol(currency=currency, days=fetch_days)

        if not fresh_dvol_data:
            print(f"[DVOL {currency}] No fresh data fetched, using historical data only")
            fresh_dvol_data = []

        # Merge with historical data
        if fresh_dvol_data:
            merged_data = merge_and_deduplicate(
                existing_data=historical_data,
                new_data=fresh_dvol_data,
                overlap_days=fetch_days
            )
        else:
            merged_data = historical_data

        # Validate data structure
        is_valid, structure_type, error_msg = validate_data_structure(merged_data)
        if not is_valid:
            print(f"[DVOL {currency}] Warning: Data validation failed: {error_msg}")

        # Save complete historical dataset
        if merged_data:
            save_historical_data(dataset_name, merged_data)

        # Filter to requested days
        if days != 'max' and merged_data:
            cutoff_date = datetime.now(tz=timezone.utc) - timedelta(days=int(days))
            cutoff_ms = int(cutoff_date.timestamp() * 1000)
            filtered_data = [d for d in merged_data if d[0] >= cutoff_ms]
        else:
            filtered_data = merged_data

        print(f"[DVOL {currency}] Returning {len(filtered_data)} DVOL data points")
        if filtered_data:
            print(f"[DVOL {currency}] Date range: {datetime.fromtimestamp(filtered_data[0][0]/1000, tz=timezone.utc).date()} to {datetime.fromtimestamp(filtered_data[-1][0]/1000, tz=timezone.utc).date()}")
            print(f"[DVOL {currency}] DVOL range: {min(d[1] for d in filtered_data):.2f}% to {max(d[1] for d in filtered_data):.2f}%")

        return {
            'metadata': metadata,
            'data': filtered_data,
            'structure': 'simple'
        }

    except Exception as e:
        print(f"[DVOL {currency}] Error in get_data: {e}")
        import traceback
        traceback.print_exc()

        # Fallback to historical data
        historical_data = load_historical_data(dataset_name)
        if historical_data:
            print(f"[DVOL {currency}] Falling back to historical data ({len(historical_data)} records)")

            if days != 'max':
                cutoff_date = datetime.now(tz=timezone.utc) - timedelta(days=int(days))
                cutoff_ms = int(cutoff_date.timestamp() * 1000)
                filtered_data = [d for d in historical_data if d[0] >= cutoff_ms]
            else:
                filtered_data = historical_data

            return {
                'metadata': metadata,
                'data': filtered_data,
                'structure': 'simple'
            }

        print(f"[DVOL {currency}] No historical data available for fallback")
        return {
            'metadata': metadata,
            'data': [],
            'structure': 'simple'
        }


if __name__ == '__main__':
    # Test the DVOL plugin
    import sys
    import os
    import numpy as np
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    print("Testing DVOL Plugin...")
    print("=" * 60)

    # Test BTC DVOL
    result = get_data(days='90', asset='btc')

    print(f"\nMetadata: {result['metadata']['label']}")
    print(f"Data points: {len(result['data'])}")

    if result['data']:
        values = [d[1] for d in result['data']]
        print(f"\nDVOL Statistics (90 days):")
        print(f"  Mean:   {np.mean(values):.2f}%")
        print(f"  Median: {np.median(values):.2f}%")
        print(f"  Min:    {np.min(values):.2f}%")
        print(f"  Max:    {np.max(values):.2f}%")

    print("\n" + "=" * 60)
    print("Test complete")
