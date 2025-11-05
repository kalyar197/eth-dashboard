# scripts/fix_current_dominance.py
"""
Fix dominance data by:
1. Fetching today's (Nov 3, 2025) real values from CoinMarketCap
2. Removing all future/improvised data
3. Ensuring only real historical data exists
"""

import sys
import os
from datetime import datetime, timezone
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.btc_dominance_cmc import fetch_current_btc_dominance
from data.usdt_dominance_cmc import fetch_current_usdt_dominance

# Today is November 3rd, 2025
TODAY = datetime(2025, 11, 3, tzinfo=timezone.utc)
TODAY_MS = int(TODAY.timestamp() * 1000)

print("="*80)
print("Fix Dominance Data - Remove Future/Improvised Values")
print(f"Today: {TODAY.strftime('%Y-%m-%d')}")
print("="*80)

# Fetch today's real values from CoinMarketCap
print("\n--- Step 1: Fetch Today's Real Values from CoinMarketCap ---")
btc_d_today = fetch_current_btc_dominance()
usdt_d_today = fetch_current_usdt_dominance()

print(f"BTC.D today: {btc_d_today[0][1]:.2f}%")
print(f"USDT.D today: {usdt_d_today[0][1]:.2f}%")

# Load existing data
print("\n--- Step 2: Load and Clean Historical Data ---")
with open('historical_data/btc_dominance.json', 'r') as f:
    btc_data = json.load(f)

with open('historical_data/usdt_dominance.json', 'r') as f:
    usdt_data = json.load(f)

print(f"BTC.D: {len(btc_data)} total records")
print(f"USDT.D: {len(usdt_data)} total records")

# Remove future data (anything after TODAY)
btc_valid = [d for d in btc_data if d[0] < TODAY_MS]
btc_future = [d for d in btc_data if d[0] >= TODAY_MS]

usdt_valid = [d for d in usdt_data if d[0] < TODAY_MS]
usdt_future = [d for d in usdt_data if d[0] >= TODAY_MS]

print(f"\nBTC.D: Removing {len(btc_future)} future/today records")
for d in btc_future:
    dt = datetime.fromtimestamp(d[0]/1000, tz=timezone.utc)
    print(f"  Removed: {dt.strftime('%Y-%m-%d')}: {d[1]}")

print(f"\nUSDT.D: Removing {len(usdt_future)} future/today records")
for d in usdt_future:
    dt = datetime.fromtimestamp(d[0]/1000, tz=timezone.utc)
    print(f"  Removed: {dt.strftime('%Y-%m-%d')}: {d[1]}")

# Add today's real values
print("\n--- Step 3: Add Today's Real Values ---")
btc_final = btc_valid + btc_d_today
usdt_final = usdt_valid + usdt_d_today

print(f"BTC.D final: {len(btc_final)} records (up to {TODAY.strftime('%Y-%m-%d')})")
print(f"USDT.D final: {len(usdt_final)} records (up to {TODAY.strftime('%Y-%m-%d')})")

# Save cleaned data
print("\n--- Step 4: Save Cleaned Data ---")
with open('historical_data/btc_dominance.json', 'w') as f:
    json.dump(btc_final, f)
print(f"Saved {len(btc_final)} BTC.D records")

with open('historical_data/usdt_dominance.json', 'w') as f:
    json.dump(usdt_final, f)
print(f"Saved {len(usdt_final)} USDT.D records")

# Verify last entries
print("\n--- Step 5: Verification ---")
print(f"BTC.D last 3 entries:")
for d in btc_final[-3:]:
    dt = datetime.fromtimestamp(d[0]/1000, tz=timezone.utc)
    print(f"  {dt.strftime('%Y-%m-%d')}: {d[1]:.2f}%")

print(f"\nUSDT.D last 3 entries:")
for d in usdt_final[-3:]:
    dt = datetime.fromtimestamp(d[0]/1000, tz=timezone.utc)
    print(f"  {dt.strftime('%Y-%m-%d')}: {d[1]:.2f}%")

print("\n" + "="*80)
print("[SUCCESS] All future/improvised data removed. Only real data remains.")
print("="*80)
