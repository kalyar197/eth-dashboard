# data/time_transformer.py
"""
Time standardization module for CoinAPI data
Ensures all timestamps are normalized to daily UTC boundaries
"""

from datetime import datetime, timezone, timedelta

def standardize_to_daily_utc(raw_data):
    """
    Takes raw data in the format [[timestamp, value], ...] and standardizes it.
    
    The goal is to eliminate all time-of-day discrepancies by forcing every
    timestamp to the beginning of its UTC day (00:00:00).
    
    This is critical for the dashboard to ensure all datasets align properly.
    
    Args:
        raw_data (list): A list of lists, where each inner list is
                         [unix_millisecond_timestamp, value].
    
    Returns:
        list: A standardized list of lists in the same format.
    """
    if not raw_data:
        return []
    
    standardized_data = []
    seen_dates = set()
    
    for item in raw_data:
        # Handle different input formats
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            ms_timestamp, value = item[0], item[1]
        else:
            print(f"Warning: Skipping invalid data point: {item}")
            continue
        
        # Validate timestamp
        if not isinstance(ms_timestamp, (int, float)):
            print(f"Warning: Invalid timestamp: {ms_timestamp}")
            continue
        
        # Convert from milliseconds to a Python datetime object, assuming UTC
        try:
            # Handle both millisecond and second timestamps
            if ms_timestamp > 1000000000000:  # Milliseconds
                dt_object = datetime.fromtimestamp(ms_timestamp / 1000, tz=timezone.utc)
            else:  # Seconds
                dt_object = datetime.fromtimestamp(ms_timestamp, tz=timezone.utc)
        except (ValueError, OSError) as e:
            print(f"Warning: Could not parse timestamp {ms_timestamp}: {e}")
            continue
        
        # CRITICAL STEP: Normalize the timestamp by removing the time part.
        # This snaps the timestamp to the beginning of the UTC day.
        normalized_dt = dt_object.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Check for duplicates on the same day
        # If we have multiple data points for the same day, keep the first one
        if normalized_dt in seen_dates:
            continue
        seen_dates.add(normalized_dt)
        
        # Convert the normalized datetime object back to a millisecond timestamp
        standardized_ms_timestamp = int(normalized_dt.timestamp() * 1000)
        
        # Validate the value
        if value is None or (isinstance(value, str) and not value.strip()):
            print(f"Warning: Invalid value for date {normalized_dt.date()}: {value}")
            continue
        
        # Try to convert value to float
        try:
            numeric_value = float(value)
        except (ValueError, TypeError):
            print(f"Warning: Could not convert value to number: {value}")
            continue
        
        # Append the fully standardized data point
        standardized_data.append([standardized_ms_timestamp, numeric_value])
    
    # Sort by timestamp to ensure chronological order
    standardized_data.sort(key=lambda x: x[0])
    
    # Fill gaps in data (optional - ensures continuous daily data)
    if len(standardized_data) > 1:
        filled_data = fill_daily_gaps(standardized_data)
        return filled_data
    
    return standardized_data

def fill_daily_gaps(data):
    """
    Fill gaps in daily data with interpolated values.
    This ensures we have continuous daily data without gaps.
    
    Args:
        data (list): Sorted list of [timestamp, value] pairs
    
    Returns:
        list: Data with gaps filled
    """
    if len(data) < 2:
        return data
    
    filled_data = []
    
    for i in range(len(data) - 1):
        current_point = data[i]
        next_point = data[i + 1]
        
        filled_data.append(current_point)
        
        # Check for gap
        current_date = datetime.fromtimestamp(current_point[0] / 1000, tz=timezone.utc)
        next_date = datetime.fromtimestamp(next_point[0] / 1000, tz=timezone.utc)
        
        days_diff = (next_date - current_date).days
        
        # If there's a gap of more than 1 day, fill it
        if days_diff > 1:
            # Linear interpolation for missing days
            value_diff = next_point[1] - current_point[1]
            value_step = value_diff / days_diff
            
            for j in range(1, days_diff):
                gap_date = current_date + timedelta(days=j)
                gap_timestamp = int(gap_date.timestamp() * 1000)
                interpolated_value = current_point[1] + (value_step * j)
                
                filled_data.append([gap_timestamp, interpolated_value])
                
                # Log gap filling for transparency
                if j == 1:  # Only log once per gap
                    print(f"Info: Filled {days_diff - 1} day gap between {current_date.date()} and {next_date.date()}")
    
    # Add the last point
    filled_data.append(data[-1])
    
    return filled_data

def validate_daily_alignment(data):
    """
    Validate that all data points are properly aligned to daily boundaries.
    
    Args:
        data (list): List of [timestamp, value] pairs
    
    Returns:
        bool: True if all timestamps are at 00:00:00 UTC
    """
    for point in data:
        timestamp_ms = point[0]
        dt = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
        
        if dt.hour != 0 or dt.minute != 0 or dt.second != 0 or dt.microsecond != 0:
            print(f"Warning: Timestamp not aligned to daily boundary: {dt}")
            return False
    
    return True

def get_date_range(data):
    """
    Get the date range of the dataset.
    
    Args:
        data (list): List of [timestamp, value] pairs
    
    Returns:
        tuple: (start_date, end_date) as datetime objects
    """
    if not data:
        return None, None
    
    start_timestamp = data[0][0]
    end_timestamp = data[-1][0]
    
    start_date = datetime.fromtimestamp(start_timestamp / 1000, tz=timezone.utc)
    end_date = datetime.fromtimestamp(end_timestamp / 1000, tz=timezone.utc)
    
    return start_date, end_date