import json
from datetime import datetime, timezone

btc = json.load(open('historical_data/btc_dominance.json'))
usdt = json.load(open('historical_data/usdt_dominance.json'))

print("=== LAST 5 BTC.D ENTRIES ===")
for d in btc[-5:]:
    dt = datetime.fromtimestamp(d[0]/1000, tz=timezone.utc)
    print(f"{dt.strftime('%Y-%m-%d')}: {d[1]}")

print("\n=== LAST 5 USDT.D ENTRIES ===")
for d in usdt[-5:]:
    dt = datetime.fromtimestamp(d[0]/1000, tz=timezone.utc)
    print(f"{dt.strftime('%Y-%m-%d')}: {d[1]}")

print(f"\nTotal BTC.D: {len(btc)}")
print(f"Total USDT.D: {len(usdt)}")
