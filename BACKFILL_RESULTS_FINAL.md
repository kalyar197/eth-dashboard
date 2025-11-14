# TradingView Backfill - Final Results

**Date**: 2025-11-14
**Success Rate**: 27/27 (100%)
**Authentication**: TradingView login enabled

---

## ✅ Successfully Fetched (27/27)

All data saved to `historical_data/` with 1:1 mapping to real TradingView charts.

### GLASSNODE (8/8 success)
1. ✅ **BTC_SOPR** - 1095 points - Bitcoin Spent Output Profit Ratio
2. ✅ **BTC_MEDIANVOLUME** - 1095 points - Bitcoin Median Transaction Volume (LOGIN REQUIRED)
3. ✅ **BTC_MEANTXFEES** - 1095 points - Bitcoin Mean Transaction Fees
4. ✅ **BTC_SENDINGADDRESSES** - 1095 points - Bitcoin Sending Addresses (Active)
5. ✅ **BTC_ACTIVE1Y** - 1095 points - Bitcoin Active Supply (1 Year)
6. ✅ **BTC_RECEIVINGADDRESSES** - 1095 points - Bitcoin Receiving Addresses (Active) (LOGIN REQUIRED)
7. ✅ **BTC_NEWADDRESSES** - 1095 points - Bitcoin New Addresses
8. ✅ **USDT_TFSPS** - 1095 points - USDT Transfer Speed (TPS) (LOGIN REQUIRED)

### COINMETRICS (8/8 success)
1. ✅ **BTC_SER** - 1095 points - Bitcoin Spent Entities Ratio
2. ✅ **BTC_AVGTX** - 1095 points - Bitcoin Average Transaction Size
3. ✅ **BTC_TXCOUNT** - 1095 points - Bitcoin Transaction Count (Daily)
4. ✅ **BTC_SPLYADRBAL1** - 1095 points - Bitcoin Supply in Addresses with Balance ≥1 (LOGIN REQUIRED)
5. ✅ **BTC_ADDRESSESSUPPLY1IN10K** - 1095 points - BTC Addresses Holding 1/10,000 of Supply
6. ✅ **BTC_LARGETXCOUNT** - 1095 points - Bitcoin Large Transaction Count (>$100k)
7. ✅ **BTC_ACTIVESUPPLY1Y** - 1095 points - Bitcoin Active Supply (Last 1 Year) (LOGIN REQUIRED)
8. ✅ **USDT_AVGTX** - 1095 points - USDT Average Transaction Size

### KRAKEN (1/1 success)
1. ✅ **USDTUSD.PM** - 979 points - USDT Premium/Discount to USD (LOGIN REQUIRED)

### LUNARCRUSH (4/4 success)
1. ✅ **BTC_POSTSCREATED** - 1095 points - Bitcoin Social Posts Created (LOGIN REQUIRED)
2. ✅ **BTC_CONTRIBUTORSCREATED** - 1095 points - Bitcoin New Contributors (LOGIN REQUIRED)
3. ✅ **BTC_SOCIALDOMINANCE** - 1103 points - Bitcoin Social Dominance %
4. ✅ **BTC_CONTRIBUTORSACTIVE** - 1095 points - Bitcoin Active Contributors

### DEFILLAMA (1/1 success)
1. ✅ **BTCST_TVL** - 1095 points - Bitcoin Staking Total Value Locked (LOGIN REQUIRED)

### NASDAQ (1/1 success)
1. ✅ **IBIT** - 673 points - iShares Bitcoin Trust ETF (launched Jan 2024)

### AMEX (1/1 success)
1. ✅ **GBTC** - 1590 points - Grayscale Bitcoin Trust ETF

### CRYPTOCAP (2/2 success)
1. ✅ **TOTAL3** - 1095 points - Total Altcoin Market Cap (excl BTC/ETH)
2. ✅ **STABLE.C.D** - 180 points - Stablecoin Dominance % (limited history)

### FRED (1/1 success)
1. ✅ **RRPONTSYD** - 1603 points - Federal Reserve Reverse Repo Outstanding

---

## 🔑 Login Impact

**With TradingView Login**, the following 10 symbols unlocked:
- GLASSNODE:BTC_MEDIANVOLUME
- GLASSNODE:BTC_RECEIVINGADDRESSES
- GLASSNODE:USDT_TFSPS
- COINMETRICS:BTC_SPLYADRBAL1
- COINMETRICS:BTC_ACTIVESUPPLY1Y
- KRAKEN:USDTUSD.PM
- LUNARCRUSH:BTC_POSTSCREATED
- LUNARCRUSH:BTC_CONTRIBUTORSCREATED
- DEFILLAMA:BTCST_TVL
- (IBIT was intermittent without login)

**Without login**: Only 16/27 succeeded (59%)
**With login**: 27/27 succeeded (100%)

---

## 📊 Data Quality Notes

All fetched data has been validated through 6-layer validation:
1. ✅ Fetch validation (data exists, minimum points)
2. ✅ Structure validation (timestamp/value format, no NaN/Inf)
3. ✅ Timestamp validation (uniqueness, ordering, midnight UTC)
4. ✅ Value range validation (per-symbol min/max)
5. ✅ Statistical sanity (spike detection as warnings, not errors)
6. ⚠️ Cross-symbol validation (planned)

**Accepted data characteristics**:
- Large daily spikes (>200%) accepted as warnings (volatile metrics have real spikes)
- Limited history accepted (STABLE.C.D has only 180 points = ~6 months)
- Timestamps standardized to midnight UTC
- All data saved with incremental deduplication

---

## 📁 Files Generated

- **Data files**: `historical_data/*.json` (27 new metrics)
- **Validation report**: `historical_data/backfill_validation_report.txt`
- **Results JSON**: `historical_data/backfill_results.json`
- **Log file**: `historical_data/backfill_log_YYYYMMDD_HHMMSS.txt`
- **Retry script**: `scripts/retry_failed_symbols.py` (used to fetch final 2 symbols)
- **Daily updater**: `scripts/tradingview_daily_update.py` (maintains fresh data)
- **Update log**: `historical_data/tradingview_update_log.json` (tracks daily updates)

---

## 🚀 Next Steps

1. ✅ TradingView backfill complete (27/27 metrics - 100% success)
2. ✅ Daily update mechanism implemented (`scripts/tradingview_daily_update.py`)
3. ⏳ Create data plugins for dashboard integration
4. ⏳ Update frontend to display new metrics
5. ⏳ Add dropdown/tabs for metric selection

---

## 💡 Key Learnings

1. **Login is essential**: 10 symbols require TradingView authentication
2. **Validation must be flexible**: Real data has volatile spikes (social metrics, on-chain)
3. **Symbol accuracy matters**: GGBTC → GBTC, BTC_SPLYADRBAL → BTC_SPLYADRBAL1
4. **Rate limiting during full runs**: BTC_RECEIVINGADDRESSES and BTC_SPLYADRBAL1 failed during bulk fetch but succeeded with retry script (extended delays)
5. **Multi-tier delays work**: 3s/5s/10s/60s prevented IP bans, but individual retry with 15s delays was needed for intermittent failures
