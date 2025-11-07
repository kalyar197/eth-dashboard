# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ✅ PROJECT STATUS: ALL OSCILLATORS VERIFIED (2025-11-06)

**Status**: All oscillators have 3+ years of historical data, Taker Ratio removed

## 🔄 RECOVERY EVENT (2025-11-07)

**Incident**: Accidental `git clean -fd` during Google Trends system removal

**Impact Analysis**:
- ❌ **Deleted**: Google Trends feature (21 files, 5,996 lines) added in commit 53c26f5
- ❌ **Deleted**: `.env` file (untracked, contained API keys)
- ✅ **Intact**: Core Dash trading system (100% preserved)
- ✅ **Intact**: All historical data files (21 JSON files, 900KB total)
- ✅ **Intact**: All data collection modules (33 Python files)
- ✅ **Intact**: All backfill scripts (17 Python files)
- ✅ **Intact**: Frontend code (HTML, CSS, JavaScript)

**Recovery Actions Completed**:
1. ✅ Comprehensive damage assessment verified no data loss
2. ✅ Created `.env` template with API key structure and provider links
3. ✅ Committed Google Trends deletion (commit 22a32d4)
4. ✅ Verified Flask startup successful (loads .env correctly)
5. ✅ Documented data_cache/ directory purpose
6. ✅ Updated CLAUDE.md with recovery event

**System Status**: Fully operational pending API key configuration

**Lessons Learned**:
- `git clean -fd` removes ALL untracked files including critical configs
- Always use `git clean -fdn` (dry run) first to preview deletions
- Keep backup copy of `.env` file outside repository
- Recovery process validated data integrity checking procedures

**Files Modified in Recovery**:
- Created: `.env` (template with placeholders)
- Created: `data_cache/README.md` (directory documentation)
- Modified: `CLAUDE.md` (this recovery documentation)
- Commit: 22a32d4 "Remove Google Trends system after accidental force delete"

---

**Latest Update (2025-11-06):**
1. **Price Oscillators Backfilled to 3 Years**:
   - DXY: 1,095 records (3.0 years, Yahoo Finance)
   - ETH Price: 1,095 records (3.0 years, Alpaca)
   - Gold Price: 1,094 records (3.0 years, FMP)
   - SPX Price: 1,094 records (3.0 years, FMP)
2. **Taker Ratio Removed**: Only 29 days of data, archived to historical_data/archived_insufficient_coverage/
3. **Backfill Scripts Created**: 4 scripts for DXY, ETH, Gold, SPX with proper UTC timestamp standardization
4. **Verification Script**: scripts/verify_3year_coverage.py validates all 12 oscillator datasets
5. **All 12 Oscillators Verified**: RSI, MACD, ADX, ATR, DVOL, Basis Spread, BTC.D, USDT.D, DXY, ETH, Gold, SPX

**Previous Update (2025-11-05):**
1. **Derivatives Oscillators Added**: Implemented 2 derivatives oscillators with full backend support:
   - DVOL Index (Deribit): 1,096 points, 3 years of data
   - Basis Spread (Binance): 476 points, 1.3 years (kept per user request)
2. **API Integration**: All oscillators registered in OSCILLATOR_PLUGINS and working via `/api/oscillator-data`
3. **Known Issue Resolved**: ~~Missing 4th breakdown chart~~ - Frontend integration added in main.js

**Previous Update (2025-11-03):**
1. **Morning**: Added Markov regime backgrounds to price chart and changed default noise level to Min (200 periods). Regime zones now display on both price chart and oscillator chart with perfect zoom synchronization.
2. **Afternoon**: Fixed critical macro oscillator data quality issues (BTC.D, USDT.D, DXY) - removed future/improvised data and established TradingView backfill + CoinMarketCap daily update system.

### 🎯 What's Currently Working:

**Core Infrastructure:**
- ✅ Flask backend structure (app.py, caching, CORS, rate limiting)
- ✅ API configuration system (config.py)
- ✅ Plugin registration framework (data/__init__.py)
- ✅ Disk caching system (data/cache_manager.py)
- ✅ Time transformation utilities (data/time_transformer.py)
- ✅ Complete frontend design (dark theme, styling, controls, UI)
- ✅ OHLCV candlestick price charts (static/js/chart.js)
- ✅ API communication layer (static/js/api.js)
- ✅ Single-tab BTC system (ETH/Gold tabs removed)
- ✅ ETH/Gold/SPX price oscillators backfilled to 3 years (2022-11-08 to present)

