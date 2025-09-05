"""Test if enhanced conversational AI is working."""

import requests
import time

def test_enhanced_endpoints():
    """Test if the enhanced conversational endpoints are working."""
    
    print("🧪 TESTING ENHANCED CONVERSATIONAL AI")
    print("=" * 60)
    
    base_url = "https://web-production-2b37.up.railway.app"
    
    # Test original endpoints
    print(f"📞 Testing original endpoints:")
    
    try:
        simple_response = requests.get(f"{base_url}/simple", timeout=5)
        print(f"   /simple: {simple_response.status_code}")
        
        railway_response = requests.get(f"{base_url}/railway-webhook", timeout=5)
        print(f"   /railway-webhook: {railway_response.status_code}")
        
        health_response = requests.get(f"{base_url}/health", timeout=5)
        print(f"   /health: {health_response.status_code}")
        
    except Exception as e:
        print(f"   ❌ Original endpoint error: {e}")
    
    # Test enhanced endpoints
    print(f"\n🎤 Testing enhanced endpoints:")
    
    try:
        voice_conv_response = requests.get(f"{base_url}/voice-conversation", timeout=10)
        print(f"   /voice-conversation: {voice_conv_response.status_code}")
        
        if voice_conv_response.status_code == 200:
            print(f"   ✅ Enhanced conversational AI is working!")
            
            # Check for enhanced features
            content = voice_conv_response.text
            
            if 'I\'m your AI assistant' in content:
                print(f"   ✅ Enhanced greeting present")
            
            if 'speechTimeout="6"' in content:
                print(f"   ✅ Enhanced speech settings present")
            
            if 'speech-handler' in content:
                print(f"   ✅ Enhanced speech processing present")
                
            print(f"   📄 Response preview:")
            lines = content.split('\\n')
            for i, line in enumerate(lines[:8]):
                if line.strip():
                    print(f"      {line.strip()}")
                    
        elif voice_conv_response.status_code == 404:
            print(f"   ❌ Enhanced endpoint not deployed yet")
            print(f"   Railway is still deploying the new code")
            
        else:
            print(f"   ⚠️ Unexpected status: {voice_conv_response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Enhanced endpoint error: {e}")
    
    # Test speech processing endpoint
    print(f"\n🎤 Testing speech processing:")
    
    try:
        speech_response = requests.post(
            f"{base_url}/speech",
            data={'SpeechResult': 'I need an appointment'},
            timeout=5
        )
        print(f"   /speech: {speech_response.status_code}")
        
        if speech_response.status_code == 200:
            print(f"   ✅ Speech processing working!")
            
            if 'appointment' in speech_response.text.lower():
                print(f"   ✅ Intelligent keyword detection working")
                
            if 'Polly.Joanna' in speech_response.text:
                print(f"   ✅ Premium voice quality confirmed")
            
        elif speech_response.status_code == 404:
            print(f"   ❌ Speech processing not deployed yet")
            
    except Exception as e:
        print(f"   ❌ Speech processing error: {e}")

def check_current_webhook():
    """Check what webhook Twilio is currently using."""
    
    print(f"\n📞 CURRENT TWILIO WEBHOOK")
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
            print(f"🔗 Current webhook: {target_number.voice_url}")
            print(f"📝 Method: {target_number.voice_method}")
            print(f"🔄 Fallback: {target_number.voice_fallback_url}")
            
            # Check if it's using enhanced endpoint
            if 'voice-conversation' in target_number.voice_url:
                print(f"✅ Using enhanced conversational endpoint")
            elif 'railway-webhook' in target_number.voice_url:
                print(f"⚠️ Using basic conversational endpoint")
            else:
                print(f"❌ Using simple static endpoint")
                
        else:
            print(f"❌ Phone number not found")
            
    except Exception as e:
        print(f"❌ Twilio check failed: {e}")

def provide_next_steps():
    """Provide next steps based on test results."""
    
    print(f"\n📋 NEXT STEPS")
    print("=" * 60)
    
    print(f"⏱️ IF ENHANCED ENDPOINTS NOT WORKING:")
    print(f"   1. Railway may still be deploying")
    print(f"   2. Wait 2-3 more minutes")
    print(f"   3. Test again")
    
    print(f"\n📞 IF ENDPOINTS ARE WORKING:")
    print(f"   1. Make a test call to +61468017757")
    print(f"   2. Listen for enhanced greeting")
    print(f"   3. Speak clearly when prompted")
    print(f"   4. Test different phrases:")
    print(f"      • 'I need an appointment'")
    print(f"      • 'My pet is sick'")
    print(f"      • 'Emergency!'")
    
    print(f"\n✅ SUCCESS INDICATORS:")
    print(f"   • AI gives intelligent responses")
    print(f"   • Recognizes different request types")
    print(f"   • Provides appropriate callbacks")
    print(f"   • Sounds professional and helpful")

def main():
    """Test enhanced conversational AI system."""
    
    print("🎤 ENHANCED CONVERSATIONAL AI TEST")
    print("=" * 70)
    print("Checking if intelligent speech processing is deployed...")
    print("=" * 70)
    
    test_enhanced_endpoints()
    check_current_webhook()
    provide_next_steps()
    
    print(f"\n" + "=" * 70)
    print("🧪 ENHANCED AI TEST COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()
