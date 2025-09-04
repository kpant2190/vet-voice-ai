"""Minimal webhook endpoint for Railway testing."""

from fastapi import FastAPI, Form
from fastapi.responses import Response

app = FastAPI(title="Minimal Voice AI Test")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "message": "Minimal service is running"}

@app.post("/api/voice/webhook")
async def minimal_voice_webhook(
    CallSid: str = Form(...),
    From: str = Form(...),
    To: str = Form(...),
    CallStatus: str = Form(...)
):
    """Minimal voice webhook that works without database."""
    
    print(f"📞 Call received: {CallSid} from {From} to {To} status {CallStatus}")
    
    # Create minimal TwiML response
    twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">Hello! You've reached Sunny Paws Veterinary Clinic. This is our AI receptionist. Please hold while I connect you to someone who can help you.</Say>
    <Pause length="2"/>
    <Say voice="alice">Thank you for calling. Have a great day!</Say>
    <Hangup/>
</Response>'''
    
    return Response(content=twiml, media_type="application/xml")

@app.post("/simple")
@app.get("/simple")
async def ultra_simple():
    """Ultra-simple test endpoint."""
    twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>Hello from Sunny Paws. This is a test call.</Say>
</Response>'''
    return Response(content=twiml, media_type="application/xml")
