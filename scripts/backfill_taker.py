"""
Backfill script for Taker Long/Short Ratio historical data.

Fetches 36 months of taker ratio data for BTCUSDT from Binance Futures API.
This serves as a CVD (Cumulative Volume Delta) proxy without downloading GB of trade data.

Data Source: Binance Futures API (free, no API key required)
Endpoint: /futures/data/takerlongshortRatio
Time Range: 36 months (1095 days)
Output File: historical_data/taker_ratio_btc.json

Taker Buy/Sell Ratio represents the buying vs selling pressure from takers (market orders).
Ratio > 1.0 indicates more buying pressure (bullish).
Ratio < 1.0 indicates more selling pressure (bearish).
"""

import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from data.binance_utils import fetch_taker_ratio, fetch_with_stitching
from data.derivatives_config import (
    DEFAULT_DAYS_BACK,
    CACHE_DIR,
    DEFAULT_SYMBOL,
    BINANCE_TAKER_LIMIT
)


def backfill_taker_ratio(symbol: str = DEFAULT_SYMBOL, days_back: int = DEFAULT_DAYS_BACK):
    """
    Backfill taker long/short ratio data for a specific symbol.

    Args:
        symbol: Trading pair symbol (default: BTCUSDT)
        days_back: Number of days to fetch (default: 1095 = 36 months)
    """
    print(f"\n{'='*60}")
    print(f"Starting Taker Ratio backfill for {symbol}")
    print(f"Days back: {days_back} ({days_back/30:.1f} months)")
    print(f"This will require ~{days_back//30} API requests (1 per month)")
    print(f"{'='*60}\n")

    try:
        # Calculate chunk size based on Binance limit
        # Taker ratio limit is 31 points = ~31 days (1:1 for daily data)
        chunk_size_days = int(BINANCE_TAKER_LIMIT * 0.95)  # Use 95% for safety

        # Fetch historical data with automatic stitching
        data = fetch_with_stitching(
            fetch_function=fetch_taker_ratio,
            days_back=days_back,
            chunk_size_days=chunk_size_days,
            symbol=symbol
        )

        if not data:
            print(f"Error: No data fetched for {symbol}")
            return False

        # Prepare output file
        output_file = Path(CACHE_DIR) / "taker_ratio_btc.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Save to JSON
        print(f"\nSaving to {output_file}...")
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"Saved {len(data)} data points")

        # Display statistics
        if data:
            values = [point[1] for point in data]
            print(f"\nTaker Ratio Statistics for {symbol}:")
            print(f"  Min: {min(values):.4f}")
            print(f"  Max: {max(values):.4f}")
            print(f"  Average: {sum(values)/len(values):.4f}")
            print(f"  Latest: {values[-1]:.4f}")

            # Show bullish/bearish distribution
            bullish_count = sum(1 for v in values if v > 1.0)
            bearish_count = sum(1 for v in values if v < 1.0)
            neutral_count = sum(1 for v in values if v == 1.0)

            print(f"\n  Bullish (>1.0): {bullish_count} days ({bullish_count/len(values)*100:.1f}%)")
            print(f"  Bearish (<1.0): {bearish_count} days ({bearish_count/len(values)*100:.1f}%)")
            print(f"  Neutral (=1.0): {neutral_count} days ({neutral_count/len(values)*100:.1f}%)")

        return True

    except Exception as e:
        print(f"\nError during {symbol} backfill: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main backfill execution."""
    print("="*60)
    print("TAKER LONG/SHORT RATIO BACKFILL (Binance Futures)")
    print("CVD Proxy - No GB downloads required!")
    print("="*60)

    # Backfill BTC taker ratio
    btc_success = backfill_taker_ratio(DEFAULT_SYMBOL)

    print(f"\n{'='*60}")
    print("BACKFILL COMPLETE")
    print(f"{'='*60}")
    print(f"BTC Taker Ratio: {'SUCCESS' if btc_success else 'FAILED'}")

    if btc_success:
        print("\nOutput files:")
        print(f"  - {CACHE_DIR}/taker_ratio_btc.json")
        print("\nThis CVD proxy is ready to use without downloading GB of trade data!")
    else:
        print("\nBackfill failed - check errors above")
        sys.exit(1)


if __name__ == "__main__":
    main()
