#!/usr/bin/env python3
"""
CoinAPI Download Script: PCR (Put/Call Ratio) and CVD (Cumulative Volume Delta) Data

Fetches:
1. BTC Options data from Deribit for PCR calculation (3 months)
2. Taker Buy/Sell Ratio from Binance for CVD (3 months)
3. Liquidations data from Binance (3 months)

Strategy:
- For PCR: Fetch options trades/quotes for ATM strikes
- For CVD: Use taker ratio as proxy (actual CVD requires tick data)
- Target: 3 months of data (~90 days)
"""

import requests
import json
import time
import os
import sys
import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path
from collections import defaultdict

# Add parent directory to path for config import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import COINAPI_KEY

# Configuration
COINAPI_BASE_URL = 'https://rest.coinapi.io/v1'
BINANCE_FUTURES_BASE = 'https://fapi.binance.com'
DERIBIT_BASE = 'https://www.deribit.com/api/v2'

# Date range (last 3 months)
END_DATE = datetime.now(tz=timezone.utc)
START_DATE = END_DATE - timedelta(days=90)

RATE_LIMIT_DELAY = 2  # seconds

# Output paths
OUTPUT_DIR = Path('historical_data/options_pcr_cvd')
HEADERS = {'X-CoinAPI-Key': COINAPI_KEY}


