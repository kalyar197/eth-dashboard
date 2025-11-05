"""
Backfill script for CVD and Taker Buy/Sell Ratio from Binance aggTrades data.

Data Source: Binance Public Data Repository (data.binance.vision)
Time Range: 3 years of historical data
Output Files:
    - historical_data/cvd_btc.json
    - historical_data/taker_ratio_btc.json

CVD Calculation:
    - Buy Volume: sum(qty where isBuyerMaker=false) - buyer is taker
    - Sell Volume: sum(qty where isBuyerMaker=true) - seller is taker
    - Daily CVD: cumsum(buy_volume - sell_volume)

Taker Ratio Calculation:
    - Taker Ratio: buy_volume / sell_volume
"""

import os
import json
import gzip
from datetime import datetime, timedelta
from pathlib import Path
from binance_historical_data import BinanceDataDumper

# Configuration
SYMBOL = "BTCUSDT"
DATA_TYPE = "aggTrades"
YEARS_OF_DATA = 3
OUTPUT_DIR = Path(__file__).parent.parent / "historical_data"
CVD_OUTPUT = OUTPUT_DIR / "cvd_btc.json"
TAKER_RATIO_OUTPUT = OUTPUT_DIR / "taker_ratio_btc.json"
TEMP_DIR = Path(__file__).parent.parent / "temp_binance_data"


def calculate_daily_metrics(agg_trades):
    """
    Calculate daily buy/sell volumes from aggTrades data.

    Args:
        agg_trades: List of aggTrade dicts with keys: q (quantity), m (isBuyerMaker)

    Returns:
        tuple: (buy_volume, sell_volume)
    """
    buy_volume = 0.0
    sell_volume = 0.0

    for trade in agg_trades:
        qty = float(trade['q'])
        is_buyer_maker = trade['m']

        if is_buyer_maker:
            # Seller is taker (maker is buyer, so taker is seller)
            sell_volume += qty
        else:
            # Buyer is taker (maker is seller, so taker is buyer)
            buy_volume += qty

    return buy_volume, sell_volume


def process_daily_file(file_path):
    """
    Process a single daily aggTrades ZIP file.

    Args:
        file_path: Path to the gzipped aggTrades file

    Returns:
        tuple: (buy_volume, sell_volume) or None if file doesn't exist
    """
    if not os.path.exists(file_path):
        return None

    agg_trades = []

    try:
        with gzip.open(file_path, 'rt') as f:
            for line in f:
                if line.strip():
                    trade = json.loads(line)
                    agg_trades.append(trade)

        return calculate_daily_metrics(agg_trades)
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None


def download_and_process():
    """
    Download aggTrades data from Binance and calculate CVD + Taker Ratio.
    """
    print(f"Starting backfill for {SYMBOL} aggTrades data...")
    print(f"Time range: {YEARS_OF_DATA} years")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Temp directory: {TEMP_DIR}")

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    # Initialize Binance data dumper
    dumper = BinanceDataDumper(
        path_dir_where_to_dump=str(TEMP_DIR),
        asset_class="spot",
        data_type=DATA_TYPE,
        data_frequency="daily"
    )

    # Calculate date range (3 years back from today)
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=YEARS_OF_DATA * 365)

    print(f"\nDownloading data from {start_date} to {end_date}...")

    # Download data
    dumper.dump_data(
        tickers=[SYMBOL],
        date_start=start_date,
        date_end=end_date,
        is_to_update_existing=False,
        tickers_to_exclude=None
    )

    print("\nProcessing downloaded files...")

    # Process downloaded files day by day
    cvd_data = []
    taker_ratio_data = []
    cumulative_cvd = 0.0

    current_date = start_date
    days_processed = 0
    days_skipped = 0

    while current_date <= end_date:
        # Construct expected file path
        date_str = current_date.strftime("%Y-%m-%d")
        file_path = TEMP_DIR / "spot" / "daily" / "aggTrades" / SYMBOL / f"{SYMBOL}-aggTrades-{date_str}.zip"

        # Process file
        result = process_daily_file(file_path)

        if result is not None:
            buy_volume, sell_volume = result

            # Calculate CVD
            daily_delta = buy_volume - sell_volume
            cumulative_cvd += daily_delta

            # Calculate Taker Ratio (avoid division by zero)
            taker_ratio = buy_volume / sell_volume if sell_volume > 0 else 0.0

            # Convert to timestamp (midnight UTC) - combine date with time for proper datetime
            dt = datetime.combine(current_date, datetime.min.time())
            timestamp_ms = int(dt.timestamp() * 1000)

            # Append to data arrays
            cvd_data.append([timestamp_ms, cumulative_cvd])
            taker_ratio_data.append([timestamp_ms, taker_ratio])

            days_processed += 1

            if days_processed % 30 == 0:
                print(f"Processed {days_processed} days... (Latest: {date_str}, CVD: {cumulative_cvd:.2f}, Ratio: {taker_ratio:.4f})")
        else:
            days_skipped += 1

        # Move to next day
        current_date += timedelta(days=1)

    print(f"\nProcessing complete!")
    print(f"Days processed: {days_processed}")
    print(f"Days skipped: {days_skipped}")
    print(f"Final CVD: {cumulative_cvd:.2f}")

    # Save CVD data
    print(f"\nSaving CVD data to {CVD_OUTPUT}...")
    with open(CVD_OUTPUT, 'w') as f:
        json.dump(cvd_data, f, indent=2)
    print(f"Saved {len(cvd_data)} CVD data points")

    # Save Taker Ratio data
    print(f"Saving Taker Ratio data to {TAKER_RATIO_OUTPUT}...")
    with open(TAKER_RATIO_OUTPUT, 'w') as f:
        json.dump(taker_ratio_data, f, indent=2)
    print(f"Saved {len(taker_ratio_data)} Taker Ratio data points")

    print("\n✅ Backfill complete!")
    print(f"CVD range: [{cvd_data[0][1]:.2f}, {cvd_data[-1][1]:.2f}]")
    print(f"Taker Ratio range: [{min(d[1] for d in taker_ratio_data):.4f}, {max(d[1] for d in taker_ratio_data):.4f}]")


if __name__ == "__main__":
    download_and_process()
