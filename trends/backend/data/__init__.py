# trends/backend/data/__init__.py
"""Data module for Google Trends system."""

from .trends_fetcher import TrendsFetcher
from .storage import (
    load_trend_data,
    save_trend_data,
    load_keywords,
    save_keywords,
    load_fetch_status,
    save_fetch_status,
    add_fetch_status_entry
)

__all__ = [
    'TrendsFetcher',
    'load_trend_data',
    'save_trend_data',
    'load_keywords',
    'save_keywords',
    'load_fetch_status',
    'save_fetch_status',
    'add_fetch_status_entry'
]
