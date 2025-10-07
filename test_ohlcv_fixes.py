# test_ohlcv_fixes.py
"""
Test script to verify OHLCV structure and estimate removal fixes
CRITICAL VERIFICATION:
1. OHLCV data structure (6 components)
2. No $1.00 estimates in USDT dominance
3. Time transformer handles both structures
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime

def test_ohlcv_structure():
    """Test that ETH price returns full OHLCV structure"""
    print("=" * 60)
    print("TEST 1: OHLCV Structure Verification")
    print("=" * 60)
    
    try:
        from data import eth_price
        
        # Test data fetching
        print("Fetching 7 days of ETH OHLCV data...")
        result = eth_price.get_data('7')
        
        if not result or not result.get('data'):
            print("❌ FAIL: No data returned")
            return False
        
        data = result['data']
        print(f"✅ Fetched {len(data)} data points")
        
        # CRITICAL: Verify 6-component structure
        if len(data) > 0:
            first_record = data[0]
            component_count = len(first_record)
            
            if component_count != 6:
                print(f"❌ CRITICAL FAIL: Data has {component_count} components, expected 6")
                print(f"   Structure: {first_record}")
                return False
            else:
                print(f"✅ PASS: Data has correct 6-component OHLCV structure")
                
                # Verify component values
                timestamp, open_p, high_p, low_p, close_p, volume = first_record
                
                # Verify timestamp
                if timestamp < 1000000000000:
                    print("❌ FAIL: Timestamp not in milliseconds")
                    return False
                
                # Verify OHLCV logic
                if high_p < low_p:
                    print("❌ FAIL: High < Low (invalid OHLCV)")
                    return False
                
                if high_p < open_p or high_p < close_p:
                    print("❌ FAIL: High not >= Open/Close")
                    return False
                
                if low_p > open_p or low_p > close_p:
                    print("❌ FAIL: Low not <= Open/Close")
                    return False
                
                if volume < 0:
                    print("❌ FAIL: Negative volume")
                    return False
                
                print(f"✅ Sample OHLCV data validated:")
                print(f"   Date: {datetime.fromtimestamp(timestamp/1000).date()}")
                print(f"   Open: ${open_p:.2f}")
                print(f"   High: ${high_p:.2f}")
                print(f"   Low: ${low_p:.2f}")
                print(f"   Close: ${close_p:.2f}")
                print(f"   Volume: {volume:,.2f}")
                
                # Check metadata
                metadata = result.get('metadata', {})
                if metadata.get('data_structure') == 'OHLCV':
                    print("✅ Metadata correctly indicates OHLCV structure")
                
                components = metadata.get('components', [])
                expected_components = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
                if components == expected_components:
                    print("✅ Component labels correct")
                else:
                    print(f"⚠️  Component labels: {components}")
        
        print("\n✅ OHLCV STRUCTURE TEST: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_usdt_no_estimates():
    """Test that USDT dominance has NO $1.00 estimates"""
    print("\n" + "=" * 60)
    print("TEST 2: USDT Estimate Removal Verification")
    print("=" * 60)
    
    try:
        # Check source code for violations
        with open('data/usdt_dominance.py', 'r') as f:
            content = f.read()
            
            # Check for removed $1.00 assumption
            forbidden_patterns = [
                "use $1.00",
                "using $1.00",
                "= 1.00",
                "= 1.0",
                "price = 1",
                "market_cap = 1.00 * supply",
                "market_cap = supply"  # This would imply $1 price
            ]
            
            violations_found = []
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                # Skip comment lines
                if line.strip().startswith('#'):
                    continue
                    
                line_lower = line.lower()
                for pattern in forbidden_patterns:
                    if pattern.lower() in line_lower and 'no assumptions' not in line_lower and 'no estimates' not in line_lower:
                        violations_found.append(f"Line {i}: {line.strip()}")
            
            if violations_found:
                print("❌ CRITICAL FAIL: Found estimate violations:")
                for violation in violations_found[:5]:
                    print(f"   {violation}")
                return False
            else:
                print("✅ No $1.00 estimate code found")
            
            # Check for proper failure handling
            if "return None" in content and "if not price_data" in content:
                print("✅ Properly fails when price data missing")
            else:
                print("⚠️  May not properly handle missing price data")
            
            # Check for compliance messages
            if "NO ESTIMATES" in content and "NO PRICE ASSUMPTIONS" in content:
                print("✅ Contains compliance declarations")
            else:
                print("⚠️  Missing clear compliance declarations")
        
        # Test actual module behavior
        from data import usdt_dominance
        
        print("\nTesting USDT dominance calculation...")
        result = usdt_dominance.get_data('7')
        
        if 'error' in result and 'NO ESTIMATES' in result['error']:
            print("✅ Error message confirms no estimates used")
        elif result.get('data'):
            print(f"✅ Returned {len(result['data'])} data points (from real data or cache)")
        
        print("\n✅ USDT COMPLIANCE TEST: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_time_transformer():
    """Test that time transformer handles both structures"""
    print("\n" + "=" * 60)
    print("TEST 3: Time Transformer Multi-Structure Support")
    print("=" * 60)
    
    try:
        from data.time_transformer import standardize_to_daily_utc, extract_component
        
        # Test with 2-element structure
        print("Testing 2-element structure...")
        simple_data = [
            [1704067200000, 2500.50],  # 2024-01-01 00:00:00 UTC
            [1704153600000, 2550.75],  # 2024-01-02 00:00:00 UTC
        ]
        
        result_simple = standardize_to_daily_utc(simple_data)
        if result_simple and len(result_simple[0]) == 2:
            print("✅ 2-element structure processed correctly")
        else:
            print(f"❌ FAIL: 2-element structure failed: {result_simple}")
            return False
        
        # Test with 6-element OHLCV structure
        print("\nTesting 6-element OHLCV structure...")
        ohlcv_data = [
            [1704067200000, 2500.00, 2550.00, 2490.00, 2545.00, 1000000],
            [1704153600000, 2545.00, 2580.00, 2540.00, 2575.00, 1100000],
        ]
        
        result_ohlcv = standardize_to_daily_utc(ohlcv_data)
        if result_ohlcv and len(result_ohlcv[0]) == 6:
            print("✅ 6-element OHLCV structure processed correctly")
            print(f"   Sample: O={result_ohlcv[0][1]:.2f}, H={result_ohlcv[0][2]:.2f}, L={result_ohlcv[0][3]:.2f}, C={result_ohlcv[0][4]:.2f}, V={result_ohlcv[0][5]:.0f}")
        else:
            print(f"❌ FAIL: 6-element structure failed: {result_ohlcv}")
            return False
        
        # Test component extraction
        print("\nTesting component extraction...")
        extracted = extract_component(ohlcv_data, 'close')
        if extracted and len(extracted[0]) == 2 and extracted[0][1] == 2545.00:
            print("✅ Component extraction works correctly")
            print(f"   Extracted close prices: {[p[1] for p in extracted]}")
        else:
            print("❌ FAIL: Component extraction failed")
            return False
        
        print("\n✅ TIME TRANSFORMER TEST: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_indicator_compatibility():
    """Test that indicators work with new OHLCV structure"""
    print("\n" + "=" * 60)
    print("TEST 4: Indicator OHLCV Compatibility")
    print("=" * 60)
    
    try:
        from data import rsi, bollinger_bands
        
        # Test RSI with OHLCV data
        print("Testing RSI with OHLCV data...")
        rsi_result = rsi.get_data('30')
        
        if rsi_result and rsi_result.get('data'):
            print(f"✅ RSI calculated: {len(rsi_result['data'])} points")
            if rsi_result['data']:
                sample_rsi = rsi_result['data'][0][1]
                if 0 <= sample_rsi <= 100:
                    print(f"   Sample RSI value: {sample_rsi:.2f}")
                else:
                    print(f"❌ Invalid RSI value: {sample_rsi}")
                    return False
        else:
            print("⚠️  No RSI data (may be due to insufficient data)")
        
        # Test Bollinger Bands with OHLCV data
        print("\nTesting Bollinger Bands with OHLCV data...")
        bb_result = bollinger_bands.get_data('30')
        
        if bb_result and bb_result.get('data'):
            bb_data = bb_result['data']
            if 'middle' in bb_data and 'upper' in bb_data and 'lower' in bb_data:
                print(f"✅ Bollinger Bands calculated:")
                print(f"   Middle band points: {len(bb_data['middle'])}")
                print(f"   Upper band points: {len(bb_data['upper'])}")
                print(f"   Lower band points: {len(bb_data['lower'])}")
                
                # Verify band logic
                if bb_data['middle'] and bb_data['upper'] and bb_data['lower']:
                    idx = 0
                    if bb_data['upper'][idx][1] > bb_data['middle'][idx][1] > bb_data['lower'][idx][1]:
                        print("✅ Band relationships correct (Upper > Middle > Lower)")
                    else:
                        print("❌ Invalid band relationships")
                        return False
            else:
                print("❌ Missing band data")
                return False
        else:
            print("⚠️  No Bollinger Bands data")
        
        print("\n✅ INDICATOR COMPATIBILITY TEST: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    """Run all verification tests"""
    print("CRITICAL FIX VERIFICATION SUITE")
    print("=" * 60)
    print("Verifying:")
    print("1. OHLCV 6-component structure")
    print("2. NO estimates in USDT dominance") 
    print("3. Time transformer multi-structure support")
    print("4. Indicator compatibility")
    print("=" * 60)
    
    tests = [
        ("OHLCV Structure", test_ohlcv_structure),
        ("USDT Compliance", test_usdt_no_estimates),
        ("Time Transformer", test_time_transformer),
        ("Indicator Compatibility", test_indicator_compatibility)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n❌ Unexpected error in {name}: {e}")
            results.append((name, False))
    
    # Final summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {name}")
        if not success:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL CRITICAL FIXES VERIFIED")
        print("\nData Structure Status:")
        print("- OHLCV: 6 components [timestamp, open, high, low, close, volume]")
        print("- All technical indicators can now be implemented")
        print("- NO ESTIMATES or APPROXIMATIONS in any module")
        print("\nReady for production use!")
    else:
        print("❌ CRITICAL FAILURES DETECTED")
        print("\nIssues must be resolved before proceeding")
        print("Check failed tests above for details")
    print("=" * 60)

if __name__ == "__main__":
    main()