**MOMENTUM OSCILLATORS** (Cyan composite line):
- ✅ Garman-Klass volatility estimation (data/volatility.py)
- ✅ 2-state Markov regime detector (data/markov_regime.py)
- ✅ User-tunable composite Z-score oscillator (data/composite_zscore.py)
- ✅ 5 noise level controls (14, 30, 50, 100, 200 periods) - Default: Min (200)
- ✅ Regime-based background shading on BOTH price chart and oscillator chart
- ✅ Regime zones (blue=low-vol, red=high-vol) sync perfectly with zoom operations
- ✅ 4 Base oscillators: RSI, MACD Histogram, ADX, ATR
- ✅ Composite + Breakdown charts with legend
- ✅ Fully interactive controls (checkboxes, buttons)

**MACRO OSCILLATORS** (Normalized Z-scores):
- ✅ DXY (U.S. Dollar Index) - 1,095 records, 3.0 years (Yahoo Finance via yfinance)
- ✅ BTC.D (Bitcoin Dominance %) - 1,095 records, 3.0 years (TradingView backfill + CoinMarketCap daily updates)
- ✅ USDT.D (Tether Dominance %) - 1,095 records, 3.0 years (TradingView backfill + CoinMarketCap daily updates)
- ✅ All datasets backfilled to 3 years (2022-11-07/08 to present)
- ✅ Timestamp standardization to midnight UTC for BTC price alignment
- ✅ None values handled properly (weekends/holidays for traditional markets)
- ✅ Data Quality Critical Fix (2025-11-03): Removed future/improvised values, established hybrid data pipeline
- ✅ DXY Backfill Complete (2025-11-06): Full 3-year historical data via scripts/backfill_dxy.py

**DERIVATIVES OSCILLATORS** (Fully Functional):
- ✅ DVOL Index (Deribit): 1,096 points, 3 years (data/dvol_index_deribit.py)
  - Deribit Volatility Index - 30-day implied volatility from options
  - Range: 32-115, Latest: 48.11
- ✅ Basis Spread (Binance): 476 points, 1.3 years (data/basis_spread_binance.py)
  - Spot vs Futures price differential
  - 91.6% contango, 8.4% backwardation
  - Kept despite <3 years per user request
- ❌ Taker Ratio (Binance): REMOVED - only 29 days of data (archived to historical_data/archived_insufficient_coverage/)
- ✅ Backend: Registered in OSCILLATOR_PLUGINS, working via API
- ✅ Frontend: Breakdown chart integrated in main.js (loadBreakdownDerivativesOscillatorData)
- ✅ Utilities: data/deribit_utils.py, data/binance_utils.py, data/derivatives_config.py
- ✅ Backfill scripts: scripts/backfill_dvol.py, scripts/backfill_basis.py

**Funding Rate Chart:**
- ✅ Binance perpetual futures funding rates
- ✅ Color-coded sentiment visualization
- ✅ 3-month historical data caching
- ✅ Real-time updates every 8 hours

**UI/Layout (2025-11-02):**
- ✅ Responsive SVG viewBox for zoom resilience (80%-120%)
- ✅ No text overlapping at any zoom level
- ✅ Proper Y-axis label spacing in all charts
- ✅ Two-tab navigation: "Main" (all charts) and "Breakdown" (empty, reserved for future use)
- ✅ Removed top heading for maximum chart space
- ✅ Moving average overlays (SMA-7, SMA-21, SMA-60, PSAR) with proper toggle functionality
- ✅ Fixed PSAR overlay clearing bug - overlays now properly removed when unchecked

**System Architecture:**
- **Pilot**: User manually tunes oscillator sensitivity via 5 noise levels
- **Radar**: Markov model provides objective volatility regime context
- **Composite Z-Score**: Weighted average normalized to standard deviations
- **Regime Shading**: Visual indication of market volatility state

### 🚧 Pending Work (As of 2025-11-02):

**Future Enhancements:**
- ❌ **Volatility Oscillator Section** (removed in previous session, can be re-implemented):
  - Realized Volatility, DVOL Index, Implied Volatility, IV Rank
  - Requires frontend implementation (~700 lines across HTML/JS)
  - Backend modules exist: data/realized_volatility.py, data/dvol_index.py, etc.
- ❌ **Advanced Volatility Metrics** (require options chain data):
  - Put/Call Ratio from options OI/volume
  - Term Structure across multiple expiries
  - Volatility Skew (25-delta put vs call IV)
