import requests
import json

print("🔍 Testing Railway endpoints...")

try:
    # Test health endpoint
    print("\n1. Testing health endpoint...")
    r = requests.get('https://web-production-2b37.up.railway.app/health', timeout=10)
    print(f"Status: {r.status_code}")
    print(f"Response: {json.dumps(r.json(), indent=2)}")
    
    # Test webhook endpoint with simple data
    print("\n2. Testing webhook endpoint...")
    webhook_data = {
        'CallSid': 'test123',
        'From': '+1234567890',
        'To': '+61468017757',
        'CallStatus': 'ringing'
    }
    
    r2 = requests.post(
        'https://web-production-2b37.up.railway.app/api/voice/webhook',
        data=webhook_data,
        timeout=10
    )
    print(f"Webhook Status: {r2.status_code}")
    print(f"Webhook Response: {r2.text[:200]}...")
    
except Exception as e:
    print(f"❌ Error: {e}")
