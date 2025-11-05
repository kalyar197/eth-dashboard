"""
Backfill script for Basis Spread from CoinAPI.

Data Source: CoinAPI Metrics API
Metrics: DERIVATIVES_MARK_PRICE, DERIVATIVES_INDEX_PRICE
Time Range: 3 years of historical data
Output File: historical_data/basis_spread_btc.json

Basis Spread Calculation:
    - Basis Spread = Perpetual Mark Price - Spot Index Price
    - Represents the premium/discount of perpetual futures vs spot
    - Positive = Perpetual trading at premium (bullish sentiment)
    - Negative = Perpetual trading at discount (bearish sentiment)
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
MARK_PRICE_METRIC = "DERIVATIVES_MARK_PRICE"
INDEX_PRICE_METRIC = "DERIVATIVES_INDEX_PRICE"
YEARS_OF_DATA = 3
OUTPUT_DIR = Path(__file__).parent.parent / "historical_data"
OUTPUT_FILE = OUTPUT_DIR / "basis_spread_btc.json"

# CoinAPI endpoint
COINAPI_BASE = "https://rest.coinapi.io/v1"
HEADERS = {"X-CoinAPI-Key": COINAPI_KEY}


def fetch_metric_history(metric_id, start_date, end_date):
    """
    Fetch metric history from CoinAPI.

    Args:
        metric_id: Metric identifier (DERIVATIVES_MARK_PRICE or DERIVATIVES_INDEX_PRICE)
        start_date: datetime.date object
        end_date: datetime.date object

    Returns:
        Dict mapping timestamp_ms -> value
    """
    # Format dates as ISO 8601
    start_str = start_date.strftime("%Y-%m-%dT00:00:00")
    end_str = end_date.strftime("%Y-%m-%dT23:59:59")

    url = f"{COINAPI_BASE}/metrics/symbol/history"
    params = {
        "metric_id": metric_id,
        "symbol_id": SYMBOL_ID,
        "period_id": "1DAY",
        "time_start": start_str,
        "time_end": end_str,
        "limit": 10000
    }

    print(f"Fetching {metric_id}...")
    print(f"  Range: {start_str} to {end_str}")

    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()
        print(f"  [OK] Received {len(data)} data points")

        # Convert to dict mapping timestamp -> value
        result = {}
        for entry in data:
            timestamp_str = entry['time_period_start']
            value = entry.get('value_close')

            if value is None:
                continue

            # Parse timestamp to midnight UTC
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            timestamp_ms = int(dt.replace(hour=0, minute=0, second=0, microsecond=0).timestamp() * 1000)

            result[timestamp_ms] = value

        return result

    except requests.exceptions.RequestException as e:
        print(f"  [ERROR] Error fetching {metric_id}: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"  Response status: {e.response.status_code}")
            print(f"  Response body: {e.response.text[:500]}")
        return {}


def calculate_basis_spread(mark_prices, index_prices):
    """
    Calculate basis spread from mark and index prices.

    Args:
        mark_prices: Dict mapping timestamp_ms -> mark_price
        index_prices: Dict mapping timestamp_ms -> index_price

    Returns:
        List of [timestamp_ms, basis_spread] pairs
    """
    if not mark_prices or not index_prices:
        return []

    # Find common timestamps
    common_timestamps = set(mark_prices.keys()) & set(index_prices.keys())

    if not common_timestamps:
        print("[ERROR] No overlapping timestamps between mark and index prices")
        return []

    # Calculate basis spread for each timestamp
    result = []
    for timestamp in sorted(common_timestamps):
        mark_price = mark_prices[timestamp]
        index_price = index_prices[timestamp]

        # Basis spread = mark - index
        basis_spread = mark_price - index_price

        result.append([timestamp, basis_spread])

    return result


def backfill_basis_spread():
    """
    Main backfill function for Basis Spread.
    """
    print("=" * 60)
    print("BASIS SPREAD BACKFILL")
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
    print(f"Symbol: {SYMBOL_ID}")
    print()

    # Fetch mark prices
    mark_prices = fetch_metric_history(MARK_PRICE_METRIC, start_date, end_date)

    # Fetch index prices
    index_prices = fetch_metric_history(INDEX_PRICE_METRIC, start_date, end_date)

    if not mark_prices or not index_prices:
        print("\n[ERROR] Failed to fetch required data. Aborting.")
        return

    # Calculate basis spread
    print("\nCalculating basis spread...")
    basis_spread_data = calculate_basis_spread(mark_prices, index_prices)

    if not basis_spread_data:
        print("[ERROR] No basis spread data calculated. Aborting.")
        return

    print(f"[OK] Calculated {len(basis_spread_data)} basis spread values")

    # Calculate statistics
    spreads = [d[1] for d in basis_spread_data]
    min_spread = min(spreads)
    max_spread = max(spreads)
    avg_spread = sum(spreads) / len(spreads)

    print()
    print("Statistics:")
    print(f"  Data points: {len(basis_spread_data)}")
    print(f"  Date range: {datetime.fromtimestamp(basis_spread_data[0][0]/1000).date()} to {datetime.fromtimestamp(basis_spread_data[-1][0]/1000).date()}")
    print(f"  Min spread: ${min_spread:.2f}")
    print(f"  Max spread: ${max_spread:.2f}")
    print(f"  Avg spread: ${avg_spread:.2f}")

    # Save to file
    print(f"\nSaving to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(basis_spread_data, f, indent=2)

    print("[DONE] Backfill complete!")


if __name__ == "__main__":
    backfill_basis_spread()
