#!/usr/bin/env python3
"""
Binance ETH Download: 5 years of ETH 1-minute data from FREE Binance API
"""

import requests
import json
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

BINANCE_BASE = 'https://api.binance.com'
SYMBOL = 'ETHUSDT'
INTERVAL = '1m'
LIMIT = 1000

START_DATE = datetime(2020, 1, 1, tzinfo=timezone.utc)
END_DATE = datetime.now(tz=timezone.utc)
OUTPUT_FILE = Path('historical_data/eth_price_1min.json')

def download_eth():
    print("="*80)
    print("BINANCE ETH DOWNLOAD: 5 YEARS OF 1-MINUTE DATA")
    print("="*80)

    start_ts = int(START_DATE.timestamp() * 1000)
    end_ts = int(END_DATE.timestamp() * 1000)

    total_minutes = (end_ts - start_ts) // 60000
    total_requests = (total_minutes // LIMIT) + 1

    print(f"[Period] {START_DATE.date()} to {END_DATE.date()}")
    print(f"[Minutes] {total_minutes:,}")
    print(f"[Requests] {total_requests}")
    print(f"[Time] ~{total_requests * 0.5 / 60:.1f} minutes\n")

    all_data = []
    current_ts = start_ts
    count = 0

    while current_ts < end_ts:
        count += 1

        url = f"{BINANCE_BASE}/api/v3/klines"
        params = {
            'symbol': SYMBOL,
            'interval': INTERVAL,
            'startTime': current_ts,
            'endTime': end_ts,
            'limit': LIMIT
        }

        try:
            print(f"[{count}/{total_requests}] {datetime.fromtimestamp(current_ts/1000, tz=timezone.utc).date()}...", end='', flush=True)

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            klines = response.json()

            if not klines:
                print(" No data")
                break

            for k in klines:
                all_data.append([
                    int(k[0]),
                    float(k[1]),
                    float(k[2]),
                    float(k[3]),
                    float(k[4]),
                    float(k[5])
                ])

            print(f" {len(klines)} bars")

            current_ts = klines[-1][0] + 60000
            time.sleep(0.5)

        except Exception as e:
            print(f" ERROR: {e}")
            break

    # Deduplicate
    seen = set()
    unique_data = []
    for record in all_data:
        ts = record[0]
        if ts not in seen:
            seen.add(ts)
            unique_data.append(record)

    unique_data.sort(key=lambda x: x[0])

    # Save
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(unique_data, f)

    print(f"\n[SAVED] {OUTPUT_FILE}")
    print(f"[Records] {len(unique_data):,}")

    if unique_data:
        first = datetime.fromtimestamp(unique_data[0][0]/1000, tz=timezone.utc)
        last = datetime.fromtimestamp(unique_data[-1][0]/1000, tz=timezone.utc)
        print(f"[Range] {first.date()} to {last.date()}")
        print(f"[Size] {OUTPUT_FILE.stat().st_size / 1024 / 1024:.1f} MB")

    print(f"\n{'='*80}")
    print("ETH DOWNLOAD COMPLETE!")
    print(f"{'='*80}")

if __name__ == '__main__':
    download_eth()
