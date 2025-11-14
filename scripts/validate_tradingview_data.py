"""
TradingView Data Validation Script
Validates existing BTC.D and USDT.D historical data for integrity issues
"""

import json
import os
from datetime import datetime, timedelta
from collections import Counter

def load_json_data(filepath):
    """Load JSON data from file"""
    with open(filepath, 'r') as f:
        return json.load(f)

def validate_data_integrity(data, metric_name, min_val, max_val):
    """
    Comprehensive validation of scraped data

    Checks:
    1. Data completeness (gaps in timeline)
    2. Value ranges
    3. Timestamp integrity
    4. Duplicates
    5. Null values
    6. Day-over-day changes
    """
    print(f"\n{'='*60}")
    print(f"VALIDATING: {metric_name}")
    print(f"{'='*60}\n")

    issues = []
    warnings = []

    # Basic stats
    print(f"Total data points: {len(data)}")
    print(f"Expected range: {min_val}% - {max_val}%\n")

    # Extract timestamps and values
    timestamps = [point[0] for point in data]
    values = [point[1] for point in data]

    # 1. CHECK FOR DUPLICATES
    timestamp_counts = Counter(timestamps)
    duplicates = {ts: count for ts, count in timestamp_counts.items() if count > 1}

    if duplicates:
        issues.append(f"[FAIL] DUPLICATE TIMESTAMPS: {len(duplicates)} duplicates found")
        for ts, count in list(duplicates.items())[:5]:  # Show first 5
            dt = datetime.fromtimestamp(ts / 1000)
            issues.append(f"   - {dt.strftime('%Y-%m-%d')}: {count} occurrences")
    else:
        print("[PASS] No duplicate timestamps")

    # 2. CHECK FOR NULL VALUES
    null_count = sum(1 for v in values if v is None)
    if null_count > 0:
        issues.append(f"[FAIL] NULL VALUES: {null_count} null values found ({null_count/len(values)*100:.2f}%)")
    else:
        print("[PASS] No null values")

    # 3. CHECK TIMESTAMP INTEGRITY
    # All timestamps should be midnight UTC
    non_midnight = []
    for ts in timestamps:
        dt = datetime.fromtimestamp(ts / 1000)
        if dt.hour != 0 or dt.minute != 0 or dt.second != 0:
            non_midnight.append(dt.strftime('%Y-%m-%d %H:%M:%S'))

    if non_midnight:
        issues.append(f"[FAIL] NON-MIDNIGHT TIMESTAMPS: {len(non_midnight)} timestamps not at midnight UTC")
        for dt_str in non_midnight[:5]:
            issues.append(f"   - {dt_str}")
    else:
        print("[PASS] All timestamps at midnight UTC")

    # 4. CHECK CHRONOLOGICAL ORDERING
    is_sorted = all(timestamps[i] <= timestamps[i+1] for i in range(len(timestamps)-1))
    if not is_sorted:
        issues.append("[FAIL] TIMESTAMPS NOT IN CHRONOLOGICAL ORDER")
    else:
        print("[PASS] Timestamps in chronological order")

    # 5. CHECK FOR GAPS (missing days)
    gaps = []
    for i in range(len(timestamps) - 1):
        current_dt = datetime.fromtimestamp(timestamps[i] / 1000)
        next_dt = datetime.fromtimestamp(timestamps[i+1] / 1000)
        expected_next = current_dt + timedelta(days=1)

        # Allow 1-3 day gaps (weekends/holidays are OK for some metrics)
        diff_days = (next_dt - current_dt).days
        if diff_days > 3:
            gaps.append({
                'from': current_dt.strftime('%Y-%m-%d'),
                'to': next_dt.strftime('%Y-%m-%d'),
                'days_missing': diff_days - 1
            })

    if gaps:
        warnings.append(f"[WARN] TIMELINE GAPS: {len(gaps)} gaps > 3 days found")
        for gap in gaps[:10]:  # Show first 10
            warnings.append(f"   - {gap['from']} to {gap['to']}: {gap['days_missing']} days missing")
    else:
        print("[PASS] No significant timeline gaps (>3 days)")

    # 6. CHECK VALUE RANGES
    valid_values = [v for v in values if v is not None]
    if valid_values:
        min_value = min(valid_values)
        max_value = max(valid_values)
        mean_value = sum(valid_values) / len(valid_values)

        print(f"\nValue statistics:")
        print(f"  Min: {min_value:.2f}%")
        print(f"  Max: {max_value:.2f}%")
        print(f"  Mean: {mean_value:.2f}%")

        out_of_range = [v for v in valid_values if v < min_val or v > max_val]
        if out_of_range:
            issues.append(f"[FAIL] OUT OF RANGE: {len(out_of_range)} values outside {min_val}-{max_val}%")
            issues.append(f"   - Min found: {min(out_of_range):.2f}%")
            issues.append(f"   - Max found: {max(out_of_range):.2f}%")
        else:
            print(f"[PASS] All values within expected range ({min_val}-{max_val}%)")

    # 7. CHECK DAY-OVER-DAY CHANGES
    large_changes = []
    for i in range(len(values) - 1):
        if values[i] is not None and values[i+1] is not None:
            pct_change = abs((values[i+1] - values[i]) / values[i] * 100)
            if pct_change > 10:  # >10% daily change is suspicious
                dt = datetime.fromtimestamp(timestamps[i] / 1000)
                large_changes.append({
                    'date': dt.strftime('%Y-%m-%d'),
                    'from': values[i],
                    'to': values[i+1],
                    'change': pct_change
                })

    if large_changes:
        warnings.append(f"[WARN] LARGE DAILY CHANGES: {len(large_changes)} changes >10%")
        for change in large_changes[:10]:
            warnings.append(f"   - {change['date']}: {change['from']:.2f}% -> {change['to']:.2f}% ({change['change']:.1f}% change)")
    else:
        print("[PASS] No suspicious daily changes (>10%)")

    # 8. DATE RANGE
    first_date = datetime.fromtimestamp(timestamps[0] / 1000).strftime('%Y-%m-%d')
    last_date = datetime.fromtimestamp(timestamps[-1] / 1000).strftime('%Y-%m-%d')
    date_span = (datetime.fromtimestamp(timestamps[-1] / 1000) -
                 datetime.fromtimestamp(timestamps[0] / 1000)).days

    print(f"\nDate range:")
    print(f"  First: {first_date}")
    print(f"  Last: {last_date}")
    print(f"  Span: {date_span} days ({date_span/365:.1f} years)")

    if date_span < 1000:  # Less than ~3 years
        warnings.append(f"[WARN] INSUFFICIENT HISTORY: Only {date_span} days ({date_span/365:.1f} years)")
    else:
        print(f"[PASS] Sufficient historical data ({date_span/365:.1f} years)")

    # PRINT SUMMARY
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)

    if not issues and not warnings:
        print("[SUCCESS] ALL CHECKS PASSED - DATA IS CLEAN")
    else:
        if issues:
            print(f"\n[FAIL] CRITICAL ISSUES FOUND: {len(issues)}")
            for issue in issues:
                print(issue)

        if warnings:
            print(f"\n[WARN] WARNINGS: {len(warnings)}")
            for warning in warnings:
                print(warning)

    print("\n")

    return {
        'metric': metric_name,
        'total_points': len(data),
        'date_range': {'first': first_date, 'last': last_date, 'days': date_span},
        'issues': len(issues),
        'warnings': len(warnings),
        'has_duplicates': len(duplicates) > 0,
        'has_nulls': null_count > 0,
        'has_gaps': len(gaps) > 0,
        'out_of_range': len(out_of_range) if valid_values else 0,
        'large_changes': len(large_changes)
    }

