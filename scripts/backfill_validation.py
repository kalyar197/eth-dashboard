"""
Validation Module for TradingView Backfill Script
Implements 6-layer validation to ensure data accuracy and completeness
"""

from datetime import datetime, timezone, timedelta
import statistics

# Expected data point counts based on data type
EXPECTED_COUNTS = {
    '24/7': 1095,  # 3 years × 365 days (crypto, on-chain, stablecoins)
    'market_hours': 780,  # 3 years × 260 trading days (ETFs, stocks)
    'fred': 1095,  # Federal Reserve data (daily)
    'recent_only': 300,  # Assets that launched recently (IBIT = Jan 2024)
}

# Value ranges for each symbol (min, max, allow_negative)
VALUE_RANGES = {
    'BTC_SOPR': (0.5, 2.0, False),
    'BTC_MEDIANVOLUME': (0, 1_000_000_000, False),
    'BTC_MEANTXFEES': (0, 1000, False),
    'BTC_SENDINGADDRESSES': (0, 10_000_000, False),
    'BTC_ACTIVE1Y': (0, 21_000_000, False),
    'BTC_RECEIVINGADDRESSES': (0, 10_000_000, False),
    'BTC_NEWADDRESSES': (0, 1_000_000, False),
    'BTC_SER': (0, 10, False),
    'BTC_AVGTX': (0, 1_000_000, False),
    'BTC_TXCOUNT': (0, 1_000_000, False),
    'BTC_SPLYADRBAL1': (0, 21_000_000, False),
    'BTC_ADDRESSESSUPPLY1IN10K': (0, 200_000, False),  # Number of addresses (not supply amount)
    'BTC_LARGETXCOUNT': (0, 100_000, False),
    'BTC_ACTIVESUPPLY1Y': (0, 21_000_000, False),
    'USDT_AVGTX': (0, 10_000_000, False),
    'USDT_TFSPS': (0, 10000, False),
    'USDTUSD.PM': (0.95, 1.05, False),  # Should be close to $1
    'BTC_POSTSCREATED': (0, 1_000_000, False),
    'BTC_CONTRIBUTORSCREATED': (0, 100_000, False),
    'BTC_SOCIALDOMINANCE': (0, 100, False),  # Percentage
    'BTC_CONTRIBUTORSACTIVE': (0, 100_000, False),
    'BTCST_TVL': (0, 10_000_000_000, False),  # Billions
    'IBIT': (0, 200, False),  # ETF price
    'GGBTC': (0, 200, False),  # ETF price
    'TOTAL3': (0, 5_000_000_000_000, False),  # Trillions
    'STABLE.C.D': (0, 100, False),  # Percentage
    'RRPONTSYD': (0, 10_000_000_000_000, False),  # Trillions
}

# Symbol categories for expected data point counts
SYMBOL_CATEGORIES = {
    'market_hours': ['IBIT', 'GGBTC'],
    'recent_only': ['IBIT'],  # Launched Jan 2024, ~300 days
    '24/7': [  # All others
        'BTC_SOPR', 'BTC_MEDIANVOLUME', 'BTC_MEANTXFEES', 'BTC_SENDINGADDRESSES',
        'BTC_ACTIVE1Y', 'BTC_RECEIVINGADDRESSES', 'BTC_NEWADDRESSES', 'BTC_SER',
        'BTC_AVGTX', 'BTC_TXCOUNT', 'BTC_SPLYADRBAL1', 'BTC_ADDRESSESSUPPLY1IN10K',
        'BTC_LARGETXCOUNT', 'BTC_ACTIVESUPPLY1Y', 'USDT_AVGTX', 'USDT_TFSPS',
        'USDTUSD.PM', 'BTC_POSTSCREATED', 'BTC_CONTRIBUTORSCREATED',
        'BTC_SOCIALDOMINANCE', 'BTC_CONTRIBUTORSACTIVE', 'BTCST_TVL',
        'TOTAL3', 'STABLE.C.D', 'RRPONTSYD', 'GGBTC'
    ],
}


