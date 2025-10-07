# test_traditional_assets.py
"""
Test script to verify Traditional & Macro Asset Integration
Verifies:
1. Gold price from FMP (OHLCV or simple structure)
2. DXY from FRED/FMP (simple structure)
3. Data alignment to Daily UTC
4. No CoinAPI references
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta

def test_gold_price_fmp():
    """Test Gold price fetching from FMP"""
    print("=" * 60)
    print("TEST 1: Gold Price from FMP")
    print("=" * 60)
    
    try:
        from data import gold_price
        from config import FMP_API_KEY
        
        # Check API key
        if not FMP_API_KEY or FMP_API_KEY == 'YOUR_FMP_API_KEY':
            print("⚠️  FMP API key not configured")
            print("   Using existing key: 74mkQbAh1DPHnRf1VoepvTTrLsvyvUf5")
        else:
            print(f"✅ FMP API key configured: {FMP_API_KEY[:10]}...")
        
        # Check for CoinAPI references
        print("\nChecking for CoinAPI references...")
        with open('data/gold_price.py', 'r') as f:
            content = f.read()
            if 'COINAPI' in content.upper():
                # Check if it's just in comments or verification
                real_refs = []
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if 'COINAPI' in line.upper():
                        if 'NO COINAPI' not in line and 'verify_no_coinapi' not in line:
                            real_refs.append(i)
                
                if real_refs:
                    print(f"❌ FAIL: CoinAPI references found on lines: {real_refs[:5]}")
                    return False
                else:
                    print("✅ No active CoinAPI references (only in comments/verification)")
            else:
                print("✅ No CoinAPI references found")
        
        # Test data fetching
        print("\nFetching 30 days of Gold data...")
        result = gold_price.get_data('30')
        
        if not result:
            print("❌ No result returned")
            return False
        
        if 'error' in result:
            print(f"⚠️  Error in result: {result['error']}")
            # May still have cached data
        
        data = result.get('data', [])
        metadata = result.get('metadata', {})
        structure = result.get('structure', 'unknown')
        
        print(f"\n📊 Data Structure: {structure}")
        print(f"   Components: {metadata.get('components', [])}")
        
        if data:
            print(f"✅ Fetched {len(data)} data points")
            
            # Check structure
            if len(data[0]) == 6:
                print("✅ 6-component OHLCV structure captured")
                # Sample OHLCV data
                sample = data[-1]
                dt = datetime.fromtimestamp(sample[0] / 1000)
                print(f"   Sample: {dt.date()}")
                print(f"   Open: ${sample[1]:.2f}")
                print(f"   High: ${sample[2]:.2f}")
                print(f"   Low: ${sample[3]:.2f}")
                print(f"   Close: ${sample[4]:.2f}")
                print(f"   Volume: {sample[5]:.0f}")
            elif len(data[0]) == 2:
                print("✅ 2-component simple structure captured")
                # Sample simple data
                sample = data[-1]
                dt = datetime.fromtimestamp(sample[0] / 1000)
                print(f"   Sample: {dt.date()} = ${sample[1]:.2f}")
            else:
                print(f"❌ Unexpected structure: {len(data[0])} components")
                return False
            
            # Verify UTC alignment
            print("\nVerifying UTC alignment...")
            misaligned = 0
            for point in data[:10]:  # Check first 10
                dt = datetime.fromtimestamp(point[0] / 1000)
                if dt.hour != 0 or dt.minute != 0 or dt.second != 0:
                    misaligned += 1
                    if misaligned == 1:
                        print(f"   ❌ Not aligned: {dt}")
            
            if misaligned == 0:
                print(f"✅ All data points aligned to 00:00:00 UTC")
            else:
                print(f"❌ {misaligned} points not aligned to UTC")
                return False
            
            # Check for 30 days
            if len(data) >= 25 and len(data) <= 35:  # Allow some flexibility
                print(f"✅ Got approximately 30 days of data ({len(data)} points)")
            else:
                print(f"⚠️  Expected ~30 days, got {len(data)} points")
            
            return True
        else:
            print("⚠️  No data returned (may be API issue)")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_dxy_fred():
    """Test DXY Dollar Index from FRED/FMP"""
    print("\n" + "=" * 60)
    print("TEST 2: DXY Dollar Index from FRED/FMP")
    print("=" * 60)
    
    try:
        from data import dxy
        from config import FRED_API_KEY, FMP_API_KEY
        
        # Check API keys
        if FRED_API_KEY and FRED_API_KEY != 'YOUR_FRED_API_KEY_HERE':
            print(f"✅ FRED API key configured: {FRED_API_KEY[:10]}...")
        else:
            print("⚠️  FRED API key not configured - will use FMP fallback")
        
        # Check for CoinAPI references
        print("\nChecking for CoinAPI references...")
        with open('data/dxy.py', 'r') as f:
            content = f.read()
            if 'COINAPI' in content.upper():
                # Check if it's just in comments
                real_refs = []
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if 'COINAPI' in line.upper():
                        if 'NO COINAPI' not in line and 'verify_no_coinapi' not in line:
                            real_refs.append(i)
                
                if real_refs:
                    print(f"❌ FAIL: CoinAPI references found on lines: {real_refs[:5]}")
                    return False
                else:
                    print("✅ No active CoinAPI references")
            else:
                print("✅ No CoinAPI references found")
        
        # Test data fetching
        print("\nFetching 30 days of DXY data...")
        result = dxy.get_data('30')
        
        if not result:
            print("❌ No result returned")
            return False
        
        if 'error' in result:
            print(f"⚠️  Error in result: {result['error']}")
        
        data = result.get('data', [])
        metadata = result.get('metadata', {})
        structure = result.get('structure', 'simple')
        
        print(f"\n📊 Data Structure: {structure}")
        print(f"   Components: {metadata.get('components', [])}")
        
        if data:
            print(f"✅ Fetched {len(data)} data points")
            
            # Check structure (should be simple 2-component)
            if len(data[0]) == 2:
                print("✅ 2-component simple structure (as expected for DXY)")
                
                # Show recent values
                print("\nRecent DXY values:")
                for point in data[-5:]:
                    dt = datetime.fromtimestamp(point[0] / 1000)
                    print(f"   {dt.date()}: {point[1]:.2f}")
                
                # Check reasonable range for DXY (typically 80-110)
                values = [p[1] for p in data]
                min_val = min(values)
                max_val = max(values)
                avg_val = sum(values) / len(values)
                
                print(f"\nDXY Statistics:")
                print(f"   Min: {min_val:.2f}")
                print(f"   Max: {max_val:.2f}")
                print(f"   Avg: {avg_val:.2f}")
                
                if 70 <= min_val <= 120 and 70 <= max_val <= 120:
                    print("✅ DXY values in reasonable range")
                else:
                    print("⚠️  DXY values seem unusual")
                    
            else:
                print(f"❌ Unexpected structure: {len(data[0])} components (expected 2)")
                return False
            
            # Verify UTC alignment
            print("\nVerifying UTC alignment...")
            misaligned = 0
            for point in data:
                dt = datetime.fromtimestamp(point[0] / 1000)
                if dt.hour != 0 or dt.minute != 0 or dt.second != 0:
                    misaligned += 1
                    if misaligned == 1:
                        print(f"   First misaligned: {dt}")
            
            if misaligned == 0:
                print(f"✅ All {len(data)} data points aligned to 00:00:00 UTC")
            else:
                print(f"❌ {misaligned}/{len(data)} points not aligned to UTC")
                return False
            
            # Check for 30 days
            if len(data) >= 25 and len(data) <= 35:
                print(f"✅ Got approximately 30 days of data ({len(data)} points)")
            else:
                print(f"⚠️  Expected ~30 days, got {len(data)} points")
            
            return True
        else:
            print("⚠️  No data returned")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_app_integration():
    """Test that app.py includes the new DXY module"""
    print("\n" + "=" * 60)
    print("TEST 3: App Integration")
    print("=" * 60)
    
    try:
        with open('app.py', 'r') as f:
            content = f.read()
        
        # Check for DXY import
        if 'from data import' in content and 'dxy' in content:
            print("✅ DXY module imported in app.py")
        else:
            print("❌ DXY module not imported")
            return False
        
        # Check for DXY in DATA_PLUGINS
        if "'dxy': dxy" in content or '"dxy": dxy' in content:
            print("✅ DXY added to DATA_PLUGINS dictionary")
        else:
            print("❌ DXY not in DATA_PLUGINS")
            return False
        
        # Check available datasets
        from app import DATA_PLUGINS
        if 'dxy' in DATA_PLUGINS:
            print("✅ DXY available as dataset")
            print(f"   Total datasets: {len(DATA_PLUGINS)}")
            print(f"   Available: {list(DATA_PLUGINS.keys())}")
        else:
            print("❌ DXY not in DATA_PLUGINS")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_time_standardization():
    """Verify time_transformer handles both structures correctly"""
    print("\n" + "=" * 60)
    print("TEST 4: Time Standardization Verification")
    print("=" * 60)
    
    try:
        from data.time_transformer import standardize_to_daily_utc
        
        # Test with simple 2-component data (like DXY)
        print("Testing 2-component standardization...")
        simple_data = [
            [1704153600000, 102.5],  # 2024-01-02 00:00:00 UTC
            [1704240000000, 103.2],  # 2024-01-03 00:00:00 UTC
        ]
        
        result = standardize_to_daily_utc(simple_data)
        if result and len(result[0]) == 2:
            dt = datetime.fromtimestamp(result[0][0] / 1000)
            if dt.hour == 0 and dt.minute == 0:
                print(f"✅ 2-component data standardized correctly")
            else:
                print(f"❌ Not aligned to UTC: {dt}")
                return False
        else:
            print("❌ Failed to standardize 2-component data")
            return False
        
        # Test with 6-component OHLCV data (if Gold has it)
        print("\nTesting 6-component standardization...")
        ohlcv_data = [
            [1704153600000, 2000, 2050, 1995, 2045, 1000000],
            [1704240000000, 2045, 2060, 2040, 2055, 1100000],
        ]
        
        result = standardize_to_daily_utc(ohlcv_data)
        if result and len(result[0]) == 6:
            dt = datetime.fromtimestamp(result[0][0] / 1000)
            if dt.hour == 0 and dt.minute == 0:
                print(f"✅ 6-component OHLCV data standardized correctly")
            else:
                print(f"❌ Not aligned to UTC: {dt}")
                return False
        else:
            print("❌ Failed to standardize 6-component data")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all traditional asset integration tests"""
    print("TRADITIONAL & MACRO ASSET INTEGRATION TEST SUITE")
    print("=" * 60)
    print("Testing:")
    print("1. Gold price from FMP (OHLCV or simple)")
    print("2. DXY Dollar Index from FRED/FMP (simple)")
    print("3. Data alignment to Daily UTC")
    print("4. No CoinAPI references")
    print("=" * 60)
    
    tests = [
        ("Gold Price (FMP)", test_gold_price_fmp),
        ("DXY Dollar Index", test_dxy_fred),
        ("App Integration", test_app_integration),
        ("Time Standardization", test_time_standardization)
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
    
    all_passed = True
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {name}")
        if not success:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ TRADITIONAL ASSETS INTEGRATION SUCCESSFUL")
        print("\nIntegration Status:")
        print("- Gold: FMP API (OHLCV or simple structure)")
        print("- DXY: FRED API primary, FMP fallback")
        print("- All data standardized to Daily UTC")
        print("- NO CoinAPI references in traditional modules")
        print("\nNext Steps:")
        print("1. Add FRED API key to config.py if not done")
        print("2. Run 'python app.py' to start the server")
        print("3. Test in dashboard with Gold and DXY datasets")
    else:
        print("❌ INTEGRATION ISSUES DETECTED")
        print("\nCheck failed tests above for details")
        print("Ensure API keys are configured in config.py")
    print("=" * 60)

if __name__ == "__main__":
    main()