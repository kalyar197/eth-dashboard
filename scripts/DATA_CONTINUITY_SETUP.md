# Data Continuity Setup Guide

## Overview

This guide ensures your BTC 1-minute data stays up-to-date automatically with NO gaps.

## Current Status

✅ **Historical Data**: 5 years (2020-2025) from CoinAPI
🔄 **Gap Fill**: Jan 7 - Nov 8, 2025 (currently running)
♻️ **Continuous Updates**: Scripts ready

---

## Setup Steps

### 1. Fill the Gap (ONE-TIME)

**Status**: ✅ Running now

```bash
python scripts/binance_fill_gap.py
```

This fills the 10-month gap from Jan 7 to today using FREE Binance API.

---

### 2. Set Up Daily Updates (AUTOMATED)

**Option A: Windows Task Scheduler** (Recommended)

Run as Administrator:
```cmd
scripts\setup_daily_update.bat
```

This creates a scheduled task that runs every day at 2 AM.

**Option B: Manual Scheduling**

```cmd
# Create task
schtasks /Create /SC DAILY /TN "BTC_Data_Update" /TR "python C:\Users\majee\Desktop\Dash\scripts\binance_daily_update.py" /ST 02:00 /F

# Run manually
python scripts/binance_daily_update.py

# Or fetch last 48 hours
python scripts/binance_daily_update.py --hours 48
```

**Option C: Cron (Linux/Mac)**

```bash
# Add to crontab
crontab -e

# Run daily at 2 AM
0 2 * * * cd /path/to/Dash && python scripts/binance_daily_update.py
```

---

### 3. Monitor Data Quality

Check last update:
```bash
python -c "import json; from datetime import datetime, timezone; data = json.load(open('historical_data/btc_price_1min_complete.json')); last = datetime.fromtimestamp(data[-1][0]/1000, tz=timezone.utc); print(f'Last record: {last}')"
```

Expected output: Should be within last 24 hours

---

## File Structure

```
historical_data/
├── btc_price_1min.json              # Original 5-year data (2020-2025)
├── btc_price_1min_complete.json     # Complete dataset with gap filled
└── btc_price_1min_complete.backup.json  # Backup (created before each update)

scripts/
├── binance_fill_gap.py              # ONE-TIME gap filler
├── binance_daily_update.py          # DAILY updater
└── setup_daily_update.bat           # Windows scheduler setup
```

---

## Data Sources

| Data | Source | API | Cost |
|------|--------|-----|------|
| 2020-2025 | CoinAPI | Startup tier | $79/month (expired) |
| Jan 7 - Now | Binance | Public API | FREE |
| Future | Binance | Public API | FREE |

---

## Verification

After gap fill completes, verify:

```bash
python -c "
import json
from datetime import datetime, timezone

with open('historical_data/btc_price_1min_complete.json') as f:
    data = json.load(f)

first = datetime.fromtimestamp(data[0][0]/1000, tz=timezone.utc)
last = datetime.fromtimestamp(data[-1][0]/1000, tz=timezone.utc)
days = (last - first).days

print(f'Records: {len(data):,}')
print(f'Range: {first.date()} to {last.date()}')
print(f'Days: {days}')
print(f'Expected: {days * 1440:,} bars (1440 per day)')
print(f'Coverage: {len(data) / (days * 1440) * 100:.2f}%')
"
```

Expected coverage: >99%

---

## Troubleshooting

**Gap filler fails:**
- Check internet connection
- Binance might be down (try later)
- Check error messages for rate limiting

**Daily updater not running:**
- Verify task is created: `schtasks /Query /TN "BTC_Data_Daily_Update"`
- Check task history in Task Scheduler GUI
- Run manually to test: `python scripts/binance_daily_update.py`

**Data gaps appear:**
- Run `binance_daily_update.py --hours 72` to fetch last 3 days
- Check if scheduled task is disabled

---

## Maintenance

### Weekly Check
```bash
# Run daily updater manually to verify
python scripts/binance_daily_update.py
```

### Monthly Backup
```bash
# Create manual backup
copy historical_data\btc_price_1min_complete.json historical_data\backups\btc_data_$(date +%Y%m%d).json
```

---

## Next Steps (Optional)

1. **ETH Data**: Same process for ETH (`ETHUSDT` symbol)
2. **PCR Data**: Fetch from Deribit free API
3. **Real-time WebSocket**: For tick-level data

---

## Support

If daily updates stop working:
1. Check Task Scheduler is running the task
2. Manually run: `python scripts/binance_daily_update.py`
3. Check `btc_price_1min_complete.backup.json` for rollback

**Last Updated**: November 8, 2025
