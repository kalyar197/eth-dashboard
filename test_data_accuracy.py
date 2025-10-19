# -*- coding: utf-8 -*-
"""
Comprehensive Data Accuracy Verification Test
Tests buffer trimming and compares our data against external sources
"""

import requests
import random
from datetime import datetime, timedelta
import time
import sys

# Configure UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = 'http://127.0.0.1:5000'

def print_header(text):
    """Print a styled header"""
    print("\n" + "="*80)
    print(f"  {text}")
    print("="*80)

def print_section(text):
    """Print a section header"""
    print(f"\n{'─'*80}")
    print(f"  {text}")
    print(f"{'─'*80}")

def print_result(passed, message):
    """Print test result with emoji"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {message}")

def fetch_our_data(dataset, days=30):
    """Fetch data from our API"""
    try:
        response = requests.get(f'{BASE_URL}/api/data?dataset={dataset}&days={days}')
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching {dataset}: {e}")
        return None

def fetch_coingecko_btc():
    """Fetch BTC price from CoinGecko (free, no API key)"""
    try:
        # Get last 30 days of BTC prices
        url = 'https://api.coingecko.com/api/v3/coins/bitcoin/market_chart'
        params = {'vs_currency': 'usd', 'days': '30', 'interval': 'daily'}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Convert to our format: [[timestamp_ms, price], ...]
        prices = [[int(point[0]), point[1]] for point in data['prices']]
        return prices
    except Exception as e:
        print(f"Error fetching CoinGecko data: {e}")
        return None

def fetch_coingecko_eth_btc():
    """Calculate ETH/BTC ratio from CoinGecko"""
    try:
        # Fetch ETH prices
        eth_url = 'https://api.coingecko.com/api/v3/coins/ethereum/market_chart'
        eth_params = {'vs_currency': 'usd', 'days': '30', 'interval': 'daily'}
        eth_response = requests.get(eth_url, params=eth_params, timeout=10)
        eth_response.raise_for_status()
        eth_data = eth_response.json()

        time.sleep(1)  # Rate limiting

        # Fetch BTC prices
        btc_url = 'https://api.coingecko.com/api/v3/coins/bitcoin/market_chart'
        btc_params = {'vs_currency': 'usd', 'days': '30', 'interval': 'daily'}
        btc_response = requests.get(btc_url, params=btc_params, timeout=10)
        btc_response.raise_for_status()
        btc_data = btc_response.json()

        # Calculate ratio
        eth_prices = {int(p[0]): p[1] for p in eth_data['prices']}
        btc_prices = {int(p[0]): p[1] for p in btc_data['prices']}

        ratios = []
        for timestamp, eth_price in eth_prices.items():
            if timestamp in btc_prices and btc_prices[timestamp] > 0:
                ratio = eth_price / btc_prices[timestamp]
                ratios.append([timestamp, ratio])

        return sorted(ratios, key=lambda x: x[0])
    except Exception as e:
        print(f"Error calculating ETH/BTC from CoinGecko: {e}")
        return None

def test_buffer_trimming():
    """Test that buffered indicators don't leak buffer data"""
    print_header("TEST 1: Buffer Trimming Verification")

    days_requested = 30

    # Test RSI
    print_section("RSI Buffer Test")
    rsi_data = fetch_our_data('rsi', days_requested)
    btc_data = fetch_our_data('btc', days_requested)

    if rsi_data and btc_data:
        rsi_points = len(rsi_data['data'])
        btc_points = len(btc_data['data'])

        # RSI should have roughly the same number of points as BTC (may be slightly less due to first valid RSI)
        difference = abs(rsi_points - btc_points)
        passed = difference <= 1  # Allow 1 day difference

        print_result(passed, f"RSI has {rsi_points} points, BTC has {btc_points} points (diff: {difference})")

        if rsi_data['data'] and btc_data['data']:
            # Check date ranges
            rsi_first_date = datetime.fromtimestamp(rsi_data['data'][0][0] / 1000).strftime('%Y-%m-%d')
            rsi_last_date = datetime.fromtimestamp(rsi_data['data'][-1][0] / 1000).strftime('%Y-%m-%d')
            btc_last_date = datetime.fromtimestamp(btc_data['data'][-1][0] / 1000).strftime('%Y-%m-%d')

            print(f"    RSI date range: {rsi_first_date} to {rsi_last_date}")
            print(f"    BTC last date: {btc_last_date}")
            print_result(rsi_last_date == btc_last_date, "RSI and BTC end on same date")

    # Test Bollinger Bands
    print_section("Bollinger Bands Buffer Test")
    bb_data = fetch_our_data('bollinger_bands', days_requested)

    if bb_data and btc_data:
        bb_points = len(bb_data['data']['middle'])
        btc_points = len(btc_data['data'])

        difference = abs(bb_points - btc_points)
        passed = difference <= 1

        print_result(passed, f"BB has {bb_points} points, BTC has {btc_points} points (diff: {difference})")

        if bb_data['data']['middle'] and btc_data['data']:
            bb_last_date = datetime.fromtimestamp(bb_data['data']['middle'][-1][0] / 1000).strftime('%Y-%m-%d')
            btc_last_date = datetime.fromtimestamp(btc_data['data'][-1][0] / 1000).strftime('%Y-%m-%d')
            print_result(bb_last_date == btc_last_date, "BB and BTC end on same date")

    # Test VWAP
    print_section("VWAP Buffer Test")
    vwap_data = fetch_our_data('vwap', days_requested)

    if vwap_data and btc_data:
        vwap_points = len(vwap_data['data'])
        btc_points = len(btc_data['data'])

        difference = abs(vwap_points - btc_points)
        passed = difference <= 1

        print_result(passed, f"VWAP has {vwap_points} points, BTC has {btc_points} points (diff: {difference})")

    # Test ADX
    print_section("ADX Buffer Test")
    adx_data = fetch_our_data('adx', days_requested)

    if adx_data and btc_data:
        adx_points = len(adx_data['data'])
        btc_points = len(btc_data['data'])

        difference = abs(adx_points - btc_points)
        passed = difference <= 1

        print_result(passed, f"ADX has {adx_points} points, BTC has {btc_points} points (diff: {difference})")

