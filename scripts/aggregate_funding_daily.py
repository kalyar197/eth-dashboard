"""
Aggregation script for converting 8-hour Funding Rate data to daily averages.

Data Source: historical_data/funding_rate_btc.json (existing 8-hour data)
Output File: historical_data/funding_rate_daily_btc.json

Aggregation Logic:
    - Existing data: 3 funding rates per day (every 8 hours)
    - Calculate daily average: mean of 3 rates for each day
    - Standardize timestamps to midnight UTC
"""

import json
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# Configuration
INPUT_FILE = Path(__file__).parent.parent / "historical_data" / "funding_rate_btc.json"
OUTPUT_FILE = Path(__file__).parent.parent / "historical_data" / "funding_rate_daily_btc.json"


def load_8hour_data():
    """
    Load existing 8-hour funding rate data.

    Returns:
        List of [timestamp_ms, funding_rate_pct] pairs
    """
    print(f"Loading 8-hour funding rate data from {INPUT_FILE}...")

    if not INPUT_FILE.exists():
        print(f"[ERROR] Input file not found: {INPUT_FILE}")
        return []

    with open(INPUT_FILE, 'r') as f:
        data = json.load(f)

    print(f"[OK] Loaded {len(data)} 8-hour data points")
    return data


def aggregate_to_daily(data_8hour):
    """
    Aggregate 8-hour funding rate data to daily averages.

    Args:
        data_8hour: List of [timestamp_ms, funding_rate_pct] pairs

    Returns:
        List of [timestamp_ms, daily_avg_funding_rate_pct] pairs
    """
    if not data_8hour:
        return []

    print("\nAggregating to daily averages...")

    # Group by date (midnight UTC)
    daily_groups = defaultdict(list)

    for timestamp_ms, funding_rate in data_8hour:
        # Convert to date (midnight UTC)
        dt = datetime.fromtimestamp(timestamp_ms / 1000)
        date = dt.date()

        # Add to daily group
        daily_groups[date].append(funding_rate)

    # Calculate daily averages
    result = []
    for date in sorted(daily_groups.keys()):
        rates = daily_groups[date]
        avg_rate = sum(rates) / len(rates)

        # Convert date to midnight UTC timestamp
        dt = datetime.combine(date, datetime.min.time())
        timestamp_ms = int(dt.timestamp() * 1000)

        result.append([timestamp_ms, avg_rate])

    print(f"[OK] Aggregated to {len(result)} daily data points")

    return result


def calculate_statistics(daily_data):
    """
    Calculate and print statistics for the daily data.

    Args:
        daily_data: List of [timestamp_ms, funding_rate_pct] pairs
    """
    if not daily_data:
        return

    rates = [d[1] for d in daily_data]
    min_rate = min(rates)
    max_rate = max(rates)
    avg_rate = sum(rates) / len(rates)

    # Calculate date range
    start_date = datetime.fromtimestamp(daily_data[0][0] / 1000).date()
    end_date = datetime.fromtimestamp(daily_data[-1][0] / 1000).date()

    print()
    print("Statistics:")
    print(f"  Data points: {len(daily_data)}")
    print(f"  Date range: {start_date} to {end_date}")
    print(f"  Min rate: {min_rate:.4f}%")
    print(f"  Max rate: {max_rate:.4f}%")
    print(f"  Avg rate: {avg_rate:.4f}%")

    # Count positive/negative days
    positive_days = sum(1 for r in rates if r > 0)
    negative_days = sum(1 for r in rates if r < 0)
    zero_days = sum(1 for r in rates if r == 0)

    print()
    print("Sentiment Distribution:")
    print(f"  Positive days: {positive_days} ({positive_days/len(rates)*100:.1f}%)")
    print(f"  Negative days: {negative_days} ({negative_days/len(rates)*100:.1f}%)")
    print(f"  Zero days: {zero_days} ({zero_days/len(rates)*100:.1f}%)")


def aggregate_funding_rate():
    """
    Main aggregation function.
    """
    print("=" * 60)
    print("FUNDING RATE DAILY AGGREGATION")
    print("=" * 60)
    print(f"Input: {INPUT_FILE}")
    print(f"Output: {OUTPUT_FILE}")
    print()

    # Load 8-hour data
    data_8hour = load_8hour_data()

    if not data_8hour:
        print("[ERROR] No data to aggregate. Aborting.")
        return

    # Aggregate to daily
    daily_data = aggregate_to_daily(data_8hour)

    if not daily_data:
        print("[ERROR] Aggregation failed. Aborting.")
        return

    # Calculate statistics
    calculate_statistics(daily_data)

    # Ensure output directory exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Save to file
    print(f"\nSaving to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(daily_data, f, indent=2)

    print("[DONE] Aggregation complete!")


if __name__ == "__main__":
    aggregate_funding_rate()
