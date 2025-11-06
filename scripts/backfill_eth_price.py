# scripts/backfill_eth_price.py
"""
One-time backfill script for ETH/USD 3-year historical price data from Alpaca.

This script fetches 3 years of historical ETH price data and backfills the cache file.
After running once, the existing eth_price_alpaca.py module will continue to fetch
daily updates incrementally.

Timezone Safety:
- All timestamps are forced to UTC timezone
- standardize_to_daily_utc() ensures midnight UTC (00:00:00) alignment
- No data bleeding between days

Data Source:
- Alpaca CryptoHistoricalDataClient
- Symbol: ETH/USD
- Historical data: 5+ years available
- No API keys required for crypto data
"""

import sys
import os
from datetime import datetime, timedelta, timezone

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.time_transformer import standardize_to_daily_utc
from data.incremental_data_manager import save_historical_data


def fetch_eth_from_alpaca(start_date, end_date):
    """
    Fetch ETH/USD price data from Alpaca for specified date range.

    Args:
        start_date (datetime): Start date for data fetch
        end_date (datetime): End date for data fetch

    Returns:
        list: [[timestamp_ms, close_price], ...] sorted by timestamp ascending

    Raises:
        Exception: If Alpaca fetch fails
    """
    print(f"\n[ETH Backfill] Fetching from Alpaca: {start_date.date()} to {end_date.date()}")

    try:
        # Import Alpaca SDK
        from alpaca.data.historical import CryptoHistoricalDataClient
        from alpaca.data.requests import CryptoBarsRequest
        from alpaca.data.timeframe import TimeFrame

        # Initialize Alpaca crypto client (no keys needed for crypto data)
        client = CryptoHistoricalDataClient()

        # Create request for ETH/USD bars
        request_params = CryptoBarsRequest(
            symbol_or_symbols=['ETH/USD'],
            timeframe=TimeFrame.Day,
            start=start_date,
            end=end_date
        )

        # Fetch bars
        bars = client.get_crypto_bars(request_params)

        # Extract data
        raw_data = []

        if 'ETH/USD' in bars.data:
            for bar in bars.data['ETH/USD']:
                # Get timestamp from bar
                dt = bar.timestamp

                # CRITICAL: Force UTC timezone to prevent data bleeding
                if dt.tzinfo is None:
                    dt_utc = dt.replace(tzinfo=timezone.utc)
                else:
                    dt_utc = dt.astimezone(timezone.utc)

                # Convert to milliseconds
                timestamp_ms = int(dt_utc.timestamp() * 1000)

                # Get close price
                close_price = float(bar.close)

                # Store as simple [timestamp, close_price]
                raw_data.append([timestamp_ms, close_price])

        if not raw_data:
            raise ValueError("No valid data extracted from Alpaca response")

        # Sort by timestamp (oldest first)
        raw_data.sort(key=lambda x: x[0])

        print(f"[ETH Backfill] Successfully fetched {len(raw_data)} data points")
        if raw_data:
            start_dt = datetime.fromtimestamp(raw_data[0][0] / 1000, tz=timezone.utc)
            end_dt = datetime.fromtimestamp(raw_data[-1][0] / 1000, tz=timezone.utc)
            print(f"[ETH Backfill] Date range: {start_dt.strftime('%Y-%m-%d')} to {end_dt.strftime('%Y-%m-%d')}")
            print(f"[ETH Backfill] Sample first: {raw_data[0]}")
            print(f"[ETH Backfill] Sample last: {raw_data[-1]}")

        return raw_data

    except Exception as e:
        print(f"[ETH Backfill] ERROR fetching from Alpaca: {e}")
        raise


def validate_eth_data(data):
    """
    Validate ETH data is within expected range.

    Args:
        data (list): [[timestamp, close_price], ...]

    Returns:
        bool: True if all values within range

    Raises:
        ValueError: If validation fails
    """
    print(f"\n[Validation] Checking ETH data...")

    if not data:
        raise ValueError("ETH: No data to validate")

    values = [d[1] for d in data]
    min_price = min(values)
    max_price = max(values)

    print(f"[Validation] ETH range: ${min_price:.2f} to ${max_price:.2f}")

    # ETH typical range: $500-$5000 (allowing wider range for historical data)
    if min_price < 100 or max_price > 10000:
        raise ValueError(
            f"ETH validation failed: Expected range $100-$10000, "
            f"got ${min_price:.2f}-${max_price:.2f}"
        )

    print(f"[Validation] ETH PASSED (within $100-$10000 range)")
    return True


def backfill_eth():
    """
    Main backfill function.

    Steps:
    1. Calculate 3-year date range
    2. Fetch ETH from Alpaca
    3. Standardize timestamps to midnight UTC
    4. Validate data ranges
    5. Save to cache file
    """
    print("="*80)
    print("ETH/USD 3-Year Historical Price Data Backfill")
    print("="*80)

    # Calculate date range: 3 years from today
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=1095)  # Exactly 3 years

    print(f"\n--- Step 1: Calculate Date Range ---")
    print(f"[Date Range] {start_date.date()} to {end_date.date()} (1095 days)")

    # Fetch ETH data
    print(f"\n--- Step 2: Fetch ETH Data ---")
    eth_raw = fetch_eth_from_alpaca(start_date, end_date)

    # Standardize timestamps to midnight UTC (critical for alignment with BTC price)
    print("\n--- Step 3: Standardize Timestamps ---")

    eth_standardized = standardize_to_daily_utc(eth_raw)
    print(f"[Timestamp Standardization] ETH: {len(eth_raw)} raw -> {len(eth_standardized)} standardized")

    # Verify standardization: Check first and last timestamps end in 00:00:00
    if eth_standardized:
        first_ts = eth_standardized[0][0]
        last_ts = eth_standardized[-1][0]
        first_dt = datetime.fromtimestamp(first_ts / 1000, tz=timezone.utc)
        last_dt = datetime.fromtimestamp(last_ts / 1000, tz=timezone.utc)
        print(f"[Timestamp Verification] ETH first: {first_dt} (hour={first_dt.hour}, min={first_dt.minute}, sec={first_dt.second})")
        print(f"[Timestamp Verification] ETH last: {last_dt} (hour={last_dt.hour}, min={last_dt.minute}, sec={last_dt.second})")

    # Validate data range
    print("\n--- Step 4: Validate Data Range ---")
    validate_eth_data(eth_standardized)

    # Save to cache file
    print("\n--- Step 5: Save to Cache File ---")

    save_historical_data('eth_price_alpaca', eth_standardized)
    print(f"[Cache] Saved {len(eth_standardized)} ETH records to historical_data/eth_price_alpaca.json")

    # Summary
    print("\n" + "="*80)
    print("[SUCCESS] ETH Backfill Complete!")
    print("="*80)
    print(f"ETH: {len(eth_standardized)} data points")
    print("\nNext steps:")
    print("1. Verify data quality")
    print("2. Test ETH Price oscillator in breakdown tab")
    print("3. Alpaca will continue to provide daily updates via eth_price_alpaca.py")
    print("="*80)


if __name__ == '__main__':
    try:
        backfill_eth()
    except Exception as e:
        print(f"\n[ERROR] Backfill failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
