# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ⚠️ PROJECT REBUILD IN PROGRESS

**Status**: Core Infrastructure Only

This project has been stripped down to its core infrastructure and is being rebuilt as a **BTC Trading System** for options and swing trading. The goal is a comprehensive trading dashboard with 12+ normalized indicators (-100 to +100 scale), multiple chart layouts, and options data integration.

**What's Currently Available:**
- ✅ Flask backend structure (app.py, caching, CORS, rate limiting)
- ✅ API configuration system (config.py)
- ✅ Plugin registration framework (data/__init__.py)
- ✅ Disk caching system (data/cache_manager.py)
- ✅ Time transformation utilities (data/time_transformer.py)
- ✅ Complete frontend design (dark theme, styling, controls, UI)
- ✅ Two chart containers (price chart + oscillators)
- ✅ API communication layer (static/js/api.js)
- ✅ UI controls system (static/js/ui.js)

**What's Been Removed:**
- ❌ All data plugins (will be added back one-by-one)
- ❌ Chart rendering logic (static/js/chart.js deleted - needs complete rewrite)
- ❌ Cached data files (clean slate)

**Next Steps:**
Data plugins and chart system will be rebuilt incrementally to support the new trading system requirements.

---

## Overview

This is being rebuilt as a **BTC Trading System** for options and swing trading. The system will fetch data from multiple APIs and display technical indicators normalized to a -100 to +100 scale for consistent analysis.

**Architecture**: Flask backend (Python) + D3.js frontend (vanilla JavaScript)

## Development Commands

### Running the Application

```bash
# Start the Flask development server
python app.py
```

The server runs on `http://127.0.0.1:5000` and serves both API endpoints and the frontend HTML.

### Testing

```bash
# Run the comprehensive data quality verification suite
python test_final_fixes.py
```

This test suite validates critical data quality fixes:
- BTC Dominance: 50-60% range validation
- DXY Index: Documented limitation check
- Gold Price: FMP endpoint verification ($1500-$3000 range)

### Python Dependencies

```bash
pip install Flask requests Flask-Cors numpy
```

No `requirements.txt` file exists yet - dependencies must be installed manually.

## Architecture Overview

### Backend Structure

**Plugin-based data architecture**: The system uses a modular plugin pattern where each dataset is a separate Python module in the `data/` directory.

```
app.py                      # Flask server with unified /api/data endpoint
config.py                   # Centralized API keys and configuration
data/
  __init__.py              # Registers all data plugins
  cache_manager.py         # Disk-based JSON caching system
  time_transformer.py      # UTC timestamp standardization
  btc_price.py             # CoinAPI BTC OHLCV data fetcher
  eth_btc_ratio.py         # CoinAPI ETH/BTC ratio data fetcher
  gold_price.py            # FMP gold price (ZGUSD symbol)
  rsi.py                   # RSI indicator (calculated from BTC)
  bollinger_bands.py       # Bollinger Bands indicator (calculated from BTC)
  vwap.py                  # Volume Weighted Avg Price (calculated from BTC)
  adx.py                   # Average Directional Index (calculated from BTC)
data_cache/                # JSON cache files for offline fallback
```

### Data Plugin System

Each plugin follows a standard interface:

```python
def get_metadata():
    """Returns display metadata for the frontend"""
    return {
        'label': 'Display Name',
        'yAxisId': 'price_usd' | 'percentage' | 'indicator',
        'yAxisLabel': 'Axis Label',
        'unit': '$' | '%' | '',
        'color': '#HEXCOLOR',
        'chartType': 'line',
        # Optional:
        'yDomain': [min, max],  # Fixed domain (e.g., RSI: [0, 100])
        'referenceLines': [...]  # Horizontal reference lines
    }

def get_data(days='365'):
    """Fetches and returns time-series data"""
    return {
        'metadata': get_metadata(),
        'data': [[timestamp_ms, value], ...],
        'structure': 'simple' | 'OHLCV'  # Optional structure indicator
    }
```

**Adding a new dataset**: Create a new file in `data/`, implement the interface, then register it in `data/__init__.py` and `app.py`'s `DATA_PLUGINS` dictionary.

### Data Structures

**Two data formats are supported**:

1. **Simple**: `[timestamp_ms, value]` - Used for most indicators and single-value datasets
2. **OHLCV**: `[timestamp_ms, open, high, low, close, volume]` - Used for BTC/ETH price data

