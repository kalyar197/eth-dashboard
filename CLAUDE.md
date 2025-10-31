# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ⚠️ PROJECT STATUS: PILOT & RADAR OSCILLATOR SYSTEM COMPLETE

**Status**: Advanced Composite Oscillator with Regime Detection

This BTC Trading System now features a mathematically rigorous **"Pilot & Radar" oscillator system** where users manually control oscillator sensitivity while an AI-powered Markov model provides objective market context.

**What's Currently Available:**
- ✅ Flask backend structure (app.py, caching, CORS, rate limiting)
- ✅ API configuration system (config.py)
- ✅ Plugin registration framework (data/__init__.py)
- ✅ Disk caching system (data/cache_manager.py)
- ✅ Time transformation utilities (data/time_transformer.py)
- ✅ Complete frontend design (dark theme, styling, controls, UI)
- ✅ OHLCV candlestick price charts (static/js/chart.js)
- ✅ **Pilot & Radar composite oscillator system** ⭐ NEW
- ✅ Garman-Klass volatility estimation (data/volatility.py)
- ✅ 2-state Markov regime detector (data/markov_regime.py)
- ✅ User-tunable composite Z-score oscillator (data/composite_zscore.py)
- ✅ 5 noise level controls (14, 30, 50, 100, 200 periods)
- ✅ Regime-based background shading (blue=low-vol, red=high-vol)
- ✅ Base oscillators: RSI, MACD Histogram, ADX, Gold Price
- ✅ BTC tab includes ETH Price oscillator (crypto alternative divergence)
- ✅ API communication layer (static/js/api.js)
- ✅ Tab-based system (BTC, ETH, Gold)

