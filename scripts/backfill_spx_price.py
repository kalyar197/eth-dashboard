# scripts/backfill_spx_price.py
"""
One-time backfill script for S&P 500 Index (SPX) 3-year historical price data from FMP.

This script fetches FULL historical data from FMP and slices to last 3 years.
After running once, the existing spx_price_fmp.py module will continue to fetch
daily updates incrementally.

CRITICAL APPROACH:
- FMP /stable/historical-price-eod/full endpoint returns ALL historical data
- We fetch everything FIRST, then slice to 3 years
- DO NOT filter dates during API call - parse full response first

Timezone Safety:
- All timestamps are forced to UTC timezone
- standardize_to_daily_utc() ensures midnight UTC (00:00:00) alignment
- No data bleeding between days

Data Source:
- Financial Modeling Prep (FMP) API
- Symbol: ^GSPC (S&P 500 Index)
- Historical data: 10+ years available
- Requires FMP API key (configured in config.py)
"""

import sys
import os
from datetime import datetime, timedelta, timezone
import requests

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import FMP_API_KEY
from data.time_transformer import standardize_to_daily_utc
from data.incremental_data_manager import save_historical_data


def fetch_spx_from_fmp():
    """
    Fetch FULL historical S&P 500 data from FMP.
    Returns ALL available data without date filtering.

    Returns:
        list: [[timestamp_ms, close_price], ...] sorted by timestamp

    Raises:
        Exception: If FMP fetch fails
    """
    print(f"\n[SPX Backfill] Fetching FULL historical data from FMP (no date filter)")

    # FMP stable endpoint configuration
    base_url = 'https://financialmodelingprep.com/stable/historical-price-eod/full'

    # API parameters - NO date filtering here!
    params = {
        'symbol': '^GSPC',  # S&P 500 Index
        'apikey': FMP_API_KEY
    }

    try:
        # Make the API request
        response = requests.get(base_url, params=params, timeout=60)
        response.raise_for_status()

        data = response.json()

        if not data:
            raise ValueError("No data returned from FMP")

        # Extract historical data array
        if isinstance(data, dict) and 'historical' in data:
            historical_data = data['historical']
        elif isinstance(data, list):
            historical_data = data
        else:
            raise ValueError(f"Unexpected FMP response structure: {type(data)}")

        if not historical_data:
            raise ValueError("Empty historical data from FMP")

        print(f"[SPX Backfill] Received {len(historical_data)} total records from FMP")

        # Process the data to simple [timestamp, close_price] format
        raw_data = []
        for item in historical_data:
            # Extract date and close price
            date_str = item.get('date')
            close_price = item.get('close')

            # Validate components exist
            if date_str and close_price is not None:
                # Parse the date string
                try:
                    dt = datetime.strptime(date_str, '%Y-%m-%d')
                    # CRITICAL: Force UTC timezone
                    dt = dt.replace(tzinfo=timezone.utc)
                    timestamp_ms = int(dt.timestamp() * 1000)
                except ValueError:
                    print(f"[SPX Backfill] Warning: Could not parse date {date_str}, skipping...")
                    continue

                # Store as simple [timestamp, close_price]
                raw_data.append([timestamp_ms, float(close_price)])
            else:
                # Silently skip incomplete records
                pass

        if not raw_data:
            raise ValueError("No valid price data extracted from FMP response")

        # Sort by timestamp (oldest first)
        raw_data.sort(key=lambda x: x[0])

        print(f"[SPX Backfill] Parsed {len(raw_data)} valid price records")
        if raw_data:
            start_dt = datetime.fromtimestamp(raw_data[0][0] / 1000, tz=timezone.utc)
            end_dt = datetime.fromtimestamp(raw_data[-1][0] / 1000, tz=timezone.utc)
            print(f"[SPX Backfill] Full date range: {start_dt.strftime('%Y-%m-%d')} to {end_dt.strftime('%Y-%m-%d')}")

        return raw_data

    except requests.exceptions.RequestException as e:
        print(f"[SPX Backfill] API request failed: {e}")
        raise
    except Exception as e:
        print(f"[SPX Backfill] ERROR fetching from FMP: {e}")
        raise


