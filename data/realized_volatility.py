# data/realized_volatility.py
"""
Realized Volatility (Historical Volatility) Indicator

Calculates backward-looking volatility from BTC price movements using
the Garman-Klass estimator, which is more efficient than close-to-close
volatility as it uses full OHLC range information.

Formula: σ_GK = sqrt(0.5 * ln(H/L)² - (2*ln(2)-1) * ln(C/O)²)

This is a "realized" metric (historical, backward-looking), distinct from
implied volatility (forward-looking, derived from options prices).

For the volatility oscillator system, this will be normalized against BTC price
using regression divergence to detect when realized vol deviates from expected levels.
"""

import numpy as np
from datetime import datetime, timedelta, timezone
from .incremental_data_manager import (
    load_historical_data,
    save_historical_data,
    merge_and_deduplicate,
    validate_data_structure
)
from .volatility import calculate_gk_volatility


def get_metadata(asset='btc'):
    """Returns metadata describing how this data should be displayed"""
    asset_names = {
        'btc': 'Bitcoin',
        'eth': 'Ethereum',
        'gold': 'Gold'
    }
    asset_name = asset_names.get(asset, asset.upper())

    return {
        'label': f'Realized Volatility ({asset_name})',
        'oscillator': True,  # Flag to identify as oscillator dataset
        'yAxisId': 'oscillator',
        'yAxisLabel': 'Realized Vol (%)',
        'unit': '%',
        'chartType': 'line',
        'color': '#9C27B0',  # Purple color
        'strokeWidth': 2,
        'description': f'Realized (historical) volatility for {asset_name} using Garman-Klass estimator - annualized %',
        'data_structure': 'simple',
        'components': ['timestamp', 'rv_percent']
    }


def get_data(days='365', asset='btc'):
    """
    Fetches Realized Volatility data using incremental fetching strategy.

    Strategy:
    1. Load historical RV data from disk
    2. Fetch asset OHLCV price data
    3. Calculate Garman-Klass volatility from OHLC
    4. Merge with historical data
    5. Save to historical_data/realized_volatility_{asset}.json
    6. Return filtered by requested days

    Args:
        days (str): Number of days to return ('7', '30', '180', '1095', 'max')
        asset (str): Asset name ('btc', 'eth', 'gold')

    Returns:
        dict: {
            'metadata': metadata dict,
            'data': [[timestamp, rv_percent], ...],
            'structure': 'simple'
        }
    """
    metadata = get_metadata(asset)
    dataset_name = f'realized_volatility_{asset}'

    try:
        requested_days = int(days) if days != 'max' else 1095

        # We need OHLC data to calculate volatility
        fetch_days = requested_days + 10  # Small buffer for edge cases

        # Load existing historical RV data
        historical_data = load_historical_data(dataset_name)

        # Import the asset price module dynamically
        if asset == 'btc':
            from . import btc_price as asset_module
        elif asset == 'eth':
            from . import eth_price as asset_module
        elif asset == 'gold':
            from . import gold_price as asset_module
        else:
            raise ValueError(f"Unsupported asset: {asset}")

        # Fetch asset OHLCV data
        print(f"[Realized Vol {asset.upper()}] Fetching {asset.upper()} price data for volatility calculation...")
        asset_data_result = asset_module.get_data(str(fetch_days))
        asset_ohlcv_data = asset_data_result['data']

        if not asset_ohlcv_data:
            raise ValueError(f"No {asset.upper()} price data available for RV calculation")

        print(f"[Realized Vol {asset.upper()}] Calculating Garman-Klass volatility from {len(asset_ohlcv_data)} price data points...")

        # Calculate Garman-Klass volatility
        calculated_rv = calculate_gk_volatility(asset_ohlcv_data)

        if not calculated_rv:
            raise ValueError("Realized volatility calculation returned no data")

        print(f"[Realized Vol {asset.upper()}] Calculated {len(calculated_rv)} RV values")

        # Merge with historical data
        # For calculated indicators, we replace all overlapping data with fresh calculations
        merged_data = merge_and_deduplicate(
            existing_data=historical_data,
            new_data=calculated_rv,
            overlap_days=fetch_days  # Replace all data in the calculated range
        )

        # Validate data structure
        is_valid, structure_type, error_msg = validate_data_structure(merged_data)
        if not is_valid:
            print(f"[Realized Vol {asset.upper()}] Warning: Data validation failed: {error_msg}")

        # Save complete historical dataset
        save_historical_data(dataset_name, merged_data)

        # Filter to requested days
        if days != 'max':
            cutoff_date = datetime.now(tz=timezone.utc) - timedelta(days=int(days))
            cutoff_ms = int(cutoff_date.timestamp() * 1000)
            filtered_data = [d for d in merged_data if d[0] >= cutoff_ms]
        else:
            filtered_data = merged_data

        print(f"[Realized Vol {asset.upper()}] Returning {len(filtered_data)} RV data points")
        if filtered_data:
            print(f"[Realized Vol {asset.upper()}] Date range: {datetime.fromtimestamp(filtered_data[0][0]/1000, tz=timezone.utc).date()} to {datetime.fromtimestamp(filtered_data[-1][0]/1000, tz=timezone.utc).date()}")
            print(f"[Realized Vol {asset.upper()}] RV range: {min(d[1] for d in filtered_data):.2f}% to {max(d[1] for d in filtered_data):.2f}%")

        return {
            'metadata': metadata,
            'data': filtered_data,
            'structure': 'simple'
        }

    except Exception as e:
        print(f"[Realized Vol {asset.upper()}] Error in get_data: {e}")

        # Fallback to historical data if available
        historical_data = load_historical_data(dataset_name)
        if historical_data:
            print(f"[Realized Vol {asset.upper()}] Falling back to historical data ({len(historical_data)} records)")

            # Filter by requested days
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

        # No data available at all
        print(f"[Realized Vol {asset.upper()}] No historical data available for fallback")
        return {
            'metadata': metadata,
            'data': [],
            'structure': 'simple'
        }


if __name__ == '__main__':
    # Test the Realized Volatility plugin
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    print("Testing Realized Volatility Plugin...")
    print("=" * 60)

    # Test BTC Realized Volatility
    result = get_data(days='90', asset='btc')

    print(f"\nMetadata: {result['metadata']['label']}")
    print(f"Data points: {len(result['data'])}")

    if result['data']:
        values = [d[1] for d in result['data']]
        print(f"\nRV Statistics (90 days):")
        print(f"  Mean:   {np.mean(values):.2f}%")
        print(f"  Median: {np.median(values):.2f}%")
        print(f"  Min:    {np.min(values):.2f}%")
        print(f"  Max:    {np.max(values):.2f}%")

    print("\n" + "=" * 60)
    print("Test complete")
