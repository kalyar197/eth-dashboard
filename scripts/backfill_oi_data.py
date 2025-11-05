"""
Backfill script for OI (Open Interest) Daily Change Rate from CoinAPI.

Data Source: CoinAPI Metrics API
Metric: DERIVATIVES_OPEN_INTEREST
Time Range: 3 years of historical data
Output File: historical_data/oi_daily_change_btc.json

OI Daily Change Calculation:
    - Fetch OI values for each day
    - Calculate percentage change: (OI_today - OI_yesterday) / OI_yesterday * 100
    - First day has 0% change (no previous value)
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import COINAPI_KEY

# Configuration
SYMBOL_ID = "BINANCEFTS_PERP_BTC_USDT"  # Binance USDT-margined perpetual futures
METRIC_ID = "DERIVATIVES_OPEN_INTEREST"
YEARS_OF_DATA = 3
OUTPUT_DIR = Path(__file__).parent.parent / "historical_data"
OUTPUT_FILE = OUTPUT_DIR / "oi_daily_change_btc.json"

# CoinAPI endpoint
COINAPI_BASE = "https://rest.coinapi.io/v1"
HEADERS = {"X-CoinAPI-Key": COINAPI_KEY}


def fetch_oi_history(start_date, end_date):
    """
    Fetch OI history from CoinAPI.

    Args:
        start_date: datetime.date object
        end_date: datetime.date object

    Returns:
        List of dicts with 'time_period_start' and 'value_close' keys
    """
    # Format dates as ISO 8601
    start_str = start_date.strftime("%Y-%m-%dT00:00:00")
    end_str = end_date.strftime("%Y-%m-%dT23:59:59")

    url = f"{COINAPI_BASE}/metrics/symbol/history"
    params = {
        "metric_id": METRIC_ID,
        "symbol_id": SYMBOL_ID,
        "period_id": "1DAY",
        "time_start": start_str,
        "time_end": end_str,
        "limit": 10000
    }

    print(f"Fetching OI data from CoinAPI...")
    print(f"URL: {url}")
    print(f"Symbol: {SYMBOL_ID}")
    print(f"Metric: {METRIC_ID}")
    print(f"Period: 1DAY")
    print(f"Range: {start_str} to {end_str}")

    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()
        print(f"[OK] Received {len(data)} data points from CoinAPI")
        return data

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Error fetching OI data: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response body: {e.response.text[:500]}")
        return []


def calculate_daily_change(oi_data):
    """
    Calculate daily percentage change from OI data.

    Args:
        oi_data: List of dicts from CoinAPI with 'time_period_start' and 'value_close'

    Returns:
        List of [timestamp_ms, daily_change_pct] pairs
    """
    if not oi_data:
        return []

    # Sort by time
    sorted_data = sorted(oi_data, key=lambda x: x['time_period_start'])

    result = []
    prev_oi = None

    for entry in sorted_data:
        timestamp_str = entry['time_period_start']
        oi_value = entry.get('value_close')

        if oi_value is None:
            continue

        # Parse timestamp
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        timestamp_ms = int(dt.timestamp() * 1000)

        # Calculate daily change
        if prev_oi is None:
            # First day: 0% change
            daily_change_pct = 0.0
        else:
            daily_change_pct = ((oi_value - prev_oi) / prev_oi) * 100

        result.append([timestamp_ms, daily_change_pct])
        prev_oi = oi_value

    return result


def backfill_oi_data():
    """
    Main backfill function for OI Daily Change.
    """
    print("=" * 60)
    print("OI DAILY CHANGE BACKFILL")
    print("=" * 60)
    print(f"Output: {OUTPUT_FILE}")
    print(f"Years: {YEARS_OF_DATA}")
    print()

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Calculate date range (3 years back from today)
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=YEARS_OF_DATA * 365)

    print(f"Date range: {start_date} to {end_date}")
    print()

    # Fetch OI history
    oi_data = fetch_oi_history(start_date, end_date)

    if not oi_data:
        print("[ERROR] No data received. Aborting.")
        return

    # Calculate daily change
    print("\nCalculating daily percentage changes...")
    daily_change_data = calculate_daily_change(oi_data)

    if not daily_change_data:
        print("[ERROR] No daily change data calculated. Aborting.")
        return

    print(f"[OK] Calculated {len(daily_change_data)} daily change values")

    # Calculate statistics
    changes = [d[1] for d in daily_change_data]
    min_change = min(changes)
    max_change = max(changes)
    avg_change = sum(changes) / len(changes)

    print()
    print("Statistics:")
    print(f"  Data points: {len(daily_change_data)}")
    print(f"  Date range: {datetime.fromtimestamp(daily_change_data[0][0]/1000).date()} to {datetime.fromtimestamp(daily_change_data[-1][0]/1000).date()}")
    print(f"  Min change: {min_change:.2f}%")
    print(f"  Max change: {max_change:.2f}%")
    print(f"  Avg change: {avg_change:.2f}%")

    # Save to file
    print(f"\nSaving to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(daily_change_data, f, indent=2)

    print("[DONE] Backfill complete!")


if __name__ == "__main__":
    backfill_oi_data()