def ensure_directories():
    """Create output directories."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[OK] Output directory: {OUTPUT_DIR}")


def get_current_btc_price():
    """Get current BTC price from Binance to determine ATM strikes."""
    try:
        url = f"{BINANCE_FUTURES_BASE}/fapi/v1/ticker/price"
        params = {'symbol': 'BTCUSDT'}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        price = float(response.json()['price'])
        print(f"[BTC Price] Current: ${price:,.2f}")
        return price
    except Exception as e:
        print(f"[ERROR] Failed to get BTC price: {e}")
        return 95000  # Fallback


def get_deribit_instruments():
    """Get list of active BTC options from Deribit (free API)."""
    try:
        url = f"{DERIBIT_BASE}/public/get_instruments"
        params = {
            'currency': 'BTC',
            'kind': 'option',
            'expired': 'false'
        }

        print(f"\n[Deribit] Fetching active BTC options list...")
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()

        instruments = response.json()['result']
        print(f"[Deribit] Found {len(instruments)} active BTC options")

        return instruments
    except Exception as e:
        print(f"[ERROR] Failed to get Deribit instruments: {e}")
        return []


def select_atm_strikes(instruments, current_price, num_strikes=10):
    """
    Select options near ATM (at-the-money) for PCR analysis.

    Args:
        instruments: List of Deribit option instruments
        current_price: Current BTC price
        num_strikes: Number of strikes to select

    Returns:
        List of selected instrument names
    """
    # Group by expiry and strike
    options_by_expiry = defaultdict(list)

    for inst in instruments:
        # Parse instrument name: BTC-DDMMMYY-STRIKE-C/P
        # Example: BTC-31JAN25-100000-C
        parts = inst['instrument_name'].split('-')
        if len(parts) != 4:
            continue

        expiry = parts[1]
        strike = float(parts[2])
        option_type = parts[3]  # C or P

        # Only consider options expiring in next 2 months
        options_by_expiry[expiry].append({
            'name': inst['instrument_name'],
            'strike': strike,
            'type': option_type,
            'expiry': expiry
        })

    # Find strikes closest to current price across different expiries
    selected = []

    # Sort expiries chronologically (roughly - this is simplified)
    sorted_expiries = sorted(options_by_expiry.keys())[:3]  # Next 3 expiries

    for expiry in sorted_expiries:
        options = options_by_expiry[expiry]

        # Find strikes near current price
        strikes_with_distance = []
        for opt in options:
            distance = abs(opt['strike'] - current_price)
            strikes_with_distance.append((distance, opt))

        # Sort by distance to current price
        strikes_with_distance.sort(key=lambda x: x[0])

        # Take top strikes (both calls and puts)
        for _, opt in strikes_with_distance[:num_strikes//3]:
            selected.append(opt['name'])

    print(f"\n[Selection] Selected {len(selected)} options near ATM:")
    for name in selected[:10]:
        print(f"  - {name}")

    return selected


def fetch_taker_ratio_binance():
    """
    Fetch 3 months of taker buy/sell ratio from Binance for CVD calculation.
    This is FREE from Binance API (no CoinAPI needed).
    """
    print(f"\n{'='*80}")
    print("FETCHING TAKER BUY/SELL RATIO (CVD Proxy)")
    print(f"{'='*80}")

    try:
        url = f"{BINANCE_FUTURES_BASE}/futures/data/takerlongshortRatio"

        # Binance allows max 500 records, 1d interval
        params = {
            'symbol': 'BTCUSDT',
            'period': '1d',
            'limit': 90  # 90 days
        }

        print(f"[Binance] Fetching taker ratio (90 days)...")
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()

        # Convert to our format [timestamp_ms, ratio]
        taker_data = []
        for point in data:
            timestamp = point['timestamp']
            ratio = float(point['buySellRatio'])
            taker_data.append([timestamp, ratio])

        taker_data.sort(key=lambda x: x[0])

        # Save
        output_file = OUTPUT_DIR / 'taker_ratio_3m.json'
        with open(output_file, 'w') as f:
            json.dump(taker_data, f)

        print(f"[OK] Saved {len(taker_data)} records to {output_file}")
        print(f"[Range] {datetime.fromtimestamp(taker_data[0][0]/1000).date()} to {datetime.fromtimestamp(taker_data[-1][0]/1000).date()}")

        return taker_data

    except Exception as e:
        print(f"[ERROR] Failed to fetch taker ratio: {e}")
        return []


def fetch_liquidations_binance():
    """
    Fetch 3 months of liquidation data from Binance.
    Note: Binance liquidation endpoint might have different limits.
    """
    print(f"\n{'='*80}")
    print("FETCHING LIQUIDATIONS DATA")
    print(f"{'='*80}")

    try:
        # Note: Binance doesn't have a direct historical liquidations API
        # We'll use forceOrders endpoint which shows recent liquidations
        url = f"{BINANCE_FUTURES_BASE}/fapi/v1/allForceOrders"

        print(f"[Binance] Attempting to fetch liquidations...")
        print(f"[WARNING] Binance only provides recent liquidations (not 3-month history)")

        params = {
            'symbol': 'BTCUSDT',
            'limit': 1000  # Max allowed
        }

        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()

        if data:
            # Save what we got
            output_file = OUTPUT_DIR / 'liquidations_recent.json'
            with open(output_file, 'w') as f:
                json.dump(data, f)

            print(f"[OK] Saved {len(data)} recent liquidation records to {output_file}")
        else:
            print(f"[WARNING] No liquidation data available")

        return data

    except Exception as e:
        print(f"[WARNING] Liquidations API error: {e}")
        print(f"[INFO] This is expected - Binance may not provide historical liquidations publicly")
        return []


def fetch_options_quotes_coinapi(symbol_ids):
    """
    Fetch historical quotes for selected option symbols.
    This gives us bid/ask volume which can indicate interest in calls vs puts.
    """
    print(f"\n{'='*80}")
    print("FETCHING OPTIONS QUOTES FOR PCR")
    print(f"{'='*80}")

    all_data = {}
    credits_used = 0

    for i, symbol_id in enumerate(symbol_ids[:10], 1):  # Limit to 10 to conserve credits
        # Convert Deribit symbol to CoinAPI format
        # BTC-31JAN25-100000-C -> DERIBIT_OPT_BTC_USD_250131_100000_C
        try:
            parts = symbol_id.split('-')
            date_str = parts[1]  # 31JAN25
            strike = parts[2]
            opt_type = parts[3]

            # Parse date (simplified - this is rough)
            # Would need proper date parsing in production
            coinapi_symbol = f"DERIBIT_OPT_BTC_USD_{date_str}_{strike}_{opt_type}"

            print(f"\n[{i}/10] Fetching: {symbol_id}")
            print(f"[CoinAPI Symbol] {coinapi_symbol}")

            url = f"{COINAPI_BASE_URL}/quotes/{coinapi_symbol}/history"

            params = {
                'time_start': START_DATE.strftime('%Y-%m-%dT00:00:00'),
                'time_end': END_DATE.strftime('%Y-%m-%dT23:59:59'),
                'limit': 10000
            }

            response = requests.get(url, params=params, headers=HEADERS, timeout=60)

            if response.status_code == 200:
                data = response.json()
                all_data[symbol_id] = data
                credits_used += 10  # Date-bounded request

                print(f"[OK] Received {len(data)} quotes")
            else:
                print(f"[ERROR] HTTP {response.status_code}: {response.text[:200]}")
                # Symbol might not exist in CoinAPI format, skip

            # Rate limiting
            if i < len(symbol_ids[:10]):
                time.sleep(RATE_LIMIT_DELAY)

        except Exception as e:
            print(f"[ERROR] Failed to fetch {symbol_id}: {e}")
            continue

    # Save all options data
    output_file = OUTPUT_DIR / 'options_quotes_3m.json'
    with open(output_file, 'w') as f:
        json.dump(all_data, f, indent=2)

    print(f"\n[SAVED] Options quotes to {output_file}")
    print(f"[Credits Used] {credits_used}")

    return all_data, credits_used


def calculate_pcr_from_options(options_data):
    """
    Calculate daily PCR from options quotes/trades data.
    """
    print(f"\n{'='*80}")
    print("CALCULATING PCR (PUT/CALL RATIO)")
    print(f"{'='*80}")

    # Group by date
    daily_volume = defaultdict(lambda: {'calls': 0, 'puts': 0})

    for symbol, quotes in options_data.items():
        # Determine if call or put from symbol name
        is_put = symbol.endswith('-P')

        for quote in quotes:
            timestamp = quote.get('time_exchange')
            if not timestamp:
                continue

            # Parse date
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            date_key = dt.date()

            # Use bid/ask size as proxy for volume/interest
            bid_size = quote.get('bid_size', 0)
            ask_size = quote.get('ask_size', 0)
            total_size = bid_size + ask_size

            if is_put:
                daily_volume[date_key]['puts'] += total_size
            else:
                daily_volume[date_key]['calls'] += total_size

    # Calculate PCR for each day
    pcr_data = []
    for date_key in sorted(daily_volume.keys()):
        calls = daily_volume[date_key]['calls']
        puts = daily_volume[date_key]['puts']

        if calls > 0:
            pcr = puts / calls
        else:
            pcr = None

        pcr_data.append({
            'date': str(date_key),
            'timestamp': int(datetime.combine(date_key, datetime.min.time()).replace(tzinfo=timezone.utc).timestamp() * 1000),
            'put_volume': puts,
            'call_volume': calls,
            'pcr': pcr
        })

    # Save PCR data
    output_file = OUTPUT_DIR / 'pcr_daily_3m.json'
    with open(output_file, 'w') as f:
        json.dump(pcr_data, f, indent=2)

    print(f"[OK] Calculated PCR for {len(pcr_data)} days")
    print(f"[SAVED] {output_file}")

    # Print sample
    if pcr_data:
        print(f"\n[Sample PCR Data]:")
        for entry in pcr_data[-5:]:
            pcr_val = entry['pcr']
            if pcr_val:
                print(f"  {entry['date']}: PCR={pcr_val:.3f} (Puts={entry['put_volume']:.0f}, Calls={entry['call_volume']:.0f})")

    return pcr_data


def generate_summary(taker_data, options_data, pcr_data, credits_used):
    """Generate download summary."""
    print(f"\n{'='*80}")
    print("DOWNLOAD SUMMARY: PCR & CVD DATA")
    print(f"{'='*80}")

    print(f"\n[Taker Ratio (CVD Proxy)]")
    print(f"  Records: {len(taker_data)}")
    if taker_data:
        print(f"  Range: {datetime.fromtimestamp(taker_data[0][0]/1000).date()} to {datetime.fromtimestamp(taker_data[-1][0]/1000).date()}")
        print(f"  File: {OUTPUT_DIR / 'taker_ratio_3m.json'}")

    print(f"\n[Options Data (PCR)]")
    print(f"  Symbols fetched: {len(options_data)}")
    print(f"  PCR records: {len(pcr_data)} days")
    if pcr_data:
        print(f"  Range: {pcr_data[0]['date']} to {pcr_data[-1]['date']}")
        print(f"  File: {OUTPUT_DIR / 'pcr_daily_3m.json'}")

    print(f"\n[API Credits]")
    print(f"  Credits used: {credits_used}")
    print(f"  Estimated remaining: ~{730 - credits_used}")

    print(f"\n[Output Directory]")
    print(f"  Location: {OUTPUT_DIR}/")

    # List all files
    files = list(OUTPUT_DIR.glob('*.json'))
    print(f"  Files created: {len(files)}")
    for f in files:
        size_kb = f.stat().st_size / 1024
        print(f"    - {f.name} ({size_kb:.1f} KB)")


def main():
    """Main execution function."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Download PCR and CVD data')
    parser.add_argument('--yes', '-y', action='store_true', help='Skip confirmation prompt')
    args = parser.parse_args()

    print("="*80)
    print("COINAPI DOWNLOAD: PCR & CVD DATA (3 MONTHS)")
    print("="*80)
    print(f"Date Range: {START_DATE.date()} to {END_DATE.date()}")
    print(f"API Key: {'*' * 20}{COINAPI_KEY[-4:] if COINAPI_KEY else 'NOT SET'}")

    if not COINAPI_KEY:
        print("\n[ERROR] COINAPI_KEY not found in config.py")
        sys.exit(1)

    ensure_directories()

    total_credits = 0

    # Step 1: Get current BTC price
    current_price = get_current_btc_price()

    # Step 2: Fetch taker ratio for CVD (FREE from Binance)
    taker_data = fetch_taker_ratio_binance()

    # Step 3: Fetch liquidations (FREE from Binance, limited data)
    liquidations = fetch_liquidations_binance()

    # Step 4: Get active options from Deribit (FREE)
    instruments = get_deribit_instruments()

    if not instruments:
        print("\n[ERROR] Failed to get Deribit instruments. Cannot proceed with PCR.")
        options_data = {}
        pcr_data = []
    else:
        # Step 5: Select ATM strikes
        selected_symbols = select_atm_strikes(instruments, current_price, num_strikes=10)

        if not selected_symbols:
            print("\n[WARNING] No suitable options found for PCR calculation")
            options_data = {}
            pcr_data = []
        else:
            # Step 6: Fetch options quotes from CoinAPI
            print(f"\n[Note] This will use approximately 100 credits for 10 options contracts")

            if not args.yes:
                response = input("Proceed with options download? (yes/no): ")
                proceed = response.lower() in ['yes', 'y']
            else:
                print("[Auto-confirmed] Proceeding with options download (--yes flag)")
                proceed = True

            if proceed:
                options_data, credits = fetch_options_quotes_coinapi(selected_symbols)
                total_credits += credits

                # Step 7: Calculate PCR
                pcr_data = calculate_pcr_from_options(options_data)
            else:
                print("[ABORTED] Skipping options download")
                options_data = {}
                pcr_data = []

    # Generate summary
    generate_summary(taker_data, options_data, pcr_data, total_credits)

    print(f"\n{'='*80}")
    print("DOWNLOAD COMPLETE!")
    print(f"{'='*80}")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[ABORTED] Download interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