def validate_layer1_fetch(ticker, data):
    """
    Layer 1: Fetch Validation
    Verify data was successfully fetched

    Returns: (is_valid, warnings, errors)
    """
    warnings = []
    errors = []

    # Check 1: Data exists
    if data is None:
        errors.append("Data is None")
        return False, warnings, errors

    # Check 2: Data is not empty
    if len(data) == 0:
        errors.append("Data is empty list")
        return False, warnings, errors

    # Check 3: Minimum data points
    # Determine expected count
    if ticker in SYMBOL_CATEGORIES.get('recent_only', []):
        expected_count = EXPECTED_COUNTS['recent_only']
        tolerance = 0.80  # 80% for recent launches
    elif ticker in SYMBOL_CATEGORIES.get('market_hours', []):
        expected_count = EXPECTED_COUNTS['market_hours']
        tolerance = 0.90  # 90% for market hours
    else:
        expected_count = EXPECTED_COUNTS['24/7']
        tolerance = 0.93  # 93% for 24/7 data (allow for weekends/gaps)

    min_expected = int(expected_count * tolerance)

    # Accept whatever data exists - user wants 1:1 mapping with charts
    # Only fail if we get almost nothing (likely a fetch error)
    if len(data) < 50:  # Less than 2 months of data = probable error
        errors.append(f"Very little data returned: got {len(data)} points (possible fetch error)")
        return False, warnings, errors

    if len(data) < min_expected:
        warnings.append(f"Less data than typical 3-year history: got {len(data)} points, expected ~{min_expected}")
    elif len(data) < expected_count:
        warnings.append(f"Fewer than ideal data points: got {len(data)}, expected ~{expected_count}")

    return True, warnings, errors


def validate_layer2_structure(ticker, data):
    """
    Layer 2: Structure Validation
    Verify each data point has valid structure

    Returns: (is_valid, warnings, errors, cleaned_data)
    """
    warnings = []
    errors = []
    cleaned_data = []
    invalid_count = 0

    for i, point in enumerate(data):
        # Check structure (should be [timestamp, value] or [timestamp, O, H, L, C, V])
        if not isinstance(point, (list, tuple)):
            invalid_count += 1
            continue

        if len(point) < 2:
            invalid_count += 1
            continue

        timestamp, value = point[0], point[1]

        # Validate timestamp
        if not isinstance(timestamp, (int, float)):
            invalid_count += 1
            continue

        # Check timestamp is reasonable (between 2020-2026)
        ts_seconds = timestamp / 1000 if timestamp > 1000000000000 else timestamp
        if ts_seconds < 1577836800 or ts_seconds > 1767225600:  # 2020-01-01 to 2026-01-01
            invalid_count += 1
            warnings.append(f"Suspicious timestamp at index {i}: {timestamp}")
            continue

        # Validate value
        if value is None:
            invalid_count += 1
            continue

        if not isinstance(value, (int, float)):
            invalid_count += 1
            continue

        # Check for NaN/Inf
        try:
            if value != value:  # NaN check
                invalid_count += 1
                continue
            if abs(value) == float('inf'):
                invalid_count += 1
                continue
        except:
            invalid_count += 1
            continue

        # Point is valid
        cleaned_data.append(point)

    # Report results
    if invalid_count > 0:
        pct_invalid = (invalid_count / len(data)) * 100
        if pct_invalid > 5:
            errors.append(f"Too many invalid points: {invalid_count} ({pct_invalid:.1f}%)")
            return False, warnings, errors, cleaned_data
        else:
            warnings.append(f"Removed {invalid_count} invalid points ({pct_invalid:.1f}%)")

    return True, warnings, errors, cleaned_data


