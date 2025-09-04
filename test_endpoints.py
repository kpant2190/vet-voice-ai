#!/usr/bin/env python3
"""Test Railway endpoints step by step."""

import requests

def test_endpoints():
    """Test different Railway endpoints."""
    
    base_url = "https://web-production-2b37.up.railway.app"
    
    endpoints = [
        "/health",
        "/",
        "/simple",
        "/test-webhook"
    ]
    
    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        print(f"\n🧪 Testing {endpoint}")
        print(f"URL: {url}")
        
        try:
            if endpoint == "/test-webhook":
                # POST request with form data
                data = {
                    "CallSid": "CA123456789testcall",
                    "From": "+1234567890", 
                    "To": "+61468017757",
                    "CallStatus": "ringing"
                }
                response = requests.post(url, data=data, timeout=10)
            else:
                # GET request
                response = requests.get(url, timeout=10)
            
            print(f"✅ Status: {response.status_code}")
            print(f"📄 Content-Type: {response.headers.get('Content-Type', 'None')}")
            print(f"📝 Content: {response.text[:200]}...")
            
        except requests.exceptions.Timeout:
            print("❌ Timeout (10s)")
        except requests.exceptions.ConnectionError:
            print("❌ Connection Error")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == '__main__':
    test_endpoints()
