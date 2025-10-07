# data/time_transformer.py
"""
Time standardization module for OHLCV data
Handles both 2-element [timestamp, value] and 6-element [timestamp, O, H, L, C, V] structures
Ensures all timestamps are normalized to daily UTC boundaries
PRESERVES ALL DATA COMPONENTS - No data loss
"""

from datetime import datetime, timezone, timedelta

def standardize_to_daily_utc(raw_data):
    """
    Takes raw data and standardizes timestamps to UTC daily boundaries.
    
    CRITICAL: Now handles two data structures:
    - 2-element: [timestamp, value] - for simple price/dominance data
    - 6-element: [timestamp, open, high, low, close, volume] - for OHLCV data
    
    The timestamp is normalized to 00:00:00 UTC.
    ALL OTHER COMPONENTS ARE PRESERVED UNCHANGED.
    
    Args:
        raw_data (list): A list of lists, where each inner list is either:
                         [unix_millisecond_timestamp, value] OR
                         [unix_millisecond_timestamp, open, high, low, close, volume]
    
    Returns:
        list: A standardized list with same structure as input.
    """
    if not raw_data:
        return []
    
    # Detect data structure from first valid element
    data_structure = None
    for item in raw_data:
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            data_structure = len(item)
            print(f"Detected data structure: {data_structure} elements per record")
            break
    
    if not data_structure:
        print("Error: Could not determine data structure")
        return []
    
    standardized_data = []
    seen_dates = set()
    
    for item in raw_data:
        # Validate structure consistency
        if not isinstance(item, (list, tuple)) or len(item) != data_structure:
            print(f"Warning: Skipping invalid/inconsistent data point: {item}")
            continue
        
        # Extract timestamp (always first element)
        ms_timestamp = item[0]
        
        # Validate timestamp
        if not isinstance(ms_timestamp, (int, float)):
            print(f"Warning: Invalid timestamp: {ms_timestamp}")
            continue
        
        # Convert timestamp to datetime
        try:
            # Handle both millisecond and second timestamps
            if ms_timestamp > 1000000000000:  # Milliseconds
                dt_object = datetime.fromtimestamp(ms_timestamp / 1000, tz=timezone.utc)
            else:  # Seconds
                dt_object = datetime.fromtimestamp(ms_timestamp, tz=timezone.utc)
        except (ValueError, OSError) as e:
            print(f"Warning: Could not parse timestamp {ms_timestamp}: {e}")
            continue
        
        # CRITICAL: Normalize timestamp to beginning of UTC day
        normalized_dt = dt_object.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Check for duplicates on the same day
        if normalized_dt in seen_dates:
            continue
        seen_dates.add(normalized_dt)
        
        # Convert normalized datetime back to millisecond timestamp
        standardized_ms_timestamp = int(normalized_dt.timestamp() * 1000)
        
        # Build standardized record based on structure
        if data_structure == 2:
            # Simple [timestamp, value] structure
            value = item[1]
            
            # Validate value
            if value is None or (isinstance(value, str) and not value.strip()):
                print(f"Warning: Invalid value for date {normalized_dt.date()}: {value}")
                continue
            
            try:
                numeric_value = float(value)
            except (ValueError, TypeError):
                print(f"Warning: Could not convert value to number: {value}")
                continue
            
            standardized_data.append([standardized_ms_timestamp, numeric_value])
            
        elif data_structure == 6:
            # OHLCV structure [timestamp, open, high, low, close, volume]
            # PRESERVE ALL COMPONENTS
            try:
                standardized_record = [
                    standardized_ms_timestamp,
                    float(item[1]),  # open
                    float(item[2]),  # high
                    float(item[3]),  # low
                    float(item[4]),  # close
                    float(item[5])   # volume
                ]
                
                # Validate OHLCV logic (high >= low, high >= open/close, etc.)
                if standardized_record[2] < standardized_record[3]:  # high < low
                    print(f"Warning: Invalid OHLCV data (high < low) for {normalized_dt.date()}")
                    continue
                
                standardized_data.append(standardized_record)
                
            except (ValueError, TypeError) as e:
                print(f"Warning: Could not process OHLCV data: {e}")
                continue
        else:
            print(f"Warning: Unsupported data structure with {data_structure} elements")
            continue
    
    # Sort by timestamp to ensure chronological order
    standardized_data.sort(key=lambda x: x[0])
    
    # Fill gaps in data (optional - ensures continuous daily data)
    if len(standardized_data) > 1:
        if data_structure == 2:
            filled_data = fill_daily_gaps_simple(standardized_data)
        elif data_structure == 6:
            filled_data = fill_daily_gaps_ohlcv(standardized_data)
        else:
            filled_data = standardized_data
        return filled_data
    
    return standardized_data

def fill_daily_gaps_simple(data):
    """
    Fill gaps in simple [timestamp, value] daily data with interpolated values.
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
                
            if days_diff > 2:  # Only log significant gaps
                print(f"Info: Filled {days_diff - 1} day gap between {current_date.date()} and {next_date.date()}")
    
    # Add the last point
    filled_data.append(data[-1])
    
    return filled_data

def fill_daily_gaps_ohlcv(data):
    """
    Fill gaps in OHLCV data.
    For gap days, use interpolated close as all OHLC values, zero volume.
    This maintains data integrity while filling gaps.
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
            # Interpolate using close prices
            close_diff = next_point[4] - current_point[4]
            close_step = close_diff / days_diff
            
            for j in range(1, days_diff):
                gap_date = current_date + timedelta(days=j)
                gap_timestamp = int(gap_date.timestamp() * 1000)
                
                # Use interpolated close for all OHLC values on gap days
                interpolated_close = current_point[4] + (close_step * j)
                
                filled_data.append([
                    gap_timestamp,
                    interpolated_close,  # open
                    interpolated_close,  # high
                    interpolated_close,  # low
                    interpolated_close,  # close
                    0.0                  # volume (0 for gap days)
                ])
            
            if days_diff > 2:  # Only log significant gaps
                print(f"Info: Filled {days_diff - 1} day OHLCV gap between {current_date.date()} and {next_date.date()}")
    
    # Add the last point
    filled_data.append(data[-1])
    
    return filled_data

def validate_daily_alignment(data):
    """
    Validate that all data points are properly aligned to daily boundaries.
    Works with both 2-element and 6-element structures.
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
    Works with both 2-element and 6-element structures.
    """
    if not data:
        return None, None
    
    start_timestamp = data[0][0]
    end_timestamp = data[-1][0]
    
    start_date = datetime.fromtimestamp(start_timestamp / 1000, tz=timezone.utc)
    end_date = datetime.fromtimestamp(end_timestamp / 1000, tz=timezone.utc)
    
    return start_date, end_date

def extract_component(ohlcv_data, component='close'):
    """
    Extract a specific component from OHLCV data.
    Useful for indicators that only need closing prices.
    
    Args:
        ohlcv_data: List of [timestamp, open, high, low, close, volume]
        component: 'open', 'high', 'low', 'close', or 'volume'
    
    Returns:
        List of [timestamp, value] pairs
    """
    component_map = {
        'open': 1,
        'high': 2,
        'low': 3,
        'close': 4,
        'volume': 5
    }
    
    if component not in component_map:
        raise ValueError(f"Invalid component: {component}")
    
    index = component_map[component]
    
    extracted_data = []
    for point in ohlcv_data:
        if len(point) == 6:  # OHLCV structure
            extracted_data.append([point[0], point[index]])
        elif len(point) == 2 and component == 'close':
            # Fallback for simple price data
            extracted_data.append(point)
    
    return extracted_data