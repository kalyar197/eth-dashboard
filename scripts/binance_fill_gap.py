#!/usr/bin/env python3
"""
Binance Gap Filler: Fill missing BTC 1-minute data from Jan 7, 2025 to now
Uses FREE Binance API (no key required, unlimited for spot markets)
"""

import requests
import json
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Configuration
BINANCE_BASE = 'https://api.binance.com'
SYMBOL = 'BTCUSDT'
INTERVAL = '1m'
LIMIT = 1000  # Binance max per request

# Files
HISTORICAL_FILE = Path('historical_data/btc_price_1min.json')
OUTPUT_FILE = Path('historical_data/btc_price_1min_complete.json')

def get_last_timestamp():
    """Get the last timestamp from existing data."""
    try:
        with open(HISTORICAL_FILE, 'r') as f:
            data = json.load(f)
        if data:
            last_ts = data[-1][0]
            last_dt = datetime.fromtimestamp(last_ts / 1000, tz=timezone.utc)
            print(f"[Last Record] {last_dt} (timestamp: {last_ts})")
            return last_ts
        return None
    except Exception as e:
        print(f"[ERROR] Failed to read historical file: {e}")
        return None


def fetch_binance_klines(start_time, end_time=None):
    """
    Fetch klines from Binance.

    Args:
        start_time: Unix timestamp in milliseconds
        end_time: Unix timestamp in milliseconds (optional)

    Returns:
        List of [timestamp, open, high, low, close, volume]
    """
    url = f"{BINANCE_BASE}/api/v3/klines"

    params = {
        'symbol': SYMBOL,
        'interval': INTERVAL,
        'startTime': start_time,
        'limit': LIMIT
    }

    if end_time:
        params['endTime'] = end_time

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()

        klines = response.json()

        # Convert to our format [timestamp, open, high, low, close, volume]
        ohlcv = []
        for k in klines:
            ohlcv.append([
                int(k[0]),  # timestamp
                float(k[1]),  # open
                float(k[2]),  # high
                float(k[3]),  # low
                float(k[4]),  # close
                float(k[5])   # volume
            ])

        return ohlcv

    except Exception as e:
        print(f"[ERROR] Binance API error: {e}")
        return []


def fill_gap():
    """Fill the gap from last historical record to now."""
    print("="*80)
    print("BINANCE GAP FILLER: BTC 1-MINUTE DATA")
    print("="*80)

    # Get last timestamp
    last_ts = get_last_timestamp()
    if not last_ts:
        print("[ERROR] No historical data found!")
        return

    # Start from next minute
    start_ts = last_ts + 60000  # Add 1 minute
    end_ts = int(datetime.now(tz=timezone.utc).timestamp() * 1000)

    start_dt = datetime.fromtimestamp(start_ts / 1000, tz=timezone.utc)
    end_dt = datetime.fromtimestamp(end_ts / 1000, tz=timezone.utc)

    print(f"\n[Gap] {start_dt} to {end_dt}")

    total_minutes = (end_ts - start_ts) // 60000
    total_requests = (total_minutes // LIMIT) + 1

    print(f"[Gap Size] {total_minutes:,} minutes ({total_minutes/1440:.1f} days)")
    print(f"[Requests] ~{total_requests} needed (1000 bars each)")
    print(f"[Estimated Time] ~{total_requests * 1:.0f} seconds\n")

    # Fetch in chunks
    all_data = []
    current_ts = start_ts
    request_count = 0

    while current_ts < end_ts:
        request_count += 1

        print(f"[{request_count}/{total_requests}] Fetching from {datetime.fromtimestamp(current_ts/1000, tz=timezone.utc).date()}...", end='')

        chunk = fetch_binance_klines(current_ts, end_ts)

        if not chunk:
            print(" FAILED")
            break

        all_data.extend(chunk)
        print(f" {len(chunk)} bars")

        # Update current timestamp to last received + 1 minute
        if chunk:
            current_ts = chunk[-1][0] + 60000
        else:
            break

        # Rate limiting (conservative)
        time.sleep(0.5)

    print(f"\n[Downloaded] {len(all_data):,} new bars")

    # Load existing data
    with open(HISTORICAL_FILE, 'r') as f:
        existing_data = json.load(f)

    print(f"[Existing] {len(existing_data):,} bars")

    # Merge
    combined = existing_data + all_data

    # Deduplicate by timestamp
    seen = set()
    unique_data = []
    duplicates = 0

    for record in combined:
        ts = record[0]
        if ts not in seen:
            seen.add(ts)
            unique_data.append(record)
        else:
            duplicates += 1

    # Sort by timestamp
    unique_data.sort(key=lambda x: x[0])

    print(f"[Deduplicated] Removed {duplicates} duplicates")
    print(f"[Total] {len(unique_data):,} unique bars")

    # Save
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(unique_data, f)

    print(f"[SAVED] {OUTPUT_FILE}")

    # Stats
    if unique_data:
        first_dt = datetime.fromtimestamp(unique_data[0][0]/1000, tz=timezone.utc)
        last_dt = datetime.fromtimestamp(unique_data[-1][0]/1000, tz=timezone.utc)
        days = (last_dt - first_dt).days

        print(f"\n[Final Dataset]")
        print(f"  Range: {first_dt.date()} to {last_dt.date()}")
        print(f"  Days: {days}")
        print(f"  Records: {len(unique_data):,}")
        print(f"  Coverage: {len(unique_data) / (days * 1440) * 100:.2f}%")
        print(f"  File Size: {OUTPUT_FILE.stat().st_size / 1024 / 1024:.1f} MB")

    print(f"\n{'='*80}")
    print("GAP FILLED!")
    print(f"{'='*80}")

    return unique_data


if __name__ == '__main__':
    try:
        fill_gap()
    except KeyboardInterrupt:
        print("\n\n[ABORTED]")
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()
