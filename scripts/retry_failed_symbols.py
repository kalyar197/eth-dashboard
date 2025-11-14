#!/usr/bin/env python3
"""
Retry script for failed TradingView symbols with extended delays
Focuses on BTC_RECEIVINGADDRESSES and BTC_SPLYADRBAL1
"""

import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tvDatafeed import TvDatafeed, Interval
from data.time_transformer import standardize_to_daily_utc
from data.incremental_data_manager import save_historical_data

# Load credentials from environment
from dotenv import load_dotenv
load_dotenv()

TV_USERNAME = os.getenv('TV_USERNAME')
TV_PASSWORD = os.getenv('TV_PASSWORD')

# Symbols to retry (BTC_RECEIVINGADDRESSES already succeeded)
FAILED_SYMBOLS = [
    {
        'exchange': 'COINMETRICS',
        'symbol': 'BTC_SPLYADRBAL1',
        'filename': 'btc_splyadrbal1',
        'description': 'Bitcoin Supply in Addresses with Balance >=1'
    }
]

def fetch_symbol(exchange, symbol, filename, description):
    """Fetch a single symbol with extended delays"""
    print(f"\n{'='*80}")
    print(f"Symbol: {exchange}:{symbol}")
    print(f"Description: {description}")
    print(f"{'='*80}")

    # Extra delay before starting
    print("Waiting 15 seconds before fetch...")
    time.sleep(15)

    try:
        # Initialize with login
        if TV_USERNAME and TV_PASSWORD:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Using TradingView login: {TV_USERNAME}")
            tv = TvDatafeed(username=TV_USERNAME, password=TV_PASSWORD)
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] WARNING: No login credentials found")
            tv = TvDatafeed()

        # Fetch data
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Fetching 1095 days of data...")
        df = tv.get_hist(
            symbol=symbol,
            exchange=exchange,
            interval=Interval.in_daily,
            n_bars=1095
        )

        # Check result
        if df is None or df.empty:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] FAILED: No data returned")
            return False

        print(f"[{datetime.now().strftime('%H:%M:%S')}] SUCCESS: Received {len(df)} rows")

        # Convert to standard format
        data = []
        for idx, row in df.iterrows():
            timestamp_ms = int(idx.timestamp() * 1000)
            value = float(row['close'])
            data.append([timestamp_ms, value])

        print(f"[{datetime.now().strftime('%H:%M:%S')}] Converted to {len(data)} data points")

        # Standardize timestamps to midnight UTC
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Standardizing timestamps to midnight UTC...")
        cleaned_data = standardize_to_daily_utc(data)

        print(f"[{datetime.now().strftime('%H:%M:%S')}] Cleaned data: {len(cleaned_data)} points")

        # Show date range
        if len(cleaned_data) > 0:
            start_date = datetime.fromtimestamp(cleaned_data[0][0] / 1000, tz=timezone.utc)
            end_date = datetime.fromtimestamp(cleaned_data[-1][0] / 1000, tz=timezone.utc)
            print(f"Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

            # Show sample values
            print(f"\nFirst 3 values:")
            for i in range(min(3, len(cleaned_data))):
                ts = datetime.fromtimestamp(cleaned_data[i][0] / 1000, tz=timezone.utc)
                print(f"  {ts.strftime('%Y-%m-%d')}: {cleaned_data[i][1]:.2f}")

            print(f"\nLast 3 values:")
            for i in range(max(0, len(cleaned_data) - 3), len(cleaned_data)):
                ts = datetime.fromtimestamp(cleaned_data[i][0] / 1000, tz=timezone.utc)
                print(f"  {ts.strftime('%Y-%m-%d')}: {cleaned_data[i][1]:.2f}")

        # Save to file
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Saving to historical_data/{filename}.json...")
        save_historical_data(filename, cleaned_data)

        print(f"[{datetime.now().strftime('%H:%M:%S')}] [SUCCESS] Saved {len(cleaned_data)} points to {filename}.json")
        return True

    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] EXCEPTION: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main execution"""
    print("="*80)
    print("RETRY FAILED TRADINGVIEW SYMBOLS")
    print("="*80)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Login status: {'ENABLED' if TV_USERNAME and TV_PASSWORD else 'DISABLED'}")
    print(f"Symbols to retry: {len(FAILED_SYMBOLS)}")
    print("="*80)

    if not TV_USERNAME or not TV_PASSWORD:
        print("\nWARNING: No TradingView credentials found in .env file")
        print("Some symbols may require login. Please add:")
        print("  TV_USERNAME=your_username")
        print("  TV_PASSWORD=your_password")
        print("\nContinuing anyway...\n")

    results = []

    for idx, symbol_info in enumerate(FAILED_SYMBOLS, 1):
        print(f"\n\n[{idx}/{len(FAILED_SYMBOLS)}] Processing {symbol_info['exchange']}:{symbol_info['symbol']}")

        success = fetch_symbol(
            symbol_info['exchange'],
            symbol_info['symbol'],
            symbol_info['filename'],
            symbol_info['description']
        )

        results.append({
            'symbol': f"{symbol_info['exchange']}:{symbol_info['symbol']}",
            'success': success
        })

        # Extended delay between symbols
        if idx < len(FAILED_SYMBOLS):
            print(f"\n{'='*80}")
            print("Waiting 20 seconds before next symbol...")
            print(f"{'='*80}")
            time.sleep(20)

    # Final summary
    print("\n\n" + "="*80)
    print("RETRY RESULTS SUMMARY")
    print("="*80)

    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]

    print(f"Total attempted: {len(results)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")

    if successful:
        print("\nSuccessful fetches:")
        for r in successful:
            print(f"  [OK] {r['symbol']}")

    if failed:
        print("\nFailed fetches:")
        for r in failed:
            print(f"  [FAIL] {r['symbol']}")

    print("="*80)

    # Exit code
    sys.exit(0 if len(failed) == 0 else 1)


if __name__ == '__main__':
    main()
