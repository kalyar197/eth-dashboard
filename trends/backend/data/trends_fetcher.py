# trends/backend/data/trends_fetcher.py
"""
Google Trends data fetcher with batch stitching for daily granularity.

This module handles:
- Fetching daily Google Trends data using pytrends
- Batch stitching to overcome 270-day API limitation
- Overlap normalization for seamless multi-batch data
- Rate limiting to avoid IP blocking
"""

import time
import pandas as pd
from datetime import datetime, timedelta, timezone
from typing import List, Tuple
from pytrends.request import TrendReq

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import MIN_REQUEST_INTERVAL, FETCH_DAYS


class TrendsFetcher:
    """Fetches Google Trends data with automatic batch stitching."""

    def __init__(self):
        """Initialize pytrends client with rate limiting."""
        self.pytrends = TrendReq(hl='en-US', tz=360, timeout=(10, 25))
        self.min_request_interval = MIN_REQUEST_INTERVAL
        self.last_request_time = None

    def _enforce_rate_limit(self):
        """
        Enforce minimum time between requests to avoid Google blocking.
        Waits if necessary to maintain MIN_REQUEST_INTERVAL seconds between calls.
        """
        if self.last_request_time:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.min_request_interval:
                wait_time = self.min_request_interval - elapsed
                print(f"[Rate Limit] Waiting {wait_time:.1f}s before next request...")
                time.sleep(wait_time)
        self.last_request_time = time.time()

    def _create_batches(self, start_date: datetime, end_date: datetime) -> List[Tuple[datetime, datetime]]:
        """
        Split date range into 270-day batches with 1-day overlap.

        Google Trends returns daily data only for timeframes ≤ 270 days.
        We split longer periods into multiple batches and stitch them later.

        Args:
            start_date: Beginning of date range
            end_date: End of date range

        Returns:
            List of (batch_start, batch_end) tuples with 1-day overlaps
        """
        batches = []
        current_start = start_date

        while current_start < end_date:
            current_end = min(current_start + timedelta(days=270), end_date)
            batches.append((current_start, current_end))
            # Move to next batch with 1-day overlap for stitching
            current_start = current_end - timedelta(days=1)

        return batches

    def _stitch_batches(self, batches: List[pd.DataFrame], keyword: str) -> pd.DataFrame:
        """
        Stitch multiple batches together using overlap normalization.

        Google Trends returns relative values (0-100) per batch. The same value
        may represent different absolute volumes across batches. We use overlap
        values as normalization anchors to align scales.

        Algorithm:
        1. Keep first batch as-is (reference scale)
        2. For each subsequent batch:
           - Find overlap date (first date of current batch)
           - Calculate adjustment_factor = prev[overlap] / curr[overlap]
           - Multiply entire current batch by adjustment_factor
           - Append to result (skip overlap day to avoid duplication)

        Args:
            batches: List of DataFrames with 1-day overlap between consecutive batches
            keyword: Column name containing trend values

        Returns:
            Single DataFrame with normalized, stitched data
        """
        if len(batches) == 1:
            return batches[0]

        stitched = batches[0].copy()
        print(f"[Stitch] Starting with batch 1: {len(stitched)} points")

        for i in range(1, len(batches)):
            # Get overlap date (first date of current batch)
            overlap_date = batches[i].index[0]

            # Get values at overlap point
            prev_value = stitched.loc[overlap_date, keyword]
            curr_value = batches[i].loc[overlap_date, keyword]

            # Calculate adjustment factor
            if curr_value > 0:
                adjustment_factor = prev_value / curr_value
            else:
                print(f"[Stitch] Warning: Zero value at overlap {overlap_date}, using factor=1.0")
                adjustment_factor = 1.0

            print(f"[Stitch] Batch {i+1}: overlap_date={overlap_date.date()}, "
                  f"prev={prev_value:.2f}, curr={curr_value:.2f}, "
                  f"adjustment_factor={adjustment_factor:.3f}")

            # Normalize entire current batch
            normalized = batches[i][keyword] * adjustment_factor

            # Append (skip overlap day to avoid duplication)
            stitched = pd.concat([stitched, normalized.iloc[1:]])
            print(f"[Stitch] After batch {i+1}: {len(stitched)} total points")

        return stitched

    def fetch_daily_data(self, keyword: str, geo_code: str, days: int = None) -> List[List]:
        """
        Fetch daily Google Trends data for a keyword and region.

        Handles batch fetching and stitching automatically for date ranges
        exceeding 270 days (Google's daily data limit).

        Args:
            keyword: Search term (e.g., "bitcoin", "ethereum")
            geo_code: Geographic filter (e.g., "US-NY-501", "CH-ZH")
            days: Number of days to fetch (default: FETCH_DAYS from config)

        Returns:
            List of [timestamp_ms, value] pairs sorted ascending
            Format matches Dash oscillator standard: [[1667865600000, 45.2], ...]

        Raises:
            ValueError: If no data returned from any batch
            Exception: If API requests fail
        """
        if days is None:
            days = FETCH_DAYS

        print(f"\n{'='*70}")
        print(f"[Trends Fetcher] Starting fetch for '{keyword}' @ {geo_code}")
        print(f"[Trends Fetcher] Timeframe: {days} days")
        print(f"{'='*70}\n")

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Split into batches if necessary (270-day limit)
        batches_dates = self._create_batches(start_date, end_date)
        print(f"[Trends Fetcher] Split into {len(batches_dates)} batch(es) (max 270 days each)\n")

        # Fetch each batch
        batch_data = []
        for i, (batch_start, batch_end) in enumerate(batches_dates):
            print(f"[Batch {i+1}/{len(batches_dates)}] Fetching {batch_start.date()} to {batch_end.date()}")

            try:
                # Enforce rate limiting before each request
                self._enforce_rate_limit()

                # Build payload and fetch data
                timeframe = f'{batch_start:%Y-%m-%d} {batch_end:%Y-%m-%d}'
                self.pytrends.build_payload(
                    kw_list=[keyword],
                    timeframe=timeframe,
                    geo=geo_code
                )

                df = self.pytrends.interest_over_time()

                if df.empty:
                    print(f"[Batch {i+1}] Warning: No data returned (keyword may have zero search volume)")
                    continue

                # Drop 'isPartial' column if present (not needed)
                if 'isPartial' in df.columns:
                    df = df.drop('isPartial', axis=1)

                batch_data.append(df)
                print(f"[Batch {i+1}] SUCCESS: Fetched {len(df)} data points\n")

            except Exception as e:
                print(f"[Batch {i+1}] ERROR: {e}\n")
                # Continue with other batches instead of failing completely

        if not batch_data:
            raise ValueError(f"No data fetched from any batch for '{keyword}' @ {geo_code}")

        # Stitch batches with overlap normalization
        if len(batch_data) > 1:
            print(f"[Trends Fetcher] Stitching {len(batch_data)} batches...\n")
            stitched_df = self._stitch_batches(batch_data, keyword)
        else:
            stitched_df = batch_data[0]

        # Convert to [[timestamp_ms, value], ...] format (Dash standard)
        data = []
        for timestamp, row in stitched_df.iterrows():
            # Convert to milliseconds Unix timestamp
            timestamp_ms = int(timestamp.timestamp() * 1000)
            # Get trend value (0-100 scale)
            value = float(row[keyword])
            data.append([timestamp_ms, value])

        print(f"{'='*70}")
        print(f"[Trends Fetcher] SUCCESS: {len(data)} data points for '{keyword}' @ {geo_code}")
        print(f"[Trends Fetcher] Date range: {datetime.fromtimestamp(data[0][0]/1000).date()} "
              f"to {datetime.fromtimestamp(data[-1][0]/1000).date()}")
        print(f"[Trends Fetcher] Value range: {min(d[1] for d in data):.2f} - {max(d[1] for d in data):.2f}")
        print(f"{'='*70}\n")

        return data
