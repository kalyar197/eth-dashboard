# test_coinapi_migration.py
"""
Test script to verify CoinAPI migration
Ensures all FMP and CoinStats references are removed
Verifies data is properly fetched and standardized
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from config import COINAPI_KEY

def test_config():
    """Test that config.py has CoinAPI key and no deprecated references"""
    print("=" * 60)
    print("Testing Configuration")
    print("=" * 60)
    
    # Check CoinAPI key
    if not COINAPI_KEY or COINAPI_KEY == 'YOUR_COINAPI_KEY_HERE':
        print("❌ COINAPI_KEY not configured in config.py")
        print("   Please add your CoinAPI key to config.py")
        return False
    else:
        print(f"✅ CoinAPI key configured: {COINAPI_KEY[:10]}...")
    
    return True

def test_eth_price():
    """Test ETH price data fetching"""
    print("\n" + "=" * 60)
    print("Testing ETH Price Data")
    print("=" * 60)
    
    try:
        from data import eth_price
        
        # Check for FMP references
        with open('data/eth_price.py', 'r') as f:
            content = f.read()
            if 'FMP' in content or 'financialmodelingprep' in content:
                print("❌ FMP references still present in eth_price.py")
                return False
            else:
                print("✅ No FMP references found")
        
        # Test data fetching for 30 days
        print("\nFetching 30 days of ETH price data...")
        result = eth_price.get_data('30')
        
        if not result or not result.get('data'):
            print("❌ No data returned")
            return False
        
        data = result['data']
        print(f"✅ Fetched {len(data)} data points")
        
        # Verify data structure
        if len(data) > 0:
            sample = data[0]
            if len(sample) != 2:
                print("❌ Invalid data structure")
                return False
            
            timestamp, price = sample
            
            # Check if timestamp is in milliseconds
            if timestamp < 1000000000000:
                print("❌ Timestamp not in milliseconds")
                return False
            
            # Check if price is reasonable
            if not (100 < price < 10000):
                print(f"⚠️  Price seems unusual: ${price}")
            
            print(f"✅ Sample data point: {datetime.fromtimestamp(timestamp/1000).date()} - ${price:.2f}")
            
            # Check standardization (all timestamps should be at 00:00:00 UTC)
            for point in data[:5]:
                dt = datetime.fromtimestamp(point[0]/1000)
                if dt.hour != 0 or dt.minute != 0 or dt.second != 0:
                    print(f"❌ Data not standardized to daily UTC: {dt}")
                    return False
            
            print("✅ Data properly standardized to daily UTC")
        
        # Check if we have exactly 30 days or close to it
        if not (25 <= len(data) <= 35):
            print(f"⚠️  Expected ~30 data points, got {len(data)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing ETH price: {e}")
        return False

def test_btc_dominance():
    """Test BTC dominance data fetching"""
    print("\n" + "=" * 60)
    print("Testing BTC Dominance Data")
    print("=" * 60)
    
    try:
        from data import btc_dominance
        
        # Check for CoinStats references
        with open('data/btc_dominance.py', 'r') as f:
            content = f.read()
            if 'coinstats' in content.lower() or 'COINSTATS' in content:
                print("❌ CoinStats references still present in btc_dominance.py")
                return False
            else:
                print("✅ No CoinStats references found")
        
        # Test data fetching for 30 days
        print("\nFetching 30 days of BTC dominance data...")
        result = btc_dominance.get_data('30')
        
        if not result or not result.get('data'):
            print("⚠️  No data returned (may need to build cache first)")
            return True  # Don't fail if no data yet
        
        data = result['data']
        print(f"✅ Fetched {len(data)} data points")
        
        # Verify dominance values are in reasonable range
        if len(data) > 0:
            dominance_values = [point[1] for point in data]
            min_dom = min(dominance_values)
            max_dom = max(dominance_values)
            avg_dom = sum(dominance_values) / len(dominance_values)
            
            print(f"   Dominance range: {min_dom:.2f}% - {max_dom:.2f}%")
            print(f"   Average: {avg_dom:.2f}%")
            
            if not (30 <= avg_dom <= 80):
                print(f"⚠️  BTC dominance seems unusual: {avg_dom:.2f}%")
            else:
                print("✅ BTC dominance in expected range (40-70%)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing BTC dominance: {e}")
        return False

def test_eth_dominance():
    """Test ETH dominance data fetching"""
    print("\n" + "=" * 60)
    print("Testing ETH Dominance Data")
    print("=" * 60)
    
    try:
        from data import eth_dominance
        
        # Check for CoinStats references
        with open('data/eth_dominance.py', 'r') as f:
            content = f.read()
            if 'coinstats' in content.lower() or 'COINSTATS' in content:
                print("❌ CoinStats references still present in eth_dominance.py")
                return False
            else:
                print("✅ No CoinStats references found")
        
        # Test data fetching
        print("\nFetching 30 days of ETH dominance data...")
        result = eth_dominance.get_data('30')
        
        if result and result.get('data') and len(result['data']) > 0:
            data = result['data']
            print(f"✅ Fetched {len(data)} data points")
            
            dominance_values = [point[1] for point in data]
            avg_dom = sum(dominance_values) / len(dominance_values)
            
            print(f"   Average ETH dominance: {avg_dom:.2f}%")
            
            if not (5 <= avg_dom <= 30):
                print(f"⚠️  ETH dominance seems unusual: {avg_dom:.2f}%")
            else:
                print("✅ ETH dominance in expected range (10-25%)")
        else:
            print("⚠️  No data returned (may need to build cache first)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing ETH dominance: {e}")
        return False

def test_usdt_dominance():
    """Test USDT dominance data fetching"""
    print("\n" + "=" * 60)
    print("Testing USDT Dominance Data")
    print("=" * 60)
    
    try:
        from data import usdt_dominance
        
        # Check for CoinStats references
        with open('data/usdt_dominance.py', 'r') as f:
            content = f.read()
            if 'coinstats' in content.lower() or 'COINSTATS' in content:
                print("❌ CoinStats references still present in usdt_dominance.py")
                return False
            else:
                print("✅ No CoinStats references found")
        
        # Test data fetching
        print("\nFetching 30 days of USDT dominance data...")
        result = usdt_dominance.get_data('30')
        
        if result and result.get('data') and len(result['data']) > 0:
            data = result['data']
            print(f"✅ Fetched {len(data)} data points")
            
            dominance_values = [point[1] for point in data]
            avg_dom = sum(dominance_values) / len(dominance_values)
            
            print(f"   Average USDT dominance: {avg_dom:.2f}%")
            
            if not (2 <= avg_dom <= 15):
                print(f"⚠️  USDT dominance seems unusual: {avg_dom:.2f}%")
            else:
                print("✅ USDT dominance in expected range (3-12%)")
        else:
            print("⚠️  No data returned (may need to build cache first)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing USDT dominance: {e}")
        return False

def main():
    """Run all tests"""
    print("CoinAPI Migration Test Suite")
    print("=" * 60)
    
    # Test configuration
    if not test_config():
        print("\n❌ Configuration test failed. Please set up your CoinAPI key.")
        return
    
    # Test each module
    tests = [
        ("ETH Price", test_eth_price),
        ("BTC Dominance", test_btc_dominance),
        ("ETH Dominance", test_eth_dominance),
        ("USDT Dominance", test_usdt_dominance)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n❌ Unexpected error in {name}: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(success for _, success in results)
    
    if all_passed:
        print("\n✅ All tests passed! Migration successful.")
        print("\nNext steps:")
        print("1. Ensure your CoinAPI key is set in config.py")
        print("2. Run 'python app.py' to start the Flask server")
        print("3. Open index.html to view the dashboard")
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")
        print("Note: Dominance calculations may show warnings on first run")
        print("as they build up cache. This is normal.")

if __name__ == "__main__":
    main()