# TradingView Daily Update Mechanism

**Status**: ✅ Implemented and tested
**Script**: `scripts/tradingview_daily_update.py`
**Coverage**: All 27 TradingView metrics

---

## Overview

This script maintains fresh data for all 27 TradingView metrics by:
1. Fetching the last 7 days of data for each symbol
2. Merging with existing historical data (automatic deduplication)
3. Only saving new data points that don't already exist
4. Logging all updates to `historical_data/tradingview_update_log.json`

**Key Features**:
- **Incremental updates**: Only adds new data points
- **Automatic deduplication**: Uses `incremental_data_manager` to merge intelligently
- **Rate limiting**: 3s between symbols, 5s between exchanges, exponential backoff on errors
- **Retry logic**: Up to 2 retries per symbol
- **Login support**: Automatically uses credentials from `.env`
- **Comprehensive logging**: Tracks success/failure for each symbol

---

## Usage

### Basic Update (All 27 Symbols)
```bash
python scripts/tradingview_daily_update.py
```

### Test Mode (First 3 Symbols)
```bash
python scripts/tradingview_daily_update.py --symbols 3
```

### Dry Run (Show What Would Be Updated)
```bash
python scripts/tradingview_daily_update.py --dry-run
```

### Custom Fetch Period
```bash
python scripts/tradingview_daily_update.py --days 14  # Fetch last 14 days
```

---

## Automation

### Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task → Name: "TradingView Daily Update"
3. Trigger: Daily at 6:00 AM (after markets close)
4. Action: Start a program
   - Program: `C:\Users\majee\AppData\Local\Programs\Python\Python311\python.exe`
   - Arguments: `C:\Users\majee\Desktop\Dash\scripts\tradingview_daily_update.py`
   - Start in: `C:\Users\majee\Desktop\Dash`
5. Finish

### Linux/Mac Cron

Add to crontab (`crontab -e`):
```bash
# Run daily at 6:00 AM
0 6 * * * cd /path/to/Dash && python scripts/tradingview_daily_update.py >> logs/tv_update.log 2>&1
```

---

## Symbols Covered (27 Total)

### On-Chain Metrics (15)
**GLASSNODE** (8):
- BTC_SOPR - Spent Output Profit Ratio
- BTC_MEDIANVOLUME - Median Transaction Volume
- BTC_MEANTXFEES - Mean Transaction Fees
- BTC_SENDINGADDRESSES - Sending Addresses (Active)
- BTC_ACTIVE1Y - Active Supply (1 Year)
- BTC_RECEIVINGADDRESSES - Receiving Addresses (Active) [LOGIN REQUIRED]
- BTC_NEWADDRESSES - New Addresses
- USDT_TFSPS - Transfer Speed (TPS) [LOGIN REQUIRED]

**COINMETRICS** (8):
- BTC_SER - Spent Entities Ratio
- BTC_AVGTX - Average Transaction Size
- BTC_TXCOUNT - Transaction Count (Daily)
- BTC_SPLYADRBAL1 - Supply in Addresses ≥1 BTC [LOGIN REQUIRED]
- BTC_ADDRESSESSUPPLY1IN10K - Addresses Holding 1/10,000 of Supply
- BTC_LARGETXCOUNT - Large Transaction Count (>$100k)
- BTC_ACTIVESUPPLY1Y - Active Supply (Last 1 Year) [LOGIN REQUIRED]
- USDT_AVGTX - USDT Average Transaction Size

### Social Metrics (4)
**LUNARCRUSH**:
- BTC_POSTSCREATED - Social Posts Created [LOGIN REQUIRED]
- BTC_CONTRIBUTORSCREATED - New Contributors [LOGIN REQUIRED]
- BTC_SOCIALDOMINANCE - Social Dominance %
- BTC_CONTRIBUTORSACTIVE - Active Contributors

### Market Metrics (2)
**CRYPTOCAP**:
- TOTAL3 - Total Altcoin Market Cap (excl BTC/ETH)
- STABLE.C.D - Stablecoin Dominance %

### ETFs (2)
- NASDAQ:IBIT - iShares Bitcoin Trust ETF
- AMEX:GBTC - Grayscale Bitcoin Trust ETF

