#!/usr/bin/env python3
"""Simple test for the voice webhook."""

import requests
import json

def test_webhook_simple():
    """Test the webhook with minimal data."""
    
    url = "http://localhost:8000/api/voice/webhook"
    
    # Minimal Twilio webhook data
    data = {
        "CallSid": "CAtest123456789",
        "From": "+1234567890",
        "To": "+61468017757",
        "CallStatus": "ringing"
    }
    
    print("🧪 Testing Voice Webhook")
    print(f"URL: {url}")
    print(f"Data: {data}")
    print("-" * 50)
    
    try:
        response = requests.post(url, data=data, timeout=10)
        print(f"✅ Status Code: {response.status_code}")
        print(f"📄 Content-Type: {response.headers.get('Content-Type')}")
        print(f"📏 Content Length: {len(response.text)}")
        print("\n📝 TwiML Response:")
        print("=" * 50)
        print(response.text)
        print("=" * 50)
        
        # Check if it's valid XML
        if response.headers.get('Content-Type') == 'application/xml':
            try:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(response.text)
                print(f"✅ Valid XML: Root element is '{root.tag}'")
                
                # Check for TwiML elements
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
    test_webhook_simple()
