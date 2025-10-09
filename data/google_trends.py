"""
Google Trends Data Plugin

Fetches historical Google Trends data using a stitching method to handle long timeframes.
Data is fetched in 6-month chunks to avoid API truncation and rate limiting issues.
"""

from pytrends.request import TrendReq
import pandas as pd
from datetime import datetime, timedelta
import time
import sys
import io
from .cache_manager import load_from_cache, save_to_cache

# Fix UTF-8 encoding for Windows console output
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


def get_metadata():
    """Returns display metadata for the frontend"""
    return {
        'label': 'Google Trends (Ethereum)',
        'yAxisId': 'indicator',
        'yAxisLabel': 'Search Interest',
        'unit': '',
        'color': '#4285F4',  # Google Blue
        'chartType': 'line',
        'yDomain': [0, 100]  # Google Trends is normalized 0-100
    }


def get_data(days='365', keyword='ethereum'):
    """
    Fetches Google Trends data using a stitching method for long timeframes.

    RATE LIMIT HANDLING:
    - Fetches data in 6-month chunks to avoid API truncation
    - Adds 15-second cooldown between chunks to prevent rate limiting
    - Works backward from present to oldest data
    - Continues fetching even if individual chunks fail
    - Caches successful fetches for offline fallback

    Args:
        days: Number of days of historical data to fetch (default: '365')
        keyword: Search term to query (default: 'ethereum')

    Returns:
        dict: {
            'metadata': {...},
            'data': [[timestamp_ms, trend_value], ...],
            'structure': 'simple'
        }

    Note: Returns cached data if API fails completely. Returns empty data only if both API and cache fail.
    """
    dataset_name = f'google_trends_{keyword}_{days}'
    metadata = get_metadata()

    try:
        # Initialize pytrends
        pytrends = TrendReq(hl='en-US', tz=0)

        # Calculate date ranges
        end_date = datetime.now()
        days_int = int(days) if days != 'max' else 365 * 5
        start_date = end_date - timedelta(days=days_int)

        # Storage for all chunks
        all_dataframes = []

        # Generate 6-month chunks (working backward from end_date)
        current_end = end_date
        chunk_size_days = 180  # Approximately 6 months
        COOLDOWN_SECONDS = 15  # Cooldown between API calls to avoid rate limiting
        INITIAL_DELAY = 3  # Initial delay before first request

        print(f"Fetching Google Trends data for '{keyword}' from {start_date.date()} to {end_date.date()}...")
        print(f"  Using {COOLDOWN_SECONDS}s cooldown between chunks to avoid rate limits")
        print(f"  Waiting {INITIAL_DELAY}s before first request...")
        time.sleep(INITIAL_DELAY)

        chunk_count = 0
        while current_end > start_date:
            chunk_count += 1

            # Calculate chunk start date (6 months before current_end)
            current_start = current_end - timedelta(days=chunk_size_days)

            # Don't go before the overall start_date
            if current_start < start_date:
                current_start = start_date

            # Format timeframe string for pytrends
            timeframe_str = f"{current_start.strftime('%Y-%m-%d')} {current_end.strftime('%Y-%m-%d')}"

            print(f"  Fetching chunk #{chunk_count}: {timeframe_str}")

            try:
                # Build payload and fetch data for this chunk
                pytrends.build_payload(
                    kw_list=[keyword],
                    cat=0,
                    timeframe=timeframe_str,
                    geo='',
                    gprop=''
                )

                # Get interest over time
                chunk_df = pytrends.interest_over_time()

                # Store the chunk if it has data
                if chunk_df is not None and not chunk_df.empty:
                    # Remove the 'isPartial' column if present
                    if 'isPartial' in chunk_df.columns:
                        chunk_df = chunk_df.drop(columns=['isPartial'])

                    all_dataframes.append(chunk_df)
                    print(f"    ✅ Retrieved {len(chunk_df)} data points")
                else:
                    print(f"    ⚠️  No data returned for this chunk")

            except Exception as chunk_error:
                # Log error but continue to next chunk
                print(f"    ❌ Error fetching chunk: {type(chunk_error).__name__}: {str(chunk_error)}")
                print(f"    Continuing to next chunk...")

            # Crucial rate limiting - wait after each API call
            # Only sleep if there are more chunks to fetch
            if current_end > start_date:
                print(f"    Cooling down for {COOLDOWN_SECONDS} seconds...")
                time.sleep(COOLDOWN_SECONDS)

            # Move to the next chunk (moving backward in time)
            current_end = current_start - timedelta(days=1)

        # Combine all chunks
        if not all_dataframes:
            print("⚠️  Warning: No data retrieved from Google Trends")
            print("    This may be due to rate limiting. Checking cache...")

            # Try to load from cache
            cached_data = load_from_cache(dataset_name)
            if cached_data:
                print(f"    ✓ Loaded {len(cached_data)} cached data points")
                return {
                    'metadata': metadata,
                    'data': cached_data,
                    'structure': 'simple'
                }
            else:
                print("    No cached data available. Try again later.")
                return {
                    'metadata': metadata,
                    'data': [],
                    'structure': 'simple'
                }

        # Concatenate all dataframes
        combined_df = pd.concat(all_dataframes, axis=0)

        # Remove duplicates (keep first occurrence)
        combined_df = combined_df[~combined_df.index.duplicated(keep='first')]

        # Sort by date (ascending order)
        combined_df = combined_df.sort_index()

        # Convert to the required format: [[timestamp_ms, value], ...]
        data_points = []
        for timestamp, row in combined_df.iterrows():
            # Convert pandas Timestamp to milliseconds since epoch
            timestamp_ms = int(timestamp.timestamp() * 1000)

            # Get the trend value for the keyword
            trend_value = row[keyword] if keyword in row else 0

            data_points.append([timestamp_ms, float(trend_value)])

        print(f"✅ Successfully fetched {len(data_points)} total data points for '{keyword}'")
        print(f"   Date range: {combined_df.index.min()} to {combined_df.index.max()}")

        # Save to cache for future use
        save_to_cache(dataset_name, data_points)
        print(f"   💾 Cached {len(data_points)} data points")

        return {
            'metadata': metadata,
            'data': data_points,
            'structure': 'simple'
        }

    except Exception as e:
        # Robust error handling: try cache first, then return empty
        print(f"❌ ERROR in Google Trends API: {type(e).__name__}: {str(e)}")
        print("   Attempting to load from cache...")

        # Try to load from cache
        cached_data = load_from_cache(dataset_name)
        if cached_data:
            print(f"   ✓ Loaded {len(cached_data)} cached data points")
            return {
                'metadata': metadata,
                'data': cached_data,
                'structure': 'simple'
            }
        else:
            print("   No cached data available")
            print("   If this is a rate limit error, wait 60 seconds and try again")
            return {
                'metadata': metadata,
                'data': [],
                'structure': 'simple'
            }


# For testing purposes
if __name__ == '__main__':
    result = get_data(days='365', keyword='ethereum')
    print(f"\nMetadata: {result['metadata']}")
    print(f"Data points: {len(result['data'])}")
    if result['data']:
        print(f"First point: {result['data'][0]}")
        print(f"Last point: {result['data'][-1]}")
