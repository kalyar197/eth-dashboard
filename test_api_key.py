import requests
import json
import sys
# Attempt to import COINAPI_KEY from config.py
try:
    from config import COINAPI_KEY
except ImportError:
    print("❌ ERROR: Could not find config.py or COINAPI_KEY. Ensure your key is set.")
    sys.exit()

def test_key_activation():
    """Fetches the latest BTC/USD exchange rate (simple, low-tier call)."""
    
    # 1. Check if key is set
    if not COINAPI_KEY or COINAPI_KEY == 'YOUR_ACTUAL_COINAPI_KEY_HERE':
        print("\n❌ FAIL: COINAPI_KEY is missing or set to placeholder in config.py.")
        return

    # 2. Define API endpoint (Latest Exchange Rate is the simplest call)
    url = "https://rest.coinapi.io/v1/exchangerate/BTC/USD"
    headers = {'X-CoinAPI-Key': COINAPI_KEY}

    print(f"\n--- Testing CoinAPI Key Activation ---")
    print(f"Requesting: {url}")
    
    # 3. Make the API request
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        # 4. Check status code
        if response.status_code == 200:
            data = response.json()
            rate = data.get('rate')
            time = data.get('time')
            print(f"✅ SUCCESS: Key is Active (Status 200)")
            print(f"   Latest BTC/USD Price: ${rate:,.2f} @ {time[:16]}")
            print(f"   (This confirms the key is structurally sound)")
            
        elif response.status_code == 403:
            print(f"❌ FAIL: Status 403 Forbidden (KEY IS VALID BUT ACCESS IS BLOCKED)")
            print("   Conclusion: Your key works, but the tier does not allow the requested data.")
        else:
            print(f"❌ FAIL: Status {response.status_code} received.")
            print(f"   Response: {response.text[:100]}")

    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: Request failed due to connection error or timeout.")
        print(f"   Details: {e}")

if __name__ == "__main__":
    test_key_activation()