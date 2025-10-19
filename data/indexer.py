# data/indexer.py
"""
Data Indexing Module
Transforms any dataset to an indexed baseline (default 100) for performance comparison.
This allows comparing assets with vastly different magnitudes on the same chart.
"""

def index_to_baseline(data, baseline=100):
    """
    Indexes a dataset to a baseline value (typically 100).

    The first data point is set to the baseline value, and all subsequent
    points are calculated as: baseline * (current_value / first_value)

    This shows percentage changes from the starting point, making it easy
    to compare different assets regardless of their absolute values.

    Args:
        data: Either:
              - Simple: [[timestamp, value], ...]
              - Bollinger Bands: {'upper': [...], 'middle': [...], 'lower': [...]}
        baseline: The value to set the first data point to (default: 100)

    Returns:
        Indexed data in the same format as input

    Examples:
        >>> data = [[1000, 50], [2000, 55], [3000, 45]]
        >>> indexed = index_to_baseline(data, 100)
        >>> # Result: [[1000, 100], [2000, 110], [3000, 90]]
    """

    # Handle empty data
    if not data:
        return data

    # Handle Bollinger Bands special case
    if isinstance(data, dict) and 'middle' in data:
        return index_bollinger_bands(data, baseline)

    # Handle simple data structure: [[timestamp, value], ...]
    if not isinstance(data, list) or len(data) == 0:
        return data

    # Get the first value as the reference point
    first_point = data[0]
    if not isinstance(first_point, (list, tuple)) or len(first_point) < 2:
        print(f"Warning: Invalid data structure for indexing: {first_point}")
        return data

    first_value = float(first_point[1])

    # Avoid division by zero
    if first_value == 0:
        print("Warning: First value is 0, cannot index. Returning original data.")
        return data

    # Calculate indexed values
    indexed_data = []
    for point in data:
        if not isinstance(point, (list, tuple)) or len(point) < 2:
            continue

        timestamp = point[0]
        current_value = float(point[1])

        # Calculate indexed value: baseline * (current / first)
        indexed_value = baseline * (current_value / first_value)

        indexed_data.append([timestamp, indexed_value])

    return indexed_data


def index_bollinger_bands(bb_data, baseline=100):
    """
    Indexes Bollinger Bands data.

    All three bands (upper, middle, lower) are indexed relative to the
    first middle value. This maintains the relative structure of the bands
    while normalizing to the baseline.

    Args:
        bb_data: Dictionary with 'upper', 'middle', 'lower' keys
        baseline: The baseline value (default: 100)

    Returns:
        Dictionary with indexed upper, middle, and lower bands
    """

    if not bb_data or 'middle' not in bb_data:
        return bb_data

    middle_data = bb_data.get('middle', [])
    upper_data = bb_data.get('upper', [])
    lower_data = bb_data.get('lower', [])

    if not middle_data or len(middle_data) == 0:
        return bb_data

    # Use the first middle value as the reference
    first_middle_value = float(middle_data[0][1])

    if first_middle_value == 0:
        print("Warning: First Bollinger Band middle value is 0, cannot index.")
        return bb_data

    # Index all three bands using the same reference point
    indexed_bb = {
        'upper': index_band(upper_data, first_middle_value, baseline),
        'middle': index_band(middle_data, first_middle_value, baseline),
        'lower': index_band(lower_data, first_middle_value, baseline)
    }

    return indexed_bb


def index_band(band_data, reference_value, baseline=100):
    """
    Helper function to index a single band.

    Args:
        band_data: [[timestamp, value], ...]
        reference_value: The reference value to index against
        baseline: The baseline value

    Returns:
        Indexed band data
    """
    indexed_band = []

    for point in band_data:
        if not isinstance(point, (list, tuple)) or len(point) < 2:
            continue

        timestamp = point[0]
        current_value = float(point[1])

        # Calculate indexed value relative to reference
        indexed_value = baseline * (current_value / reference_value)

        indexed_band.append([timestamp, indexed_value])

    return indexed_band


def reindex_from_timestamp(data, start_timestamp, baseline=100):
    """
    Re-indexes data starting from a specific timestamp.

    This is useful for aligning multiple datasets to start from the same point.
    All data before start_timestamp is discarded.

    Args:
        data: [[timestamp, value], ...] or Bollinger Bands dict
        start_timestamp: The timestamp (in ms) to start indexing from
        baseline: The baseline value (default: 100)

    Returns:
        Indexed data starting from the specified timestamp
    """
    # Handle empty data
    if not data:
        return data

    # Handle Bollinger Bands
    if isinstance(data, dict) and 'middle' in data:
        return {
            'upper': reindex_from_timestamp(data['upper'], start_timestamp, baseline),
            'middle': reindex_from_timestamp(data['middle'], start_timestamp, baseline),
            'lower': reindex_from_timestamp(data['lower'], start_timestamp, baseline)
        }

    # Filter data to only include points >= start_timestamp
    filtered_data = [point for point in data if point[0] >= start_timestamp]

    if not filtered_data:
        return []

    # Index from the first point in filtered data
    return index_to_baseline(filtered_data, baseline)


def calculate_percentage_change(data):
    """
    Alternative approach: Calculate percentage change from first value.

    This is similar to indexing but returns actual percentage values
    instead of an indexed baseline.

    Args:
        data: [[timestamp, value], ...]

    Returns:
        [[timestamp, percentage_change], ...]

    Example:
        >>> data = [[1000, 100], [2000, 110], [3000, 90]]
        >>> pct_change = calculate_percentage_change(data)
        >>> # Result: [[1000, 0], [2000, 10], [3000, -10]]
    """
    if not data or len(data) == 0:
        return data

    first_value = float(data[0][1])

    if first_value == 0:
        return data

    pct_data = []
    for point in data:
        timestamp = point[0]
        current_value = float(point[1])

        # Calculate percentage change
        pct_change = ((current_value - first_value) / first_value) * 100

        pct_data.append([timestamp, pct_change])

    return pct_data