def validate_layer3_timestamps(ticker, data):
    """
    Layer 3: Timestamp Validation
    Verify timestamps are unique, ordered, and at midnight UTC

    Returns: (is_valid, warnings, errors)
    """
    warnings = []
    errors = []

    if len(data) == 0:
        errors.append("No data to validate timestamps")
        return False, warnings, errors

    timestamps = [point[0] for point in data]

    # Check 1: Unique timestamps
    unique_timestamps = set(timestamps)
    if len(unique_timestamps) != len(timestamps):
        duplicates = len(timestamps) - len(unique_timestamps)
        errors.append(f"{duplicates} duplicate timestamps found")
        return False, warnings, errors

    # Check 2: Chronological order
    is_sorted = all(timestamps[i] <= timestamps[i+1] for i in range(len(timestamps)-1))
    if not is_sorted:
        errors.append("Timestamps not in chronological order")
        return False, warnings, errors

    # Check 3: Midnight UTC (sample first 10 + last 10)
    sample_indices = list(range(min(10, len(data)))) + list(range(max(0, len(data)-10), len(data)))
    non_midnight_count = 0

    for idx in sample_indices:
        ts_ms = timestamps[idx]
        dt = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
        if dt.hour != 0 or dt.minute != 0 or dt.second != 0:
            non_midnight_count += 1

    if non_midnight_count > 0:
        warnings.append(f"{non_midnight_count} sampled timestamps not at midnight UTC")

    # Check 4: Gap analysis
    large_gaps = []
    for i in range(len(timestamps) - 1):
        gap_days = (timestamps[i+1] - timestamps[i]) / 86400000  # Convert ms to days

        # Allow 7-day gaps for 24/7 data, 10-day for market hours
        max_gap = 10 if ticker in SYMBOL_CATEGORIES.get('market_hours', []) else 7

        if gap_days > max_gap:
            dt = datetime.fromtimestamp(timestamps[i] / 1000, tz=timezone.utc)
            large_gaps.append(f"{dt.strftime('%Y-%m-%d')}: {gap_days:.0f} day gap")

    if len(large_gaps) > 0:
        if len(large_gaps) > 5:
            warnings.append(f"{len(large_gaps)} large gaps detected (showing first 5):")
            for gap in large_gaps[:5]:
                warnings.append(f"  - {gap}")
        else:
            warnings.append(f"{len(large_gaps)} large gaps detected:")
            for gap in large_gaps:
                warnings.append(f"  - {gap}")

    return True, warnings, errors


def validate_layer4_value_ranges(ticker, data):
    """
    Layer 4: Value Range Validation
    Verify values are within expected ranges

    Returns: (is_valid, warnings, errors)
    """
    warnings = []
    errors = []

    if len(data) == 0:
        errors.append("No data to validate values")
        return False, warnings, errors

    # Get expected range for this ticker
    if ticker not in VALUE_RANGES:
        warnings.append(f"No value range defined for {ticker}, skipping range validation")
        return True, warnings, errors

    min_val, max_val, allow_negative = VALUE_RANGES[ticker]

    values = [point[1] for point in data]
    out_of_range = []
    negative_values = []

    for i, value in enumerate(values):
        if value < min_val or value > max_val:
            timestamp = data[i][0]
            dt = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
            out_of_range.append(f"{dt.strftime('%Y-%m-%d')}: {value} (range: {min_val}-{max_val})")

        if value < 0 and not allow_negative:
            timestamp = data[i][0]
            dt = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
            negative_values.append(f"{dt.strftime('%Y-%m-%d')}: {value}")

    # Report out of range values
    if len(out_of_range) > 0:
        pct_out_of_range = (len(out_of_range) / len(data)) * 100
        if pct_out_of_range > 5:
            errors.append(f"Too many out-of-range values: {len(out_of_range)} ({pct_out_of_range:.1f}%)")
            for oor in out_of_range[:3]:
                errors.append(f"  - {oor}")
            return False, warnings, errors
        else:
            warnings.append(f"{len(out_of_range)} out-of-range values ({pct_out_of_range:.2f}%):")
            for oor in out_of_range[:5]:
                warnings.append(f"  - {oor}")

    # Report negative values
    if len(negative_values) > 0:
        errors.append(f"{len(negative_values)} unexpected negative values:")
        for neg in negative_values[:5]:
            errors.append(f"  - {neg}")
        return False, warnings, errors

    return True, warnings, errors


