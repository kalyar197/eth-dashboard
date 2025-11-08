# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

**BTC Trading System** for options and swing trading. Flask backend (Python) + D3.js frontend with technical indicators normalized to Z-score scale.

**Quick Start:**
```bash
python app.py  # Server runs on http://127.0.0.1:5000
```

### Current System Status

**Oscillators** (All have 3+ years historical data):
- **Momentum**: RSI, MACD Histogram, ADX, ATR
- **Macro**: BTC.D, USDT.D, DXY, ETH, Gold, SPX
- **Derivatives**: DVOL Index (Deribit), Basis Spread (Binance)
- **Composite Z-Score**: RSI + ADX (equal weights, 5 noise levels: 14, 30, 50, 100, 200 periods)
- **Markov Regime Detection**: Blue (low-vol) / Red (high-vol) backgrounds on ALL oscillators (composite + breakdown)

**Features**:
- Plugin-based data architecture (`data/` modules)
- Two-tier caching (disk + in-memory 5min TTL)
- OHLCV candlestick charts with moving average overlays
- Funding rate chart (Binance, 3-month cache)
- Minimalist UI (no redundant labels)
- Chart margin alignment: 60px left/right for vertical date sync

**Dependencies**:
```bash
pip install Flask requests Flask-Cors numpy statsmodels
```

## MCP Servers

**Use freely without permission** - All 10 servers available for proactive use:

1. **Context7** - Library/framework documentation
2. **Playwright** - Browser testing, screenshots
3. **Sequential-Thinking** - Complex planning, multi-step reasoning
4. **Sentry** - Error monitoring
5. **Filesystem** - Batch file operations (prefer Read/Write/Edit for single files)
6. **Memory** - Cross-project patterns/lessons
7. **Git** - Version control
8. **Shadcn-UI** - React component patterns (ALWAYS consult for UI work)
9. **Serena** - Code navigation, project-specific memory (`write_memory`)
10. **Alpaca Markets** - News/sentiment (no keys), options data (requires keys)

**Key Workflows**:
- Before commit: Update CLAUDE.md + Serena memory
- Multiple API options: Ask user which to use (CoinAPI vs Alpaca)
- UI work: Shadcn-UI (patterns) + Playwright (testing)

## API Configuration

**API Keys** (stored in `config.py` - not committed):
- **CoinAPI**: Cryptocurrency OHLCV data (Startup tier: 1000 req/day)
- **FMP**: Gold/SPX price data (using ZGUSD, ^GSPC symbols)
- **CoinMarketCap**: BTC.D/USDT.D daily updates (free tier)
- **Alpaca**: News (no keys), options/stocks (requires keys)

**Data Sources**:
- BTC.D/USDT.D: TradingView backfill + CoinMarketCap daily
- DXY: Yahoo Finance (yfinance)
- DVOL: Deribit API
- Basis Spread: Binance API

## Oscillator System

**Two Independent Components**:

1. **Pilot (User-Tunable Z-Score)**:
   - Composite Z-score from RSI + ADX (equal weights, both normal values)
   - 5 noise levels: 14, 30, 50, 100, 200 periods
   - ±2σ = 95% confidence, ±3σ = 99.7% confidence
   - Files: `data/composite_zscore.py`, `static/js/oscillator.js`

2. **Radar (Markov Regime)**:
   - Garman-Klass volatility → 2-state Markov model
   - Blue (low-vol) / Red (high-vol) backgrounds **on ALL oscillators**
   - Applied to composite AND all breakdown charts (Momentum, Price, Macro, Derivatives)
   - Date-filtered to match each oscillator's specific date range
   - Regime data aligned to composite timestamps for perfect synchronization
   - Independent of user's noise level
   - Files: `data/volatility.py`, `data/markov_regime.py`

**Regime Background Implementation**:
- Backend (`app.py:439-471`): Regime data generated from aligned OHLCV matching composite timestamps
- Frontend (`oscillator.js:454-475`): Date filtering ensures backgrounds only show for valid date ranges
- Global state (`main.js:85`): `window.appState` exposes regime data to all chart modules
- Z-ordering: Backgrounds inserted first (`:first-child`) to render behind oscillator lines
- Asset extraction: Smart pattern matching handles all breakdown IDs (`breakdown-price-btc` → `btc`)
- Zoom support: Regime rectangles update during pan/zoom operations

**Visual Enhancements**:
- 0 line visibility: Orange (#F7931A, 2px, 50% opacity) on ALL charts - matches composite styling
- Previous: Gray (#666, 1px, 30% opacity) - barely visible
- Consistent UI: All oscillators (composite + breakdown) now have identical visual treatment

**API**: `/api/oscillator-data?asset=btc&mode=composite&noise_level=200`

## Architecture

**Backend** (`data/` plugin system):
```python
def get_metadata():
    return {'label': 'Name', 'yAxisId': 'price_usd', 'color': '#HEX', ...}

def get_data(days='365'):
    return {'metadata': {...}, 'data': [[ts_ms, value], ...]}
```

**Data Formats**:
- Simple: `[timestamp_ms, value]`
- OHLCV: `[timestamp_ms, open, high, low, close, volume]`

**Caching**: Disk (`data_cache/`) + in-memory (5min TTL)

**Frontend**: D3.js (`index.html`, `static/js/`) - chart rendering, zoom/pan, multi-axis
- `main.js`: Application state + data fetching (`window.appState` exposed globally)
- `oscillator.js`: Chart rendering, regime backgrounds, zoom/pan
- `chart.js`: Price charts, funding rate charts

## Critical Notes

**OHLCV Handling**:
- BTC price returns full 6-component OHLCV for indicator calculations
- Use `time_transformer.extract_component()` to get close/volume
- Do NOT discard OHLCV components

**Timestamps**: Millisecond Unix timestamps (not seconds) - `standardize_to_daily_utc()`

**Rate Limiting**: 2-second delay between API calls (`RATE_LIMIT_DELAY`)

**Chart Margins**: 60px left/right for vertical date alignment across all charts

**Flask Debug**: Socket error on Windows auto-reload is harmless

**Regime Backgrounds**:
- Always filter regime data to xScale domain before rendering (prevents date misalignment)
- Extract base asset from breakdown IDs using regex: `asset.match(/-(btc|eth|gold)$/)`
- Backgrounds MUST be inserted first (`:first-child`) for proper z-ordering
- Update regime rectangles in zoom handlers: `updateRegimeRectangles(chart, newXScale)`

**Null Handling in Normalization** (`data/normalizers/zscore.py:118`):
- Weekend/holiday nulls are **skipped entirely** (not rendered as 0.0)
- This prevents false "gaps at 0.0" on charts for non-trading periods
- Applies to all oscillators with market-hours data (DXY, BTC.D, USDT.D, Gold, SPX, ETH)
- Continuous oscillators (RSI, MACD, ADX, ATR) have no nulls and are unaffected

## Minimalist Design Philosophy

**"Why tell myself what I already know?"** - Personal dashboard for expert user.

**Remove**:
- ❌ Control labels ("Noise Level:", "Moving Averages:")
- ❌ Axis labels ("Date", "Price ($)")
- ❌ Help text ("Click and drag to zoom")
- ❌ Reference line labels ("+2σ", "-3σ")

**Keep**:
- ✅ Data values (numbers, percentages)
- ✅ Multi-line legends (RSI, ADX)
- ✅ Interactive controls (buttons, checkboxes)

**Guidelines**: Default to minimalism, use visual cues over text, test without labels first.