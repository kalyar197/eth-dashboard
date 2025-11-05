"""
Test script to determine historical data depth for Deribit API endpoints.

Tests:
1. DVOL (Volatility Index) - BTC & ETH
2. Ticker data with IV
3. Options book summary

Goal: Find maximum historical data available for volatility metrics.
"""

import requests
from datetime import datetime, timedelta
import json

BASE_URL = "https://www.deribit.com/api/v2"

def test_dvol_history(currency, days_back=1095):
    """
    Test DVOL (Deribit Volatility Index) historical data.

    Args:
        currency: 'BTC' or 'ETH'
        days_back: Number of days to look back (default: 1095 = 3 years)
    """
    print(f"\n{'='*60}")
    print(f"Testing: DVOL Index - {currency}")
    print(f"{'='*60}")

    end_timestamp = int(datetime.now().timestamp() * 1000)
    start_timestamp = int((datetime.now() - timedelta(days=days_back)).timestamp() * 1000)

    params = {
        'currency': currency,
        'resolution': '1D',  # Daily resolution
        'start_timestamp': start_timestamp,
        'end_timestamp': end_timestamp
    }

    print(f"Request parameters:")
    print(f"  Currency: {currency}")
    print(f"  Resolution: 1D (daily)")
    print(f"  Start: {datetime.fromtimestamp(start_timestamp/1000).strftime('%Y-%m-%d')}")
    print(f"  End: {datetime.fromtimestamp(end_timestamp/1000).strftime('%Y-%m-%d')}")
    print(f"  Days requested: {days_back}")

    try:
        response = requests.get(
            f"{BASE_URL}/public/get_volatility_index_data",
            params=params
        )
        response.raise_for_status()
        data = response.json()

        if data.get('result'):
            result = data['result']

            # DVOL data structure: {'data': [[timestamp, value], ...], ...}
            if 'data' in result and isinstance(result['data'], list):
                data_points = result['data']
                print(f"\n[OK] Success! Received {len(data_points)} data points")

                if len(data_points) > 0:
                    first_point = data_points[0]
                    last_point = data_points[-1]

                    first_ts = first_point[0]
                    last_ts = last_point[0]

                    first_date = datetime.fromtimestamp(first_ts / 1000)
                    last_date = datetime.fromtimestamp(last_ts / 1000)

                    days_span = (last_date - first_date).days

                    print(f"First record: {first_date.strftime('%Y-%m-%d')} - DVOL: {first_point[1]:.2f}")
                    print(f"Last record: {last_date.strftime('%Y-%m-%d')} - DVOL: {last_point[1]:.2f}")
                    print(f"Total span: {days_span} days ({days_span / 30:.1f} months)")

                    # Show sample records
                    print(f"\nFirst 3 records:")
                    for point in data_points[:3]:
                        ts = datetime.fromtimestamp(point[0] / 1000)
                        print(f"  {ts.strftime('%Y-%m-%d')}: {point[1]:.2f}")

                    return {
                        'success': True,
                        'count': len(data_points),
                        'first_date': first_date.isoformat(),
                        'last_date': last_date.isoformat(),
                        'days_span': days_span,
                        'months_span': days_span / 30
                    }
                else:
                    print("[WARN] Empty data array")
                    return {'success': False, 'error': 'Empty data'}
            else:
                print(f"[WARN] Unexpected result structure")
                print(json.dumps(result, indent=2)[:500])
                return {'success': False, 'error': 'Unexpected structure'}
        else:
            print(f"❌ No result in response")
            print(json.dumps(data, indent=2))
            return {'success': False, 'error': 'No result field'}

    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return {'success': False, 'error': str(e)}


def test_ticker_iv(instrument='BTC-PERPETUAL'):
    """Test real-time IV data from ticker endpoint."""
    print(f"\n{'='*60}")
    print(f"Testing: Ticker IV Data - {instrument}")
    print(f"{'='*60}")

    try:
        response = requests.get(
            f"{BASE_URL}/public/ticker",
            params={'instrument_name': instrument}
        )
        response.raise_for_status()
        data = response.json()

        if data.get('result'):
            result = data['result']

            print(f"[OK] Ticker data retrieved successfully")
            print(f"\nKey fields:")
            print(f"  Last Price: ${result.get('last_price', 'N/A')}")
            print(f"  Mark Price: ${result.get('mark_price', 'N/A')}")
            print(f"  Open Interest: {result.get('open_interest', 'N/A')}")
            print(f"  Mark IV: {result.get('mark_iv', 'N/A')}")

            # Show all IV-related fields
            iv_fields = {k: v for k, v in result.items() if 'iv' in k.lower() or 'volatility' in k.lower()}
            if iv_fields:
                print(f"\nIV-related fields:")
                for key, value in iv_fields.items():
                    print(f"  {key}: {value}")

            return {'success': True, 'has_iv': 'mark_iv' in result}
        else:
            print(f"❌ No result in response")
            return {'success': False, 'error': 'No result'}

    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return {'success': False, 'error': str(e)}


def main():
    """Test all Deribit endpoints."""

    results = {}

    # Test 1: BTC DVOL History (3 years)
    results['btc_dvol'] = test_dvol_history('BTC', days_back=1095)

    # Test 2: ETH DVOL History (3 years)
    results['eth_dvol'] = test_dvol_history('ETH', days_back=1095)

    # Test 3: Real-time IV from ticker
    results['ticker_iv'] = test_ticker_iv('BTC-PERPETUAL')

    # Summary
    print(f"\n\n{'='*60}")
    print("SUMMARY - DERIBIT HISTORICAL DATA DEPTH")
    print(f"{'='*60}\n")

    for name, result in results.items():
        if result.get('success'):
            if 'months_span' in result:
                months = result['months_span']
                print(f"[OK] {name.upper()}:")
                print(f"   - Data points: {result['count']}")
                print(f"   - Time span: {months:.1f} months")
                print(f"   - Covers 36 months: {'YES' if months >= 36 else 'NO (may need multiple requests)'}")
            else:
                print(f"[OK] {name.upper()}: Real-time data available")
        else:
            print(f"[ERROR] {name.upper()}: {result.get('error', 'Unknown error')}")
        print()

    # Determine if stitching is needed
    dvol_results = [r for k, r in results.items() if 'dvol' in k and r.get('success')]
    if dvol_results:
        max_months = max([r.get('months_span', 0) for r in dvol_results])

        print(f"{'='*60}")
        if max_months >= 36:
            print("NO STITCHING NEEDED - Single request covers 36 months!")
        else:
            print(f"Historical depth: {max_months:.1f} months")
            print(f"   - For 36 months: May need multiple requests or limited data")
            print(f"   - Recommendation: Use available data depth as-is")
        print(f"{'='*60}")


if __name__ == "__main__":
    main()
