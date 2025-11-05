# scripts/backfill_dominance_data.py
"""
One-time backfill script for BTC.D and USDT.D historical data from TradingView.

This script fetches 3 years of historical dominance data and backfills the cache files.
After running once, the existing btc_dominance_cmc.py and usdt_dominance_cmc.py modules
will continue to fetch daily updates from CoinMarketCap API.

Timezone Safety:
- All timestamps are forced to UTC timezone
- standardize_to_daily_utc() ensures midnight UTC (00:00:00) alignment
- No data bleeding between days

Data Sources:
- BTC.D: TradingView CRYPTOCAP:BTC.D
- USDT.D: TradingView CRYPTOCAP:USDT.D
"""

import sys
import os
from datetime import datetime, timedelta, timezone
from tvDatafeed import TvDatafeed, Interval

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.time_transformer import standardize_to_daily_utc
from data.incremental_data_manager import save_historical_data


def fetch_tradingview_data(symbol_name, exchange='CRYPTOCAP', n_bars=1095):
    """
    Fetch historical data from TradingView using tvdatafeed.

    Args:
        symbol_name (str): Symbol name (e.g., 'BTC.D', 'USDT.D')
        exchange (str): Exchange name (default: 'CRYPTOCAP')
        n_bars (int): Number of bars to fetch (default: 1095 = 3 years)

    Returns:
        list: [[timestamp_ms, close_price], ...] sorted by timestamp ascending

    Raises:
        Exception: If TradingView fetch fails
    """
    print(f"\n[TradingView tvdatafeed] Fetching {exchange}:{symbol_name} - {n_bars} daily bars")

    try:
        # Initialize TvDatafeed (no login required for public data)
        tv = TvDatafeed()

        # Fetch historical data
        # Returns pandas DataFrame with columns: ['symbol', 'open', 'high', 'low', 'close', 'volume']
        # Index is datetime
        data = tv.get_hist(
            symbol=symbol_name,
            exchange=exchange,
            interval=Interval.in_daily,
            n_bars=n_bars
        )

        if data is None or len(data) == 0:
            print(f"[TradingView tvdatafeed] No data returned for {exchange}:{symbol_name}")
            return []

        # Extract timestamp and Close price
        raw_data = []
        for index, row in data.iterrows():
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

            # Extract close price as dominance percentage
            dominance_pct = float(row['close'])

            raw_data.append([timestamp_ms, dominance_pct])

        # Sort by timestamp (should already be sorted, but ensure)
        raw_data.sort(key=lambda x: x[0])

        print(f"[TradingView tvdatafeed] Successfully fetched {len(raw_data)} data points")
        if raw_data:
            start_dt = datetime.fromtimestamp(raw_data[0][0] / 1000, tz=timezone.utc)
            end_dt = datetime.fromtimestamp(raw_data[-1][0] / 1000, tz=timezone.utc)
            print(f"[TradingView tvdatafeed] Date range: {start_dt.strftime('%Y-%m-%d')} to {end_dt.strftime('%Y-%m-%d')}")
            print(f"[TradingView tvdatafeed] Sample first: {raw_data[0]}")
            print(f"[TradingView tvdatafeed] Sample last: {raw_data[-1]}")

        return raw_data

    except Exception as e:
        print(f"[TradingView tvdatafeed] Error fetching {exchange}:{symbol_name}: {e}")
        raise


def validate_dominance_data(data, symbol, min_val, max_val):
    """
    Validate dominance data is within expected range.

    Args:
        data (list): [[timestamp, dominance_pct], ...]
        symbol (str): Symbol name for logging
        min_val (float): Minimum expected dominance %
        max_val (float): Maximum expected dominance %

    Returns:
        bool: True if all values within range

    Raises:
        ValueError: If validation fails
    """
    print(f"\n[Validation] Checking {symbol} data...")

    if not data:
        raise ValueError(f"{symbol}: No data to validate")

    values = [d[1] for d in data]
    min_dominance = min(values)
    max_dominance = max(values)

    print(f"[Validation] {symbol} range: {min_dominance:.2f}% to {max_dominance:.2f}%")

    if min_dominance < min_val or max_dominance > max_val:
        raise ValueError(
            f"{symbol} validation failed: Expected range {min_val}-{max_val}%, "
            f"got {min_dominance:.2f}-{max_dominance:.2f}%"
        )

    print(f"[Validation] {symbol} PASSED (within {min_val}-{max_val}% range)")
    return True