def main():
    """Main validation function"""
    base_path = os.path.join(os.path.dirname(__file__), '..', 'historical_data')

    print("\n" + "="*60)
    print("TRADINGVIEW DATA VALIDATION REPORT")
    print("="*60)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    validation_results = []

    # Validate BTC.D
    btc_d_path = os.path.join(base_path, 'btc_dominance.json')
    if os.path.exists(btc_d_path):
        btc_d_data = load_json_data(btc_d_path)
        result = validate_data_integrity(btc_d_data, 'BTC.D (Bitcoin Dominance)', 35, 75)
        validation_results.append(result)
    else:
        print(f"\n[FAIL] ERROR: File not found: {btc_d_path}")

    # Validate USDT.D
    usdt_d_path = os.path.join(base_path, 'usdt_dominance.json')
    if os.path.exists(usdt_d_path):
        usdt_d_data = load_json_data(usdt_d_path)
        result = validate_data_integrity(usdt_d_data, 'USDT.D (USDT Dominance)', 2, 10)
        validation_results.append(result)
    else:
        print(f"\n[FAIL] ERROR: File not found: {usdt_d_path}")

    # Final summary
    print("\n" + "="*60)
    print("OVERALL SUMMARY")
    print("="*60)

    total_issues = sum(r['issues'] for r in validation_results)
    total_warnings = sum(r['warnings'] for r in validation_results)

    print(f"\nMetrics validated: {len(validation_results)}")
    print(f"Total critical issues: {total_issues}")
    print(f"Total warnings: {total_warnings}")

    if total_issues == 0 and total_warnings == 0:
        print("\n[SUCCESS] ALL DATA VALIDATED SUCCESSFULLY")
        print("\nReady to proceed with expansion to 28 new metrics!")
    elif total_issues == 0:
        print("\n[SUCCESS] No critical issues, but some warnings to review")
        print("Data quality is acceptable for expansion")
    else:
        print("\n[FAIL] Critical issues found - recommend fixing before expansion")

    print("\n")

    # Save results to file
    report_path = os.path.join(base_path, 'validation_report.json')
    with open(report_path, 'w') as f:
        json.dump({
            'generated_at': datetime.now().isoformat(),
            'results': validation_results
        }, f, indent=2)

    print(f"Detailed report saved to: {report_path}\n")

if __name__ == '__main__':
    main()