def slice_to_three_years(data):
    """
    Slice data to last 3 years only.

    Args:
        data (list): Full historical data [[timestamp, close_price], ...]

    Returns:
        list: Last 3 years of data
    """
    if not data:
        return []

    # Calculate cutoff timestamp (3 years ago from now)
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=1095)
    cutoff_timestamp = int(cutoff_date.timestamp() * 1000)

    # Filter data >= cutoff
    sliced_data = [d for d in data if d[0] >= cutoff_timestamp]

    print(f"[Slice] Filtered {len(data)} records -> {len(sliced_data)} records (last 3 years)")

    return sliced_data


def validate_spx_data(data):
    """
    Validate SPX data is within expected range.

    Args:
        data (list): [[timestamp, close_price], ...]

    Returns:
        bool: True if all values within range

    Raises:
        ValueError: If validation fails
    """
    print(f"\n[Validation] Checking SPX data...")

    if not data:
        raise ValueError("SPX: No data to validate")

    # Extract close prices, filter out None values (weekends/holidays)
    close_prices = [d[1] for d in data if d[1] is not None]

    if not close_prices:
        raise ValueError("SPX: All values are None")

    none_count = len(data) - len(close_prices)
    print(f"[Validation] Total records: {len(data)}, Valid: {len(close_prices)}, None: {none_count}")

    min_price = min(close_prices)
    max_price = max(close_prices)

    print(f"[Validation] SPX range: ${min_price:.2f} to ${max_price:.2f}")

    # SPX typical range: 3000-6000 (allowing wider range for market movements)
    if min_price < 2000 or max_price > 8000:
        raise ValueError(
            f"SPX validation failed: Expected range $2000-$8000, "
            f"got ${min_price:.2f}-${max_price:.2f}"
        )

    print(f"[Validation] SPX PASSED (within $2000-$8000 range)")
    return True


def backfill_spx():
    """
    Main backfill function.

    Steps:
    1. Fetch FULL historical data from FMP
    2. Slice to last 3 years
    3. Standardize timestamps to midnight UTC
    4. Validate data ranges
    5. Save to cache file
    """
    print("="*80)
    print("S&P 500 Index (SPX) 3-Year Historical Price Data Backfill")
    print("="*80)

    # Fetch FULL historical data from FMP
    print(f"\n--- Step 1: Fetch FULL Historical Data ---")
    spx_raw = fetch_spx_from_fmp()

    # Slice to last 3 years
    print(f"\n--- Step 2: Slice to Last 3 Years ---")
    spx_3years = slice_to_three_years(spx_raw)

    # Standardize timestamps to midnight UTC (critical for alignment with BTC price)
    print("\n--- Step 3: Standardize Timestamps ---")

    spx_standardized = standardize_to_daily_utc(spx_3years)
    print(f"[Timestamp Standardization] SPX: {len(spx_3years)} raw -> {len(spx_standardized)} standardized")

    # Verify standardization: Check first and last timestamps end in 00:00:00
    if spx_standardized:
        first_ts = spx_standardized[0][0]
        last_ts = spx_standardized[-1][0]
        first_dt = datetime.fromtimestamp(first_ts / 1000, tz=timezone.utc)
        last_dt = datetime.fromtimestamp(last_ts / 1000, tz=timezone.utc)
        print(f"[Timestamp Verification] SPX first: {first_dt} (hour={first_dt.hour}, min={first_dt.minute}, sec={first_dt.second})")
        print(f"[Timestamp Verification] SPX last: {last_dt} (hour={last_dt.hour}, min={last_dt.minute}, sec={last_dt.second})")

    # Validate data range
    print("\n--- Step 4: Validate Data Range ---")
    validate_spx_data(spx_standardized)

    # Save to cache file
    print("\n--- Step 5: Save to Cache File ---")

    save_historical_data('spx_price', spx_standardized)
    print(f"[Cache] Saved {len(spx_standardized)} SPX records to historical_data/spx_price.json")

    # Summary
    print("\n" + "="*80)
    print("[SUCCESS] SPX Backfill Complete!")
    print("="*80)
    print(f"SPX: {len(spx_standardized)} data points")
    print("\nNext steps:")
    print("1. Verify data quality")
    print("2. Test SPX Price oscillator in breakdown tab")
    print("3. FMP will continue to provide daily updates via spx_price_fmp.py")
    print("="*80)


if __name__ == '__main__':
    try:
        backfill_spx()
    except Exception as e:
        print(f"\n[ERROR] Backfill failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
