"""Minimal voice webhook for ultra-fast response to Twilio."""

from fastapi import APIRouter, Form
from fastapi.responses import Response
from typing import Optional

router = APIRouter()


@router.post("/minimal-webhook")
async def minimal_voice_webhook(
    CallSid: str = Form(...),
    From: str = Form(...),
    To: str = Form(...),
    CallStatus: str = Form(...),
    SpeechResult: Optional[str] = Form(None)
):
    """Ultra-minimal webhook for immediate Twilio response."""
    
    print(f"📞 MINIMAL: {CallSid} from {From} status {CallStatus}")
    
    # Immediate TwiML response - no database, no services, no delays
    if CallStatus == "ringing":
        twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">Hello! Thank you for calling AI Veterinary Clinic. I'm your AI assistant. How can I help you and your pet today?</Say>
    <Gather input="speech" action="/api/voice/minimal-process" method="POST" speechTimeout="auto">
        <Say voice="alice">Please tell me what you need help with.</Say>
    </Gather>
    <Say voice="alice">I didn't hear anything. Please call back if you need assistance. Goodbye!</Say>
    <Hangup/>
</Response>'''
    
    elif SpeechResult:
        # Basic keyword responses
        speech_lower = SpeechResult.lower()
        
        if any(word in speech_lower for word in ["emergency", "urgent", "dying", "bleeding"]):
            twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">This sounds like an emergency! Please hang up and call our emergency line immediately, or visit the nearest emergency veterinary clinic. Thank you.</Say>
    <Hangup/>
</Response>'''
        
        elif any(word in speech_lower for word in ["appointment", "schedule", "book"]):
            twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">I'd love to help you schedule an appointment! Our team will call you back within 10 minutes to book that for you. Thank you for calling AI Veterinary Clinic!</Say>
    <Hangup/>
</Response>'''
        
        else:
            twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">Thank you for calling AI Veterinary Clinic. Our team will call you back within 10 minutes to assist you. Have a great day!</Say>
    <Hangup/>
</Response>'''
    
    else:
        twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">Thank you for calling AI Veterinary Clinic. If you need immediate assistance, please call back. Goodbye!</Say>
    <Hangup/>
</Response>'''
    
    return Response(content=twiml, media_type="application/xml")


@router.post("/minimal-process")
async def minimal_process(
    SpeechResult: str = Form(...),
    CallSid: str = Form(...)
):
    """Process speech with minimal delay."""
    
    print(f"🎤 MINIMAL PROCESS: {SpeechResult}")
    
    # Super fast keyword matching
    speech_lower = SpeechResult.lower()
    
    if any(word in speech_lower for word in ["emergency", "urgent", "dying", "bleeding", "collapsed"]):
        twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">This is an emergency! Please hang up immediately and call emergency services or visit the nearest emergency veterinary clinic. Your pet needs immediate care!</Say>
    <Hangup/>
</Response>'''
    
    elif any(word in speech_lower for word in ["appointment", "schedule", "book", "visit"]):
        twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">Perfect! I'll have our team call you back within 10 minutes to schedule your appointment. What's the best number to reach you?</Say>
    <Gather input="speech" action="/api/voice/minimal-final" method="POST" speechTimeout="auto">
        <Say voice="alice">Please say your phone number.</Say>
    </Gather>
    <Say voice="alice">Thank you! We'll call you back soon. Goodbye!</Say>
    <Hangup/>
</Response>'''
    
    elif any(word in speech_lower for word in ["prescription", "medication", "refill"]):
        twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">I can help with prescription refills! Our team will call you back within 10 minutes to process that refill for you. Thank you!</Say>
    <Hangup/>
</Response>'''
    
    else:
        twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">Thank you for calling! Our team will call you back within 10 minutes to help with your request. Have a wonderful day!</Say>
    <Hangup/>
</Response>'''
    
    return Response(content=twiml, media_type="application/xml")


@router.post("/minimal-final")
async def minimal_final(
    SpeechResult: str = Form(...),
    CallSid: str = Form(...)
):
    """Final response in minimal flow."""
    
    print(f"📞 FINAL: {SpeechResult}")
    
    twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">Perfect! We have your information and will call you back within 10 minutes. Thank you for choosing AI Veterinary Clinic. Goodbye!</Say>
    <Hangup/>
</Response>'''
    
    return Response(content=twiml, media_type="application/xml")