def compare_with_external_sources():
    """Compare our data with external sources"""
    print_header("TEST 2: External Source Comparison")

    # BTC Price Comparison
    print_section("Bitcoin Price Comparison (CoinGecko)")

    our_btc = fetch_our_data('btc', 30)
    external_btc = fetch_coingecko_btc()

    if our_btc and external_btc and our_btc['data'] and external_btc:
        # Extract closing prices from our OHLCV data
        our_prices = {point[0]: point[4] for point in our_btc['data']}  # timestamp: close_price

        # Sample 5 random dates for comparison
        sample_size = min(5, len(external_btc))
        samples = random.sample(external_btc, sample_size)

        total_diff_pct = 0
        comparisons = 0

        print("\n    Random Date Comparisons:")
        for ext_timestamp, ext_price in samples:
            # Find closest match in our data (within 1 day)
            closest_timestamp = min(our_prices.keys(),
                                   key=lambda t: abs(t - ext_timestamp))

            time_diff_hours = abs(closest_timestamp - ext_timestamp) / (1000 * 60 * 60)

            if time_diff_hours <= 24:  # Within 1 day
                our_price = our_prices[closest_timestamp]
                diff_pct = abs(our_price - ext_price) / ext_price * 100
                total_diff_pct += diff_pct
                comparisons += 1

                date_str = datetime.fromtimestamp(ext_timestamp / 1000).strftime('%Y-%m-%d')
                print(f"    {date_str}:")
                print(f"      Our price:      ${our_price:,.2f}")
                print(f"      CoinGecko:      ${ext_price:,.2f}")
                print(f"      Difference:     {diff_pct:.3f}%")

        if comparisons > 0:
            avg_diff = total_diff_pct / comparisons
            passed = avg_diff < 1.0  # Less than 1% average difference
            print(f"\n    Average difference: {avg_diff:.3f}%")
            print_result(passed, f"BTC prices match within {avg_diff:.3f}% (threshold: 1%)")

    # ETH/BTC Ratio Comparison
    print_section("ETH/BTC Ratio Comparison (CoinGecko)")

    our_eth_btc = fetch_our_data('eth_btc', 30)
    external_eth_btc = fetch_coingecko_eth_btc()

    if our_eth_btc and external_eth_btc and our_eth_btc['data'] and external_eth_btc:
        our_ratios = {point[0]: point[1] for point in our_eth_btc['data']}

        # Sample 5 random dates
        sample_size = min(5, len(external_eth_btc))
        samples = random.sample(external_eth_btc, sample_size)

        total_diff_pct = 0
        comparisons = 0

        print("\n    Random Date Comparisons:")
        for ext_timestamp, ext_ratio in samples:
            closest_timestamp = min(our_ratios.keys(),
                                   key=lambda t: abs(t - ext_timestamp))

            time_diff_hours = abs(closest_timestamp - ext_timestamp) / (1000 * 60 * 60)

            if time_diff_hours <= 24:
                our_ratio = our_ratios[closest_timestamp]
                diff_pct = abs(our_ratio - ext_ratio) / ext_ratio * 100
                total_diff_pct += diff_pct
                comparisons += 1

                date_str = datetime.fromtimestamp(ext_timestamp / 1000).strftime('%Y-%m-%d')
                print(f"    {date_str}:")
                print(f"      Our ratio:      {our_ratio:.6f}")
                print(f"      CoinGecko:      {ext_ratio:.6f}")
                print(f"      Difference:     {diff_pct:.3f}%")

        if comparisons > 0:
            avg_diff = total_diff_pct / comparisons
            passed = avg_diff < 2.0  # Less than 2% for ratios (more tolerance)
            print(f"\n    Average difference: {avg_diff:.3f}%")
            print_result(passed, f"ETH/BTC ratios match within {avg_diff:.3f}% (threshold: 2%)")

