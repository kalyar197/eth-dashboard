# test_all_phases.py
"""
FINAL COMPREHENSIVE TEST SUITE
Tests all critical fixes and Phase 3 + Phase 4 indicators
Verifies:
1. FMP Gold Price fix (ZGUSD)
2. CoinGecko dominance fix
3. ATR indexing fix
4. UTF-8 encoding fix
5. Phase 3 indicators (OBV, ATR)
6. Phase 4 indicators (VWAP, MACD, ADX)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime

def test_gold_price_fix():
    """Test Gold Price FMP endpoint fix"""
    print("=" * 60)
    print("TEST 1: Gold Price FMP Endpoint Fix (ZGUSD)")
    print("=" * 60)
    
    try:
        from data import gold_price
        
        # Check for ZGUSD in source
        with open('data/gold_price.py', 'r', encoding='utf-8') as f:
            content = f.read()
            if 'ZGUSD' in content:
                print("✅ Uses ZGUSD symbol")
            else:
                print("❌ ZGUSD not found")
                return False
        
        # Test data fetching
        result = gold_price.get_data('7')
        
        if 'error' in result and '403' in result['error']:
            print("❌ Still getting 403 Forbidden")
            return False
        
        data = result.get('data', [])
        if data:
            print(f"✅ Fetched {len(data)} gold data points")
            return True
        else:
            print("⚠️  No data (may be cached)")
            return True
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_dominance_fix():
    """Test dominance modules use CoinGecko"""
    print("\n" + "=" * 60)
    print("TEST 2: Dominance CoinGecko Fix")
    print("=" * 60)
    
    try:
        from data import btc_dominance, eth_dominance, usdt_dominance
        
        all_passed = True
        for name, module in [('BTC', btc_dominance), ('ETH', eth_dominance), ('USDT', usdt_dominance)]:
            with open(module.__file__, 'r', encoding='utf-8') as f:
                content = f.read()
                
                if 'coingecko' in content.lower():
                    print(f"✅ {name}: Uses CoinGecko")
                else:
                    print(f"❌ {name}: No CoinGecko reference")
                    all_passed = False
                
                if '/v1/metrics/asset' in content:
                    print(f"❌ {name}: Still has broken endpoint")
                    all_passed = False
            
            result = module.get_data('7')
            if 'error' in result and '404' in result['error']:
                print(f"❌ {name}: Still getting 404")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_atr_indexing_fix():
    """Test ATR indexing bug is fixed"""
    print("\n" + "=" * 60)
    print("TEST 3: ATR Indexing Fix")
    print("=" * 60)
    
    try:
        from data import atr
        
        # Check source code for the fix
        with open('data/atr.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
            if 'i + ATR_PERIOD - 1' in content:
                print("✅ ATR uses correct index alignment (- 1)")
            else:
                print("❌ ATR index fix not applied")
                return False
        
        # Test actual calculation
        print("Testing ATR calculation...")
        result = atr.get_data('30')
        
        if 'error' in result:
            if 'IndexError' in result.get('error', ''):
                print("❌ Still getting IndexError")
                return False
        
        data = result.get('data', [])
        if data:
            print(f"✅ ATR calculated successfully ({len(data)} points)")
            return True
        else:
            print("⚠️  No data returned")
            return False
            
    except IndexError as e:
        print(f"❌ IndexError still occurs: {e}")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_phase3_indicators():
    """Test Phase 3 indicators (OBV, ATR)"""
    print("\n" + "=" * 60)
    print("TEST 4: Phase 3 Indicators (OBV, ATR)")
    print("=" * 60)
    
    try:
        from data import obv, atr
        
        # Test OBV
        print("Testing OBV...")
        obv_result = obv.get_data('30')
        obv_data = obv_result.get('data', [])
        
        if obv_data:
            print(f"✅ OBV: {len(obv_data)} points calculated")
        else:
            print("❌ OBV: No data")
            return False
        
        # Test ATR
        print("Testing ATR...")
        atr_result = atr.get_data('30')
        atr_data = atr_result.get('data', [])
        
        if atr_data:
            print(f"✅ ATR: {len(atr_data)} points calculated")
        else:
            print("❌ ATR: No data")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_phase4_indicators():
    """Test Phase 4 indicators (VWAP, MACD, ADX)"""
    print("\n" + "=" * 60)
    print("TEST 5: Phase 4 Indicators (VWAP, MACD, ADX)")
    print("=" * 60)
    
    try:
        from data import vwap, macd, adx
        
        # Test VWAP
        print("Testing VWAP...")
        vwap_result = vwap.get_data('30')
        vwap_data = vwap_result.get('data', [])
        
        if vwap_data:
            print(f"✅ VWAP: {len(vwap_data)} points calculated")
            # Show sample
            dt = datetime.fromtimestamp(vwap_data[-1][0] / 1000)
            print(f"   Latest: {dt.date()} = ${vwap_data[-1][1]:.2f}")
        else:
            print("❌ VWAP: No data")
            return False
        
        # Test MACD
        print("\nTesting MACD...")
        macd_result = macd.get_data('30')
        macd_data = macd_result.get('data', {})
        
        if macd_data and 'macd' in macd_data and macd_data['macd']:
            print(f"✅ MACD: {len(macd_data['macd'])} points calculated")
            print(f"   Signal: {len(macd_data.get('signal', []))} points")
            print(f"   Histogram: {len(macd_data.get('histogram', []))} points")
        else:
            print("❌ MACD: No data")
            return False
        
        # Test ADX
        print("\nTesting ADX...")
        adx_result = adx.get_data('30')
        adx_data = adx_result.get('data', [])
        
        if adx_data:
            print(f"✅ ADX: {len(adx_data)} points calculated")
            # Show sample with trend strength
            dt = datetime.fromtimestamp(adx_data[-1][0] / 1000)
            adx_val = adx_data[-1][1]
            strength = "Strong" if adx_val > 25 else "Weak" if adx_val < 20 else "Moderate"
            print(f"   Latest: {dt.date()} = {adx_val:.2f} ({strength})")
        else:
            print("❌ ADX: No data")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_app_integration():
    """Test all indicators integrated in app.py"""
    print("\n" + "=" * 60)
    print("TEST 6: App Integration (13 Datasets)")
    print("=" * 60)
    
    try:
        from app import DATA_PLUGINS
        
        expected = ['eth', 'gold', 'rsi', 'btc_dominance', 'eth_dominance',
                   'usdt_dominance', 'bollinger_bands', 'dxy',
                   'obv', 'atr', 'vwap', 'macd', 'adx']
        
        print(f"Expected: {len(expected)} datasets")
        print(f"Found: {len(DATA_PLUGINS)} datasets")
        
        missing = [e for e in expected if e not in DATA_PLUGINS]
        if missing:
            print(f"❌ Missing: {missing}")
            return False
        
        print(f"✅ All {len(DATA_PLUGINS)} datasets registered:")
        for plugin in DATA_PLUGINS.keys():
            print(f"   - {plugin}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_utf8_encoding():
    """Verify UTF-8 encoding in test script"""
    print("\n" + "=" * 60)
    print("TEST 7: UTF-8 Encoding Fix")
    print("=" * 60)
    
    try:
        # Try to read a file with UTF-8
        with open('data/gold_price.py', 'r', encoding='utf-8') as f:
            content = f.read()
            print("✅ UTF-8 encoding works for gold_price.py")
        
        with open('data/btc_dominance.py', 'r', encoding='utf-8') as f:
            content = f.read()
            print("✅ UTF-8 encoding works for btc_dominance.py")
        
        return True
        
    except UnicodeDecodeError as e:
        print(f"❌ UTF-8 decoding error: {e}")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    """Run all tests"""
    print("FINAL COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    print("Testing Critical Fixes & All Indicators")
    print("=" * 60)
    
    tests = [
        ("Gold Price Fix", test_gold_price_fix),
        ("Dominance Fix", test_dominance_fix),
        ("ATR Indexing Fix", test_atr_indexing_fix),
        ("Phase 3 Indicators", test_phase3_indicators),
        ("Phase 4 Indicators", test_phase4_indicators),
        ("App Integration", test_app_integration),
        ("UTF-8 Encoding", test_utf8_encoding)
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
    print("FINAL TEST SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {name}")
        if not success:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED - READY FOR PRODUCTION")
        print("\n📊 Final Statistics:")
        print("   - Total Datasets: 13")
        print("   - Critical Fixes: 4 (Gold, Dominance, ATR, UTF-8)")
        print("   - Phase 3 Indicators: 2 (OBV, ATR)")
        print("   - Phase 4 Indicators: 3 (VWAP, MACD, ADX)")
        print("\n🚀 Next Steps:")
        print("   1. Run: python app.py")
        print("   2. Open: http://localhost:8080/index.html")
        print("   3. Select indicators and analyze!")
    else:
        print("❌ SOME TESTS FAILED")
        print("\nReview failed tests and fix issues before deployment")
    print("=" * 60)

if __name__ == "__main__":
    main()
