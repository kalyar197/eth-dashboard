# data/iv_rank.py
"""
IV Rank (Implied Volatility Rank)

IV Rank measures where the current implied volatility stands relative to its
historical range over a lookback period (typically 1 year / 252 trading days).

Formula:
    IVR = (Current IV - Min IV over period) / (Max IV over period - Min IV over period) * 100

Interpretation:
- IVR = 0%: Current IV is at the lowest level in the lookback period
- IVR = 50%: Current IV is in the middle of the range
- IVR = 100%: Current IV is at the highest level in the lookback period

High IVR (>75%): Options are expensive, potential premium selling opportunities
Low IVR (<25%): Options are cheap, potential premium buying opportunities

Lookback Period: 252 days (1 year of trading days)
"""

import numpy as np
from datetime import datetime, timedelta, timezone
from .incremental_data_manager import (
    load_historical_data,
    save_historical_data,
    merge_and_deduplicate,
    validate_data_structure
)
from . import implied_volatility


def get_metadata(asset='btc'):
    """Returns metadata describing how this data should be displayed"""
    asset_names = {
        'btc': 'Bitcoin',
        'eth': 'Ethereum'
    }
    asset_name = asset_names.get(asset, asset.upper())

    return {
        'label': f'IV Rank ({asset_name})',
        'oscillator': True,
        'yAxisId': 'oscillator',
        'yAxisLabel': 'IV Rank (%)',
        'unit': '%',
        'chartType': 'line',
        'color': '#4ECDC4',  # Teal color
        'strokeWidth': 2,
        'description': f'IV Rank for {asset_name} - percentile ranking of current IV (252-day lookback)',
        'data_structure': 'simple',
        'components': ['timestamp', 'ivr_percent'],
        'yDomain': [0, 100],  # IV Rank is always 0-100%
        'referenceLines': [
            {'value': 75, 'label': 'High IVR', 'color': '#ef5350'},
            {'value': 50, 'label': 'Mid', 'color': '#888'},
            {'value': 25, 'label': 'Low IVR', 'color': '#26a69a'}
        ]
    }


def calculate_iv_rank(iv_data, window=252):
    """
    Calculate rolling IV Rank from IV time series.

    Args:
        iv_data (list): [[timestamp, iv_value], ...] - Implied volatility data
        window (int): Rolling window size (default: 252 = 1 year)

    Returns:
        list: [[timestamp, ivr_percent], ...] - IV Rank values
    """
    if not iv_data or len(iv_data) < window:
        return []

    ivr_data = []

    # Extract IV values
    iv_values = np.array([d[1] for d in iv_data])

    # Calculate rolling IV Rank
    for i in range(window, len(iv_data)):
        timestamp = iv_data[i][0]
        current_iv = iv_values[i]

        # Get window of IV values
        iv_window = iv_values[i - window:i]

        # Calculate min and max over window
        min_iv = np.min(iv_window)
        max_iv = np.max(iv_window)

        # Calculate IV Rank
        if max_iv > min_iv:
            ivr = (current_iv - min_iv) / (max_iv - min_iv) * 100
        else:
            # If min == max (no variance), IV Rank is 50%
            ivr = 50.0

        # Clamp to [0, 100]
        ivr = max(0.0, min(100.0, ivr))

        ivr_data.append([timestamp, ivr])

    return ivr_data


