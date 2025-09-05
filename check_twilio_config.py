from twilio.rest import Client
import os

# Get Twilio credentials from environment variables
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
phone_number = os.getenv('TWILIO_PHONE_NUMBER', '+61468017757')

if not account_sid or not auth_token:
    print("❌ Missing Twilio credentials in environment variables")
    print("Please set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN")
    exit(1)

client = Client(account_sid, auth_token)

print("🔍 Checking Twilio phone number configuration...")

try:
    # Get the phone number configuration
    phone_numbers = client.incoming_phone_numbers.list()
    
    target_number = None
    for number in phone_numbers:
        if number.phone_number == phone_number:
            target_number = number
            break
    
    if target_number:
        print(f"✅ Phone Number: {target_number.phone_number}")
        print(f"📞 Voice URL: {target_number.voice_url}")
        print(f"🔄 Voice Method: {target_number.voice_method}")
        print(f"📱 SMS URL: {target_number.sms_url}")
        print(f"🔄 SMS Method: {target_number.sms_method}")
        
        # Check if webhook URL matches Railway
        expected_webhook = "https://web-production-2b37.up.railway.app/api/voice/webhook"
        
        if target_number.voice_url == expected_webhook:
            print("✅ Webhook URL is correctly configured!")
        else:
            print(f"⚠️  Webhook URL mismatch!")
            print(f"Expected: {expected_webhook}")
            print(f"Current:  {target_number.voice_url}")
            
            # Update the webhook URL
            print("🔧 Updating webhook URL...")
            target_number.update(voice_url=expected_webhook)
            print("✅ Webhook URL updated!")
    else:
        print(f"❌ Phone number {phone_number} not found in your Twilio account")
        print("Available numbers:")
        for number in phone_numbers:
            print(f"  - {number.phone_number}")

except Exception as e:
    print(f"❌ Error checking Twilio configuration: {e}")
