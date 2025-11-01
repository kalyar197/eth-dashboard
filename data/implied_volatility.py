# data/implied_volatility.py
"""
Implied Volatility - Forward-Looking Volatility Expectations

Implied Volatility (IV) represents the market's expectation of future volatility,
derived from options prices. Unlike realized volatility (historical), IV is
forward-looking and reflects what traders expect volatility to be.

Data Sources (in priority order):
1. DVOL from Deribit (free API) - 30-day IV index
2. CoinAPI (if DVOL unavailable) - aggregated IV across exchanges

This is a simplified version that uses DVOL as a proxy for IV. For more granular
IV data (by strike/expiry), use the Term Structure or Skew plugins.

Historical Data: Available since 2019 (6+ years via Deribit)
"""

from datetime import datetime, timedelta, timezone
from .incremental_data_manager import (
    load_historical_data,
    save_historical_data,
    merge_and_deduplicate,
    validate_data_structure
)
from . import dvol_index


def get_metadata(asset='btc'):
    """Returns metadata describing how this data should be displayed"""
    asset_names = {
        'btc': 'Bitcoin',
        'eth': 'Ethereum'
    }
    asset_name = asset_names.get(asset, asset.upper())

    return {
        'label': f'Implied Volatility ({asset_name})',
        'oscillator': True,
        'yAxisId': 'oscillator',
        'yAxisLabel': 'IV (%)',
        'unit': '%',
        'chartType': 'line',
        'color': '#FF6B6B',  # Red color
        'strokeWidth': 2,
        'description': f'Implied Volatility for {asset_name} (30-day forward expectation)',
        'data_structure': 'simple',
        'components': ['timestamp', 'iv_percent']
    }


def get_data(days='365', asset='btc'):
    """
    Fetches Implied Volatility data using incremental fetching strategy.

    For now, this uses DVOL as the primary IV source. In the future, this could
    be enhanced to aggregate IV across multiple exchanges via CoinAPI.

    Strategy:
    1. Load historical IV data from disk
    2. Fetch DVOL data (proxy for 30-day IV)
    3. Merge with historical data
    4. Save to historical_data/implied_volatility_{asset}.json
    5. Return filtered by requested days

    Args:
        days (str): Number of days to return ('7', '30', '180', '1095', 'max')
        asset (str): Asset name ('btc', 'eth')

    Returns:
        dict: {
            'metadata': metadata dict,
            'data': [[timestamp, iv_percent], ...],
            'structure': 'simple'
        }
    """
    metadata = get_metadata(asset)
    dataset_name = f'implied_volatility_{asset}'

    try:
        requested_days = int(days) if days != 'max' else 1095

        # Load existing historical IV data
        historical_data = load_historical_data(dataset_name)

        # Fetch DVOL data (which represents 30-day IV)
        print(f"[IV {asset.upper()}] Fetching DVOL data as IV proxy...")
        dvol_result = dvol_index.get_data(days=str(requested_days + 10), asset=asset)
        dvol_data = dvol_result.get('data', [])

        if not dvol_data:
            print(f"[IV {asset.upper()}] No DVOL data available")
            dvol_data = []

        print(f"[IV {asset.upper()}] Got {len(dvol_data)} IV data points from DVOL")

        # For now, IV = DVOL (they're essentially the same for our purposes)
        # In the future, we could enhance this to fetch IV from CoinAPI for multi-exchange aggregation
        fresh_iv_data = dvol_data

        # Merge with historical data
        if fresh_iv_data:
            merged_data = merge_and_deduplicate(
                existing_data=historical_data,
                new_data=fresh_iv_data,
                overlap_days=requested_days + 10
            )
        else:
            merged_data = historical_data

        # Validate data structure
        is_valid, structure_type, error_msg = validate_data_structure(merged_data)
        if not is_valid:
            print(f"[IV {asset.upper()}] Warning: Data validation failed: {error_msg}")

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

        print(f"[IV {asset.upper()}] Returning {len(filtered_data)} IV data points")
        if filtered_data:
            print(f"[IV {asset.upper()}] Date range: {datetime.fromtimestamp(filtered_data[0][0]/1000, tz=timezone.utc).date()} to {datetime.fromtimestamp(filtered_data[-1][0]/1000, tz=timezone.utc).date()}")
            print(f"[IV {asset.upper()}] IV range: {min(d[1] for d in filtered_data):.2f}% to {max(d[1] for d in filtered_data):.2f}%")

        return {
            'metadata': metadata,
            'data': filtered_data,
            'structure': 'simple'
        }

    except Exception as e:
        print(f"[IV {asset.upper()}] Error in get_data: {e}")
        import traceback
        traceback.print_exc()

        # Fallback to historical data
        historical_data = load_historical_data(dataset_name)
        if historical_data:
            print(f"[IV {asset.upper()}] Falling back to historical data ({len(historical_data)} records)")

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

        print(f"[IV {asset.upper()}] No historical data available for fallback")
        return {
            'metadata': metadata,
            'data': [],
            'structure': 'simple'
        }


if __name__ == '__main__':
    # Test the IV plugin
    import sys
    import os
    import numpy as np
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    print("Testing Implied Volatility Plugin...")
    print("=" * 60)

    # Test BTC IV
    result = get_data(days='90', asset='btc')

    print(f"\nMetadata: {result['metadata']['label']}")
    print(f"Data points: {len(result['data'])}")

    if result['data']:
        values = [d[1] for d in result['data']]
        print(f"\nIV Statistics (90 days):")
        print(f"  Mean:   {np.mean(values):.2f}%")
        print(f"  Median: {np.median(values):.2f}%")
        print(f"  Min:    {np.min(values):.2f}%")
        print(f"  Max:    {np.max(values):.2f}%")

    print("\n" + "=" * 60)
    print("Test complete")
