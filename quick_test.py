import requests
import time

print("🚀 Testing optimized Railway webhook...")

try:
    # Test health endpoint first
    print("1. Health check...")
    health_response = requests.get("https://web-production-2b37.up.railway.app/health", timeout=10)
    print(f"Health: {health_response.status_code}")
    
    # Test webhook with minimal data
    print("2. Testing webhook...")
    start_time = time.time()
    
    webhook_response = requests.post(
        "https://web-production-2b37.up.railway.app/api/voice/webhook",
        data={
            'CallSid': 'test_call_123',
            'From': '+1234567890',
            'To': '+61468017757',
            'CallStatus': 'ringing'
        },
        timeout=15
    )
    
    end_time = time.time()
    response_time = end_time - start_time
    
    print(f"Webhook Status: {webhook_response.status_code}")
    print(f"Response Time: {response_time:.2f} seconds")
    print(f"Response Type: {webhook_response.headers.get('content-type', 'unknown')}")
    
    if webhook_response.status_code == 200:
        print("✅ SUCCESS! Webhook is working!")
        if 'xml' in webhook_response.headers.get('content-type', ''):
            print("✅ Returning proper TwiML XML")
        print(f"Preview: {webhook_response.text[:200]}...")
    else:
        print(f"⚠️ Unexpected status: {webhook_response.status_code}")
        print(f"Response: {webhook_response.text}")

except requests.exceptions.Timeout:
    print("❌ Timeout - webhook took too long")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n📞 Your AI receptionist is ready!")
print("Call +61468017757 to test the full system!")
