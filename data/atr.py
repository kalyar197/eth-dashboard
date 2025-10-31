# data/atr.py
"""
ATR (Average True Range) Indicator

Calculates ATR from asset OHLC data with incremental fetching.
ATR measures market volatility on an absolute price scale.

Formula:
- True Range (TR) = max(high - low, |high - prev_close|, |low - prev_close|)
- ATR = Wilder's smooth of TR over period (default: 14)

Standard period: 14

Interpretation:
- Higher ATR = Higher volatility / larger price movements
- Lower ATR = Lower volatility / smaller price movements
- ATR is expressed in same units as price (e.g., USD for BTC)
- Rising ATR suggests increasing volatility
- Falling ATR suggests decreasing volatility

Usage:
- Position sizing: Larger ATR → smaller position size
- Stop-loss placement: Use multiple of ATR (e.g., 2× ATR)
- Breakout confirmation: High ATR confirms genuine breakout
"""

import numpy as np
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
        'label': f'ATR ({asset_name})',
        'oscillator': True,
        'yAxisId': 'oscillator',
        'yAxisLabel': 'ATR (Volatility)',
        'unit': '$',
        'chartType': 'line',
        'color': '#FF5722',  # Deep Orange
        'strokeWidth': 2,
        'description': f'Average True Range for {asset_name} - Measures market volatility',
        'data_structure': 'simple',
        'components': ['timestamp', 'atr_value']
    }


def wilder_smooth(values, period):
    """
    Apply Wilder's smoothing (modified EMA).

    Formula: smooth[t] = (smooth[t-1] * (period - 1) + value[t]) / period

    Args:
        values (list): List of values to smooth
        period (int): Smoothing period

    Returns:
        list: Smoothed values (first 'period' values will be None, then SMA, then Wilder smooth)
    """
    if len(values) < period:
        return [None] * len(values)

    smoothed = [None] * (period - 1)

    # First smoothed value is simple average
    first_smooth = np.mean(values[:period])
    smoothed.append(first_smooth)

    # Subsequent values use Wilder's smoothing
    for i in range(period, len(values)):
        smooth = (smoothed[-1] * (period - 1) + values[i]) / period
        smoothed.append(smooth)

    return smoothed


def calculate_atr(high, low, close, period=14):
    """
    Calculate ATR (Average True Range).

    Args:
        high (list): List of high prices
        low (list): List of low prices
        close (list): List of closing prices
        period (int): ATR period (default: 14)

    Returns:
        list: ATR values (first 'period' values will be None)
    """
    if len(high) < period + 1 or len(low) < period + 1 or len(close) < period + 1:
        return [None] * len(high)

    n = len(high)

    # Calculate True Range for each bar
    true_ranges = []

    for i in range(1, n):
        # True Range = max(high - low, |high - prev_close|, |low - prev_close|)
        tr = max(
            high[i] - low[i],
            abs(high[i] - close[i-1]),
            abs(low[i] - close[i-1])
        )
        true_ranges.append(tr)

    # Apply Wilder's smoothing to True Range
    atr_values = wilder_smooth(true_ranges, period)

    # Add None at start to account for first bar not having a previous close
    atr = [None] + atr_values

    return atr


def calculate_atr_from_ohlcv(ohlcv_data, period=14):
    """
    Calculate ATR from OHLCV data.

    Args:
        ohlcv_data (list): [[timestamp, open, high, low, close, volume], ...]
        period (int): ATR period (default: 14)

    Returns:
        list: [[timestamp, atr_value], ...] (skips None values)
    """
    if not ohlcv_data or len(ohlcv_data) < period + 1:
        return []

    # Extract OHLC components
    high = [item[2] for item in ohlcv_data]
    low = [item[3] for item in ohlcv_data]
    close = [item[4] for item in ohlcv_data]

    # Calculate ATR
    atr_values = calculate_atr(high, low, close, period)

    # Pair timestamps with ATR values, skip None values
    result = []
    for i, item in enumerate(ohlcv_data):
        timestamp = item[0]
        atr_value = atr_values[i]

        if atr_value is not None:
            result.append([timestamp, atr_value])

    return result


def get_data(days='365', asset='btc', period=14):
    """
    Fetches ATR data using incremental fetching strategy.

    Args:
        days (str): Number of days to return ('7', '30', '180', '1095', 'max')
        asset (str): Asset name ('btc', 'eth', 'gold')
        period (int): ATR period (default: 14)

    Returns:
        dict: {
            'metadata': metadata dict,
            'data': [[timestamp, atr_value], ...],
            'structure': 'simple'
        }
    """
    metadata = get_metadata(asset)
    dataset_name = f'atr_{asset}'

    try:
        requested_days = int(days) if days != 'max' else 1095

        # Need extra days for ATR calculation (period + buffer)
        fetch_days = requested_days + period + 10

        # Load existing historical ATR data
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
        print(f"[ATR {asset.upper()}] Fetching {asset.upper()} price data for ATR calculation...")
        asset_data_result = asset_module.get_data(str(fetch_days))
        asset_ohlcv_data = asset_data_result['data']

        if not asset_ohlcv_data:
            raise ValueError(f"No {asset.upper()} price data available for ATR calculation")

        print(f"[ATR {asset.upper()}] Calculating ATR from {len(asset_ohlcv_data)} price data points...")

        # Calculate ATR from OHLCV data
        calculated_atr = calculate_atr_from_ohlcv(asset_ohlcv_data, period)

        if not calculated_atr:
            raise ValueError("ATR calculation returned no data")

        print(f"[ATR {asset.upper()}] Calculated {len(calculated_atr)} ATR values")

        # Merge with historical data
        merged_data = merge_and_deduplicate(
            existing_data=historical_data,
            new_data=calculated_atr,
            overlap_days=fetch_days
        )

        # Validate data structure
        is_valid, structure_type, error_msg = validate_data_structure(merged_data)
        if not is_valid:
            print(f"[ATR {asset.upper()}] Warning: Data validation failed: {error_msg}")

        # Save complete historical dataset
        save_historical_data(dataset_name, merged_data)

        # Filter to requested days
        if days != 'max':
            cutoff_date = datetime.now(tz=timezone.utc) - timedelta(days=int(days))
            cutoff_ms = int(cutoff_date.timestamp() * 1000)
            filtered_data = [d for d in merged_data if d[0] >= cutoff_ms]
        else:
            filtered_data = merged_data

        print(f"[ATR {asset.upper()}] Returning {len(filtered_data)} ATR data points")
        if filtered_data:
            print(f"[ATR {asset.upper()}] Date range: {datetime.fromtimestamp(filtered_data[0][0]/1000, tz=timezone.utc).date()} to {datetime.fromtimestamp(filtered_data[-1][0]/1000, tz=timezone.utc).date()}")
            values = [d[1] for d in filtered_data]
            print(f"[ATR {asset.upper()}] ATR range: ${min(values):.2f} to ${max(values):.2f}")

        return {
            'metadata': metadata,
            'data': filtered_data,
            'structure': 'simple'
        }

    except Exception as e:
        print(f"[ATR {asset.upper()}] Error in get_data: {e}")

        # Fallback to historical data if available
        historical_data = load_historical_data(dataset_name)
        if historical_data:
            print(f"[ATR {asset.upper()}] Falling back to historical data ({len(historical_data)} records)")

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
        print(f"[ATR {asset.upper()}] No historical data available for fallback")
        return {
            'metadata': metadata,
            'data': [],
            'structure': 'simple'
        }
