# scripts/backfill_gold_price.py
"""
One-time backfill script for Gold (XAU/USD) 3-year historical price data from FMP.

This script fetches FULL historical data from FMP and slices to last 3 years.
After running once, the existing gold_price.py module will continue to fetch
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
- Symbol: GCUSD (Gold Continuous Contract)
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


def fetch_gold_from_fmp():
    """
    Fetch FULL historical Gold OHLCV data from FMP.
    Returns ALL available data without date filtering.

    Returns:
        list: [[timestamp_ms, open, high, low, close, volume], ...] sorted by timestamp

    Raises:
        Exception: If FMP fetch fails
    """
    print(f"\n[Gold Backfill] Fetching FULL historical data from FMP (no date filter)")

    # FMP stable endpoint configuration
    base_url = 'https://financialmodelingprep.com/stable/historical-price-eod/full'

    # API parameters - NO date filtering here!
    params = {
        'symbol': 'GCUSD',  # Gold Continuous Contract
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

        print(f"[Gold Backfill] Received {len(historical_data)} total records from FMP")

        # Process the OHLC data
        raw_data = []
        for item in historical_data:
            # Extract date and OHLC values
            date_str = item.get('date')
            open_price = item.get('open')
            high_price = item.get('high')
            low_price = item.get('low')
            close_price = item.get('close')

            # Validate all components exist
            if (date_str and
                open_price is not None and
                high_price is not None and
                low_price is not None and
                close_price is not None):

                # Parse the date string
                try:
                    dt = datetime.strptime(date_str, '%Y-%m-%d')
                    # CRITICAL: Force UTC timezone
                    dt = dt.replace(tzinfo=timezone.utc)
                    timestamp_ms = int(dt.timestamp() * 1000)
                except ValueError:
                    print(f"[Gold Backfill] Warning: Could not parse date {date_str}, skipping...")
                    continue

                # Store as OHLCV (volume = 0 for gold spot)
                raw_data.append([
                    timestamp_ms,
                    float(open_price),
                    float(high_price),
                    float(low_price),
                    float(close_price),
                    0.0  # Gold spot price doesn't have volume
                ])
            else:
                # Silently skip incomplete records
                pass

        if not raw_data:
            raise ValueError("No valid OHLC data extracted from FMP response")

        # Sort by timestamp (oldest first)
        raw_data.sort(key=lambda x: x[0])

        print(f"[Gold Backfill] Parsed {len(raw_data)} valid OHLCV records")
        if raw_data:
            start_dt = datetime.fromtimestamp(raw_data[0][0] / 1000, tz=timezone.utc)
            end_dt = datetime.fromtimestamp(raw_data[-1][0] / 1000, tz=timezone.utc)
            print(f"[Gold Backfill] Full date range: {start_dt.strftime('%Y-%m-%d')} to {end_dt.strftime('%Y-%m-%d')}")

        return raw_data

    except requests.exceptions.RequestException as e:
        print(f"[Gold Backfill] API request failed: {e}")
        raise
    except Exception as e:
        print(f"[Gold Backfill] ERROR fetching from FMP: {e}")
        raise


def slice_to_three_years(data):
    """
    Slice data to last 3 years only.

    Args:
        data (list): Full historical data [[timestamp, ...], ...]

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


def validate_gold_data(data):
    """
    Validate Gold data is within expected range.

    Args:
        data (list): [[timestamp, open, high, low, close, volume], ...]

    Returns:
        bool: True if all values within range

    Raises:
        ValueError: If validation fails
    """
    print(f"\n[Validation] Checking Gold data...")

    if not data:
        raise ValueError("Gold: No data to validate")

    # Extract close prices (index 4), filter out None values (weekends/holidays)
    close_prices = [d[4] for d in data if d[4] is not None]

    if not close_prices:
        raise ValueError("Gold: All values are None")

    none_count = len(data) - len(close_prices)
    print(f"[Validation] Total records: {len(data)}, Valid: {len(close_prices)}, None: {none_count}")

    min_price = min(close_prices)
    max_price = max(close_prices)

    print(f"[Validation] Gold range: ${min_price:.2f} to ${max_price:.2f}")

    # Gold typical range: $1500-$3000 (allowing wider range for record highs)
    if min_price < 1000 or max_price > 5000:
        raise ValueError(
            f"Gold validation failed: Expected range $1000-$5000, "
            f"got ${min_price:.2f}-${max_price:.2f}"
        )

    print(f"[Validation] Gold PASSED (within $1000-$5000 range)")
    return True


def backfill_gold():
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
    print("Gold (XAU/USD) 3-Year Historical Price Data Backfill")
    print("="*80)

    # Fetch FULL historical data from FMP
    print(f"\n--- Step 1: Fetch FULL Historical Data ---")
    gold_raw = fetch_gold_from_fmp()

    # Slice to last 3 years
    print(f"\n--- Step 2: Slice to Last 3 Years ---")
    gold_3years = slice_to_three_years(gold_raw)

    # Standardize timestamps to midnight UTC (critical for alignment with BTC price)
    print("\n--- Step 3: Standardize Timestamps ---")

    gold_standardized = standardize_to_daily_utc(gold_3years)
    print(f"[Timestamp Standardization] Gold: {len(gold_3years)} raw -> {len(gold_standardized)} standardized")

    # Verify standardization: Check first and last timestamps end in 00:00:00
    if gold_standardized:
        first_ts = gold_standardized[0][0]
        last_ts = gold_standardized[-1][0]
        first_dt = datetime.fromtimestamp(first_ts / 1000, tz=timezone.utc)
        last_dt = datetime.fromtimestamp(last_ts / 1000, tz=timezone.utc)
        print(f"[Timestamp Verification] Gold first: {first_dt} (hour={first_dt.hour}, min={first_dt.minute}, sec={first_dt.second})")
        print(f"[Timestamp Verification] Gold last: {last_dt} (hour={last_dt.hour}, min={last_dt.minute}, sec={last_dt.second})")

    # Validate data range
    print("\n--- Step 4: Validate Data Range ---")
    validate_gold_data(gold_standardized)

    # Save to cache file
    print("\n--- Step 5: Save to Cache File ---")

    save_historical_data('gold_price', gold_standardized)
    print(f"[Cache] Saved {len(gold_standardized)} Gold records to historical_data/gold_price.json")

    # Summary
    print("\n" + "="*80)
    print("[SUCCESS] Gold Backfill Complete!")
    print("="*80)
    print(f"Gold: {len(gold_standardized)} data points")
    print("\nNext steps:")
    print("1. Verify data quality")
    print("2. Test Gold Price oscillator in breakdown tab")
    print("3. FMP will continue to provide daily updates via gold_price.py")
    print("="*80)


if __name__ == '__main__':
    try:
        backfill_gold()
    except Exception as e:
        print(f"\n[ERROR] Backfill failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
