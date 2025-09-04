"""Minimal webhook handler that works without database for testing."""

from fastapi import FastAPI, Form
from fastapi.responses import Response

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "ok", "message": "Minimal service running"}

@app.post("/api/voice/webhook")
async def minimal_webhook(
    CallSid: str = Form(...),
    From: str = Form(...),
    To: str = Form(...),
    CallStatus: str = Form(...)
):
    """Minimal webhook that responds immediately without database."""
    
    print(f"📞 Incoming call: {CallSid} from {From} to {To} status {CallStatus}")
    
    if CallStatus == "ringing":
        # Simple TwiML response for greeting
        twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Gather input="speech" action="/api/voice/process" method="POST" speechTimeout="3">
        <Say voice="alice">Hello! Thank you for calling AI Veterinary Clinic. I'm your AI assistant. How can I help you and your pet today?</Say>
    </Gather>
    <Say voice="alice">I didn't hear anything. Please call back.</Say>
</Response>'''
        
        return Response(content=twiml, media_type="application/xml")
    
    # Default response
    twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">Thank you for calling. Goodbye!</Say>
    <Hangup/>
</Response>'''
    
    return Response(content=twiml, media_type="application/xml")

@app.post("/api/voice/process")
async def process_speech(
    CallSid: str = Form(...),
    SpeechResult: str = Form(...)
):
    """Process speech input."""
    
    print(f"🎤 Speech from {CallSid}: {SpeechResult}")
    
    # Simple response based on keywords
    if any(word in SpeechResult.lower() for word in ["emergency", "urgent", "help"]):
        response = "This sounds urgent. Let me connect you with our emergency service right away."
    elif any(word in SpeechResult.lower() for word in ["appointment", "book", "schedule"]):
        response = "I'd be happy to help you schedule an appointment. Our staff will call you back within 10 minutes."
    else:
        response = "Thank you for calling. Our staff will assist you shortly. Have a great day!"
    
    twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">{response}</Say>
    <Hangup/>
</Response>'''
    
    return Response(content=twiml, media_type="application/xml")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