- ❌ Moving average overlay integration with oscillators
- ❌ Zoom/pan synchronization between all charts
- ❌ Export to CSV/JSON functionality
- ❌ Mobile responsive design

**Known Limitations:**
- Historical data: 3+ years for most indicators (sufficient)
- CoinAPI Startup tier: 1000 requests/day limit
- Funding rate data: ~3 months cached from Binance

**Files Changed in Latest Session (2025-11-03):**

**Morning Session - Regime Backgrounds:**
```
Modified Files (3):
- static/js/chart.js (regime background implementation for price chart)
- static/js/main.js (regime data flow + default noise level change)
- index.html (Min button active by default)

Feature: Price Chart Regime Backgrounds with zoom synchronization
Bug Fix: Regime rectangles rendering before candles group clear
```

**Afternoon Session - Macro Oscillator Data Quality Fix:**
```
Modified Files (7):
- data/coinmarketcap_client.py (dynamic API key import timing fix)
- data/btc_dominance_cmc.py (field extraction + timestamp standardization + None handling)
- data/usdt_dominance_cmc.py (timestamp standardization + None handling)
- data/dxy_price_yfinance.py (timestamp standardization for BTC alignment)
- historical_data/btc_dominance.json (cleaned: removed future/None values)
- historical_data/usdt_dominance.json (cleaned: removed future/None values)

Created Scripts (3):
- scripts/backfill_dominance_data.py (one-time 3-year TradingView backfill)
- scripts/check_data.py (data verification utility)
- scripts/final_fix_dominance.py (removed future data, fetched real Nov 2-3)

Critical Data Quality Fix:
PROBLEM: BTC.D and USDT.D had None values for Nov 2 and future/improvised data for Nov 4-5
ROOT CAUSE 1: CMC API provides current values only, no historical endpoint
ROOT CAUSE 2: Timestamp misalignment (DXY at 04:00 UTC vs BTC at 00:00 UTC) caused flat 0σ line
ROOT CAUSE 3: Incremental manager creating None placeholders for missing days

SOLUTION - Hybrid Data Pipeline:
1. Historical Backfill: TradingView (tvdatafeed library) for 3 years (2022-11-07 to present)
2. Daily Updates: CoinMarketCap API (free tier) fetches today's value every 15 minutes
3. Timestamp Standardization: All timestamps normalized to midnight UTC via standardize_to_daily_utc()
4. Data Integrity: No None values, no future dates, 100% real historical data
5. Validation: BTC.D range 35-75%, USDT.D range 2-10%

FINAL STATE (as of 2025-11-03):
- BTC.D: 1093 records, last value 60.75% (Nov 3, 2025)
- USDT.D: 1093 records, last value 5.24% (Nov 3, 2025)
- DXY: Fixed flat 0σ line via timestamp standardization
- All macro oscillators now display correctly with proper divergence values
```

**Quick Start:**
1. Start server: `python app.py`
2. Access: `http://127.0.0.1:5000`
3. All features fully functional
4. Tested at 80%, 100%, 120% browser zoom - no overlapping

---

## Overview

This is being rebuilt as a **BTC Trading System** for options and swing trading. The system will fetch data from multiple APIs and display technical indicators normalized to a -100 to +100 scale for consistent analysis.

**Architecture**: Flask backend (Python) + D3.js frontend (vanilla JavaScript)

## 🔧 MCP (Model Context Protocol) Usage Guidelines

This project has **10 MCP servers** configured to enhance development efficiency and code precision. Claude should proactively use these tools when they improve the workflow.

### Available MCP Servers:

1. **Context7** (`context7-mcp`)
   - Purpose: Fetch up-to-date library/framework documentation
   - Use When: Researching APIs, syntax, or best practices
   - Context Cost: Low

2. **Playwright** (`mcp-server-playwright`)
   - Purpose: Browser automation and testing
   - Use When: Testing UI, taking screenshots, verifying functionality
   - Context Cost: Medium

3. **Sequential-Thinking** (`@modelcontextprotocol/server-sequential-thinking`)
   - Purpose: Dynamic problem-solving through thought sequences
   - Use When: Planning complex features, breaking down tasks, multi-step reasoning
   - Context Cost: High (use freely - efficiency gains outweigh costs)

4. **Sentry** (`@sentry/mcp-server`)
   - Purpose: Error monitoring and debugging
   - Use When: Checking for production errors, debugging issues, after deployments
   - Context Cost: Low

