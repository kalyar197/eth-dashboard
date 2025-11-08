# BTC Multi-Timeframe Pre-Computed Data

This directory contains **pre-computed** OHLCV data for all timeframes used in the Depth chart.

## Files

| Timeframe | File | Size | Candles | Date Range |
|-----------|------|------|---------|------------|
| 1 minute | `btc_price_1m.json` | 211.13 MB | 3.0M | 2020-01-01 to 2025-11-08 |
| 15 minutes | `btc_price_15m.json` | 13.80 MB | 205K | 2020-01-01 to 2025-11-08 |
| 1 hour | `btc_price_1h.json` | 3.42 MB | 51K | 2020-01-01 to 2025-11-08 |
| 4 hours | `btc_price_4h.json` | 0.85 MB | 12.8K | 2020-01-01 to 2025-11-08 |

## Generation

These files are **pre-computed** from the source 1-minute data using pandas resampling with exact OHLCV aggregation:

- **Open**: First value in period
- **High**: Maximum value in period
- **Low**: Minimum value in period
- **Close**: Last value in period
- **Volume**: Sum of volumes in period

## Regeneration

To regenerate these files (e.g., after updating source 1-minute data):

```bash
python scripts/precompute_btc_1min_timeframes.py
```

This script:
1. Loads `historical_data/btc_price_1min_complete.json` (source data)
2. Resamples to all timeframes using pandas
3. Saves pre-computed files to this directory

**Processing time**: ~90 seconds for 3.0M records

## Architecture

### Why Pre-Compute?

**Before** (❌ Inefficient):
- Load 3.0M 1-minute candles on every request
- Resample on-the-fly using pandas
- Filter and return data
- **Total time**: 5-10 seconds per request

**After** (✅ Efficient):
- Load only the requested timeframe file
- Filter and return data
- **Total time**: 50-200ms per request

### Data Flow

```
Source Data (historical_data/btc_price_1min_complete.json)
    ↓
[scripts/precompute_btc_1min_timeframes.py]
    ↓
Pre-computed Files (historical_data/btc_1min/*.json)
    ↓
[data/btc_price_1min_resampled.py] ← NO COMPUTATION
    ↓
API Endpoint (/api/depth-chart)
    ↓
Frontend (Depth Chart)
```

## Data Structure

All files use the same OHLCV format:

```json
[
  [timestamp_ms, open, high, low, close, volume],
  [1577836800000, 7195.24, 7196.25, 7183.14, 7186.68, 51.64],
  ...
]
```

Where:
- `timestamp_ms`: Unix timestamp in milliseconds (UTC)
- `open`, `high`, `low`, `close`: Price in USD
- `volume`: Trading volume in BTC

## Maintenance

### Updating Data

1. Update the source 1-minute data file
2. Run the pre-computation script
3. Restart the Flask server to clear cache

### Disk Space

Total space required: ~229 MB for all timeframes

To conserve space, you can delete unused timeframes, but the Depth chart requires all four files.
