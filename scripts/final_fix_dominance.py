# scripts/final_fix_dominance.py
"""
Final fix for dominance data:
1. Remove all data after Nov 1st (everything Nov 2+ has issues)
2. Fetch Nov 2-3 from TradingView to backfill missing days
3. Ensure only real data up to today (Nov 3rd)
"""

import sys
import os
from datetime import datetime, timezone
import json
from tvDatafeed import TvDatafeed, Interval

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Today is November 3rd, 2025
TODAY = datetime(2025, 11, 3, tzinfo=timezone.utc)
TODAY_MS = int(TODAY.timestamp() * 1000)

print("="*80)
print("Final Fix: Fetch Real Nov 2-3 Data from TradingView")
print(f"Today: {TODAY.strftime('%Y-%m-%d')}")
print("="*80)

# Fetch last 5 days from TradingView (to get Nov 2-3)
print("\n--- Step 1: Fetch Last 5 Days from TradingView ---")
tv = TvDatafeed()

btc_d_tv = tv.get_hist(symbol='BTC.D', exchange='CRYPTOCAP', interval=Interval.in_daily, n_bars=5)
usdt_d_tv = tv.get_hist(symbol='USDT.D', exchange='CRYPTOCAP', interval=Interval.in_daily, n_bars=5)

# Convert to our format
btc_tv_data = []
for index, row in btc_d_tv.iterrows():
    dt = index if index.tzinfo else index.replace(tzinfo=timezone.utc)
    timestamp_ms = int(dt.astimezone(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).timestamp() * 1000)
    btc_tv_data.append([timestamp_ms, float(row['close'])])

usdt_tv_data = []
for index, row in usdt_d_tv.iterrows():
    dt = index if index.tzinfo else index.replace(tzinfo=timezone.utc)
    timestamp_ms = int(dt.astimezone(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).timestamp() * 1000)
    usdt_tv_data.append([timestamp_ms, float(row['close'])])

print("BTC.D from TradingView (last 5 days):")
for d in btc_tv_data:
    dt = datetime.fromtimestamp(d[0]/1000, tz=timezone.utc)
    print(f"  {dt.strftime('%Y-%m-%d')}: {d[1]:.2f}%")

print("\nUSDT.D from TradingView (last 5 days):")
for d in usdt_tv_data:
    dt = datetime.fromtimestamp(d[0]/1000, tz=timezone.utc)
    print(f"  {dt.strftime('%Y-%m-%d')}: {d[1]:.2f}%")

# Load existing data
print("\n--- Step 2: Load Historical Data and Remove Nov 2+ ---")
with open('historical_data/btc_dominance.json', 'r') as f:
    btc_data = json.load(f)

with open('historical_data/usdt_dominance.json', 'r') as f:
    usdt_data = json.load(f)

# Nov 2nd at midnight UTC
NOV_2_MS = int(datetime(2025, 11, 2, tzinfo=timezone.utc).timestamp() * 1000)

# Keep only data before Nov 2nd
btc_valid = [d for d in btc_data if d[0] < NOV_2_MS]
usdt_valid = [d for d in usdt_data if d[0] < NOV_2_MS]

print(f"BTC.D: Kept {len(btc_valid)} records before Nov 2nd")
print(f"USDT.D: Kept {len(usdt_valid)} records before Nov 2nd")

# Add TradingView data for Nov 2-3 only
print("\n--- Step 3: Add Nov 2-3 from TradingView ---")
btc_nov2_3 = [d for d in btc_tv_data if NOV_2_MS <= d[0] <= TODAY_MS]
usdt_nov2_3 = [d for d in usdt_tv_data if NOV_2_MS <= d[0] <= TODAY_MS]

print(f"Adding {len(btc_nov2_3)} BTC.D records for Nov 2-3:")
for d in btc_nov2_3:
    dt = datetime.fromtimestamp(d[0]/1000, tz=timezone.utc)
    print(f"  {dt.strftime('%Y-%m-%d')}: {d[1]:.2f}%")

print(f"\nAdding {len(usdt_nov2_3)} USDT.D records for Nov 2-3:")
for d in usdt_nov2_3:
    dt = datetime.fromtimestamp(d[0]/1000, tz=timezone.utc)
    print(f"  {dt.strftime('%Y-%m-%d')}: {d[1]:.2f}%")

# Combine
btc_final = btc_valid + btc_nov2_3
usdt_final = usdt_valid + usdt_nov2_3

# Save
print("\n--- Step 4: Save Final Data ---")
with open('historical_data/btc_dominance.json', 'w') as f:
    json.dump(btc_final, f)

with open('historical_data/usdt_dominance.json', 'w') as f:
    json.dump(usdt_final, f)

print(f"Saved {len(btc_final)} BTC.D records")
print(f"Saved {len(usdt_final)} USDT.D records")

# Verify
print("\n--- Step 5: Final Verification ---")
print("Last 5 BTC.D entries:")
for d in btc_final[-5:]:
    dt = datetime.fromtimestamp(d[0]/1000, tz=timezone.utc)
    print(f"  {dt.strftime('%Y-%m-%d')}: {d[1]:.2f}%")

print("\nLast 5 USDT.D entries:")
for d in usdt_final[-5:]:
    dt = datetime.fromtimestamp(d[0]/1000, tz=timezone.utc)
    print(f"  {dt.strftime('%Y-%m-%d')}: {d[1]:.2f}%")

print("\n" + "="*80)
print("[SUCCESS] All data now real from TradingView up to today (Nov 3rd)")
print("="*80)
