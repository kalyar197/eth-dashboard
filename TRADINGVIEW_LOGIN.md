# TradingView Login for Premium Data Access

Some TradingView data (especially Glassnode, CoinMetrics premium metrics) requires authentication.

## Setup Instructions

### Option 1: Environment Variables (Recommended)

Add these lines to your `.env` file:

```bash
TV_USERNAME=your_tradingview_username
TV_PASSWORD=your_tradingview_password
```

### Option 2: Command Line Arguments

```bash
python scripts/backfill_all_metrics.py --tv-username YOUR_USERNAME --tv-password YOUR_PASSWORD
```

## Testing Login

Run a dry-run to verify login works:

```bash
python scripts/backfill_all_metrics.py --dry-run --symbols 3
```

You should see:
```
TradingView Login: ENABLED (user: your_username)
```

Instead of:
```
TradingView Login: DISABLED (some premium data may be unavailable)
```

## Symbols Requiring Login

The following 5 symbols failed without login and may require TradingView authentication:

1. **GLASSNODE:BTC_MEDIANVOLUME** - Bitcoin median transaction volume
2. **COINMETRICS:BTC_SPLYADRBAL1** - Bitcoin supply in addresses with balance ≥1
3. **COINMETRICS:BTC_ACTIVESUPPLY1Y** - Bitcoin active supply (1 year)
4. **LUNARCRUSH:BTC_CONTRIBUTORSCREATED** - Bitcoin new contributors (social)
5. **DEFILLAMA:BTCST_TVL** - Bitcoin staking TVL

## Security Notes

- Never commit `.env` file to git (already in `.gitignore`)
- Use a strong, unique password for TradingView
- Consider using a dedicated TradingView account for API access

## Troubleshooting

If login fails:
- Verify credentials are correct
- Check if TradingView requires 2FA (may need to disable for API access)
- Try logging in manually at tradingview.com first
- Some symbols may still be unavailable even with login (premium subscription required)
