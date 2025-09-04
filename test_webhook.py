#!/usr/bin/env python3
"""Test webhook endpoint locally."""

import requests
import json

def test_webhook():
    url = "http://localhost:8000/api/voice/webhook"
    data = {
        "CallSid": "CA123456789",
        "From": "+1234567890",
        "To": "+61468017757",
        "CallStatus": "ringing"
    }
    
    try:
        print(f"🧪 Testing webhook at {url}")
        response = requests.post(url, data=data)
        print(f"📊 Status Code: {response.status_code}")
        print(f"📄 Response Headers: {dict(response.headers)}")
        print(f"📝 Response Content: {response.text}")
        
        if response.status_code == 200:
            print("✅ Webhook is working locally!")
        else:
            print(f"❌ Webhook failed with status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing webhook: {e}")

def test_public_webhook():
    url = "https://vet-ai-receptionist.loca.lt/api/voice/webhook"
    data = {
        "CallSid": "CA123456789",
        "From": "+1234567890", 
        "To": "+61468017757",
        "CallStatus": "ringing"
    }
    
    try:
        print(f"🌐 Testing public webhook at {url}")
        response = requests.post(url, data=data, timeout=10)
        print(f"📊 Status Code: {response.status_code}")
        print(f"📄 Response Headers: {dict(response.headers)}")
        print(f"📝 Response Content: {response.text}")
        
        if response.status_code == 200:
            print("✅ Public webhook is working!")
        else:
            print(f"❌ Public webhook failed with status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing public webhook: {e}")

if __name__ == '__main__':
    print("🔧 Testing Voice AI Webhooks\n")
    test_webhook()
    print("\n" + "="*50 + "\n")
    test_public_webhook()
