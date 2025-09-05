"""Main FastAPI application."""

# Railway startup check
import os
import sys
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
    """Enhanced health check endpoint with database connectivity."""
    try:
        # Check if database is initialized
        if engine is None:
            return {
                "status": "degraded",
                "message": "Service running but database not initialized",
                "database": "not_initialized"
            }
        
        # Quick database connection test
        with engine.connect() as conn:
            # Simple query to test connection
            from sqlalchemy import text
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        
        return {
            "status": "ok", 
            "message": "Service is running",
            "database": "connected",
            "database_host": settings.DATABASE_URL.split('@')[1].split('/')[0] if '@' in settings.DATABASE_URL else 'localhost'
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
    """Ultra-simple webhook with minimal processing"""
    twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>Hello from Sunny Paws Veterinary Clinic. This is a test call.</Say>
</Response>'''
    return Response(content=twiml, media_type="application/xml")


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