def test_indexed_data():
    """Test indexed data alignment"""
    print_header("TEST 3: Indexed Data Verification")

    print_section("Common Baseline Alignment Test")

    # Fetch indexed data for multiple datasets
    indexed_btc = fetch_our_data('btc', 30)
    indexed_rsi = fetch_our_data('rsi', 30)

    if indexed_btc and indexed_rsi:
        btc_data = indexed_btc['data']
        rsi_data = indexed_rsi['data']

        if btc_data and rsi_data:
            btc_start = datetime.fromtimestamp(btc_data[0][0] / 1000).strftime('%Y-%m-%d')
            rsi_start = datetime.fromtimestamp(rsi_data[0][0] / 1000).strftime('%Y-%m-%d')

            print(f"    BTC starts: {btc_start}")
            print(f"    RSI starts: {rsi_start}")

            # RSI might start later due to calculation period
            # This is expected and correct
            btc_start_ts = btc_data[0][0]
            rsi_start_ts = rsi_data[0][0]

            # RSI should start on or after BTC
            passed = rsi_start_ts >= btc_start_ts
            print_result(passed, "RSI starts on or after BTC (expected due to calculation period)")

            # Check that they both end around the same time
            btc_end = datetime.fromtimestamp(btc_data[-1][0] / 1000).strftime('%Y-%m-%d')
            rsi_end = datetime.fromtimestamp(rsi_data[-1][0] / 1000).strftime('%Y-%m-%d')

            print(f"    BTC ends: {btc_end}")
            print(f"    RSI ends: {rsi_end}")

            passed = btc_end == rsi_end
            print_result(passed, "BTC and RSI end on the same date")

def generate_summary():
    """Generate final summary"""
    print_header("DATA ACCURACY SUMMARY")

    print("\n📊 Dataset Status:")
    print("    • BTC Price: Using CoinAPI (BINANCE_SPOT_BTC_USDT)")
    print("    • ETH/BTC Ratio: Using CoinAPI (BINANCE_SPOT_ETH_BTC)")
    print("    • Gold Price: Using FMP (ZGUSD symbol)")
    print("    • RSI: Calculated from BTC closing prices")
    print("    • Bollinger Bands: Calculated from BTC closing prices")
    print("    • VWAP: Calculated from BTC OHLCV data")
    print("    • ADX: Calculated from BTC OHLCV data")

    print("\n✅ Verification Complete!")
    print("    Check results above for any failures or discrepancies.")

def main():
    """Run all tests"""
    print("="*80)
    print("  FINANCIAL DASHBOARD DATA ACCURACY VERIFICATION")
    print("="*80)
    print(f"  Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    try:
        # Test 1: Buffer trimming
        test_buffer_trimming()

        # Test 2: External source comparison
        time.sleep(2)  # Rate limiting
        compare_with_external_sources()

        # Test 3: Indexed data
        test_indexed_data()

        # Generate summary
        generate_summary()

    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