The `time_transformer.py` module handles standardization to daily UTC timestamps and can extract specific components from OHLCV data (e.g., closing prices for RSI calculation).

### Y-Axis Management

The frontend supports **multiple Y-axes** based on `yAxisId`:
- `price_usd`: USD prices (left axis, formatted as `$X,XXX`)
- `percentage`: Percentage values (right axis, formatted as `X%`)
- `indicator`: Technical indicator values (right axis)

Axes are automatically positioned and colored based on their priority order.

### Caching Strategy

**Two-tier caching**:
1. **Disk cache** (`data_cache/`): JSON files persist data between restarts for offline fallback
2. **In-memory cache** (`app.py`): 5-minute TTL cache (configurable via `CACHE_DURATION`)

When API calls fail, the system automatically falls back to disk cache if available.

### API Configuration

**Two API providers** configured in `config.py`:
- **CoinAPI**: Cryptocurrency OHLCV data
- **FMP (Financial Modeling Prep)**: Gold price data (using ZGUSD symbol)

**API keys are stored in `config.py`** - This file contains sensitive credentials and should not be committed to version control.

### Frontend Architecture

**Single-page D3.js application** (`index.html`):
- Chart rendering with zoom/pan capabilities
- Crosshair and tooltip for data inspection
- Dynamic plugin selection (checkboxes)
- Time range controls (1M, 3M, 1Y, ALL)
- Multi-axis support with automatic positioning

The frontend dynamically queries `/api/datasets` to discover available datasets and build UI controls.

## Critical Implementation Notes

### Data Quality Fixes (Phase 3/4)

**Gold Price**: Fixed to use FMP's `/stable/historical-price-eod/full` endpoint with ZGUSD symbol. The `/historical-chart/` endpoint returns 403 Forbidden.

### OHLCV Data Handling

The BTC price module returns **full 6-component OHLCV data** to enable technical indicator calculations. Indicators like RSI, Bollinger Bands, VWAP, and ADX use `time_transformer.extract_component()` to get specific values (typically closing prices) from OHLCV arrays.

**Do not discard OHLCV components** when modifying data pipelines - indicators depend on having access to open, high, low, close, and volume data.

### Bollinger Bands Special Case

Bollinger Bands return a **non-standard data structure**:
```python
{
    'data': {
        'upper': [[timestamp, value], ...],
        'middle': [[timestamp, value], ...],
        'lower': [[timestamp, value], ...]
    }
}
```

The frontend has special rendering logic to draw the three bands and shaded area between them.

### Rate Limiting

The Flask backend implements **2-second rate limiting** between API calls (configurable via `RATE_LIMIT_DELAY`). This prevents hitting API rate limits when multiple datasets are selected.

## Common Gotchas

1. **Timestamp format**: All data must use **millisecond Unix timestamps** (not seconds). The `time_transformer.standardize_to_daily_utc()` function ensures consistency.

2. **API key status**: The server startup logs show API key configuration status. If an API key is invalid or missing, data for that provider will fallback to cache.

3. **UTF-8 encoding**: Test scripts must specify UTF-8 encoding for emoji rendering on Windows systems.

4. **Chart dimensions**: The frontend has a **320px right margin** to accommodate multiple Y-axes. Changing margin values requires updating SVG positioning logic.

5. **Days parameter**: The `days` parameter accepts either a number string (`'30'`, `'365'`) or `'max'`. Indicator calculations may request extra days as a buffer (e.g., RSI requests `days + RSI_PERIOD + 10`).

6. **Flask debug mode socket error (Windows)**: When running in debug mode on Windows, you may see `OSError: [WinError 10038] An operation was attempted on something that is not a socket` during auto-reload. This is a known issue with Flask/Werkzeug's auto-reload mechanism on Windows and can be safely ignored in development. For production deployments, use a proper WSGI server (e.g., Gunicorn, uWSGI) instead of Flask's built-in development server.

## Project Phases

The codebase references implementation phases:
- **Phase 1-2**: Core infrastructure (BTC/ETH, Gold, RSI, Bollinger Bands)
- **Phase 3**: Migrated technical indicators from ETH to BTC
- **Phase 4**: Added VWAP and ADX indicators

Phase comments in code indicate feature evolution and can guide understanding of system complexity layers.
