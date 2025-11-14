"""
NULL VALUE INVESTIGATION SCRIPT
Finds exact dates with null values and traces root cause
"""

import json
import os
from datetime import datetime, timezone

def investigate_nulls(filepath, metric_name):
    """Find all null values and their exact dates"""
    print(f"\n{'='*80}")
    print(f"INVESTIGATING NULL VALUES: {metric_name}")
    print(f"{'='*80}\n")

    with open(filepath, 'r') as f:
        data = json.load(f)

    # Find all null entries
    null_entries = []
    for item in data:
        timestamp_ms = item[0]
        value = item[1]

        if value is None:
            dt = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
            null_entries.append({
                'timestamp_ms': timestamp_ms,
                'date': dt.strftime('%Y-%m-%d'),
                'datetime': dt.strftime('%Y-%m-%d %H:%M:%S %Z'),
                'day_of_week': dt.strftime('%A'),
                'index': data.index(item)
            })

    print(f"Total null values found: {len(null_entries)}")
    print(f"Percentage of dataset: {len(null_entries)/len(data)*100:.2f}%\n")

    if not null_entries:
        print("[SUCCESS] No null values found!\n")
        return []

    # Print each null with context
    print("NULL VALUE DETAILS:")
    print("-" * 80)

    for i, entry in enumerate(null_entries, 1):
        print(f"\n{i}. Date: {entry['date']} ({entry['day_of_week']})")
        print(f"   Full datetime: {entry['datetime']}")
        print(f"   Index in array: {entry['index']}")
        print(f"   Timestamp (ms): {entry['timestamp_ms']}")

        # Get surrounding values for context
        idx = entry['index']

        if idx > 0:
            prev_ts = data[idx-1][0]
            prev_val = data[idx-1][1]
            prev_dt = datetime.fromtimestamp(prev_ts / 1000, tz=timezone.utc)
            print(f"   Previous: {prev_dt.strftime('%Y-%m-%d')} = {prev_val}")
        else:
            print(f"   Previous: [FIRST ENTRY]")

        if idx < len(data) - 1:
            next_ts = data[idx+1][0]
            next_val = data[idx+1][1]
            next_dt = datetime.fromtimestamp(next_ts / 1000, tz=timezone.utc)
            print(f"   Next:     {next_dt.strftime('%Y-%m-%d')} = {next_val}")
        else:
            print(f"   Next:     [LAST ENTRY]")

    # Analyze patterns
    print("\n" + "="*80)
    print("PATTERN ANALYSIS")
    print("="*80 + "\n")

    # Check if nulls are consecutive
    consecutive_groups = []
    current_group = [null_entries[0]]

    for i in range(1, len(null_entries)):
        prev_idx = null_entries[i-1]['index']
        curr_idx = null_entries[i]['index']

        if curr_idx == prev_idx + 1:
            # Consecutive
            current_group.append(null_entries[i])
        else:
            # Gap - save current group and start new one
            consecutive_groups.append(current_group)
            current_group = [null_entries[i]]

    # Add last group
    consecutive_groups.append(current_group)

    if len(consecutive_groups) == len(null_entries):
        print(f"All {len(null_entries)} null values are ISOLATED (non-consecutive)")
    else:
        print(f"Null values grouped into {len(consecutive_groups)} consecutive blocks:")
        for i, group in enumerate(consecutive_groups, 1):
            if len(group) == 1:
                print(f"  Block {i}: Single null on {group[0]['date']}")
            else:
                print(f"  Block {i}: {len(group)} consecutive nulls from {group[0]['date']} to {group[-1]['date']}")

    # Check day of week pattern
    print("\nDay of week distribution:")
    day_counts = {}
    for entry in null_entries:
        day = entry['day_of_week']
        day_counts[day] = day_counts.get(day, 0) + 1

    for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
        count = day_counts.get(day, 0)
        if count > 0:
            print(f"  {day}: {count}")

    # Check if recent (last 30 days)
    latest_null = max(null_entries, key=lambda x: x['timestamp_ms'])
    oldest_null = min(null_entries, key=lambda x: x['timestamp_ms'])

    now = datetime.now(timezone.utc)
    days_since_latest = (now - datetime.fromtimestamp(latest_null['timestamp_ms'] / 1000, tz=timezone.utc)).days

    print(f"\nTemporal distribution:")
    print(f"  Oldest null: {oldest_null['date']}")
    print(f"  Latest null: {latest_null['date']} ({days_since_latest} days ago)")

    if days_since_latest < 30:
        print(f"  [WARNING] Latest null is RECENT ({days_since_latest} days ago)")
        print(f"  [LIKELY CAUSE] CMC API updates are failing to fetch current data")
    else:
        print(f"  [INFO] All nulls are historical (>30 days old)")

    return null_entries


def check_cmc_plugin(metric_name):
    """Check CMC plugin for null handling logic"""
    print(f"\n{'='*80}")
    print(f"CHECKING CMC PLUGIN NULL HANDLING: {metric_name}")
    print(f"{'='*80}\n")

    if 'BTC.D' in metric_name:
        plugin_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'btc_dominance_cmc.py')
    else:
        plugin_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'usdt_dominance_cmc.py')

    if not os.path.exists(plugin_path):
        print(f"[ERROR] Plugin file not found: {plugin_path}")
        return

    with open(plugin_path, 'r') as f:
        code = f.read()

    # Check for null handling
    print("Searching for null/None handling in code...")

    if 'is None' in code:
        print("[FOUND] Code contains 'is None' checks")
        # Find relevant lines
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            if 'is None' in line and not line.strip().startswith('#'):
                print(f"  Line {i}: {line.strip()}")
    else:
        print("[WARNING] No explicit null checks found")

    if 'None' in code and 'if' in code:
        print("[INFO] Code contains conditional logic with None")

    # Check for API error handling
    if 'try:' in code and 'except' in code:
        print("[FOUND] Code has try/except error handling")
    else:
        print("[WARNING] No try/except blocks found - API errors not caught")