**Key Features:**
- **Pilot**: User manually tunes oscillator sensitivity via 5 noise levels
- **Radar**: Markov model provides objective volatility regime context
- **Composite Z-Score**: Weighted average of multiple oscillators normalized to standard deviations
- **Regime Shading**: Visual indication of market volatility state

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
pip install Flask requests Flask-Cors numpy statsmodels
```

**Required packages**:
- `Flask` - Web server
- `requests` - API calls
- `Flask-Cors` - CORS handling
- `numpy` - Mathematical calculations
- `statsmodels` - Markov switching models for regime detection

No `requirements.txt` file exists yet - dependencies must be installed manually.

## Pilot & Radar Oscillator System

The system implements an advanced composite oscillator with two independent components:

### Component 1: The Pilot (User-Tunable Composite Z-Score)

**Purpose**: User manually controls oscillator sensitivity to find the signal-to-noise ratio that works for their trading style.

**How It Works**:
1. Fetches multiple oscillators (RSI, MACD Histogram, ADX, Gold Price)
2. Calculates rolling Z-score for each: `Z = (x - μ) / σ`
   - `μ` = rolling mean over user-selected window
   - `σ` = rolling standard deviation over window
3. Computes weighted average (currently equal weights: 0.25 each)
4. Returns composite Z-score time series

**Noise Level Controls** (5 options):
- **14 periods** - Max Noise: Fast response, very sensitive to recent changes
- **30 periods** - Med-High Noise: Moderate sensitivity
- **50 periods** - Default: Balanced signal-to-noise
- **100 periods** - Med-Low Noise: Smoother, less reactive
- **200 periods** - Min Noise: Very smooth, shows long-term trends

**Interpretation**:
- Z-score represents standard deviations from mean
- ±2σ: Statistically significant divergence (95% confidence)
- ±3σ: Extreme divergence (99.7% confidence)
- Larger window → smoother line, less noise, slower response
- Smaller window → noisier line, faster response to changes

**Files**:
- `data/composite_zscore.py` - Composite Z-score calculator
- Backend logic in `app.py` (`mode='composite'`)
- Frontend: `static/js/oscillator.js` (`renderCompositeOscillator()`)
- UI controls: `index.html` (`.noise-btn` elements)

### Component 2: The Radar (Markov Regime Detector)

**Purpose**: Provides objective, model-based classification of market volatility independent of user settings.

**How It Works**:
1. **Volatility Estimation**: Uses Garman-Klass estimator from OHLC data
   - `σ_GK = sqrt(0.5 * ln(H/L)² - (2*ln(2)-1) * ln(C/O)²)`
   - More robust than close-to-close volatility
   - Annualized to percentage (×sqrt(252))

2. **Markov Switching Model**: Fits 2-state AR(1) model to volatility
   - Uses `statsmodels.tsa.regime_switching.MarkovAutoregression`
   - Two hidden states: Regime 0 (Low-Vol), Regime 1 (High-Vol)
   - Bayesian inference determines most probable regime for each timestamp
   - Model uses full time series for smoothed probabilities

3. **Regime Classification**:
   - **Regime 0 (Low Volatility)**: Stable, range-bound conditions → Blue background
   - **Regime 1 (High Volatility)**: Unstable, trending conditions → Red background

**Visual Representation**:
- Background shading on oscillator chart
- Blue: Low-volatility regime (typical: 70-85% of time)
- Red: High-volatility regime (typical: 15-30% of time)
- Regime transitions indicate structural changes in market dynamics

**Key Feature**: Regime classification is **independent** of user's noise level selection. It provides objective context regardless of how the user tunes the oscillator.

**Files**:
- `data/volatility.py` - Garman-Klass volatility estimator
- `data/markov_regime.py` - 2-state Markov switching model
- Backend: Returns regime data alongside composite data
- Frontend: `oscillator.js` (`renderRegimeBackground()`)

### API Endpoint: `/api/oscillator-data`

**Parameters**:
- `asset`: 'btc' | 'eth' | 'gold'
- `datasets`: Comma-separated list (e.g., 'rsi,macd_histogram,adx,gold')
- `days`: Number of days ('7' | '30' | '90' | '365')
- `mode`: 'composite' | 'individual' (default: composite)
- `noise_level`: 14 | 30 | 50 | 100 | 200 (default: 50)
- `normalizer`: 'zscore' (only option currently)

**Response (composite mode)**:
```json
{
    "mode": "composite",
    "asset": "btc",
    "noise_level": 50,
    "composite": {
        "data": [[timestamp, zscore], ...],
        "metadata": {
            "label": "Composite Z-Score",
            "window": 50,
            "components": ["RSI", "MACD Histogram", "ADX", "Gold Price"],
            "weights": [0.25, 0.25, 0.25, 0.25]
        }
    },
    "regime": {
        "data": [[timestamp, regime_int], ...],
        "metadata": {
            "states": {
                "0": {"label": "Low Volatility", "color": "rgba(0, 122, 255, 0.1)"},
                "1": {"label": "High Volatility", "color": "rgba(255, 59, 48, 0.1)"}
            }
        }
    }
}
```

### Frontend Implementation

**Noise Level Controls** (`index.html`):
- 5 buttons per asset tab (BTC, ETH, Gold)
- Active button highlighted in cyan (#00D9FF)
- Triggers reload of oscillator data with new window size

**State Management** (`main.js`):
- `appState.noiseLevel`: Stores current noise level per asset
- `appState.compositeMode`: Boolean flag (default: true)
- `setupNoiseLevelControls()`: Event handlers for button clicks
- `loadOscillatorData()`: Fetches and renders data

**Chart Rendering** (`oscillator.js`):
- `renderCompositeOscillator()`: Main composite rendering function
  1. Renders regime background (first, so it's behind)
  2. Renders reference lines at ±2σ and ±3σ
  3. Renders composite Z-score line (cyan)
  4. Updates axes with symmetrical Y-domain around 0
- `renderRegimeBackground()`: Groups consecutive regime timestamps and renders colored rectangles
- `renderIndividualOscillator()`: Original multi-line rendering (when `mode='individual'`)

### Mathematical Foundations

**Z-Score Normalization**:
- Standardizes oscillators to common scale (standard deviations)
- Makes RSI (0-100), MACD (price-scaled), and Volume (count) directly comparable
- Rolling window captures local context rather than global statistics

**Markov Switching Models**:
- Assumes market alternates between latent volatility states
- AR(1) structure: `volatility_t = α + β·volatility_{t-1} + ε_t`
- Each regime has different parameters (α, β, σ)
- Transition probabilities govern regime switches

**Garman-Klass Volatility**:
- Uses full OHLC range, not just closing prices
- Statistically more efficient (requires fewer observations for same precision)
- Formula accounts for both intraday range and open-close movement

### Design Philosophy

**Separation of Concerns**:
- **Pilot** (User): Subjective tuning for their strategy
- **Radar** (Model): Objective market characterization
- Neither component influences the other

**Equal Weighting (Current)**:
- All oscillators contribute equally to composite
- Architecture supports custom weights (future enhancement)
- Designed for extensibility (can add more oscillators)

**Performance Considerations**:
- Markov model fitted once per request (expensive)
- Results cached for 5 minutes (configurable)
- Regime classifications stored in memory
- Composite Z-scores recalculated on-demand per noise level

### Oscillator Plugins

The system includes multiple oscillator plugins that can be normalized and combined into composite indicators:

**Core Oscillators** (all tabs):
- **RSI**: Relative Strength Index - momentum oscillator (0-100 scale)
- **MACD Histogram**: Trend direction and strength indicator
- **ADX**: Average Directional Index - trend strength (0-100 scale)

**External Asset Oscillators**:
- **Gold Price** (`data/gold_oscillator.py`): Available on BTC, ETH, and Gold tabs
  - Wraps `gold_price` module to extract closing prices
  - Shows safe-haven vs crypto divergence
  - Positive z-score: Gold expensive relative to asset (risk-off sentiment)
  - Negative z-score: Gold cheap relative to asset (risk-on sentiment)

- **ETH Price** (`data/eth_oscillator.py`): Available on BTC tab only
  - Wraps `eth_price` module to extract closing prices
  - Shows crypto alternative divergence (ETH vs BTC)
  - Positive z-score: ETH outperforming BTC (alt season signal)
  - Negative z-score: BTC outperforming ETH (flight to BTC)

- **SPX (S&P 500)** (`data/spx_oscillator.py`): Available on all tabs
  - Wraps `spx_price` module to extract closing prices
  - Shows traditional equity vs crypto/gold divergence
  - Positive z-score: Stocks outperforming crypto/gold (rotation to traditional markets)
  - Negative z-score: Crypto/gold outperforming stocks (alternative asset strength)
  - Classic risk indicator: stocks up + gold down = risk-on; stocks down + gold up = risk-off

**Mathematical Treatment**:
- All oscillators normalized via Rolling OLS Regression Divergence
- External asset oscillators don't take asset parameter
- Returns simple format: `[[timestamp, close_price], ...]`
- Normalized by regressing against target asset price (BTC, ETH, or Gold)
- **Dynamic 0 line**: Represents expected relationship with tab's main asset price
  - BTC tab: all oscillators regressed against BTC price
  - ETH tab: all oscillators regressed against ETH price
  - Gold tab: all oscillators regressed against Gold price

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
