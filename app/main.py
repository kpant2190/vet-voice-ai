"""Main FastAPI application."""

# Railway startup check
import os
import sys
import time
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
try:
    import railway_startup_check
except ImportError:
    print("⚠️ Railway startup check not available")

from fastapi import FastAPI, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
import uvicorn

from .core.config import settings
from .core.database import initialize_database, create_tables, engine
from .api.voice import router as voice_router
from .api.minimal_voice import router as minimal_voice_router
from .api.sms import router as sms_router
from .api.appointments import router as appointments_router
from .api.clinics import router as clinics_router

# Create FastAPI instance
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI Receptionist for Veterinary Clinics",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add comprehensive request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"🔥 INCOMING REQUEST: {request.method} {request.url}")
    print(f"🔥 Headers: {dict(request.headers)}")
    print(f"🔥 Client: {request.client}")
    
    # Try to read body for POST requests
    if request.method == "POST":
        body = await request.body()
        print(f"🔥 Body: {body.decode('utf-8', errors='ignore')}")
    
    response = await call_next(request)
    print(f"🔥 Response status: {response.status_code}")
    return response

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    voice_router,
    prefix=f"{settings.API_V1_STR}/voice",
    tags=["voice"]
)

app.include_router(
    minimal_voice_router,
    prefix=f"{settings.API_V1_STR}/voice",
    tags=["minimal-voice"]
)

app.include_router(
    sms_router,
    prefix=f"{settings.API_V1_STR}/sms",
    tags=["sms"]
)

app.include_router(
    appointments_router,
    prefix=f"{settings.API_V1_STR}/appointments",
    tags=["appointments"]
)

app.include_router(
    clinics_router,
    prefix=f"{settings.API_V1_STR}/clinics",
    tags=["clinics"]
)

# Health check endpoint for Railway
@app.get("/")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "AI Veterinary Receptionist"}

@app.get("/health")
async def health():
    """Enhanced health check endpoint with Railway database support."""
    try:
        # Use the new health check function from database module
        from .core.database import check_database_health
        
        health_result = check_database_health()
        
        # Add additional service information
        health_result.update({
            "service": "AI Veterinary Receptionist",
            "version": "1.0.0",
            "railway_deployment": True
        })
        
        return health_result
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Health check failed: {str(e)}",
            "database": "unknown",
            "service": "AI Veterinary Receptionist"
        }
    except Exception as e:
        return {
            "status": "degraded",
            "message": "Service running with database issues",
            "database": f"error: {str(e)}"
        }

# Test webhook for debugging
@app.post("/test-webhook")
async def test_webhook(
    CallSid: str = Form(...),
    From: str = Form(...),
    To: str = Form(...),
    CallStatus: str = Form(...)
):
    """Simple test webhook."""
    print(f"📞 TEST WEBHOOK: {CallSid} from {From} to {To} status {CallStatus}")
    twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">Hello! This is a simple test. Your webhook is working!</Say>
    <Hangup/>
</Response>'''
    return Response(content=twiml, media_type="application/xml")

@app.get("/test-webhook")
async def test_webhook_get():
    """Simple test webhook for GET requests (browser testing)"""
    twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">Hello! This is a GET test. Your webhook is working!</Say>
    <Hangup/>
</Response>'''
    return Response(content=twiml, media_type="application/xml")

# Ultra-simple webhook for maximum Twilio compatibility
@app.post("/simple")
@app.get("/simple")
async def ultra_simple_webhook():
    """Ultra-simple webhook with minimal processing - guaranteed to work."""
    try:
        twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">Hello! You have reached AI Veterinary Clinic. This call is working correctly. Thank you for calling!</Say>
    <Hangup/>
</Response>'''
        return Response(content=twiml, media_type="application/xml")
    except Exception as e:
        # Emergency fallback - should never fail
        emergency_twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>Hello! Thank you for calling AI Veterinary Clinic. Please call back later.</Say>
    <Hangup/>
</Response>'''
        return Response(content=emergency_twiml, media_type="application/xml")

# Enhanced conversational AI webhook
@app.post("/voice-conversation")
@app.get("/voice-conversation")
async def voice_conversation():
    """Enhanced conversational AI webhook with intelligent responses."""
    try:
        print(f"🎤 Enhanced voice conversation started at {time.time()}")
        
        twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">Hello! You've reached AI Veterinary Clinic. I'm your AI assistant, and I'm here to help you and your pet. How can I assist you today?</Say>
    <Gather input="speech" action="/process-speech" method="POST" speechTimeout="5" timeout="15" language="en-AU">
        <Say voice="alice">Please tell me what you need help with, such as booking an appointment, asking about your pet's health, or if this is an emergency.</Say>
    </Gather>
    <Redirect>/voice-conversation-retry</Redirect>
