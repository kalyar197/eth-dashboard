#!/usr/bin/env python3
"""
Quick status checker for gap filler completion
"""

import json
from pathlib import Path
from datetime import datetime, timezone

COMPLETE_FILE = Path('historical_data/btc_price_1min_complete.json')

if not COMPLETE_FILE.exists():
    print("❌ Gap filler not complete - file doesn't exist yet")
    print(f"   Waiting for: {COMPLETE_FILE}")
    exit(1)

try:
    with open(COMPLETE_FILE, 'r') as f:
        data = json.load(f)

    if not data:
        print("❌ File exists but is empty")
        exit(1)

    last_ts = data[-1][0]
    last_dt = datetime.fromtimestamp(last_ts / 1000, tz=timezone.utc)
    now = datetime.now(tz=timezone.utc)
    gap_hours = (now - last_dt).total_seconds() / 3600

    print(f"✅ Gap filler complete!")
    print(f"   Records: {len(data):,}")
    print(f"   Last bar: {last_dt}")
    print(f"   Gap from now: {gap_hours:.1f} hours")

    if gap_hours < 24:
        print(f"\n🎯 READY FOR VALIDATION")
        print(f"   Run: python scripts/validate_btc_data.py")
    else:
        print(f"\n⚠️  Data is {gap_hours:.1f} hours old")
        print(f"   Run daily updater to catch up")

    exit(0)

except Exception as e:
    print(f"❌ Error reading file: {e}")
    exit(1)
