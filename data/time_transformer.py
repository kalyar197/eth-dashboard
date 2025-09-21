# data/time_transformer.py

from datetime import datetime, timezone

def standardize_to_daily_utc(raw_data):
    """
    Takes raw data in the format [[timestamp, value], ...] and standardizes it.

    The goal is to eliminate all time-of-day discrepancies by forcing every
    timestamp to the beginning of its UTC day (00:00:00).

    Args:
        raw_data (list): A list of lists, where each inner list is
                         [unix_millisecond_timestamp, value].

    Returns:
        list: A standardized list of lists in the same format.
    """
    standardized_data = []
    seen_dates = set()

    for item in raw_data:
        # 1. Unpack timestamp and value
        ms_timestamp, value = item

        # 2. Convert from milliseconds to a Python datetime object, assuming UTC
        dt_object = datetime.fromtimestamp(ms_timestamp / 1000, tz=timezone.utc)

        # 3. CRITICAL STEP: Normalize the timestamp by removing the time part.
        #    This snaps the timestamp to the beginning of the UTC day.
        normalized_dt = dt_object.replace(hour=0, minute=0, second=0, microsecond=0)

        # 4. Check for duplicates on the same day (some APIs give multiple points)
        if normalized_dt in seen_dates:
            continue
        seen_dates.add(normalized_dt)

        # 5. Convert the normalized datetime object back to a millisecond timestamp
        standardized_ms_timestamp = int(normalized_dt.timestamp() * 1000)

        # 6. Append the fully standardized data point
        standardized_data.append([standardized_ms_timestamp, value])

    # Sort by timestamp to ensure chronological order
    standardized_data.sort(key=lambda x: x[0])
    return standardized_data