</Response>'''
        return Response(content=twiml, media_type="application/xml")
    except Exception as e:
        print(f"❌ Voice conversation error: {e}")
        # Safe fallback
        return Response(
            content='<?xml version="1.0" encoding="UTF-8"?><Response><Say voice="alice">Thank you for calling AI Veterinary Clinic!</Say><Hangup/></Response>',
            media_type="application/xml"
        )

@app.post("/voice-conversation-retry")
@app.get("/voice-conversation-retry")
async def voice_conversation_retry():
    """Retry voice conversation with shorter timeout."""
    try:
        twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">I didn't catch that. Could you please tell me briefly what you need help with?</Say>
    <Gather input="speech" action="/process-speech" method="POST" speechTimeout="3" timeout="10" language="en-AU">
        <Say voice="alice">For example, say appointment, emergency, or health question.</Say>
    </Gather>
    <Say voice="alice">I'm having trouble hearing you. Our team will call you back within 10 minutes to assist you. Thank you for calling AI Veterinary Clinic!</Say>
    <Hangup/>
</Response>'''
        return Response(content=twiml, media_type="application/xml")
    except Exception as e:
        return Response(
            content='<?xml version="1.0" encoding="UTF-8"?><Response><Say voice="alice">Thank you for calling!</Say><Hangup/></Response>',
            media_type="application/xml"
        )

@app.post("/process-speech")
async def process_speech(
    SpeechResult: str = Form(None),
    CallSid: str = Form(None),
    From: str = Form(None),
    Confidence: str = Form(None)
):
    """Process speech with intelligent keyword detection and responses."""
    try:
        print(f"🎤 Speech processing: '{SpeechResult}' (confidence: {Confidence})")
        
        # Default response
        response = "Thank you for calling AI Veterinary Clinic! Our team will call you back within 10 minutes to assist you."
        
        if SpeechResult:
            speech_lower = SpeechResult.lower()
            
            # Simple keyword checks
            if "emergency" in speech_lower or "urgent" in speech_lower or "bleeding" in speech_lower:
                response = "This sounds like an emergency! Please hang up immediately and call your nearest emergency veterinary clinic right away. Time is critical!"
            elif "appointment" in speech_lower or "schedule" in speech_lower or "book" in speech_lower:
                response = "Perfect! I'd be happy to help you schedule an appointment. Our booking team will call you back within 10 minutes to check available times."
            elif "sick" in speech_lower or "ill" in speech_lower or "health" in speech_lower:
                response = "I understand you have concerns about your pet's health. Our veterinary team will call you back within 10 minutes to discuss your pet's symptoms."
            elif "prescription" in speech_lower or "medication" in speech_lower or "refill" in speech_lower:
                response = "Of course! Our pharmacy team will call you back within 10 minutes to help with your pet's prescription needs."
        
        twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">{response}</Say>
    <Hangup/>
</Response>'''
        
        return Response(content=twiml, media_type="application/xml")
        
    except Exception as e:
        print(f"❌ Speech processing error: {e}")
        # Ultra-safe fallback
        twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">Thank you for calling AI Veterinary Clinic!</Say>
    <Hangup/>
</Response>'''
        return Response(content=twiml, media_type="application/xml")

@app.post("/partial-result")
async def partial_result(
    UnstableSpeechResult: str = Form(None),
    StableSpeechResult: str = Form(None),
    CallSid: str = Form(None)
):
    """Handle partial speech results for real-time processing."""
    try:
        print(f"🎤 Partial speech - Stable: '{StableSpeechResult}', Unstable: '{UnstableSpeechResult}'")
        
        # Return empty TwiML to continue gathering
        return Response(
            content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
            media_type="application/xml"
        )
    except Exception as e:
        print(f"❌ Partial result error: {e}")
        return Response(
            content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
            media_type="application/xml"
        )