def compare_timestamps():
    """Compare timestamp format between BTC.D and USDT.D"""
    print(f"\n{'='*80}")
    print("TIMESTAMP FORMAT COMPARISON")
    print(f"{'='*80}\n")

    base_path = os.path.join(os.path.dirname(__file__), '..', 'historical_data')

    btc_path = os.path.join(base_path, 'btc_dominance.json')
    usdt_path = os.path.join(base_path, 'usdt_dominance.json')

    with open(btc_path, 'r') as f:
        btc_data = json.load(f)

    with open(usdt_path, 'r') as f:
        usdt_data = json.load(f)

    # Check if timestamps align
    print("Checking if BTC.D and USDT.D have same timestamps...")

    btc_timestamps = set([item[0] for item in btc_data])
    usdt_timestamps = set([item[0] for item in usdt_data])

    if btc_timestamps == usdt_timestamps:
        print("[SUCCESS] Timestamps are PERFECTLY ALIGNED")
    else:
        print("[FAIL] Timestamps are MISALIGNED")

        only_in_btc = btc_timestamps - usdt_timestamps
        only_in_usdt = usdt_timestamps - btc_timestamps

        if only_in_btc:
            print(f"\n  Timestamps only in BTC.D ({len(only_in_btc)}):")
            for ts in sorted(only_in_btc)[:5]:
                dt = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
                print(f"    {dt.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            if len(only_in_btc) > 5:
                print(f"    ... and {len(only_in_btc) - 5} more")

        if only_in_usdt:
            print(f"\n  Timestamps only in USDT.D ({len(only_in_usdt)}):")
            for ts in sorted(only_in_usdt)[:5]:
                dt = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
                print(f"    {dt.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            if len(only_in_usdt) > 5:
                print(f"    ... and {len(only_in_usdt) - 5} more")

    # Check timestamp format (5am vs midnight)
    print("\nChecking timestamp precision...")

    sample_timestamps = btc_data[:5]
    all_midnight = True
    all_5am = True

    for item in sample_timestamps:
        dt = datetime.fromtimestamp(item[0] / 1000, tz=timezone.utc)

        if dt.hour != 0 or dt.minute != 0 or dt.second != 0:
            all_midnight = False

        if dt.hour != 5 or dt.minute != 0 or dt.second != 0:
            all_5am = False

    if all_midnight:
        print("[INFO] All timestamps are at midnight UTC (00:00:00)")
    elif all_5am:
        print("[INFO] All timestamps are at 5am UTC (05:00:00)")
        print("[WARNING] This is WRONG - should be midnight UTC")
    else:
        print("[FAIL] Timestamps have INCONSISTENT hour values")
        for item in sample_timestamps:
            dt = datetime.fromtimestamp(item[0] / 1000, tz=timezone.utc)
            print(f"  {dt.strftime('%Y-%m-%d %H:%M:%S %Z')}")


def main():
    """Main investigation"""
    base_path = os.path.join(os.path.dirname(__file__), '..', 'historical_data')

    print("\n" + "="*80)
    print("NULL VALUE FORENSIC INVESTIGATION")
    print("="*80)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Investigate BTC.D
    btc_nulls = investigate_nulls(
        os.path.join(base_path, 'btc_dominance.json'),
        'BTC.D (Bitcoin Dominance)'
    )

    # Investigate USDT.D
    usdt_nulls = investigate_nulls(
        os.path.join(base_path, 'usdt_dominance.json'),
        'USDT.D (USDT Dominance)'
    )

    # Check if nulls are on same dates
    if btc_nulls and usdt_nulls:
        print(f"\n{'='*80}")
        print("CROSS-REFERENCE ANALYSIS")
        print(f"{'='*80}\n")

        btc_dates = set([n['date'] for n in btc_nulls])
        usdt_dates = set([n['date'] for n in usdt_nulls])

        common_dates = btc_dates & usdt_dates

        if common_dates:
            print(f"[CRITICAL] {len(common_dates)} dates have nulls in BOTH datasets:")
            for date in sorted(common_dates):
                print(f"  - {date}")
            print("\n[LIKELY CAUSE] CMC API failed to return data on these dates")
        else:
            print("[INFO] No common null dates - different failure modes")

    # Check CMC plugins
    check_cmc_plugin('BTC.D')
    check_cmc_plugin('USDT.D')

    # Compare timestamps
    compare_timestamps()

    # Final verdict
    print(f"\n{'='*80}")
    print("FINAL VERDICT")
    print(f"{'='*80}\n")

    if btc_nulls or usdt_nulls:
        print("[FAIL] Data integrity compromised - null values found")
        print("\nRECOMMENDATIONS:")
        print("1. Re-run backfill script to get clean TradingView data")
        print("2. Fix CMC plugin to handle API failures gracefully")
        print("3. Implement null value filling strategy (forward fill? interpolation?)")
        print("4. Add monitoring to alert on new nulls")
    else:
        print("[SUCCESS] No null values - data integrity intact")

    print("\n")


if __name__ == '__main__':
    main()