5. **Filesystem** (`@modelcontextprotocol/server-filesystem`)
   - Purpose: Secure file operations with access controls
   - Use When: Batch operations (rename/move/copy multiple files), cache management
   - **Prefer native tools** (Read/Write/Edit) for single-file operations (faster, less overhead)
   - Context Cost: Low

6. **Memory** (`@modelcontextprotocol/server-memory`)
   - Purpose: Knowledge graph-based persistent memory (general patterns, cross-project)
   - Use When: Storing general patterns, cross-project lessons learned
   - Context Cost: High (use freely - token savings compound over sessions)

7. **Git** (`@cyanheads/git-mcp-server`)
   - Purpose: Git repository operations (commit, branch, diff, log, etc.)
   - Use When: Version control, tracking changes, managing branches
   - Context Cost: Low

8. **Shadcn-UI** (`shadcn-ui-mcp-server`)
   - Purpose: React component library assistance
   - Use When: Creating/modifying UI components, learning component APIs
   - **ALWAYS consult** when working with UI components for best practices
   - Context Cost: Low

9. **Serena** (custom - project-specific)
   - Purpose: Semantic code analysis and intelligent navigation
   - Use When: Finding symbols, analyzing code structure, symbolic edits
   - **Project-specific memory storage** via `write_memory` tool
   - Context Cost: Low

10. **Alpaca Markets** (`alpaca-mcp-server`)
   - Purpose: Financial market data and trading API access
   - Use When: Fetching stock/crypto/options data, market analysis, cross-validation with CoinAPI
   - **No API keys required** for crypto data (BTC, ETH) - higher limits with keys
   - Available Data: Stocks, crypto, options, news, corporate actions
   - Context Cost: Low

### Usage Rules:

**All MCPs: Use Freely (No Permission Required)**
- All 10 servers are available for proactive use without asking permission
- Efficiency gains and token savings outweigh context costs
- Use the right tool for the job

**Tool Selection Guidelines:**

**Context7:**
- Research library APIs and syntax when implementing new features
- Get latest documentation for D3.js, NumPy, Flask, etc.

**Playwright:**
- Test UI after major changes
- Take screenshots for verification
- Automate browser interactions

**Sequential-Thinking:**
- Plan complex multi-step implementations
- Break down large features
- Explore alternative approaches
- Use for hypothesis testing and revision

**Sentry:**
- Check proactively when user mentions bugs/errors
- Query after deployments
- Use when debugging production issues

**Filesystem:**
- ✅ Batch rename/move/copy operations
- ✅ Directory-wide cache management
- ✅ Complex file tree operations
- ❌ Single file reads (use Read tool instead)
- ❌ Single file edits (use Edit tool instead)

**Memory (MCP):**
- Store **general patterns** applicable across projects
- Cross-project lessons learned
- Generic best practices

**Git:**
- Manage branches for features
- Create commits with proper messages
- Review diffs and logs
- Track changes history

**Shadcn-UI:**
- **ALWAYS consult** when creating/modifying UI components
- Get component usage examples
- Learn accessibility best practices
- Follow React component patterns

**Serena:**
- Navigate code with symbolic tools (find_symbol, get_symbols_overview)
- Find references to symbols
- Perform symbolic edits (rename, replace)
- Store **project-specific knowledge** via `write_memory` tool
  - Architecture decisions
  - Critical bug fixes
  - Design patterns specific to this project
  - File relationships and dependencies

**Alpaca Markets:**
- **UNIQUE DATASETS** (not available on CoinAPI Startup $79/month tier):
  - ✅ **News & Sentiment** (NO API KEYS REQUIRED!)
    - Historical news articles by symbol
    - Date range queries
    - Sentiment analysis ready
  - ✅ **Corporate Actions** (requires API keys)
    - Dividends, splits, earnings dates
    - Ex-dividend dates, payment dates
    - Historical corporate events
  - ✅ **Options Data** (requires API keys)
    - Options chains (calls/puts)
    - Greeks (delta, gamma, theta, vega, rho)
    - Implied volatility (IV)
    - Open interest and volume
    - Strike prices and expirations
  - ✅ **Real-Time WebSocket Streams** (requires API keys)
    - Live quotes (bid/ask)
    - Live trades (price/volume)
    - Millisecond-level data
    - Multiple symbols simultaneously

- **OVERLAPPING DATA** (also available on CoinAPI):
  - 📊 BTC/USD, ETH/USD OHLCV bars (requires API keys)
  - 📊 Stock data (SPY, equities) (requires API keys)
  - 📊 Latest quotes and trades (requires API keys)