def backfill_dominance_data():
    """
    Main backfill function.

    Steps:
    1. Fetch BTC.D from TradingView
    2. Fetch USDT.D from TradingView
    3. Standardize timestamps to midnight UTC
    4. Validate data ranges
    5. Save to cache files
    """
    print("="*80)
    print("BTC.D and USDT.D Historical Data Backfill")
    print("="*80)

    # Fetch BTC Dominance
    print("\n--- Step 1: Fetch BTC Dominance ---")
    btc_d_raw = fetch_tradingview_data('BTC.D', exchange='CRYPTOCAP', n_bars=1095)

    # Fetch USDT Dominance
    print("\n--- Step 2: Fetch USDT Dominance ---")
    usdt_d_raw = fetch_tradingview_data('USDT.D', exchange='CRYPTOCAP', n_bars=1095)

    # Standardize timestamps to midnight UTC (critical for alignment with BTC price)
    print("\n--- Step 3: Standardize Timestamps ---")

    btc_d_standardized = standardize_to_daily_utc(btc_d_raw)
    print(f"[Timestamp Standardization] BTC.D: {len(btc_d_raw)} raw -> {len(btc_d_standardized)} standardized")

    usdt_d_standardized = standardize_to_daily_utc(usdt_d_raw)
    print(f"[Timestamp Standardization] USDT.D: {len(usdt_d_raw)} raw -> {len(usdt_d_standardized)} standardized")

    # Verify standardization: Check first and last timestamps end in 00:00:00
    if btc_d_standardized:
        first_ts = btc_d_standardized[0][0]
        last_ts = btc_d_standardized[-1][0]
        first_dt = datetime.fromtimestamp(first_ts / 1000, tz=timezone.utc)
        last_dt = datetime.fromtimestamp(last_ts / 1000, tz=timezone.utc)
        print(f"[Timestamp Verification] BTC.D first: {first_dt} (hour={first_dt.hour}, min={first_dt.minute}, sec={first_dt.second})")
        print(f"[Timestamp Verification] BTC.D last: {last_dt} (hour={last_dt.hour}, min={last_dt.minute}, sec={last_dt.second})")

    if usdt_d_standardized:
        first_ts = usdt_d_standardized[0][0]
        last_ts = usdt_d_standardized[-1][0]
        first_dt = datetime.fromtimestamp(first_ts / 1000, tz=timezone.utc)
        last_dt = datetime.fromtimestamp(last_ts / 1000, tz=timezone.utc)
        print(f"[Timestamp Verification] USDT.D first: {first_dt} (hour={first_dt.hour}, min={first_dt.minute}, sec={first_dt.second})")
        print(f"[Timestamp Verification] USDT.D last: {last_dt} (hour={last_dt.hour}, min={last_dt.minute}, sec={last_dt.second})")

    # Validate data ranges
    print("\n--- Step 4: Validate Data Ranges ---")
    validate_dominance_data(btc_d_standardized, 'BTC.D', min_val=35.0, max_val=75.0)
    validate_dominance_data(usdt_d_standardized, 'USDT.D', min_val=2.0, max_val=10.0)

    # Save to cache files
    print("\n--- Step 5: Save to Cache Files ---")

    save_historical_data('btc_dominance', btc_d_standardized)
    print(f"[Cache] Saved {len(btc_d_standardized)} BTC.D records to historical_data/btc_dominance.json")

    save_historical_data('usdt_dominance', usdt_d_standardized)
    print(f"[Cache] Saved {len(usdt_d_standardized)} USDT.D records to historical_data/usdt_dominance.json")

    # Summary
    print("\n" + "="*80)
    print("[SUCCESS] Backfill Complete!")
    print("="*80)
    print(f"BTC.D:  {len(btc_d_standardized)} data points")
    print(f"USDT.D: {len(usdt_d_standardized)} data points")
    print("\nNext steps:")
    print("1. Refresh your dashboard")
    print("2. Navigate to Breakdown tab")
    print("3. Check that BTC.D and USDT.D oscillators now appear")
    print("4. CMC API will continue to add daily updates automatically")
    print("="*80)


if __name__ == '__main__':
    try:
        backfill_dominance_data()
    except Exception as e:
        print(f"\n[ERROR] Backfill failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
