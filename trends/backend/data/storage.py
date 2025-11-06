# trends/backend/data/storage.py
"""
JSON storage utilities for Google Trends data.

Handles:
- Loading/saving historical trend data
- Keyword metadata management
- Fetch status tracking
"""

import json
import os
from typing import List, Dict, Any
from datetime import datetime, timezone

import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import KEYWORDS_FILE, FETCH_STATUS_FILE, HISTORICAL_DATA_DIR


def ensure_directories():
    """Create necessary directories if they don't exist."""
    base_dir = os.path.dirname(os.path.dirname(__file__))

    dirs = [
        os.path.join(base_dir, 'historical_data'),
        os.path.join(base_dir, 'metadata')
    ]

    for dir_path in dirs:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"[Storage] Created directory: {dir_path}")


def get_trend_data_path(keyword: str, region: str) -> str:
    """
    Get file path for trend data.

    Args:
        keyword: Search term
        region: Geographic code (e.g., 'US-NY-501')

    Returns:
        Absolute path to JSON file
    """
    base_dir = os.path.dirname(os.path.dirname(__file__))
    filename = f"trends_{keyword}_{region}.json"
    return os.path.join(base_dir, HISTORICAL_DATA_DIR, filename)


def load_trend_data(keyword: str, region: str) -> List[List]:
    """
    Load historical trend data for keyword and region.

    Args:
        keyword: Search term
        region: Geographic code

    Returns:
        List of [timestamp_ms, value] pairs, or empty list if file doesn't exist
    """
    filepath = get_trend_data_path(keyword, region)

    if not os.path.exists(filepath):
        return []

    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        print(f"[Storage] Loaded {len(data)} data points from {os.path.basename(filepath)}")
        return data
    except json.JSONDecodeError:
        print(f"[Storage] Warning: Corrupt JSON file {filepath}, returning empty list")
        return []


def save_trend_data(keyword: str, region: str, data: List[List]):
    """
    Save historical trend data for keyword and region.

    Args:
        keyword: Search term
        region: Geographic code
        data: List of [timestamp_ms, value] pairs
    """
    ensure_directories()
    filepath = get_trend_data_path(keyword, region)

    with open(filepath, 'w') as f:
        json.dump(data, f)

    print(f"[Storage] Saved {len(data)} data points to {os.path.basename(filepath)}")


def load_keywords() -> List[Dict[str, Any]]:
    """
    Load keyword metadata.

    Returns:
        List of keyword dictionaries with structure:
        [{id, keyword, created_at, last_updated, status, regions}, ...]
    """
    ensure_directories()
    base_dir = os.path.dirname(os.path.dirname(__file__))
    filepath = os.path.join(base_dir, KEYWORDS_FILE)

    if not os.path.exists(filepath):
        return []

    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        return data.get('keywords', [])
    except json.JSONDecodeError:
        return []


def save_keywords(keywords: List[Dict[str, Any]]):
    """
    Save keyword metadata.

    Args:
        keywords: List of keyword dictionaries
    """
    ensure_directories()
    base_dir = os.path.dirname(os.path.dirname(__file__))
    filepath = os.path.join(base_dir, KEYWORDS_FILE)

    with open(filepath, 'w') as f:
        json.dump({'keywords': keywords}, f, indent=2)

    print(f"[Storage] Saved {len(keywords)} keywords to {KEYWORDS_FILE}")


def load_fetch_status() -> List[Dict[str, Any]]:
    """
    Load fetch status log.

    Returns:
        List of fetch status entries with structure:
        [{keyword_id, keyword, region, status, fetched_at, error, data_points}, ...]
    """
    ensure_directories()
    base_dir = os.path.dirname(os.path.dirname(__file__))
    filepath = os.path.join(base_dir, FETCH_STATUS_FILE)

    if not os.path.exists(filepath):
        return []

    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        return data.get('fetch_log', [])
    except json.JSONDecodeError:
        return []


def save_fetch_status(fetch_log: List[Dict[str, Any]]):
    """
    Save fetch status log.

    Args:
        fetch_log: List of fetch status entries
    """
    ensure_directories()
    base_dir = os.path.dirname(os.path.dirname(__file__))
    filepath = os.path.join(base_dir, FETCH_STATUS_FILE)

    with open(filepath, 'w') as f:
        json.dump({'fetch_log': fetch_log}, f, indent=2)


def add_fetch_status_entry(keyword_id: str, keyword: str, region: str,
                           status: str, error: str = None, data_points: int = 0):
    """
    Add a fetch status entry to the log.

    Args:
        keyword_id: Unique keyword identifier
        keyword: Search term
        region: Geographic code
        status: 'completed', 'failed', 'in_progress'
        error: Error message if failed
        data_points: Number of data points fetched
    """
    fetch_log = load_fetch_status()

    entry = {
        'keyword_id': keyword_id,
        'keyword': keyword,
        'region': region,
        'status': status,
        'fetched_at': datetime.now(timezone.utc).isoformat(),
        'error': error,
        'data_points': data_points
    }

    fetch_log.append(entry)
    save_fetch_status(fetch_log)

    print(f"[Storage] Added fetch status: {keyword} @ {region} = {status}")
