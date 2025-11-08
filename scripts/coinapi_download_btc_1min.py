#!/usr/bin/env python3
"""
CoinAPI Bulk Download Script: BTC 1-Minute OHLCV Data
Downloads 5 years of Bitcoin 1-minute candles before subscription expires.

Strategy:
- Date range: 2020-01-01 to 2025-01-08 (5 years)
- Chunk size: 69 days (~100K minutes per request)
- Credits per request: 10 (date-bounded cap)
- Total requests: 27
- Total credits: 270
"""

import requests
import json
import time
import os
import sys
import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add parent directory to path for config import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import COINAPI_KEY

# Configuration
BASE_URL = 'https://rest.coinapi.io/v1/ohlcv'
SYMBOL_ID = 'BINANCE_SPOT_BTC_USDT'
PERIOD_ID = '1MIN'
CHUNK_DAYS = 69  # ~100K minutes per request
RATE_LIMIT_DELAY = 2  # seconds between requests

# Date range
START_DATE = datetime(2020, 1, 1, tzinfo=timezone.utc)
END_DATE = datetime(2025, 1, 8, tzinfo=timezone.utc)

# Output paths
CHUNK_DIR = Path('historical_data/btc_1min')
MERGED_FILE = Path('historical_data/btc_price_1min.json')

# Headers
HEADERS = {'X-CoinAPI-Key': COINAPI_KEY}


def ensure_directories():
    """Create output directories if they don't exist."""
    CHUNK_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[OK] Output directory: {CHUNK_DIR}")


def download_chunk(start_date, end_date, chunk_num, total_chunks):
    """
    Download a single chunk of OHLCV data.

    Args:
        start_date: Chunk start datetime
        end_date: Chunk end datetime
        chunk_num: Current chunk number
        total_chunks: Total number of chunks

    Returns:
        List of OHLCV records or None if failed
    """
    url = f'{BASE_URL}/{SYMBOL_ID}/history'

    params = {
        'period_id': PERIOD_ID,
        'time_start': start_date.strftime('%Y-%m-%dT%H:%M:%S'),
        'time_end': end_date.strftime('%Y-%m-%dT%H:%M:%S'),
        'limit': 100000
    }

    print(f"\n[{chunk_num}/{total_chunks}] Downloading: {start_date.date()} to {end_date.date()}")
    print(f"[API] {url}")
    print(f"[Params] {params}")

    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=60)
        response.raise_for_status()

        data = response.json()

        if not data:
            print(f"[WARNING] No data returned for chunk {chunk_num}")
            return []

        # Convert to OHLCV format [timestamp_ms, open, high, low, close, volume]
        ohlcv_data = []
        for candle in data:
            timestamp_str = candle.get('time_period_start')
            open_price = candle.get('price_open')
            high_price = candle.get('price_high')
            low_price = candle.get('price_low')
            close_price = candle.get('price_close')
            volume = candle.get('volume_traded')

            if all(v is not None for v in [timestamp_str, open_price, high_price, low_price, close_price, volume]):
                dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                timestamp_ms = int(dt.timestamp() * 1000)

                ohlcv_data.append([
                    timestamp_ms,
                    float(open_price),
                    float(high_price),
                    float(low_price),
                    float(close_price),
                    float(volume)
                ])

        ohlcv_data.sort(key=lambda x: x[0])

        print(f"[OK] Received {len(ohlcv_data)} records")
        if ohlcv_data:
            first_dt = datetime.fromtimestamp(ohlcv_data[0][0] / 1000, tz=timezone.utc)
            last_dt = datetime.fromtimestamp(ohlcv_data[-1][0] / 1000, tz=timezone.utc)
            print(f"[Range] {first_dt} to {last_dt}")
            print(f"[Sample] O=${ohlcv_data[0][1]:.2f} H=${ohlcv_data[0][2]:.2f} L=${ohlcv_data[0][3]:.2f} C=${ohlcv_data[0][4]:.2f}")

        return ohlcv_data

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] API request failed: {e}")
        return None
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return None


def save_chunk(data, start_date, chunk_num):
    """Save chunk to JSON file."""
    filename = CHUNK_DIR / f"chunk_{chunk_num:03d}_{start_date.strftime('%Y-%m-%d')}.json"

    with open(filename, 'w') as f:
        json.dump(data, f)

    print(f"[SAVED] {filename} ({len(data)} records)")


def merge_chunks():
    """Merge all chunks into a single file."""
    print("\n" + "="*80)
    print("MERGING CHUNKS")
    print("="*80)

    all_data = []
    chunk_files = sorted(CHUNK_DIR.glob('chunk_*.json'))

    for chunk_file in chunk_files:
        with open(chunk_file, 'r') as f:
            chunk_data = json.load(f)
            all_data.extend(chunk_data)
            print(f"[Loaded] {chunk_file.name}: {len(chunk_data)} records")

    # Sort by timestamp and deduplicate
    all_data.sort(key=lambda x: x[0])

    # Deduplicate by timestamp (keep first occurrence)
    seen_timestamps = set()
    deduplicated = []
    duplicates = 0

    for record in all_data:
        ts = record[0]
        if ts not in seen_timestamps:
            seen_timestamps.add(ts)
            deduplicated.append(record)
        else:
            duplicates += 1

    print(f"\n[Deduplication] Removed {duplicates} duplicate records")
    print(f"[Total] {len(deduplicated)} unique records")

    # Save merged file
    with open(MERGED_FILE, 'w') as f:
        json.dump(deduplicated, f)

    print(f"[SAVED] {MERGED_FILE}")

    return deduplicated


