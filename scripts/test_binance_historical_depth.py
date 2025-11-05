"""
Test script to determine historical data depth for Binance Futures endpoints.

Tests:
1. Basis Spread - /futures/data/basis
2. Open Interest History - /futures/data/openInterestHist
3. Taker Long/Short Ratio - /futures/data/takerlongshortRatio

Goal: Find maximum historical data available and if stitching is needed for 36 months.
"""

import requests
from datetime import datetime, timedelta
import json

BASE_URL = "https://fapi.binance.com"

def test_endpoint(endpoint, params, name):
    """Test a Binance endpoint with given parameters."""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"Endpoint: {endpoint}")
    print(f"Params: {params}")
    print(f"{'='*60}")

    try:
        response = requests.get(f"{BASE_URL}{endpoint}", params=params)
        response.raise_for_status()
        data = response.json()

        if isinstance(data, list) and len(data) > 0:
            print(f"[OK] Success! Received {len(data)} data points")

            # Parse timestamps
            first_item = data[0]
            last_item = data[-1]

            # Different endpoints have different timestamp keys
            ts_key = 'timestamp' if 'timestamp' in first_item else 'time'

            if ts_key in first_item:
                first_ts = first_item[ts_key]
                last_ts = last_item[ts_key]

                first_date = datetime.fromtimestamp(first_ts / 1000)
                last_date = datetime.fromtimestamp(last_ts / 1000)

                days_span = (last_date - first_date).days

                print(f"First record: {first_date.strftime('%Y-%m-%d')}")
                print(f"Last record: {last_date.strftime('%Y-%m-%d')}")
                print(f"Total span: {days_span} days ({days_span / 30:.1f} months)")

                # Show sample data
                print(f"\nSample first record:")
                print(json.dumps(first_item, indent=2))

                return {
                    'success': True,
                    'count': len(data),
                    'first_date': first_date.isoformat(),
                    'last_date': last_date.isoformat(),
                    'days_span': days_span,
                    'months_span': days_span / 30
                }
            else:
                print(f"[WARN] No timestamp field found. Keys: {first_item.keys()}")
                print(json.dumps(first_item, indent=2))
                return {'success': False, 'error': 'No timestamp field'}
        else:
            print(f"[WARN] Unexpected response format or empty data")
            print(json.dumps(data, indent=2))
            return {'success': False, 'error': 'Empty or unexpected format'}

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Request failed: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        return {'success': False, 'error': str(e)}


def main():
    """Test all Binance derivatives endpoints."""

    results = {}

    # Test 1: Basis Spread
    results['basis'] = test_endpoint(
        endpoint="/futures/data/basis",
        params={
            'pair': 'BTCUSDT',
            'contractType': 'PERPETUAL',
            'period': '1d',  # Daily data
            'limit': 500  # Max allowed (assumption)
        },
        name="Basis Spread"
    )

    # Test 2: Open Interest History
    results['open_interest'] = test_endpoint(
        endpoint="/futures/data/openInterestHist",
        params={
            'symbol': 'BTCUSDT',
            'period': '1d',
            'limit': 500
        },
        name="Open Interest History"
    )

    # Test 3: Taker Long/Short Ratio
    results['taker_ratio'] = test_endpoint(
        endpoint="/futures/data/takerlongshortRatio",
        params={
            'symbol': 'BTCUSDT',
            'period': '1d',
            'limit': 500
        },
        name="Taker Long/Short Ratio"
    )

    # Summary
    print(f"\n\n{'='*60}")
    print("SUMMARY - BINANCE HISTORICAL DATA DEPTH")
    print(f"{'='*60}\n")

    for name, result in results.items():
        if result.get('success'):
            months = result.get('months_span', 0)
            print(f"[OK] {name.upper()}:")
            print(f"   - Data points: {result['count']}")
            print(f"   - Time span: {months:.1f} months")
            print(f"   - Covers 36 months: {'YES' if months >= 36 else 'NO (stitching needed)'}")
        else:
            print(f"[ERROR] {name.upper()}: {result.get('error', 'Unknown error')}")
        print()

    # Determine if stitching is needed
    max_months = max([r.get('months_span', 0) for r in results.values() if r.get('success')])

    print(f"{'='*60}")
    if max_months >= 36:
        print("NO STITCHING NEEDED - Single request covers 36 months!")
    else:
        needed_requests = int(36 / max_months) + 1
        print(f"STITCHING REQUIRED")
        print(f"   - Max span per request: {max_months:.1f} months")
        print(f"   - Requests needed for 36 months: ~{needed_requests}")
        print(f"   - Implementation: Loop with date ranges")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
