# Derivatives Data Research
## Available Metrics from Various APIs

Last Updated: 2025-11-05

---

## 🎯 Target Metrics

1. **Put/Call Ratio** - Options sentiment indicator
2. **Basis Spread** - Spot vs Futures price difference
3. **CVD** (Cumulative Volume Delta) - Net buying/selling pressure
4. **Historical Implied Volatility** - Options pricing IV
5. **OI Change Rate** - Open Interest momentum

---

## 📊 Data Source Capabilities

### 1. BINANCE FUTURES API
**Documentation**: `docs/api_references/binance_derivatives.html`
**Base URL**: `https://fapi.binance.com` (USDT-M) / `https://dapi.binance.com` (COIN-M)

#### Available Endpoints:

**✅ Basis Spread**
- Endpoint: `GET /futures/data/basis`
- Historical: Yes
- Rate Limit: TBD
- Data Depth: **TBD - needs testing**

**✅ Open Interest History**
- Endpoint: `GET /futures/data/openInterestHist`
- Historical: Yes
- Includes: `CMCCirculatingSupply` field
- Data Depth: **TBD - needs testing**

**✅ Taker Long/Short Ratio** (proxy for CVD sentiment)
- Endpoint: `GET /futures/data/takerlongshortRatio`
- Shows: Taker buy vs sell ratio by period
- Historical: Yes
- Data Depth: **TBD - needs testing**

**✅ Current Open Interest**
- Endpoint: `GET /fapi/v1/openInterest`
- Real-time only
- Symbol-specific

**⚠️ CVD** - Not directly available
- Would need to calculate from trade data (not practical)
- Alternative: Use Taker Long/Short Ratio as proxy