### Other (4)
- KRAKEN:USDTUSD.PM - USDT Premium/Discount [LOGIN REQUIRED]
- DEFILLAMA:BTCST_TVL - Bitcoin Staking TVL [LOGIN REQUIRED]
- FRED:RRPONTSYD - Federal Reserve Reverse Repo

---

## Login Requirements

**10 symbols require TradingView authentication**:
- GLASSNODE:BTC_RECEIVINGADDRESSES
- GLASSNODE:USDT_TFSPS
- COINMETRICS:BTC_SPLYADRBAL1
- COINMETRICS:BTC_ACTIVESUPPLY1Y
- KRAKEN:USDTUSD.PM
- LUNARCRUSH:BTC_POSTSCREATED
- LUNARCRUSH:BTC_CONTRIBUTORSCREATED
- DEFILLAMA:BTCST_TVL
- (IBIT was intermittent without login)

Ensure credentials are in `.env`:
```bash
TV_USERNAME=your_tradingview_username
TV_PASSWORD=your_tradingview_password
```

---

## Monitoring

### Check Last Update
```bash
# View update log
cat historical_data/tradingview_update_log.json | jq '.[-1]'
```

### Check Data Freshness
```bash
python -c "
import json
from datetime import datetime, timezone
files = ['btc_sopr', 'btc_medianvolume', 'total3', 'ibit']
for f in files:
    with open(f'historical_data/{f}.json') as file:
        data = json.load(file)
        last_ts = data[-1][0] / 1000
        last_date = datetime.fromtimestamp(last_ts, tz=timezone.utc)
        age_hours = (datetime.now(tz=timezone.utc) - last_date).total_seconds() / 3600
        print(f'{f:30} {last_date.strftime(\"%Y-%m-%d\")} ({age_hours:.1f}h ago)')
"
```

---

## Troubleshooting

### No New Data
This is **normal** if:
- Last data is from yesterday (data updates lag by 1-2 days for on-chain metrics)
- Weekend (ETF data only available weekdays)
- Data hasn't changed (some metrics update infrequently)

### Failed Symbols
Common causes:
1. **Rate limiting**: Wait 30 minutes, try again
2. **No login**: Check `.env` credentials for login-required symbols
3. **Symbol temporarily unavailable**: TradingView API intermittent issues

### Connection Timeout
- Check internet connection
- Check if TradingView is accessible
- Try again in 10-15 minutes

---

## Expected Behavior

**Daily Update at 6:00 AM**:
- Runtime: ~5-8 minutes (27 symbols × 3-5s delay)
- New data: 0-27 symbols (depends on data availability)
- Up-to-date: Most symbols (no new data since yesterday)
- Failed: 0-2 symbols (temporary API issues)

**Weekly Check (Manual)**:
```bash
python scripts/tradingview_daily_update.py --days 14
```
This ensures no gaps from missed updates.

---

## Integration with Dashboard

The 27 metrics are ready for dashboard integration:
1. ✅ Historical data backfilled (3 years)
2. ✅ Daily update mechanism implemented
3. ⏳ Data plugins needed (optional - can load directly from JSON)
4. ⏳ Frontend display (add to oscillator tabs)

Next step: Create data plugins or load directly from JSON files in Flask routes.

---

## Related Files

- **Update script**: `scripts/tradingview_daily_update.py`
- **Backfill script**: `scripts/backfill_all_metrics.py`
- **Symbol mapping**: `scripts/tradingview_symbols_final.json`
- **Data files**: `historical_data/*.json` (27 files)
- **Update log**: `historical_data/tradingview_update_log.json`
- **Retry script**: `scripts/retry_failed_symbols.py` (for manual recovery)

---

## Maintenance

**Weekly**:
- Check update log for consistent failures
- Verify data freshness with monitoring script

**Monthly**:
- Review `tradingview_update_log.json` for patterns
- Update symbol list if new metrics added

**Quarterly**:
- Re-run full backfill to catch any gaps:
  ```bash
  python scripts/backfill_all_metrics.py --resume
  ```
