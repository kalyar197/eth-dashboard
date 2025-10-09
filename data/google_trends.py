"""
Google Trends Data Plugin

Fetches historical Google Trends data using a stitching method to handle long timeframes.
Data is fetched in 6-month chunks to avoid API truncation and rate limiting issues.
"""

from pytrends.request import TrendReq
import pandas as pd
from datetime import datetime, timedelta
import time


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


def get_data(keyword='ethereum', timeframe_years=5):
    """
    Fetches Google Trends data using a stitching method for long timeframes.

    Args:
        keyword: Search term to query (default: 'ethereum')
        timeframe_years: Number of years of historical data to fetch (default: 5)

    Returns:
        dict: {
            'metadata': {...},
            'data': [[timestamp_ms, trend_value], ...],
            'structure': 'simple'
        }

    Note: Returns empty data list on any API errors to comply with error handling requirements.
    """
    try:
        # Initialize pytrends
        pytrends = TrendReq(hl='en-US', tz=0)

        # Calculate date ranges
        end_date = datetime.now()
        start_date = end_date - timedelta(days=timeframe_years * 365)

        # Storage for all chunks
        all_dataframes = []

        # Generate 6-month chunks (working backward from end_date)
        current_end = end_date
        chunk_size_days = 180  # Approximately 6 months

        print(f"Fetching Google Trends data for '{keyword}' from {start_date.date()} to {end_date.date()}...")

        while current_end > start_date:
            # Calculate chunk start date (6 months before current_end)
            current_start = current_end - timedelta(days=chunk_size_days)

            # Don't go before the overall start_date
            if current_start < start_date:
                current_start = start_date

            # Format timeframe string for pytrends
            timeframe_str = f"{current_start.strftime('%Y-%m-%d')} {current_end.strftime('%Y-%m-%d')}"

            print(f"  Fetching chunk: {timeframe_str}")

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

            # Crucial rate limiting - wait 5 seconds after each API call
            time.sleep(5)

            # Store the chunk if it has data
            if chunk_df is not None and not chunk_df.empty:
                # Remove the 'isPartial' column if present
                if 'isPartial' in chunk_df.columns:
                    chunk_df = chunk_df.drop(columns=['isPartial'])

                all_dataframes.append(chunk_df)
                print(f"    Retrieved {len(chunk_df)} data points")
            else:
                print(f"    No data returned for this chunk")

            # Move to the next chunk (moving backward in time)
            current_end = current_start - timedelta(days=1)

        # Combine all chunks
        if not all_dataframes:
            print("Warning: No data retrieved from Google Trends")
            return {
                'metadata': get_metadata(),
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

        print(f"Successfully fetched {len(data_points)} total data points for '{keyword}'")

        return {
            'metadata': get_metadata(),
            'data': data_points,
            'structure': 'simple'
        }

    except Exception as e:
        # Robust error handling: fail cleanly and return empty data
        print(f"ERROR in Google Trends API: {type(e).__name__}: {str(e)}")
        print("Returning empty dataset due to API failure")

        return {
            'metadata': get_metadata(),
            'data': [],
            'structure': 'simple'
        }


# For testing purposes
if __name__ == '__main__':
    result = get_data(keyword='ethereum', timeframe_years=5)
    print(f"\nMetadata: {result['metadata']}")
    print(f"Data points: {len(result['data'])}")
    if result['data']:
        print(f"First point: {result['data'][0]}")
        print(f"Last point: {result['data'][-1]}")
