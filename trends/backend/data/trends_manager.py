# trends/backend/data/trends_manager.py
"""
Keyword management and orchestration for Google Trends fetching.

Handles:
- Keyword CRUD operations
- Multi-region fetch orchestration
- Status tracking and error handling
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List

from .trends_fetcher import TrendsFetcher
from .storage import (
    load_keywords,
    save_keywords,
    save_trend_data,
    load_trend_data,
    add_fetch_status_entry
)

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import GEO_CODES, ALL_REGION_CODES


class TrendsManager:
    """Manages keywords and orchestrates Google Trends data fetching."""

    def __init__(self):
        """Initialize with trends fetcher."""
        self.fetcher = TrendsFetcher()

    def get_all_keywords(self) -> List[Dict[str, Any]]:
        """
        Get list of all keywords with metadata.

        Returns:
            List of keyword dictionaries
        """
        return load_keywords()

    def get_keyword_by_id(self, keyword_id: str) -> Dict[str, Any]:
        """
        Get specific keyword by ID.

        Args:
            keyword_id: Unique keyword identifier

        Returns:
            Keyword dictionary or None if not found
        """
        keywords = load_keywords()
        for kw in keywords:
            if kw['id'] == keyword_id:
                return kw
        return None

    def add_keyword(self, keyword: str) -> Dict[str, Any]:
        """
        Add new keyword and trigger fetch across all regions.

        Args:
            keyword: Search term to add

        Returns:
            Created keyword dictionary with status

        Raises:
            ValueError: If keyword already exists
        """
        keywords = load_keywords()

        # Check for duplicates
        for kw in keywords:
            if kw['keyword'].lower() == keyword.lower():
                raise ValueError(f"Keyword '{keyword}' already exists")

        # Create keyword entry
        keyword_entry = {
            'id': str(uuid.uuid4()),
            'keyword': keyword,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'last_updated': datetime.now(timezone.utc).isoformat(),
            'status': 'in_progress',
            'regions': ALL_REGION_CODES,
            'completed_regions': [],
            'failed_regions': []
        }

        keywords.append(keyword_entry)
        save_keywords(keywords)

        print(f"\n[Trends Manager] Added keyword '{keyword}' (ID: {keyword_entry['id']})")
        print(f"[Trends Manager] Starting fetch for {len(ALL_REGION_CODES)} regions...\n")

        # Fetch data for all regions
        self._fetch_all_regions(keyword_entry)

        # Update final status
        keyword_entry = self._update_keyword_status(keyword_entry['id'])

        return keyword_entry

    def delete_keyword(self, keyword_id: str) -> bool:
        """
        Delete keyword and associated data files.

        Args:
            keyword_id: Unique keyword identifier

        Returns:
            True if deleted successfully, False if not found
        """
        keywords = load_keywords()
        keyword_entry = None

        # Find and remove keyword
        for i, kw in enumerate(keywords):
            if kw['id'] == keyword_id:
                keyword_entry = kw
                keywords.pop(i)
                break

        if not keyword_entry:
            return False

        # Save updated keywords list
        save_keywords(keywords)

        # Delete associated data files
        keyword = keyword_entry['keyword']
        base_dir = os.path.dirname(os.path.dirname(__file__))
        deleted_count = 0

        for region in ALL_REGION_CODES:
            filepath = os.path.join(base_dir, 'historical_data', f"trends_{keyword}_{region}.json")
            if os.path.exists(filepath):
                os.remove(filepath)
                deleted_count += 1

        print(f"[Trends Manager] Deleted keyword '{keyword}' and {deleted_count} data files")
        return True

    def _fetch_all_regions(self, keyword_entry: Dict[str, Any]):
        """
        Fetch data for keyword across all regions.

        Args:
            keyword_entry: Keyword dictionary with metadata
        """
        keyword = keyword_entry['keyword']
        keyword_id = keyword_entry['id']

        for i, region in enumerate(ALL_REGION_CODES, 1):
            print(f"\n[Region {i}/{len(ALL_REGION_CODES)}] Fetching '{keyword}' for {region}")
            print(f"-" * 70)

            try:
                # Fetch data
                data = self.fetcher.fetch_daily_data(keyword, region)

                # Save to file
                save_trend_data(keyword, region, data)

                # Update status
                keyword_entry['completed_regions'].append(region)
                add_fetch_status_entry(
                    keyword_id=keyword_id,
                    keyword=keyword,
                    region=region,
                    status='completed',
                    error=None,
                    data_points=len(data)
                )

                print(f"[Region {i}] SUCCESS: {region}\n")

            except Exception as e:
                error_msg = str(e)
                print(f"[Region {i}] FAILED: {region} - {error_msg}\n")

                # Update status
                keyword_entry['failed_regions'].append(region)
                add_fetch_status_entry(
                    keyword_id=keyword_id,
                    keyword=keyword,
                    region=region,
                    status='failed',
                    error=error_msg,
                    data_points=0
                )

    def _update_keyword_status(self, keyword_id: str) -> Dict[str, Any]:
        """
        Update keyword status based on region fetch results.

        Args:
            keyword_id: Unique keyword identifier

        Returns:
            Updated keyword dictionary
        """
        keywords = load_keywords()

        for kw in keywords:
            if kw['id'] == keyword_id:
                # Determine overall status
                total_regions = len(ALL_REGION_CODES)
                completed_count = len(kw['completed_regions'])
                failed_count = len(kw['failed_regions'])

                if completed_count == total_regions:
                    kw['status'] = 'completed'
                elif completed_count > 0:
                    kw['status'] = 'partial'
                else:
                    kw['status'] = 'failed'

                kw['last_updated'] = datetime.now(timezone.utc).isoformat()

                # Save updated keywords
                save_keywords(keywords)

                print(f"\n{'='*70}")
                print(f"[Trends Manager] Final Status for '{kw['keyword']}':")
                print(f"  Status: {kw['status']}")
                print(f"  Completed: {completed_count}/{total_regions} regions")
                print(f"  Failed: {failed_count}/{total_regions} regions")
                print(f"{'='*70}\n")

                return kw

        return None

    def get_trend_data_for_keyword(self, keyword: str) -> Dict[str, List[List]]:
        """
        Get trend data for a keyword across all regions.

        Args:
            keyword: Search term

        Returns:
            Dictionary mapping region codes to data arrays:
            {'US-NY-501': [[timestamp, value], ...], 'CH-ZH': [...], ...}
        """
        result = {}

        for region in ALL_REGION_CODES:
            data = load_trend_data(keyword, region)
            if data:
                result[region] = data

        return result

    def get_trend_data_for_region(self, region: str) -> Dict[str, List[List]]:
        """
        Get trend data for all keywords in a specific region.

        Args:
            region: Geographic code

        Returns:
            Dictionary mapping keywords to data arrays:
            {'bitcoin': [[timestamp, value], ...], 'ethereum': [...], ...}
        """
        result = {}
        keywords = load_keywords()

        for kw_entry in keywords:
            keyword = kw_entry['keyword']
            data = load_trend_data(keyword, region)
            if data:
                result[keyword] = data

        return result

    def get_all_regions(self) -> List[Dict[str, str]]:
        """
        Get list of all configured regions with metadata.

        Returns:
            List of region dictionaries
        """
        regions = []
        for key, info in GEO_CODES.items():
            regions.append({
                'key': key,
                'code': info['code'],
                'label': info['label'],
                'level': info['level'],
                'country': info['country'],
                'note': info.get('note', '')
            })
        return regions
