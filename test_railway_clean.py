#!/usr/bin/env python3
"""Clean Railway webhook test without secrets."""

import requests
import os

def test_railway_webhook():
    """Test the Railway webhook with safe test data."""
    
    url = "https://web-production-2b37.up.railway.app/api/voice/webhook"
    
    # Safe test data - no real credentials
    data = {
        "AccountSid": "ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",  # Test Account SID
        "CallSid": "CA123456789testcall",
        "From": "+1234567890",
        "To": "+61468017757",
        "CallStatus": "ringing",
        "Direction": "inbound",
        "ApiVersion": "2010-04-01"
    }
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    print("🧪 Testing Railway Voice Webhook (Clean Version)")
    print(f"URL: {url}")
    print(f"Test Data: {data}")
    print("-" * 50)
    
    try:
        response = requests.post(url, data=data, headers=headers, timeout=30)
        print(f"✅ Status Code: {response.status_code}")
        print(f"📄 Content-Type: {response.headers.get('Content-Type')}")
        print(f"📏 Content Length: {len(response.text)}")
        print("\n📝 TwiML Response:")
        print("=" * 50)
        print(response.text)
        print("=" * 50)
        
        if response.headers.get('Content-Type') == 'application/xml':
            try:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(response.text)
                print(f"✅ Valid XML: Root element is '{root.tag}'")
                
                for child in root:
                    print(f"   - {child.tag}: {child.text}")
                    
            except Exception as e:
                print(f"❌ Invalid XML: {e}")
        else:
            print("⚠️  Content-Type is not application/xml")
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - is the server running?")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    test_railway_webhook()