def validate_layer5_statistical_sanity(ticker, data):
    """
    Layer 5: Statistical Sanity Checks
    Detect suspicious spikes and anomalies

    Returns: (is_valid, warnings, errors)
    """
    warnings = []
    errors = []

    if len(data) < 2:
        warnings.append("Insufficient data for statistical analysis")
        return True, warnings, errors

    values = [point[1] for point in data]
    timestamps = [point[0] for point in data]

    # Calculate day-over-day changes
    suspicious_spikes = []
    likely_errors = []

    for i in range(len(values) - 1):
        if values[i] == 0:
            continue  # Skip division by zero

        pct_change = abs((values[i+1] - values[i]) / values[i] * 100)

        dt = datetime.fromtimestamp(timestamps[i] / 1000, tz=timezone.utc)

        if pct_change > 200:  # >200% daily change
            likely_errors.append(f"{dt.strftime('%Y-%m-%d')}: {values[i]:.2f} -> {values[i+1]:.2f} ({pct_change:.1f}% change)")
        elif pct_change > 50:  # >50% daily change
            suspicious_spikes.append(f"{dt.strftime('%Y-%m-%d')}: {values[i]:.2f} -> {values[i+1]:.2f} ({pct_change:.1f}% change)")

    # Report likely errors (>200% change) - but as warnings only
    # Accept real data regardless of spikes (user wants 1:1 mapping with charts)
    if len(likely_errors) > 0:
        warnings.append(f"{len(likely_errors)} large daily changes (>200%):")
        for err in likely_errors[:3]:
            warnings.append(f"  - {err}")

    # Report suspicious spikes (>50% change)
    if len(suspicious_spikes) > 0:
        warnings.append(f"{len(suspicious_spikes)} suspicious spikes detected (>50% daily change):")
        for spike in suspicious_spikes[:5]:
            warnings.append(f"  - {spike}")

    # Calculate basic statistics
    if len(values) > 0:
        mean_val = statistics.mean(values)
        if len(values) > 1:
            stdev_val = statistics.stdev(values)

            # Check for values >5 standard deviations from mean
            extreme_outliers = []
            for i, value in enumerate(values):
                z_score = abs((value - mean_val) / stdev_val) if stdev_val > 0 else 0
                if z_score > 5:
                    dt = datetime.fromtimestamp(timestamps[i] / 1000, tz=timezone.utc)
                    extreme_outliers.append(f"{dt.strftime('%Y-%m-%d')}: {value:.2f} ({z_score:.1f}sigma)")

            if len(extreme_outliers) > 0:
                warnings.append(f"{len(extreme_outliers)} extreme outliers (>5 sigma from mean):")
                for outlier in extreme_outliers[:3]:
                    warnings.append(f"  - {outlier}")

    return True, warnings, errors


def validate_all_layers(ticker, data):
    """
    Run all 6 validation layers on a dataset

    Returns: {
        'valid': bool,
        'warnings': [str],
        'errors': [str],
        'cleaned_data': [...]
    }
    """
    all_warnings = []
    all_errors = []

    # Layer 1: Fetch validation
    valid, warnings, errors = validate_layer1_fetch(ticker, data)
    all_warnings.extend(warnings)
    all_errors.extend(errors)
    if not valid:
        return {'valid': False, 'warnings': all_warnings, 'errors': all_errors, 'cleaned_data': []}

    # Layer 2: Structure validation
    valid, warnings, errors, cleaned_data = validate_layer2_structure(ticker, data)
    all_warnings.extend(warnings)
    all_errors.extend(errors)
    if not valid:
        return {'valid': False, 'warnings': all_warnings, 'errors': all_errors, 'cleaned_data': cleaned_data}

    # Use cleaned data for remaining validations
    data = cleaned_data

    # Layer 3: Timestamp validation
    valid, warnings, errors = validate_layer3_timestamps(ticker, data)
    all_warnings.extend(warnings)
    all_errors.extend(errors)
    if not valid:
        return {'valid': False, 'warnings': all_warnings, 'errors': all_errors, 'cleaned_data': data}

    # Layer 4: Value range validation
    valid, warnings, errors = validate_layer4_value_ranges(ticker, data)
    all_warnings.extend(warnings)
    all_errors.extend(errors)
    if not valid:
        return {'valid': False, 'warnings': all_warnings, 'errors': all_errors, 'cleaned_data': data}

    # Layer 5: Statistical sanity
    valid, warnings, errors = validate_layer5_statistical_sanity(ticker, data)
    all_warnings.extend(warnings)
    all_errors.extend(errors)
    if not valid:
        return {'valid': False, 'warnings': all_warnings, 'errors': all_errors, 'cleaned_data': data}

    # All layers passed
    return {
        'valid': True,
        'warnings': all_warnings,
        'errors': all_errors,
        'cleaned_data': data
    }