- **API ARCHITECTURE**:
  - Free Paper Trading API keys (no credit card)
  - 5+ years of historical data
  - No rate limits on news endpoint
  - Separate clients: `StockHistoricalDataClient`, `CryptoHistoricalDataClient`, `OptionHistoricalDataClient`, `NewsClient`

- **USE CASES**:
  - Primary: News sentiment, options Greeks, corporate actions
  - Secondary: Cross-validation with CoinAPI
  - Fallback: When CoinAPI rate limits hit

### Mandatory Workflows:

**Before Commit / After Compact:**
1. **Update CLAUDE.md** with latest changes, bug fixes, and status
2. **Update Serena Memory** (`write_memory`) with new patterns/fixes/lessons
3. **Use Serena symbolic tools** for code operations

**When Creating/Modifying UI:**
1. **Consult Shadcn-UI** for component patterns and best practices
2. Implement following accessibility guidelines
3. Use recommended component APIs

**When Planning Complex Features:**
1. **Use Sequential-Thinking** for multi-step planning
2. Break down into actionable tasks
3. Explore alternative approaches before implementation

**When Debugging:**
1. **Check Sentry** if production errors mentioned
2. Use Git to review recent changes
3. Use Serena to navigate code structure

**When Working with UI Components:**
1. **Use Playwright + Shadcn-UI together** for comprehensive UI development
2. Shadcn-UI: Get component structure, patterns, and accessibility guidelines
3. Playwright: Test component rendering, interactions, and visual regression
4. Workflow: Design → Implement → Test → Iterate

**When Multiple APIs Can Provide Same Data:**
1. **ALWAYS ask user explicitly which API to use**
2. Present options with pros/cons:
   - CoinAPI: Rate limits, coverage, cost
   - Alpaca: Rate limits, coverage, features
3. Do not assume or default to one API
4. Examples:
   - "Both CoinAPI and Alpaca can provide BTC OHLCV data. Which should I use?"
   - "ETH price is available from both APIs. CoinAPI has your Startup tier (1000 req/day), Alpaca has unlimited Paper Trading. Preference?"

### Example Workflows:

**Adding a New Indicator:**
1. Sequential-Thinking: Plan implementation steps, explore approaches
2. Context7: Research NumPy/technical indicator formulas
3. Serena: Find existing indicator files as templates (find_symbol)
4. Git: Create feature branch
5. Native tools (Write/Edit): Create new indicator files
6. Playwright: Test the new indicator in browser
7. Git: Commit changes with descriptive message
8. Serena Memory: Store implementation pattern for future reference

**Debugging an Issue:**
1. Sentry: Check for recent errors (if production issue)
2. Git: Review recent changes (git diff, git log)
3. Serena: Navigate code structure (find_symbol, find_referencing_symbols)
4. Native tools (Read): Read relevant source files
5. Playwright: Reproduce issue in browser
6. Context7: Research solution if needed

**Creating UI Components:**
1. **Shadcn-UI + Playwright together**: Comprehensive UI workflow
2. Shadcn-UI: Get component structure, accessibility patterns, and best practices
3. Sequential-Thinking: Plan component architecture if complex
4. Native tools (Edit): Implement component following Shadcn-UI patterns
5. Playwright: Test rendering, interactions, responsive behavior, visual regression
6. Playwright: Take screenshots for documentation/verification
7. Serena Memory: Store UI patterns if novel

**Commit/Compact Workflow:**
1. Git: Review changes (git diff, git status)
2. Native tools (Edit): Update CLAUDE.md with changes
3. Serena: Update project memories with new patterns/fixes
4. Git: Create commit with descriptive message

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

**Core Oscillators** (BTC tab only):
- **RSI**: Relative Strength Index - momentum oscillator (0-100 scale)
- **MACD Histogram**: Trend direction and strength indicator
- **ADX**: Average Directional Index - trend strength (0-100 scale)
- **ATR**: Average True Range - volatility indicator

**Price Oscillators** (Normalized against BTC):
- **ETH Price** (`data/eth_price_alpaca.py`): 1,095 records, 3.0 years (Alpaca)
  - Ethereum price data normalized against BTC
  - Crypto alternative divergence indicator (ETH vs BTC)
  - Backfilled via scripts/backfill_eth_price.py