**❌ Put/Call Ratio** - Not available (Binance doesn't offer options)

**❌ Implied Volatility** - Not available (no options)

---

### 2. DERIBIT API
**Documentation**: `docs/api_references/deribit_api.html`
**Base URL**: `https://www.deribit.com/api/v2`
**Specialty**: Crypto options & futures (BTC, ETH, SOL, USDC)

#### Available Endpoints:

**✅ Open Interest**
- Endpoint: `GET /public/get_book_summary_by_currency`
- Field: `open_interest` in response
- Per-instrument basis
- Real-time

**✅ Implied Volatility**
- Available in multiple endpoints:
  - `mark_iv` - IV for mark price
  - `bid_iv` - IV for best bid
  - `ask_iv` - IV for best ask
- Endpoint: `GET /public/ticker` or `/public/get_book_summary_by_instrument`
- Options only
- Real-time

**✅ Historical Implied Volatility**
- Endpoint: `GET /public/get_volatility_index_data`
- Returns: DVOL index (Deribit Volatility Index)
- Historical: Yes
- Data Depth: **TBD - needs testing**

**⚠️ Put/Call Ratio** - Not directly provided
- Can calculate from: `get_book_summary_by_currency` with `kind=option`
- Would need to aggregate put vs call open interest or volume
- Possible but requires multiple API calls

**✅ Greeks** (bonus data)
- Delta, Gamma, Theta, Vega, Rho
- Available in ticker data for options
- Real-time

**❌ Basis Spread** - Not directly available
- Can calculate: spot price - futures price
- Would need to fetch both separately

**❌ CVD** - Not available
- No aggregate trade delta data

---

### 3. COINAPI
**Documentation**: `docs/api_references/coinapi_docs.html`
**Current Plan**: Startup ($79/month, 1000 req/day)

#### Available Endpoints:

**✅ Open Interest**
- Endpoint: `/v1/ohlcv/{symbol_id}/history` with `oi` field
- Historical: Yes
- Perpetual futures data
- **Known Working**: Already implemented in project

**⚠️ Implied Volatility** - Not explicitly documented
- May be available in options data (needs verification)
- Contact support to confirm

**❌ Put/Call Ratio** - Not found in docs

**❌ Basis Spread** - Not found in docs
- Can calculate from spot + futures data

**❌ CVD** - Not available

**❌ Taker Ratios** - Not available

---

### 4. ALPACA MARKETS
**Documentation**: `docs/api_references/alpaca_options.html`
**MCP Server**: Available (alpaca-mcp-server)
**Specialty**: US equities options (NOT crypto)

#### Available Data:

**✅ Options Chain Data**
- Greeks: Delta, Gamma, Theta, Vega, Rho
- Implied Volatility per strike
- Open Interest per contract
- Historical: Yes (5+ years)

**✅ Put/Call Ratio** - Calculable
- Can aggregate put vs call OI and volume
- Historical data available

**✅ Historical IV**
- Available per strike/expiry
- Can aggregate for ATM IV index

**❌ Crypto Options** - Not supported
- Alpaca only offers US equities & ETF options
- No BTC/ETH options

**Note**: Alpaca is excellent for **traditional markets** but not applicable for crypto derivatives.

---

## 🔍 Data Depth Research Results ✅

**Tests Completed**: 2025-11-05

### Test Results:

### Binance Futures (TESTED ✅):

**1. Basis Spread** `/futures/data/basis`
- **Limit**: 500 data points
- **Max Span**: 16.6 months per request
- **For 36 months**: ~3 requests needed
- **Data Quality**: Excellent (full OHLC basis data)
- **Stitching**: Simple date range loop

**2. Open Interest History** `/futures/data/openInterestHist`
- **Limit**: 31 data points
- **Max Span**: 1 month per request
- **For 36 months**: ~36 requests needed
- **Data Quality**: Good (sumOpenInterest, sumOpenInterestValue)
- **Stitching**: Loop through 36 months (manageable)

**3. Taker Long/Short Ratio** `/futures/data/takerlongshortRatio`
- **Limit**: 31 data points
- **Max Span**: 1 month per request
- **For 36 months**: ~36 requests needed
- **Data Quality**: Excellent (buy/sell volumes + ratio)
- **Stitching**: Loop through 36 months (manageable)

### Deribit (TESTED ✅):

**1. DVOL Index** `/public/get_volatility_index_data`
- **Limit**: 1000 data points
- **Max Span**: 33.3 months per request
- **For 36 months**: 1-2 requests (almost there!)
- **Data Quality**: Excellent (official volatility index)
- **Stitching**: Minimal (just 1 extra request for 2-3 extra months)

**2. Ticker IV** `/public/ticker`
- **Availability**: Real-time only
- **Use Case**: Current IV snapshot, not historical
- **Note**: BTC-PERPETUAL doesn't have mark_iv (only options do)

### CoinAPI (KNOWN):
- **OI with OHLCV**: 3+ years historical ✅
- **Already implemented** in project

---

## ✅ Recommended Implementation Strategy

### Phase 1: Quick Wins (2 hours implementation)

**1. DVOL Index (Deribit)** - EASIEST ⭐
- **Why First**: Only 1-2 requests for 36 months
- **Complexity**: Low (simple date range, single loop)
- **Value**: High (official IV index for BTC/ETH)
- **Implementation**:
  ```python
  # Request 1: Last 33 months
  # Request 2: First 3 months (if needed)
  # Combine and cache
  ```

**2. Basis Spread (Binance)** - EASY ⭐⭐
- **Why Second**: Only 3 requests for 36 months
- **Complexity**: Low (3-iteration loop)
- **Value**: High (critical derivatives metric)
- **Implementation**:
  ```python
  # Loop 3 times: [0-500], [501-1000], [1001-1500] days back
  # Combine results
  # Cache to historical_data/
  ```

### Phase 2: Medium Effort (4 hours implementation)

**3. Taker Long/Short Ratio (Binance)** - MODERATE ⭐⭐⭐
- **Requests**: 36 (one per month)
- **Complexity**: Medium (month iteration loop)
- **Value**: High (CVD proxy without GB downloads)
- **Implementation**:
  ```python
  # Loop through 36 months
  # Fetch 1 month at a time
  # Combine and cache
  # Daily updates: fetch only current month
  ```

**4. Open Interest History (Binance)** - MODERATE ⭐⭐⭐
- **Requests**: 36 (one per month)
- **Complexity**: Medium (month iteration loop)
- **Value**: Medium (already have OI from CoinAPI)
- **Implementation**: Same as Taker Ratio

### Data Stitching Pattern (Reusable):

```python
def fetch_historical_stitched(endpoint, start_date, end_date, period_days):
    """
    Generic stitching function for any Binance endpoint.

    Args:
        endpoint: API endpoint path
        start_date: datetime object
        end_date: datetime object
        period_days: Max days per request (e.g., 30 for OI/Taker, 500 for Basis)

    Returns:
        Combined time series data
    """
    all_data = []
    current_start = start_date

    while current_start < end_date:
        current_end = min(current_start + timedelta(days=period_days), end_date)

        # Fetch chunk
        chunk = fetch_chunk(endpoint, current_start, current_end)
        all_data.extend(chunk)

        current_start = current_end
        time.sleep(0.5)  # Rate limit protection

    return all_data
```

### Phase 2: Deribit Options Data (Medium Difficulty)
**Endpoints to implement**:
1. ✅ **DVOL Index** - `/public/get_volatility_index_data`
   - Historical IV index for BTC/ETH
   - Excellent volatility metric

2. ⚠️ **Put/Call Ratio** - Calculate from book summary
   - Requires aggregation across all options
   - More complex but valuable

### Phase 3: Cross-API Validation
- Compare Binance OI vs CoinAPI OI
- Validate data quality and alignment
- Choose best source per metric

---

## 🚫 What's NOT Feasible

**❌ CVD from Raw Trades**
- Requires downloading 100+ GB of trade data
- Processing time: 8-10 hours
- Storage: 25+ GB
- **Verdict**: Not practical, use Taker Long/Short Ratio instead

**❌ Crypto Options from Alpaca**
- Alpaca doesn't offer crypto options
- Only US equities/ETFs
- **Verdict**: Use Deribit for crypto options

**❌ TradingView Scraping**
- Against ToS
- Unreliable and fragile
- **Verdict**: Use official APIs only

---

## 📋 Summary Table

| Metric | Best Source | Endpoint | Historical Depth | Requests Needed | Priority | Difficulty |
|--------|------------|----------|-----------------|----------------|----------|-----------|
| **DVOL Index** | Deribit | `/public/get_volatility_index_data` | 33.3 mo | 1-2 | HIGH ⭐ | EASY |
| **Basis Spread** | Binance | `/futures/data/basis` | 16.6 mo | 3 | HIGH ⭐ | EASY |
| **Taker Ratio** (CVD proxy) | Binance | `/futures/data/takerlongshortRatio` | 1 mo | 36 | HIGH | MEDIUM |
| **OI History** | Binance | `/futures/data/openInterestHist` | 1 mo | 36 | MEDIUM | MEDIUM |
| **Put/Call Ratio** | Deribit | Calculate from book summary | Real-time | N/A | LOW | HARD |
| **Options Greeks** | Deribit | `/public/ticker` | Real-time | N/A | LOW | N/A |

---

## 🔬 Implementation Roadmap

### ✅ Completed:
1. ✅ Tested Binance historical limits
2. ✅ Tested Deribit DVOL history
3. ✅ Confirmed feasibility of all metrics
4. ✅ Determined stitching requirements

### 🚀 Next Action Items:

**Quick Wins (Do These First)**:
1. Implement `data/dvol_index_deribit.py` (1-2 hours)
   - Fetch BTC & ETH DVOL
   - 1-2 API requests total
   - Cache to `historical_data/`

2. Implement `data/basis_spread_binance.py` (2 hours)
   - 3-request loop
   - Cache to `historical_data/`

**Medium Effort (Do After Quick Wins)**:
3. Implement `data/taker_ratio_binance.py` (3-4 hours)
   - 36-request loop with rate limiting
   - Incremental daily updates

4. Implement `data/oi_history_binance.py` (3-4 hours)
   - Same pattern as taker ratio
   - Optional (already have OI from CoinAPI)

**Integration**:
5. Add oscillator normalization - Z-score with configurable windows
6. Add to frontend charts with proper legends
7. Test with existing Markov regime backgrounds

---

## 📝 Notes

- Binance rate limits: TBD (needs testing)
- Deribit rate limits: TBD (needs testing)
- All Binance endpoints are FREE (no API key required for market data)
- Deribit API is FREE (no API key required for public endpoints)
- **No additional costs** beyond existing CoinAPI subscription
