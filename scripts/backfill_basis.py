"""
Backfill script for Basis Spread historical data.

Fetches 36 months of basis spread data for BTCUSDT from Binance Futures API.

Data Source: Binance Futures API (free, no API key required)
Endpoint: /futures/data/basis
Time Range: 36 months (1095 days)
Output File: historical_data/basis_spread_btc.json

Basis Spread = Spot Price - Futures Price
Positive values indicate spot trading above futures (backwardation).
Negative values indicate futures trading above spot (contango).
"""

import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from data.binance_utils import fetch_basis_spread, fetch_with_stitching
from data.derivatives_config import (
    DEFAULT_DAYS_BACK,
    CACHE_DIR,
    DEFAULT_SYMBOL,
    BINANCE_BASIS_LIMIT
)


def backfill_basis_spread(symbol: str = DEFAULT_SYMBOL, days_back: int = DEFAULT_DAYS_BACK):
    """
    Backfill basis spread data for a specific symbol.

    Args:
        symbol: Trading pair symbol (default: BTCUSDT)
        days_back: Number of days to fetch (default: 1095 = 36 months)
    """
    print(f"\n{'='*60}")
    print(f"Starting Basis Spread backfill for {symbol}")
    print(f"Days back: {days_back} ({days_back/30:.1f} months)")
    print(f"{'='*60}\n")

    try:
        # Calculate chunk size based on Binance limit
        # Basis limit is 500 points = ~500 days (1:1 for daily data)
        chunk_size_days = int(BINANCE_BASIS_LIMIT * 0.95)  # Use 95% for safety

        # Fetch historical data with automatic stitching
        data = fetch_with_stitching(
            fetch_function=fetch_basis_spread,
            days_back=days_back,
            chunk_size_days=chunk_size_days,
            symbol=symbol
        )

        if not data:
            print(f"Error: No data fetched for {symbol}")
            return False

        # Prepare output file
        output_file = Path(CACHE_DIR) / "basis_spread_btc.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Save to JSON
        print(f"\nSaving to {output_file}...")
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"Saved {len(data)} data points")

        # Display statistics
        if data:
            values = [point[1] for point in data]
            print(f"\nBasis Spread Statistics for {symbol}:")
            print(f"  Min: {min(values):.2f}")
            print(f"  Max: {max(values):.2f}")
            print(f"  Average: {sum(values)/len(values):.2f}")
            print(f"  Latest: {values[-1]:.2f}")

            # Show contango/backwardation distribution
            contango_count = sum(1 for v in values if v < 0)
            backwardation_count = sum(1 for v in values if v > 0)
            print(f"\n  Contango (negative): {contango_count} days ({contango_count/len(values)*100:.1f}%)")
            print(f"  Backwardation (positive): {backwardation_count} days ({backwardation_count/len(values)*100:.1f}%)")

        return True

    except Exception as e:
        print(f"\nError during {symbol} backfill: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main backfill execution."""
    print("="*60)
    print("BASIS SPREAD BACKFILL (Binance Futures)")
    print("="*60)

    # Backfill BTC basis spread
    btc_success = backfill_basis_spread(DEFAULT_SYMBOL)

    print(f"\n{'='*60}")
    print("BACKFILL COMPLETE")
    print(f"{'='*60}")
    print(f"BTC Basis Spread: {'SUCCESS' if btc_success else 'FAILED'}")

    if btc_success:
        print("\nOutput files:")
        print(f"  - {CACHE_DIR}/basis_spread_btc.json")
    else:
        print("\nBackfill failed - check errors above")
        sys.exit(1)


if __name__ == "__main__":
    main()