- **Gold Price** (`data/gold_price_oscillator.py`): 1,094 records, 3.0 years (FMP)
  - Gold (XAU/USD) price data normalized against BTC
  - Safe-haven vs crypto divergence indicator
  - OHLCV format with weekend/holiday gaps
  - Backfilled via scripts/backfill_gold_price.py

- **SPX Price** (`data/spx_price_fmp.py`): 1,094 records, 3.0 years (FMP)
  - S&P 500 index data normalized against BTC
  - Traditional equity vs crypto divergence indicator
  - Backfilled via scripts/backfill_spx_price.py

**Mathematical Treatment**:
- All oscillators normalized via Rolling OLS Regression Divergence
- All oscillators take asset parameter (currently 'btc')
- Returns simple format: `[[timestamp, value], ...]`
- Normalized by regressing against BTC price
- **Dynamic 0 line**: Represents expected relationship with BTC price

---

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
- the volatilty oscillators were removed in another session whihc wasnt compacted into progress

---

## Minimalist Dashboard Design Philosophy (2025-11-03)

### Core Principle
**"Why tell myself what I already know?"**

This is a **personal, private dashboard** designed for an expert user who is intimately familiar with the data and visualizations. The design philosophy emphasizes **eliminating redundant labels and descriptions** to create a clean, distraction-free analytical environment optimized for visual analysis.

### What to Remove

#### 1. Control Labels
- ❌ Labels like "Noise Level:", "Moving Averages:", etc.
- ✅ Keep only the actual controls (buttons, checkboxes)
- **Rationale**: The user knows what these controls do without needing labels

#### 2. Axis Labels
- ❌ Descriptive axis labels like "Date", "Funding Rate (%)", "Price ($)"
- ✅ Keep axis tick values and numbers
- **Rationale**: Chart context makes the axis meaning obvious

#### 3. Info Text / Help Text
- ❌ Instructional text like "Click and drag to zoom", "Hover for details"
- ❌ Descriptive text like "Breakdown: Individual Normalized Oscillators"
- ✅ Keep functional elements (zoom buttons, etc.)
- **Rationale**: The user knows how to interact with charts

#### 4. Reference Line Labels
- ❌ Labels like "0 (Price)", "+2σ", "-3σ" on chart overlays
- ✅ Keep the reference lines themselves visible
- **Rationale**: Visual lines provide context without text clutter

### What to Keep

#### 1. Data Values
- ✅ Actual numbers, percentages, prices
- ✅ Tick mark values on axes
- **Rationale**: These are information, not redundant labels

#### 2. Legends with Non-Obvious Information
- ✅ Dataset names in multi-line charts (e.g., "RSI", "MACD", "ADX")
- ✅ Color-coded indicators
- **Rationale**: Differentiating between similar-looking lines requires labels

#### 3. Interactive Controls
- ✅ Buttons, checkboxes, dropdowns
- ✅ Zoom controls
- **Rationale**: Functional elements that enable interaction

### Implementation Guidelines for Future Features

1. **Default to minimalism**: Don't add labels unless absolutely necessary
2. **Test without labels first**: If the feature is usable without labels, leave them off
3. **Use visual cues**: Colors, positioning, and context over text labels
4. **Consider the audience**: This is for a single, expert user, not general public

### Chart Alignment Critical Rule

**All charts must maintain identical left/right margins for vertical date alignment:**
- Price chart: `{ top: 20, right: 60, bottom: 40, left: 60 }`
- Funding rate: `{ top: 30, right: 60, bottom: 40, left: 60 }`
- Composite oscillator: `{ top: 20, right: 60, bottom: 40, left: 60 }`
- Breakdown oscillator: `{ top: 30, right: 60, bottom: 40, left: 60 }`

**Critical**: Left and right margins MUST be identical across all charts (60px) to ensure plotting areas have the same width and dates align vertically across all charts for visual analysis.

### Code Examples

**Removing Labels (HTML)**:
```html
<!-- BEFORE -->
<label class="control-label">Noise Level:</label>
<button>Max</button>

<!-- AFTER -->
<button>Max</button>
```

**Hiding Labels (JavaScript)**:
```javascript
// BEFORE
.text('0 (Price)');

// AFTER (keep DOM structure but hide text)
.text('');
```

**Files Modified (2025-11-03)**:
- `index.html`: Removed control labels, info-text divs, .info-text CSS
- `static/js/chart.js`: Removed axis labels, fixed funding rate margin
- `static/js/oscillator.js`: Fixed margins (50→60), hidden zero line label

**Status**: Active design philosophy applied to all features.