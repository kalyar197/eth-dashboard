# test_coinstats_api.py
# Script to test CoinStats API and find the correct endpoints

import requests
import json
from config import COINSTATS_API_KEY

def test_coinstats_endpoints():
    """Test various CoinStats API endpoints to find dominance data"""
    
    headers = {
        'X-API-KEY': COINSTATS_API_KEY,
        'Accept': 'application/json'
    }
    
    print("=" * 60)
    print("Testing CoinStats API Endpoints")
    print("=" * 60)
    
    # List of endpoints to test
    endpoints_to_test = [
        {
            'name': 'Public Charts Dominance',
            'url': 'https://api.coinstats.app/public/v1/charts/dominance',
            'params': {'coin': 'bitcoin', 'period': '1m'}
        },
        {
            'name': 'Bitcoin Charts',
            'url': 'https://openapiv1.coinstats.app/coins/bitcoin/charts',
            'params': {'period': '1m', 'type': 'dominance'}
        },
        {
            'name': 'Market Dominance',
            'url': 'https://api.coinstats.app/public/v1/markets/dominance',
            'params': {'period': '1m'}
        },
        {
            'name': 'Global Stats',
            'url': 'https://api.coinstats.app/public/v1/global',
            'params': {}
        },
        {
            'name': 'Bitcoin Data',
            'url': 'https://api.coinstats.app/public/v1/coins/bitcoin',
            'params': {}
        }
    ]
    
    # Additional endpoints based on different API versions
    additional_endpoints = [
        'https://api.coinstats.app/v1/charts/bitcoin/dominance',
        'https://api.coinstats.app/v2/dominance/bitcoin',
        'https://openapiv1.coinstats.app/dominance',
        'https://api.coinstats.app/public/v1/dominance/bitcoin'
    ]
    
    successful_endpoints = []
    
    # Test main endpoints
    for endpoint_info in endpoints_to_test:
        print(f"\nTesting: {endpoint_info['name']}")
        print(f"URL: {endpoint_info['url']}")
        print(f"Params: {endpoint_info['params']}")
        
        try:
            response = requests.get(
                endpoint_info['url'], 
                headers=headers, 
                params=endpoint_info['params'],
                timeout=10
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Response Keys: {list(data.keys())}")
                
                # Check for dominance data
                if 'dominance' in str(data).lower() or 'chart' in data or 'data' in data:
                    print("✅ FOUND: This endpoint may contain dominance data!")
                    successful_endpoints.append(endpoint_info)
                    
                    # Print sample data structure
                    if 'chart' in data and data['chart']:
                        print(f"Sample data point: {data['chart'][0] if data['chart'] else 'Empty'}")
                    elif 'data' in data and isinstance(data['data'], list) and data['data']:
                        print(f"Sample data point: {data['data'][0]}")
                    elif 'dominance' in data:
                        print(f"Dominance data structure: {type(data['dominance'])}")
            else:
                print(f"Error: {response.text[:200]}")
                
        except Exception as e:
            print(f"Failed: {str(e)}")
    
    # Test additional endpoints
    print("\n" + "=" * 60)
    print("Testing additional endpoint patterns...")
    print("=" * 60)
    
    for url in additional_endpoints:
        print(f"\nTesting: {url}")
        try:
            response = requests.get(url, headers=headers, timeout=10)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Endpoint exists!")
                successful_endpoints.append({'name': 'Direct URL', 'url': url})
        except Exception as e:
            print(f"Failed: {str(e)}")
    
    # Test for USDT dominance
    print("\n" + "=" * 60)
    print("Testing USDT dominance availability...")
    print("=" * 60)
    
    usdt_identifiers = ['tether', 'usdt', 'tether-usdt', 'USDT']
    
    for identifier in usdt_identifiers:
        print(f"\nTrying identifier: {identifier}")
        
        test_urls = [
            f'https://api.coinstats.app/public/v1/charts/dominance?coin={identifier}&period=1m',
            f'https://openapiv1.coinstats.app/coins/{identifier}/charts?period=1m&type=dominance',
            f'https://api.coinstats.app/public/v1/coins/{identifier}'
        ]
        
        for url in test_urls:
            try:
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    print(f"✅ Found USDT with identifier: {identifier}")
                    print(f"URL: {url}")
                    break
            except:
                pass
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if successful_endpoints:
        print("\n✅ Working endpoints found:")
        for endpoint in successful_endpoints:
            print(f"  - {endpoint['name']}: {endpoint['url']}")
    else:
        print("\n❌ No working dominance endpoints found.")
        print("Please check:")
        print("1. Your API key is correct")
        print("2. Your API plan includes dominance data")
        print("3. The API documentation for correct endpoints")
    
    return successful_endpoints

if __name__ == "__main__":
    # Make sure you've set your API key in config.py
    if COINSTATS_API_KEY == 'your_coinstats_api_key_here':
        print("ERROR: Please set your CoinStats API key in config.py first!")
    else:
        test_coinstats_endpoints()