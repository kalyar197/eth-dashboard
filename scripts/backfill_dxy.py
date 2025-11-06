# scripts/backfill_dxy.py
"""
One-time backfill script for DXY (US Dollar Index) 3-year historical data from Yahoo Finance.

This script fetches 3 years of historical DXY data and backfills the cache file.
After running once, the existing dxy_price_yfinance.py module will continue to fetch
daily updates incrementally.

Timezone Safety:
- All timestamps are forced to UTC timezone
- standardize_to_daily_utc() ensures midnight UTC (00:00:00) alignment
- No data bleeding between days

Data Source:
- Yahoo Finance (yfinance library)
- Symbol: DX-Y.NYB
- Historical data: 10+ years available
- No API key required
"""

import sys
import os
from datetime import datetime, timedelta, timezone
import yfinance as yf

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.time_transformer import standardize_to_daily_utc
from data.incremental_data_manager import save_historical_data


def fetch_dxy_from_yfinance(start_date_str, end_date_str):
    """
    Fetch DXY data from Yahoo Finance for specified date range.

    Args:
        start_date_str (str): Start date in 'YYYY-MM-DD' format
        end_date_str (str): End date in 'YYYY-MM-DD' format

    Returns:
        list: [[timestamp_ms, close_price], ...] sorted by timestamp ascending

    Raises:
        Exception: If Yahoo Finance fetch fails
    """
    print(f"\n[DXY Backfill] Fetching from Yahoo Finance: {start_date_str} to {end_date_str}")

    try:
        # Create ticker object for DXY
        ticker = yf.Ticker("DX-Y.NYB")

        # Fetch historical data
        hist = ticker.history(start=start_date_str, end=end_date_str)

        if hist.empty:
            print(f"[DXY Backfill] ERROR: No data returned from Yahoo Finance")
            return []

        # Convert DataFrame to simple format [[timestamp_ms, close_price], ...]
        raw_data = []
        for index, row in hist.iterrows():
            # Get timestamp from index (pandas datetime)
            dt = index

            # CRITICAL: Force UTC timezone to prevent data bleeding
            if dt.tzinfo is None:
                # Assume naive datetime is UTC
                dt_utc = dt.replace(tzinfo=timezone.utc)
            else:
                # Convert to UTC if in different timezone
                dt_utc = dt.astimezone(timezone.utc)

            # Convert to milliseconds
            timestamp_ms = int(dt_utc.timestamp() * 1000)

            # Extract close price
            close_price = float(row['Close'])

            raw_data.append([timestamp_ms, close_price])

        # Sort by timestamp (should already be sorted, but ensure)
        raw_data.sort(key=lambda x: x[0])

        print(f"[DXY Backfill] Successfully fetched {len(raw_data)} data points")
        if raw_data:
            start_dt = datetime.fromtimestamp(raw_data[0][0] / 1000, tz=timezone.utc)
            end_dt = datetime.fromtimestamp(raw_data[-1][0] / 1000, tz=timezone.utc)
            print(f"[DXY Backfill] Date range: {start_dt.strftime('%Y-%m-%d')} to {end_dt.strftime('%Y-%m-%d')}")
            print(f"[DXY Backfill] Sample first: {raw_data[0]}")
            print(f"[DXY Backfill] Sample last: {raw_data[-1]}")

        return raw_data

    except Exception as e:
        print(f"[DXY Backfill] ERROR fetching from Yahoo Finance: {e}")
        raise


def validate_dxy_data(data):
    """
    Validate DXY data is within expected range.

    Args:
        data (list): [[timestamp, close_price], ...]

    Returns:
        bool: True if all values within range

    Raises:
        ValueError: If validation fails
    """
    print(f"\n[Validation] Checking DXY data...")

    if not data:
        raise ValueError("DXY: No data to validate")

    # Filter out None values (weekends/holidays when DXY doesn't trade)
    values = [d[1] for d in data if d[1] is not None]

    if not values:
        raise ValueError("DXY: All values are None")

    none_count = len(data) - len(values)
    print(f"[Validation] Total records: {len(data)}, Valid: {len(values)}, None: {none_count}")

    min_price = min(values)
    max_price = max(values)

    print(f"[Validation] DXY range: ${min_price:.2f} to ${max_price:.2f}")

    # DXY typical range: 90-115
    if min_price < 80 or max_price > 120:
        raise ValueError(
            f"DXY validation failed: Expected range 80-120, "
            f"got {min_price:.2f}-{max_price:.2f}"
        )

    print(f"[Validation] DXY PASSED (within 80-120 range)")
    return True


def backfill_dxy():
    """
    Main backfill function.

    Steps:
    1. Calculate 3-year date range
    2. Fetch DXY from Yahoo Finance
    3. Standardize timestamps to midnight UTC
    4. Validate data ranges
    5. Save to cache file
    """
    print("="*80)
    print("DXY (US Dollar Index) 3-Year Historical Data Backfill")
    print("="*80)

    # Calculate date range: 3 years from today
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=1095)  # Exactly 3 years

    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    print(f"\n--- Step 1: Calculate Date Range ---")
    print(f"[Date Range] {start_date_str} to {end_date_str} (1095 days)")

    # Fetch DXY data
    print(f"\n--- Step 2: Fetch DXY Data ---")
    dxy_raw = fetch_dxy_from_yfinance(start_date_str, end_date_str)

    # Standardize timestamps to midnight UTC (critical for alignment with BTC price)
    print("\n--- Step 3: Standardize Timestamps ---")

    dxy_standardized = standardize_to_daily_utc(dxy_raw)
    print(f"[Timestamp Standardization] DXY: {len(dxy_raw)} raw -> {len(dxy_standardized)} standardized")

    # Verify standardization: Check first and last timestamps end in 00:00:00
    if dxy_standardized:
        first_ts = dxy_standardized[0][0]
        last_ts = dxy_standardized[-1][0]
        first_dt = datetime.fromtimestamp(first_ts / 1000, tz=timezone.utc)
        last_dt = datetime.fromtimestamp(last_ts / 1000, tz=timezone.utc)
        print(f"[Timestamp Verification] DXY first: {first_dt} (hour={first_dt.hour}, min={first_dt.minute}, sec={first_dt.second})")
        print(f"[Timestamp Verification] DXY last: {last_dt} (hour={last_dt.hour}, min={last_dt.minute}, sec={last_dt.second})")

    # Validate data range
    print("\n--- Step 4: Validate Data Range ---")
    validate_dxy_data(dxy_standardized)

    # Save to cache file
    print("\n--- Step 5: Save to Cache File ---")

    save_historical_data('dxy_price', dxy_standardized)
    print(f"[Cache] Saved {len(dxy_standardized)} DXY records to historical_data/dxy_price.json")

    # Summary
    print("\n" + "="*80)
    print("[SUCCESS] DXY Backfill Complete!")
    print("="*80)
    print(f"DXY: {len(dxy_standardized)} data points")
    print("\nNext steps:")
    print("1. Verify data quality")
    print("2. Test DXY oscillator in breakdown tab")
    print("3. Yahoo Finance will continue to provide daily updates via dxy_price_yfinance.py")
    print("="*80)


if __name__ == '__main__':
    try:
        backfill_dxy()
    except Exception as e:
        print(f"\n[ERROR] Backfill failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