def generate_report(merged_data, total_requests, total_credits):
    """Generate download summary report."""
    print("\n" + "="*80)
    print("DOWNLOAD SUMMARY")
    print("="*80)

    if merged_data:
        first_ts = merged_data[0][0]
        last_ts = merged_data[-1][0]
        first_dt = datetime.fromtimestamp(first_ts / 1000, tz=timezone.utc)
        last_dt = datetime.fromtimestamp(last_ts / 1000, tz=timezone.utc)
        days_covered = (last_dt - first_dt).days

        print(f"Total Records: {len(merged_data):,}")
        print(f"Date Range: {first_dt.date()} to {last_dt.date()}")
        print(f"Days Covered: {days_covered}")
        print(f"Expected Records: ~{days_covered * 1440:,} (1440 per day)")
        print(f"Data Coverage: {len(merged_data) / (days_covered * 1440) * 100:.1f}%")

        print(f"\nAPI Usage:")
        print(f"Total Requests: {total_requests}")
        print(f"Credits Used: {total_credits}")
        print(f"Credits Remaining: ~{1000 - total_credits} (estimated)")

        print(f"\nFile Locations:")
        print(f"Chunks: {CHUNK_DIR}/ ({len(list(CHUNK_DIR.glob('chunk_*.json')))} files)")
        print(f"Merged: {MERGED_FILE} ({MERGED_FILE.stat().st_size / 1024 / 1024:.1f} MB)")
    else:
        print("[ERROR] No data to report")


def main():
    """Main execution function."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Download BTC 1-minute OHLCV data from CoinAPI')
    parser.add_argument('--yes', '-y', action='store_true', help='Skip confirmation prompt')
    args = parser.parse_args()

    print("="*80)
    print("COINAPI BULK DOWNLOAD: BTC 1-MINUTE DATA (5 YEARS)")
    print("="*80)
    print(f"Date Range: {START_DATE.date()} to {END_DATE.date()}")
    print(f"Chunk Size: {CHUNK_DAYS} days (~100K minutes)")
    print(f"Symbol: {SYMBOL_ID}")
    print(f"Period: {PERIOD_ID}")
    print(f"API Key: {'*' * 20}{COINAPI_KEY[-4:] if COINAPI_KEY else 'NOT SET'}")

    if not COINAPI_KEY:
        print("\n[ERROR] COINAPI_KEY not found in config.py")
        sys.exit(1)

    ensure_directories()

    # Calculate chunks
    current_date = START_DATE
    chunks = []

    while current_date < END_DATE:
        chunk_end = min(current_date + timedelta(days=CHUNK_DAYS), END_DATE)
        chunks.append((current_date, chunk_end))
        current_date = chunk_end

    total_chunks = len(chunks)
    total_credits_estimated = total_chunks * 10

    print(f"\nTotal Chunks: {total_chunks}")
    print(f"Estimated Credits: {total_credits_estimated}")
    print(f"Estimated Time: ~{total_chunks * (RATE_LIMIT_DELAY + 3) / 60:.1f} minutes")

    # Confirm before proceeding (unless --yes flag is used)
    if not args.yes:
        print("\n" + "="*80)
        response = input("Proceed with download? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("[ABORTED] Download cancelled by user")
            sys.exit(0)
    else:
        print("\n[Auto-confirmed] Proceeding with download (--yes flag)")

    # Download chunks
    print("\n" + "="*80)
    print("DOWNLOADING CHUNKS")
    print("="*80)

    successful_chunks = 0
    failed_chunks = []

    for chunk_num, (start, end) in enumerate(chunks, 1):
        data = download_chunk(start, end, chunk_num, total_chunks)

        if data is not None:
            save_chunk(data, start, chunk_num)
            successful_chunks += 1
        else:
            failed_chunks.append(chunk_num)
            print(f"[FAILED] Chunk {chunk_num}")

        # Rate limiting
        if chunk_num < total_chunks:
            print(f"[Wait] {RATE_LIMIT_DELAY}s...")
            time.sleep(RATE_LIMIT_DELAY)

    print(f"\n[Complete] {successful_chunks}/{total_chunks} chunks downloaded successfully")

    if failed_chunks:
        print(f"[Warning] Failed chunks: {failed_chunks}")

    # Merge chunks
    merged_data = merge_chunks()

    # Generate report
    actual_credits = successful_chunks * 10
    generate_report(merged_data, successful_chunks, actual_credits)

    print("\n" + "="*80)
    print("DOWNLOAD COMPLETE!")
    print("="*80)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[ABORTED] Download interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
