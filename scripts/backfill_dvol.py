"""
Backfill script for DVOL (Deribit Volatility Index) historical data.

Fetches 36 months of DVOL data for BTC (and optionally ETH) from Deribit API.

Data Source: Deribit API (free, no API key required)
Time Range: 36 months (1095 days)
Output Files:
    - historical_data/dvol_btc.json
    - historical_data/dvol_eth.json (if enabled)

DVOL is Deribit's implied volatility index, calculated from option prices.
It represents the market's expectation of 30-day future volatility.
"""

import json
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from data.deribit_utils import fetch_dvol_with_stitching
from data.derivatives_config import DEFAULT_DAYS_BACK, CACHE_DIR


def backfill_dvol(currency: str, days_back: int = DEFAULT_DAYS_BACK):
    """
    Backfill DVOL data for a specific currency.

    Args:
        currency: 'BTC' or 'ETH'
        days_back: Number of days to fetch (default: 1095 = 36 months)
    """
    print(f"\n{'='*60}")
    print(f"Starting DVOL backfill for {currency}")
    print(f"Days back: {days_back} ({days_back/30:.1f} months)")
    print(f"{'='*60}\n")

    try:
        # Fetch historical data with automatic stitching
        data = fetch_dvol_with_stitching(currency, days_back)

        if not data:
            print(f"Error: No data fetched for {currency}")
            return False

        # Prepare output file
        output_file = Path(CACHE_DIR) / f"dvol_{currency.lower()}.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Save to JSON
        print(f"\nSaving to {output_file}...")
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"Saved {len(data)} data points")

        # Display statistics
        if data:
            values = [point[1] for point in data]
            print(f"\nDVOL Statistics for {currency}:")
            print(f"  Min: {min(values):.2f}")
            print(f"  Max: {max(values):.2f}")
            print(f"  Average: {sum(values)/len(values):.2f}")
            print(f"  Latest: {values[-1]:.2f}")

        return True

    except Exception as e:
        print(f"\nError during {currency} backfill: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main backfill execution."""
    print("="*60)
    print("DVOL INDEX BACKFILL")
    print("="*60)

    # Backfill BTC DVOL (required)
    btc_success = backfill_dvol('BTC')

    # Optionally backfill ETH DVOL
    # Uncomment the next line if you want ETH DVOL data
    # eth_success = backfill_dvol('ETH')

    print(f"\n{'='*60}")
    print("BACKFILL COMPLETE")
    print(f"{'='*60}")
    print(f"BTC DVOL: {'SUCCESS' if btc_success else 'FAILED'}")
    # print(f"ETH DVOL: {'SUCCESS' if eth_success else 'FAILED'}")

    if btc_success:
        print("\nOutput files:")
        print(f"  - {CACHE_DIR}/dvol_btc.json")
        # print(f"  - {CACHE_DIR}/dvol_eth.json")
    else:
        print("\nBackfill failed - check errors above")
        sys.exit(1)


if __name__ == "__main__":
    main()