# Database-independent webhook for Railway
@app.post("/railway-webhook")
@app.get("/railway-webhook")
async def railway_webhook():
    """Railway-optimized webhook that works without database."""
    try:
        # Log the call for debugging
        print(f"Railway webhook called at {time.time()}")
        
        twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">Hello! You have reached AI Veterinary Clinic. We are an AI-powered veterinary receptionist. How can we help you and your pet today?</Say>
    <Gather input="speech" action="/simple-response" method="POST" speechTimeout="3" timeout="10">
        <Say voice="alice">Please tell us what you need help with.</Say>
    </Gather>
    <Say voice="alice">We didn't hear anything. Please call back if you need assistance. Thank you!</Say>
    <Hangup/>
</Response>'''
        return Response(content=twiml, media_type="application/xml")
    except Exception as e:
        # Ultra-safe fallback
        return Response(
            content='<?xml version="1.0" encoding="UTF-8"?><Response><Say>Thank you for calling!</Say><Hangup/></Response>',
            media_type="application/xml"
        )

@app.post("/simple-response")
async def simple_response(SpeechResult: str = Form(None)):
    """Handle simple speech responses without database."""
    try:
        import time
        print(f"Speech received: {SpeechResult} at {time.time()}")
        
        if SpeechResult:
            speech_lower = SpeechResult.lower()
            
            if any(word in speech_lower for word in ["emergency", "urgent", "dying", "bleeding"]):
                response = "This sounds like an emergency! Please hang up and call emergency services or visit the nearest emergency veterinary clinic immediately!"
            elif any(word in speech_lower for word in ["appointment", "schedule", "book"]):
                response = "I'd be happy to help you schedule an appointment! Our staff will call you back within 10 minutes to book that for you."
            else:
                response = "Thank you for calling AI Veterinary Clinic! Our team will call you back within 10 minutes to assist you."
        else:
            response = "Thank you for calling AI Veterinary Clinic!"
        
        twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice">{response}</Say>
    <Hangup/>
</Response>'''
        return Response(content=twiml, media_type="application/xml")
        
    except Exception as e:
        return Response(
            content='<?xml version="1.0" encoding="UTF-8"?><Response><Say>Thank you for calling!</Say><Hangup/></Response>',
            media_type="application/xml"
        )


@app.on_event("startup")
async def startup_event():
    """Application startup event with proper database initialization."""
    print(f"🚀 Starting {settings.PROJECT_NAME}...")
    
    # Initialize database connection
    db_success = initialize_database()
    
    if db_success:
        # Create database tables
        tables_created = create_tables()
        if tables_created:
            print(f"✅ Database initialized successfully!")
        else:
            print(f"⚠️ Database connected but table creation failed")
    else:
        print(f"⚠️ Database initialization failed - app will run in degraded mode")
        print(f"📝 Check DATABASE_URL: {settings.DATABASE_URL[:50]}...")
    
    print(f"🚀 {settings.PROJECT_NAME} startup complete!")
    print(f"📊 API Documentation: http://localhost:{settings.PORT}/docs")
    print(f"🔗 Twilio Webhook URL: https://your-railway-domain.com{settings.API_V1_STR}/voice/webhook")


@app.get("/")
async def root():
    """Root endpoint with basic information."""
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "version": "1.0.0",
        "docs": "/docs",
        "voice_webhook": f"{settings.API_V1_STR}/voice/webhook",
        "status": "healthy"
    }


# Remove duplicate health endpoint - keeping only the enhanced one above
# Lines 180-186 removed to prevent conflicts


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    if settings.DEBUG:
        import traceback
        error_detail = {
            "error": str(exc),
            "traceback": traceback.format_exc()
        }
    else:
        error_detail = {"error": "Internal server error"}
    
    return JSONResponse(
        status_code=500,
        content=error_detail
    )


# WebSocket endpoint for real-time communication
from fastapi import WebSocket, WebSocketDisconnect
from typing import List
import json


class ConnectionManager:
    """Manage WebSocket connections."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


@app.websocket("/ws/audio")
async def websocket_audio_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time audio streaming."""
    await manager.connect(websocket)
    
    try:
        while True:
            # Receive audio data
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message["type"] == "audio_chunk":
                # Process audio chunk (placeholder)
                response = {
                    "type": "transcription",
                    "text": "Processing audio...",  # Replace with actual transcription
                    "timestamp": "2024-01-01T00:00:00Z"
                }
                await manager.send_personal_message(json.dumps(response), websocket)
            
            elif message["type"] == "ping":
                await manager.send_personal_message(
                    json.dumps({"type": "pong"}),
                    websocket
                )
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
