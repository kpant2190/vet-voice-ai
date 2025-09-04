"""Simplified voice webhook for testing."""

from fastapi import APIRouter, Request, Form
from fastapi.responses import Response

# Create a simple test router
test_router = APIRouter()

@test_router.post("/test-webhook")
async def test_voice_webhook(
    CallSid: str = Form(...),
    From: str = Form(...),
    To: str = Form(...),
    CallStatus: str = Form(...)
):
    """Simple test webhook that just returns basic TwiML."""
    
    print(f"📞 Received call: {CallSid} from {From} to {To} status {CallStatus}")
    
    # Create simple TwiML response
    twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">Hello! This is a test from your AI receptionist. Your call is working!</Say>
    <Hangup/>
</Response>'''
    
    return Response(content=twiml, media_type="application/xml")
