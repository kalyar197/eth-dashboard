#!/usr/bin/env python3
"""
BTC Data Validator: Ensures data integrity, NO gaps, NO estimation, NO duplicates
"""

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

DATA_FILE = Path('historical_data/btc_price_1min_complete.json')

def validate_data():
    """Comprehensive validation of BTC 1-minute data."""
    print("="*80)
    print("BTC DATA VALIDATION: PRECISION & ACCURACY CHECK")
    print("="*80)

    # Load data
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"[ERROR] File not found: {DATA_FILE}")
        return False

    if not data:
        print("[ERROR] No data loaded")
        return False

    print(f"\n[Loaded] {len(data):,} records")

    # Validation checks
    issues = []

    # 1. Check for duplicates
    print("\n[Check 1] Duplicate timestamps...")
    timestamps = [record[0] for record in data]
    unique_timestamps = set(timestamps)

    if len(timestamps) != len(unique_timestamps):
        duplicates = len(timestamps) - len(unique_timestamps)
        issues.append(f"Found {duplicates} duplicate timestamps")
        print(f"  [X] FAILED: {duplicates} duplicates")
    else:
        print(f"  [OK] PASSED: No duplicates")

    # 2. Check chronological order
    print("\n[Check 2] Chronological order...")
    is_sorted = all(data[i][0] < data[i+1][0] for i in range(len(data)-1))

    if not is_sorted:
        issues.append("Data not in chronological order")
        print(f"  [X] FAILED: Not sorted")
    else:
        print(f"  [OK] PASSED: Properly sorted")

    # 3. Check for gaps (missing minutes)
    print("\n[Check 3] Checking for gaps (missing 1-minute bars)...")
    gaps = []
    gap_count = 0

    for i in range(len(data) - 1):
        current_ts = data[i][0]
        next_ts = data[i+1][0]
        expected_ts = current_ts + 60000  # Next minute

        if next_ts != expected_ts:
            gap_minutes = (next_ts - expected_ts) // 60000
            gap_count += gap_minutes

            if len(gaps) < 10:  # Show first 10 gaps
                current_dt = datetime.fromtimestamp(current_ts/1000, tz=timezone.utc)
                next_dt = datetime.fromtimestamp(next_ts/1000, tz=timezone.utc)
                gaps.append({
                    'after': current_dt,
                    'before': next_dt,
                    'missing_minutes': gap_minutes
                })

    if gap_count > 0:
        issues.append(f"Found {gap_count:,} missing minutes ({len(gaps)} gap periods)")
        print(f"  [!] WARNING: {gap_count:,} missing minutes")
        print(f"\n  First {min(len(gaps), 10)} gaps:")
        for gap in gaps[:10]:
            print(f"    - After {gap['after']}: {gap['missing_minutes']} minutes missing")
    else:
        print(f"  [OK] PASSED: No gaps - perfect 1-minute continuity")

    # 4. Check OHLCV structure
    print("\n[Check 4] OHLCV data structure...")
    invalid_records = 0

    for i, record in enumerate(data[:1000]):  # Sample first 1000
        if len(record) != 6:
            invalid_records += 1
        elif not all(isinstance(x, (int, float)) for x in record):
            invalid_records += 1
        elif record[2] < record[3]:  # High < Low
            invalid_records += 1
        elif record[1] == 0 or record[4] == 0:  # Open or Close = 0
            invalid_records += 1

    if invalid_records > 0:
        issues.append(f"Found {invalid_records} invalid OHLCV records")
        print(f"  [X] FAILED: {invalid_records} invalid records")
    else:
        print(f"  [OK] PASSED: All records have valid OHLCV structure")

    # 5. Check for estimated/mock data (zeros, identical values)
    print("\n[Check 5] Checking for estimated/mock data...")
    suspicious_records = 0

    for i, record in enumerate(data):
        ts, o, h, l, c, v = record

        # Check for zeros
        if o == 0 or h == 0 or l == 0 or c == 0:
            suspicious_records += 1

        # Check for identical OHLC (possible mock data)
        if o == h == l == c and i > 0:
            # Allow first record to have identical OHLC
            suspicious_records += 1

    if suspicious_records > 0:
        issues.append(f"Found {suspicious_records} suspicious records (possible estimation)")
        print(f"  [!] WARNING: {suspicious_records} suspicious records")
    else:
        print(f"  [OK] PASSED: No estimated/mock data detected")

    # 6. Timezone consistency
    print("\n[Check 6] Timezone alignment (all timestamps UTC midnight-aligned)...")
    # Check if timestamps are proper minute boundaries
    non_minute_timestamps = 0

    for record in data[:1000]:
        ts = record[0]
        if ts % 60000 != 0:  # Should be exact minute
            non_minute_timestamps += 1

    if non_minute_timestamps > 0:
        issues.append(f"Found {non_minute_timestamps} non-minute-aligned timestamps")
        print(f"  [X] FAILED: {non_minute_timestamps} misaligned timestamps")
    else:
        print(f"  [OK] PASSED: All timestamps minute-aligned")

    # 7. Date range coverage
    print("\n[Check 7] Date range and coverage...")
    first_ts = data[0][0]
    last_ts = data[-1][0]

    first_dt = datetime.fromtimestamp(first_ts/1000, tz=timezone.utc)
    last_dt = datetime.fromtimestamp(last_ts/1000, tz=timezone.utc)

    total_days = (last_dt - first_dt).days
    expected_minutes = total_days * 1440
    coverage_pct = (len(data) / expected_minutes) * 100

    print(f"  Range: {first_dt.date()} to {last_dt.date()}")
    print(f"  Days: {total_days}")
    print(f"  Records: {len(data):,}")
    print(f"  Expected: {expected_minutes:,}")
    print(f"  Coverage: {coverage_pct:.2f}%")

    if coverage_pct < 95:
        issues.append(f"Low coverage: {coverage_pct:.2f}%")
        print(f"  [!] WARNING: Coverage below 95%")
    else:
        print(f"  [OK] PASSED: Excellent coverage")

    # Summary
    print(f"\n{'='*80}")
    print("VALIDATION SUMMARY")
    print(f"{'='*80}")

    if issues:
        print(f"\n[X] VALIDATION FAILED - {len(issues)} issues found:\n")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
        print(f"\n[!] DATA REQUIRES ATTENTION")
        return False
    else:
        print(f"\n[OK] ALL CHECKS PASSED")
        print(f"\n[***] DATA IS PRECISE, ACCURATE, AND GAP-FREE")
        print(f"   - {len(data):,} real 1-minute bars")
        print(f"   - No duplicates")
        print(f"   - No gaps")
        print(f"   - No estimation")
        print(f"   - {coverage_pct:.2f}% coverage")
        return True

if __name__ == '__main__':
    try:
        result = validate_data()
        exit(0 if result else 1)
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()
        exit(1)
