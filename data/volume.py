# data/volume.py
"""
Volume Indicator

Extracts volume data from asset OHLCV data with incremental fetching.
Volume shows trading activity and can be used to confirm price movements.

High volume during price moves = strong trend
Low volume during price moves = weak trend (potential reversal)

Note: Gold (XAU/USD) is a spot price and doesn't have volume data.
"""

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
        'eth': 'Ethereum',
        'gold': 'Gold'
    }
    asset_name = asset_names.get(asset, asset.upper())

    return {
        'label': f'Volume ({asset_name})',
        'oscillator': True,
        'yAxisId': 'oscillator',
        'yAxisLabel': 'Volume',
        'unit': '',
        'chartType': 'line',
        'color': '#9C27B0',  # Purple color
        'strokeWidth': 2,
        'description': f'Trading volume for {asset_name}',
        'data_structure': 'simple',
        'components': ['timestamp', 'volume'],
        'note': 'Gold (XAU/USD) is a spot price and has no volume data'
    }


def extract_volume_from_ohlcv(ohlcv_data):
    """
    Extract volume from OHLCV data.

    Args:
        ohlcv_data (list): [[timestamp, open, high, low, close, volume], ...]

    Returns:
        list: [[timestamp, volume], ...]
    """
    if not ohlcv_data:
        return []

    result = []
    for item in ohlcv_data:
        timestamp = item[0]
        volume = item[5]  # Index 5 is volume

        result.append([timestamp, volume])

    return result


def get_data(days='365', asset='btc'):
    """
    Fetches Volume data using incremental fetching strategy.

    Strategy:
    1. Load historical volume data from disk
    2. Fetch asset price data (OHLCV)
    3. Extract volume from OHLCV data
    4. Merge with historical data using overlap strategy
    5. Save to historical_data/volume_{asset}.json
    6. Return filtered by requested days

    Args:
        days (str): Number of days to return ('7', '30', '180', '1095', 'max')
        asset (str): Asset name ('btc', 'eth', 'gold')

    Returns:
        dict: {
            'metadata': metadata dict,
            'data': [[timestamp, volume], ...],
            'structure': 'simple'
        }
    """
    metadata = get_metadata(asset)
    dataset_name = f'volume_{asset}'

    try:
        requested_days = int(days) if days != 'max' else 1095

        # Load existing historical volume data
        historical_data = load_historical_data(dataset_name)

        # Import the asset price module dynamically
        if asset == 'btc':
            from . import btc_price as asset_module
        elif asset == 'eth':
            from . import eth_price as asset_module
        elif asset == 'gold':
            from . import gold_price as asset_module
            # Gold doesn't have volume, but we'll process it anyway (will be all zeros)
            print(f"[Volume {asset.upper()}] Note: Gold spot price doesn't have volume data")
        else:
            raise ValueError(f"Unsupported asset: {asset}")

        # Fetch asset OHLCV data
        print(f"[Volume {asset.upper()}] Fetching {asset.upper()} price data for volume extraction...")
        asset_data_result = asset_module.get_data(str(requested_days))
        asset_ohlcv_data = asset_data_result['data']

        if not asset_ohlcv_data:
            raise ValueError(f"No {asset.upper()} price data available for volume extraction")

        print(f"[Volume {asset.upper()}] Extracting volume from {len(asset_ohlcv_data)} price data points...")

        # Extract volume from OHLCV data
        extracted_volume = extract_volume_from_ohlcv(asset_ohlcv_data)

        if not extracted_volume:
            raise ValueError("Volume extraction returned no data")

        print(f"[Volume {asset.upper()}] Extracted {len(extracted_volume)} volume data points")

        # Merge with historical data
        merged_data = merge_and_deduplicate(
            existing_data=historical_data,
            new_data=extracted_volume,
            overlap_days=requested_days
        )

        # Validate data structure
        is_valid, structure_type, error_msg = validate_data_structure(merged_data)
        if not is_valid:
            print(f"[Volume {asset.upper()}] Warning: Data validation failed: {error_msg}")

        # Save complete historical dataset
        save_historical_data(dataset_name, merged_data)

        # Filter to requested days
        if days != 'max':
            cutoff_date = datetime.now(tz=timezone.utc) - timedelta(days=int(days))
            cutoff_ms = int(cutoff_date.timestamp() * 1000)
            filtered_data = [d for d in merged_data if d[0] >= cutoff_ms]
        else:
            filtered_data = merged_data

        print(f"[Volume {asset.upper()}] Returning {len(filtered_data)} volume data points")
        if filtered_data:
            print(f"[Volume {asset.upper()}] Date range: {datetime.fromtimestamp(filtered_data[0][0]/1000, tz=timezone.utc).date()} to {datetime.fromtimestamp(filtered_data[-1][0]/1000, tz=timezone.utc).date()}")

            # Check if all volumes are zero (like for Gold)
            volumes = [d[1] for d in filtered_data]
            if all(v == 0 for v in volumes):
                print(f"[Volume {asset.upper()}] Note: All volume values are zero (expected for Gold)")
            else:
                print(f"[Volume {asset.upper()}] Volume range: {min(volumes):.0f} to {max(volumes):.0f}")

        return {
            'metadata': metadata,
            'data': filtered_data,
            'structure': 'simple'
        }

    except Exception as e:
        print(f"[Volume {asset.upper()}] Error in get_data: {e}")

        # Fallback to historical data
        historical_data = load_historical_data(dataset_name)
        if historical_data:
            print(f"[Volume {asset.upper()}] Falling back to historical data ({len(historical_data)} records)")

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

        print(f"[Volume {asset.upper()}] No historical data available for fallback")
        return {
            'metadata': metadata,
            'data': [],
            'structure': 'simple'
        }
