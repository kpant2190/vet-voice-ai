"""Real-time call diagnostics to see what's happening during actual phone calls."""

import requests
import time
from datetime import datetime

def monitor_call_flow():
    """Monitor the actual call flow in real-time."""
    
    print("🔍 REAL-TIME CALL DIAGNOSTICS")
    print("=" * 60)
    print(f"📞 Phone Number: +61468017757")
    print(f"🌐 Server: web-production-2b37.up.railway.app")
    print(f"⏰ Monitoring started at: {datetime.now()}")
    print("=" * 60)
    
    base_url = "https://web-production-2b37.up.railway.app"
    
    # Test 1: Verify voice conversation endpoint (what Twilio calls first)
    print("📞 TESTING INITIAL CALL FLOW:")
    
    try:
        response = requests.get(f"{base_url}/voice-conversation", timeout=10)
        print(f"✅ Voice conversation: {response.status_code}")
        
        if response.status_code == 200:
            content = response.text
            print(f"📄 TwiML Response Preview:")
            
            # Check key elements
            if 'Hello! You\'ve reached AI Veterinary Clinic' in content:
                print("   ✅ Greeting message present")
            if 'action="/speech"' in content:
                print("   ✅ Speech action correctly set to /speech")
            if 'Polly.Joanna' in content:
                print("   ✅ Premium voice configured")
            if 'enhanced="true"' in content:
                print("   ✅ Enhanced speech recognition enabled")
            if 'speechTimeout="6"' in content:
                print("   ✅ Extended speech timeout (6 seconds)")
            if 'timeout="18"' in content:
                print("   ✅ Extended total timeout (18 seconds)")
                
            # Show the actual TwiML
            print(f"\n📋 ACTUAL TwiML TWILIO RECEIVES:")
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.strip():
                    print(f"   {line.strip()}")
        else:
            print(f"❌ Voice conversation failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Voice conversation error: {e}")
    
    # Test 2: Test speech processing (what happens when you speak)
    print(f"\n🎤 TESTING SPEECH PROCESSING:")
    
    test_speeches = [
        "I need an appointment",
        "My pet is sick", 
        "Emergency",
        "Hello"
    ]
    
    for speech in test_speeches:
        try:
            start_time = time.time()
            response = requests.post(
                f"{base_url}/speech",
                data={'SpeechResult': speech},
                timeout=8
            )
            response_time = time.time() - start_time
            
            print(f"   Speech: '{speech}'")
            print(f"   Status: {response.status_code} (in {response_time:.2f}s)")
            
            if response.status_code == 200:
                content = response.text
                if 'appointment' in speech.lower() and 'appointment' in content.lower():
                    print("   ✅ Appointment response detected")
                elif 'sick' in speech.lower() and ('vet' in content.lower() or 'call' in content.lower()):
                    print("   ✅ Health concern response detected")
                elif 'emergency' in speech.lower() and 'emergency' in content.lower():
                    print("   ✅ Emergency response detected")
                else:
                    print("   ✅ General response provided")
                    
                print(f"   Response: {content.split('<Say')[1].split('</Say>')[0] if '<Say' in content else 'No Say tag found'}")
            else:
                print(f"   ❌ Failed with status {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()  # Empty line between tests
    
    # Test 3: Check for any conflicting endpoints
    print(f"🔍 CHECKING FOR ENDPOINT CONFLICTS:")
    
    endpoints_to_check = ["/simple", "/railway-webhook", "/simple-response", "/process-speech"]
    
    for endpoint in endpoints_to_check:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=3)
            print(f"   {endpoint}: {response.status_code}")
        except:
            print(f"   {endpoint}: Not accessible or timeout")

def check_twilio_webhook_config():
    """Check current Twilio webhook configuration."""
    
    print(f"\n📞 TWILIO WEBHOOK CONFIGURATION:")
    print("=" * 60)
    
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    phone_number = os.getenv('TWILIO_PHONE_NUMBER')
    
    try:
        from twilio.rest import Client
        client = Client(account_sid, auth_token)
        
        # Find the phone number
        phone_numbers = client.incoming_phone_numbers.list()
        target_number = None
        
        for number in phone_numbers:
            if number.phone_number == phone_number:
                target_number = number
                break
        
        if target_number:
            print(f"📞 Phone: {target_number.phone_number}")
            print(f"🔗 Voice URL: {target_number.voice_url}")
            print(f"📝 Method: {target_number.voice_method}")
            print(f"🔄 Fallback URL: {target_number.voice_fallback_url}")
            print(f"📱 SMS URL: {target_number.sms_url}")
            
            # Verify URL is correct
            expected_url = "https://web-production-2b37.up.railway.app/voice-conversation"
            if target_number.voice_url == expected_url:
                print(f"✅ Webhook URL is correct!")
            else:
                print(f"❌ Webhook URL mismatch!")
                print(f"   Expected: {expected_url}")
                print(f"   Actual: {target_number.voice_url}")
                
        else:
            print(f"❌ Phone number {phone_number} not found")
            
    except Exception as e:
        print(f"❌ Twilio check failed: {e}")

def provide_call_instructions():
    """Provide specific call testing instructions."""
    
    print(f"\n🎯 CALL TESTING INSTRUCTIONS:")
    print("=" * 60)
    print(f"1. 📞 Call +61468017757")
    print(f"2. 🎧 Listen for: 'Hello! You've reached AI Veterinary Clinic...'")
    print(f"3. ⏱️  Wait for prompt: 'Please tell me what you need help with...'")
    print(f"4. 🗣️  Speak clearly: Try one of these phrases:")
    print(f"   • 'I need an appointment'")
    print(f"   • 'My pet is sick'")
    print(f"   • 'This is an emergency'")
    print(f"5. ⏰ Wait up to 6 seconds after speaking")
    print(f"6. 🎤 Listen for intelligent response")
    print(f"")
    print(f"🔧 If still not working, the issue might be:")
    print(f"   • Network delay between Twilio and Railway")
    print(f"   • Speech recognition sensitivity")
    print(f"   • Microphone/audio quality")
    print(f"   • Background noise interference")

if __name__ == "__main__":
    monitor_call_flow()
    check_twilio_webhook_config()
    provide_call_instructions()
