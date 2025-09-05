"""Direct test of speech processing endpoint with detailed debugging."""

import requests
import time

def test_speech_endpoint_directly():
    """Test the speech processing endpoint with debugging."""
    
    print("🎤 DIRECT SPEECH PROCESSING TEST")
    print("=" * 60)
    
    base_url = "https://web-production-2b37.up.railway.app"
    endpoint = f"{base_url}/process-speech"
    
    test_cases = [
        {
            "name": "Emergency Test",
            "data": {
                "SpeechResult": "Emergency my pet is bleeding",
                "CallSid": "test123",
                "From": "+1234567890",
                "Confidence": "0.9"
            }
        },
        {
            "name": "Appointment Test", 
            "data": {
                "SpeechResult": "I need an appointment",
                "CallSid": "test456",
                "From": "+1234567890",
                "Confidence": "0.8"
            }
        },
        {
            "name": "Health Test",
            "data": {
                "SpeechResult": "My pet is sick",
                "CallSid": "test789",
                "From": "+1234567890", 
                "Confidence": "0.7"
            }
        },
        {
            "name": "No Speech Test",
            "data": {
                "CallSid": "test000",
                "From": "+1234567890"
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📞 Test {i}: {test_case['name']}")
        print(f"   Data: {test_case['data']}")
        
        try:
            start_time = time.time()
            
            response = requests.post(
                endpoint,
                data=test_case['data'],
                timeout=30,  # Longer timeout
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"   ✅ Status: {response.status_code}")
            print(f"   ⏱️ Duration: {duration:.2f}s")
            print(f"   📄 Content-Type: {response.headers.get('content-type', 'unknown')}")
            
            if response.status_code == 200:
                content = response.text[:500]  # First 500 chars
                print(f"   📝 Response preview:")
                lines = content.split('\n')
                for line in lines[:5]:
                    if line.strip():
                        print(f"      {line.strip()}")
                        
                # Check for TwiML validity
                if '<?xml' in content and '<Response>' in content:
                    print(f"   ✅ Valid TwiML structure")
                else:
                    print(f"   ❌ Invalid TwiML structure")
                    
                # Check for Say element
                if '<Say' in content:
                    print(f"   ✅ Contains Say element")
                else:
                    print(f"   ❌ Missing Say element")
                    
            else:
                print(f"   ❌ Error response: {response.text[:200]}")
                
        except requests.exceptions.Timeout:
            print(f"   ❌ TIMEOUT after 30 seconds")
            
        except requests.exceptions.ConnectionError as e:
            print(f"   ❌ CONNECTION ERROR: {e}")
            
        except Exception as e:
            print(f"   ❌ UNEXPECTED ERROR: {e}")
    
    print(f"\n" + "=" * 60)

def test_basic_connectivity():
    """Test basic connectivity to Railway."""
    
    print("🌐 BASIC CONNECTIVITY TEST")
    print("=" * 60)
    
    base_url = "https://web-production-2b37.up.railway.app"
    
    endpoints = [
        "/health",
        "/simple", 
        "/voice-conversation"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            print(f"   {endpoint}: {response.status_code} ✅")
        except Exception as e:
            print(f"   {endpoint}: ERROR - {e} ❌")

if __name__ == "__main__":
    test_basic_connectivity()
    print()
    test_speech_endpoint_directly()