def get_data(days='365', asset='btc', window=252):
    """
    Fetches IV Rank data using incremental fetching strategy.

    Strategy:
    1. Load historical IV Rank data from disk
    2. Fetch IV data (need extra days for rolling window)
    3. Calculate IV Rank using rolling window
    4. Merge with historical data
    5. Save to historical_data/iv_rank_{asset}.json
    6. Return filtered by requested days

    Args:
        days (str): Number of days to return ('7', '30', '180', '1095', 'max')
        asset (str): Asset name ('btc', 'eth')
        window (int): Rolling window for IV Rank (default: 252 days = 1 year)

    Returns:
        dict: {
            'metadata': metadata dict,
            'data': [[timestamp, ivr_percent], ...],
            'structure': 'simple'
        }
    """
    metadata = get_metadata(asset)
    dataset_name = f'iv_rank_{asset}'

    try:
        requested_days = int(days) if days != 'max' else 1095

        # Need extra days for rolling window calculation
        fetch_days = requested_days + window + 10

        # Load existing historical IV Rank data
        historical_data = load_historical_data(dataset_name)

        # Fetch IV data (need window + requested days)
        print(f"[IV Rank {asset.upper()}] Fetching IV data for {fetch_days} days (need {window}-day window)...")
        iv_result = implied_volatility.get_data(days=str(fetch_days), asset=asset)
        iv_data = iv_result.get('data', [])

        if not iv_data:
            raise ValueError(f"No IV data available for IV Rank calculation")

        print(f"[IV Rank {asset.upper()}] Got {len(iv_data)} IV data points")

        # Calculate IV Rank
        print(f"[IV Rank {asset.upper()}] Calculating IV Rank with {window}-day window...")
        calculated_ivr = calculate_iv_rank(iv_data, window=window)

        if not calculated_ivr:
            raise ValueError("IV Rank calculation returned no data")

        print(f"[IV Rank {asset.upper()}] Calculated {len(calculated_ivr)} IV Rank values")

        # Merge with historical data
        merged_data = merge_and_deduplicate(
            existing_data=historical_data,
            new_data=calculated_ivr,
            overlap_days=requested_days + window
        )

        # Validate data structure
        is_valid, structure_type, error_msg = validate_data_structure(merged_data)
        if not is_valid:
            print(f"[IV Rank {asset.upper()}] Warning: Data validation failed: {error_msg}")

        # Save complete historical dataset
        save_historical_data(dataset_name, merged_data)

        # Filter to requested days
        if days != 'max':
            cutoff_date = datetime.now(tz=timezone.utc) - timedelta(days=int(days))
            cutoff_ms = int(cutoff_date.timestamp() * 1000)
            filtered_data = [d for d in merged_data if d[0] >= cutoff_ms]
        else:
            filtered_data = merged_data

        print(f"[IV Rank {asset.upper()}] Returning {len(filtered_data)} IV Rank data points")
        if filtered_data:
            print(f"[IV Rank {asset.upper()}] Date range: {datetime.fromtimestamp(filtered_data[0][0]/1000, tz=timezone.utc).date()} to {datetime.fromtimestamp(filtered_data[-1][0]/1000, tz=timezone.utc).date()}")
            print(f"[IV Rank {asset.upper()}] IV Rank range: {min(d[1] for d in filtered_data):.2f}% to {max(d[1] for d in filtered_data):.2f}%")

        return {
            'metadata': metadata,
            'data': filtered_data,
            'structure': 'simple'
        }

    except Exception as e:
        print(f"[IV Rank {asset.upper()}] Error in get_data: {e}")
        import traceback
        traceback.print_exc()

        # Fallback to historical data
        historical_data = load_historical_data(dataset_name)
        if historical_data:
            print(f"[IV Rank {asset.upper()}] Falling back to historical data ({len(historical_data)} records)")

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

        print(f"[IV Rank {asset.upper()}] No historical data available for fallback")
        return {
            'metadata': metadata,
            'data': [],
            'structure': 'simple'
        }


if __name__ == '__main__':
    # Test the IV Rank plugin
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    print("Testing IV Rank Plugin...")
    print("=" * 60)

    # Test BTC IV Rank
    result = get_data(days='90', asset='btc')

    print(f"\nMetadata: {result['metadata']['label']}")
    print(f"Data points: {len(result['data'])}")

    if result['data']:
        values = [d[1] for d in result['data']]
        print(f"\nIV Rank Statistics (90 days):")
        print(f"  Mean:   {np.mean(values):.2f}%")
        print(f"  Median: {np.median(values):.2f}%")
        print(f"  Min:    {np.min(values):.2f}%")
        print(f"  Max:    {np.max(values):.2f}%")

        # Distribution
        low_ivr = sum(1 for v in values if v < 25)
        mid_ivr = sum(1 for v in values if 25 <= v <= 75)
        high_ivr = sum(1 for v in values if v > 75)

        print(f"\nIV Rank Distribution:")
        print(f"  Low (<25%):   {low_ivr}/{len(values)} ({low_ivr/len(values)*100:.1f}%)")
        print(f"  Mid (25-75%): {mid_ivr}/{len(values)} ({mid_ivr/len(values)*100:.1f}%)")
        print(f"  High (>75%):  {high_ivr}/{len(values)} ({high_ivr/len(values)*100:.1f}%)")

    print("\n" + "=" * 60)
    print("Test complete")
