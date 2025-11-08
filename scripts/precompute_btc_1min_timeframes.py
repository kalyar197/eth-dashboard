"""
Pre-compute all timeframes from 1-minute BTC data
Generates and saves: 1m, 15m, 1h, 4h OHLCV data
Run this script once to generate all timeframe files
"""

import json
import pandas as pd
from datetime import datetime, timezone
import os

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_FILE = os.path.join(BASE_DIR, 'historical_data', 'btc_price_1min_complete.json')  # Use COMPLETE file (3M records)
OUTPUT_DIR = os.path.join(BASE_DIR, 'historical_data', 'btc_1min')

# Timeframe configurations
TIMEFRAMES = {
    '1m': '1T',    # Already have this, but include for completeness
    '15m': '15T',
    '1h': '1H',
    '4h': '4H'
}

def load_1min_data():
    """Load 1-minute BTC data"""
    print(f"Loading 1-minute data from {INPUT_FILE}...")

    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(f"1-minute data file not found: {INPUT_FILE}")

    with open(INPUT_FILE, 'r') as f:
        data = json.load(f)

    print(f"Loaded {len(data)} 1-minute candles")

    # Get date range
    first_date = datetime.fromtimestamp(data[0][0] / 1000, tz=timezone.utc)
    last_date = datetime.fromtimestamp(data[-1][0] / 1000, tz=timezone.utc)
    print(f"Date range: {first_date} to {last_date}")

    return data

def resample_to_timeframe(data, timeframe_label, resample_rule):
    """
    Resample 1-minute data to specified timeframe

    Args:
        data: 1-minute OHLCV data
        timeframe_label: Label for output file (e.g., '15m', '1h')
        resample_rule: Pandas resample rule (e.g., '15T', '1H')

    Returns:
        Resampled OHLCV data
    """
    print(f"\nResampling to {timeframe_label}...")

    # Convert to DataFrame
    df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

    # Note: Source 1-minute data is already clean with zero None values
    # No dropna() needed - preserves raw data integrity

    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
    df.set_index('timestamp', inplace=True)

    # Resample with OHLCV aggregation
    ohlc_dict = {
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }

    if timeframe_label == '1m':
        # No resampling needed for 1m
        df_resampled = df
    else:
        df_resampled = df.resample(resample_rule).agg(ohlc_dict)
        df_resampled.dropna(inplace=True)

    # Convert back to list format
    result = []
    for timestamp, row in df_resampled.iterrows():
        result.append([
            int(timestamp.timestamp() * 1000),
            float(row['open']),
            float(row['high']),
            float(row['low']),
            float(row['close']),
            float(row['volume'])
        ])

    print(f"Resampled to {len(result)} {timeframe_label} candles")

    # Get date range
    if result:
        first_date = datetime.fromtimestamp(result[0][0] / 1000, tz=timezone.utc)
        last_date = datetime.fromtimestamp(result[-1][0] / 1000, tz=timezone.utc)
        print(f"Date range: {first_date} to {last_date}")

    return result

def save_timeframe_data(data, timeframe_label):
    """Save resampled data to file"""
    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    output_file = os.path.join(OUTPUT_DIR, f'btc_price_{timeframe_label}.json')

    print(f"Saving to {output_file}...")
    with open(output_file, 'w') as f:
        json.dump(data, f)

    # Get file size
    file_size_mb = os.path.getsize(output_file) / (1024 * 1024)
    print(f"Saved {len(data)} records ({file_size_mb:.2f} MB)")

def main():
    """Pre-compute all timeframes"""
    print("=" * 60)
    print("BTC 1-Minute Data Pre-computation")
    print("=" * 60)

    # Load 1-minute data
    data_1m = load_1min_data()

    # Process each timeframe
    for timeframe_label, resample_rule in TIMEFRAMES.items():
        try:
            # Resample
            resampled_data = resample_to_timeframe(data_1m, timeframe_label, resample_rule)

            # Save
            save_timeframe_data(resampled_data, timeframe_label)

        except Exception as e:
            print(f"Error processing {timeframe_label}: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print("Pre-computation complete!")
    print("=" * 60)
    print(f"\nGenerated files in: {OUTPUT_DIR}")
    print("\nTimeframes available:")
    for tf in TIMEFRAMES.keys():
        file_path = os.path.join(OUTPUT_DIR, f'btc_price_{tf}.json')
        if os.path.exists(file_path):
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            print(f"  - {tf}: {size_mb:.2f} MB")

if __name__ == '__main__':
    main()
