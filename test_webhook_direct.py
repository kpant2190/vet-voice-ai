import requests
import time

print("🚀 Testing Railway webhook endpoint directly...")

webhook_url = "https://web-production-2b37.up.railway.app/api/voice/webhook"

# Test data that mimics a Twilio webhook call
test_data = {
    'CallSid': 'CAtest123456789',
    'From': '+1234567890', 
    'To': '+61468017757',
    'CallStatus': 'ringing',
    'Direction': 'inbound'
}

try:
    print(f"📞 Sending test webhook to: {webhook_url}")
    print(f"📋 Test data: {test_data}")
    
    start_time = time.time()
    
    response = requests.post(
        webhook_url,
        data=test_data,
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        timeout=30  # Increased timeout
    )
    
    end_time = time.time()
    response_time = end_time - start_time
    
    print(f"⏱️  Response time: {response_time:.2f} seconds")
    print(f"📊 Status code: {response.status_code}")
    print(f"📄 Content type: {response.headers.get('content-type', 'unknown')}")
    print(f"📝 Response length: {len(response.text)} characters")
    
    if response.status_code == 200:
        print("✅ Webhook responded successfully!")
        print("📋 Response preview:")
        print(response.text[:300])
    else:
        print(f"⚠️  Non-200 status code: {response.status_code}")
        print("📋 Response:")
        print(response.text[:500])

except requests.exceptions.Timeout:
    print("❌ Request timed out after 30 seconds")
except requests.exceptions.ConnectionError:
    print("❌ Connection error - Railway service might be down")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n🔍 Quick health check...")
try:
    health_response = requests.get(
        "https://web-production-2b37.up.railway.app/health",
        timeout=10
    )
    print(f"Health check: {health_response.status_code} - {health_response.text}")
except Exception as e:
    print(f"Health check failed: {e}")
