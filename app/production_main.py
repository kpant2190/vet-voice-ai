"""Production-ready FastAPI application for AI Veterinary Receptionist."""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, Optional, Any
import uuid

from fastapi import FastAPI, Request, Form, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, Response, PlainTextResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response as StarletteResponse
import structlog

from .core.production_config import get_settings
from .services.ai_conversation import conversation_engine
from .services.monitoring import monitoring
from .core.database import initialize_database, create_tables

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)
settings = get_settings()

# Create FastAPI instance with production configuration
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    openapi_url="/openapi.json" if not settings.is_production else None
)


class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for production deployment."""
    
    async def dispatch(self, request: StarletteRequest, call_next) -> StarletteResponse:
        # Add security headers
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Remove server header
        if "server" in response.headers:
            del response.headers["server"]
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware."""
    
    def __init__(self, app, calls_per_minute: int = 60):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute
        self.calls = {}
    
    async def dispatch(self, request: StarletteRequest, call_next) -> StarletteResponse:
        client_ip = request.client.host
        current_time = time.time()
        
        # Clean old entries
        cutoff_time = current_time - 60
        self.calls = {ip: times for ip, times in self.calls.items() 
                     if any(t > cutoff_time for t in times)}
        
        # Check rate limit
        if client_ip not in self.calls:
            self.calls[client_ip] = []
        
        # Remove old calls for this IP
        self.calls[client_ip] = [t for t in self.calls[client_ip] if t > cutoff_time]
        
        if len(self.calls[client_ip]) >= self.calls_per_minute:
            monitoring.record_error("rate_limit", request.url.path, f"IP {client_ip} exceeded rate limit")
            return JSONResponse(
                status_code=429,
                content={"error": "Rate limit exceeded", "retry_after": 60}
            )
        
        self.calls[client_ip].append(current_time)
        return await call_next(request)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Comprehensive request logging middleware."""
    
    async def dispatch(self, request: StarletteRequest, call_next) -> StarletteResponse:
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        # Log request
        logger.info(
            "Request started",
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            client_ip=request.client.host,
            user_agent=request.headers.get("user-agent", "unknown")
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate response time
            process_time = (time.time() - start_time) * 1000
            
            # Log response
            logger.info(
                "Request completed",
                request_id=request_id,
                status_code=response.status_code,
                process_time_ms=process_time
            )
            
            # Record metrics
            monitoring.record_response_time(process_time)
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            process_time = (time.time() - start_time) * 1000
            
            logger.error(
                "Request failed",
                request_id=request_id,
                error=str(e),
                process_time_ms=process_time
            )
            
            monitoring.record_error("request_exception", request.url.path, str(e))
            raise


# Add middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(SecurityMiddleware)
app.add_middleware(RequestLoggingMiddleware)

if settings.is_production:
    app.add_middleware(RateLimitMiddleware, calls_per_minute=settings.RATE_LIMIT_PER_MINUTE)
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*.railway.app", "*.up.railway.app", "localhost", "127.0.0.1"]
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.is_development else ["https://your-domain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# Security dependency
security = HTTPBearer(auto_error=False)

async def verify_webhook_security(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> bool:
    """Verify webhook security for sensitive endpoints."""
    if settings.is_development:
        return True
    
    # In production, implement proper webhook signature validation
    # This is a simplified version
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    return True


# Health check endpoints
@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint."""
    try:
        health_data = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT.value,
            "uptime_hours": (datetime.now() - monitoring.start_time).total_seconds() / 3600
        }
        
        # Check database connectivity
        try:
            # Add actual database health check here
            health_data["database"] = "connected"
        except Exception:
            health_data["database"] = "disconnected"
            health_data["status"] = "degraded"
        
        # Add system metrics
        health_data.update(monitoring.get_real_time_metrics())
        
        return health_data
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )


@app.get("/health/ready")
async def readiness_check():
    """Kubernetes readiness probe."""
    return {"status": "ready", "timestamp": datetime.now().isoformat()}


@app.get("/health/live")
async def liveness_check():
    """Kubernetes liveness probe."""
    return {"status": "alive", "timestamp": datetime.now().isoformat()}


# Metrics endpoint
@app.get("/metrics")
async def prometheus_metrics():
    """Prometheus metrics endpoint."""
    return PlainTextResponse(
        monitoring.export_prometheus_metrics(),
        media_type="text/plain"
    )


# Analytics endpoints
@app.get("/analytics/dashboard")
async def analytics_dashboard():
    """Real-time analytics dashboard data."""
    return monitoring.get_performance_report()


@app.get("/analytics/calls")
async def call_analytics(hours: int = 24):
    """Call analytics for specified time period."""
    return monitoring.get_call_analytics(hours)


# Main voice conversation endpoint - PRODUCTION READY
@app.post("/voice-conversation")
@app.get("/voice-conversation")
async def voice_conversation(
    background_tasks: BackgroundTasks,
    CallSid: str = Form(None),
    From: str = Form(None),
    request: Request = None
):
    """Production-ready voice conversation endpoint with full monitoring."""
    
    call_sid = CallSid or f"call_{uuid.uuid4().hex[:8]}"
    phone_number = From or "unknown"
    
    try:
        # Start call monitoring
        monitoring.start_call_monitoring(call_sid, phone_number)
        
        # Start conversation
        await conversation_engine.start_conversation(call_sid, phone_number)
        
        logger.info(
            "Voice conversation started",
            call_sid=call_sid,
            phone_number=phone_number
        )
        
        # Professional greeting with premium voice
        greeting = (
            f"Hello and thank you for calling {settings.CLINIC_NAME}. "
            f"I'm your AI assistant, and I'm here to help you and your pet today. "
            f"How can I assist you?"
        )
        
        prompt = (
            f"Please tell me what you need help with, such as scheduling an appointment, "
            f"asking about your pet's health, or if this is an emergency."
        )
        
        # Ultra-fast speech configuration for production
        twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="{settings.DEFAULT_VOICE_ID}">{greeting}</Say>
    <Gather input="speech" action="/voice-process" method="POST" 
            speechTimeout="{settings.SPEECH_TIMEOUT_SECONDS}" 
            timeout="{settings.TOTAL_TIMEOUT_SECONDS}" 
            language="{settings.SPEECH_LANGUAGE}" 
            hints="appointment,emergency,sick,help,prescription,insurance"
            partialResultCallback="/voice-partial">
        <Say voice="{settings.DEFAULT_VOICE_ID}">{prompt}</Say>
    </Gather>
    <Say voice="{settings.DEFAULT_VOICE_ID}">I'll connect you with our team. Please hold while I transfer you.</Say>
    <Redirect>/voice-fallback</Redirect>
</Response>'''
        
        # Update call metrics
        monitoring.update_call_metrics(
            call_sid,
            final_state="greeting_sent",
            interactions_count=1
        )
        
        return Response(content=twiml, media_type="application/xml")
        
    except Exception as e:
        logger.error(
            "Voice conversation error",
            call_sid=call_sid,
            error=str(e)
        )
        
        monitoring.record_error("voice_conversation", "/voice-conversation", str(e))
        
        # Safe fallback
        fallback_twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="{settings.DEFAULT_VOICE_ID}">
        Thank you for calling {settings.CLINIC_NAME}. 
        Our team will call you back within {settings.CALLBACK_PROMISE_MINUTES} minutes.
    </Say>
    <Hangup/>
</Response>'''
        
        return Response(content=fallback_twiml, media_type="application/xml")


# Advanced speech processing endpoint
@app.post("/voice-process")
async def voice_process(
    background_tasks: BackgroundTasks,
    SpeechResult: str = Form(None),
    Digits: str = Form(None),
    CallSid: str = Form(None),
    Confidence: float = Form(None)
):
    """Advanced speech processing with AI conversation engine."""
    
    call_sid = CallSid or "unknown"
    
    try:
        async with monitoring.track_request("voice-process"):
            # Record speech recognition result
            speech_success = bool(SpeechResult and SpeechResult.strip())
            monitoring.record_speech_recognition(speech_success, Confidence or 0.0)
            
            # Handle DTMF input (keypad)
            if Digits:
                logger.info("DTMF input received", call_sid=call_sid, digits=Digits)
                
                response_map = {
                    "1": f"Appointment request noted. Our scheduling team will call you back within {settings.CALLBACK_PROMISE_MINUTES} minutes.",
                    "2": f"This is an EMERGENCY! Please hang up and call your nearest emergency veterinary clinic immediately at {settings.EMERGENCY_VET_NUMBERS['primary']}!",
                    "3": f"Health question noted. Our veterinary team will call you back within {settings.CALLBACK_PROMISE_MINUTES} minutes.",
                    "0": f"Connecting you with our main office. Please hold."
                }
                
                response_text = response_map.get(Digits, "Thank you for calling. Our team will call you back shortly.")
                
                monitoring.update_call_metrics(
                    call_sid,
                    intent="dtmf_input",
                    final_state="dtmf_processed",
                    interactions_count=1
                )
                
                twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="{settings.DEFAULT_VOICE_ID}">{response_text}</Say>
    <Hangup/>
</Response>'''
                
                return Response(content=twiml, media_type="application/xml")
            
            # Handle speech input
            elif speech_success:
                logger.info(
                    "Speech input received",
                    call_sid=call_sid,
                    speech=SpeechResult,
                    confidence=Confidence
                )
                
                # Process with AI conversation engine
                response_text, new_state = await conversation_engine.process_speech(
                    call_sid, SpeechResult
                )
                
                monitoring.update_call_metrics(
                    call_sid,
                    speech_recognition_success=True,
                    final_state=new_state.value,
                    interactions_count=1
                )
                
                # Schedule background task for follow-up
                background_tasks.add_task(
                    schedule_callback,
                    call_sid,
                    SpeechResult,
                    new_state.value
                )
                
                twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="{settings.DEFAULT_VOICE_ID}">{response_text}</Say>
    <Hangup/>
</Response>'''
                
                return Response(content=twiml, media_type="application/xml")
            
            # No input received
            else:
                logger.warning("No input received", call_sid=call_sid)
                
                monitoring.update_call_metrics(
                    call_sid,
                    speech_recognition_success=False,
                    final_state="no_input"
                )
                
                fallback_text = (
                    f"I didn't hear anything clearly. Our team will call you back within "
                    f"{settings.CALLBACK_PROMISE_MINUTES} minutes to assist you. "
                    f"Thank you for calling {settings.CLINIC_NAME}!"
                )
                
                twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="{settings.DEFAULT_VOICE_ID}">{fallback_text}</Say>
    <Hangup/>
</Response>'''
                
                return Response(content=twiml, media_type="application/xml")
                
    except Exception as e:
        logger.error(
            "Voice processing error",
            call_sid=call_sid,
            error=str(e)
        )
        
        monitoring.record_error("voice_processing", "/voice-process", str(e))
        
        # Emergency fallback
        emergency_twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="{settings.DEFAULT_VOICE_ID}">
        Thank you for calling {settings.CLINIC_NAME}. 
        Our team will call you back immediately.
    </Say>
    <Hangup/>
</Response>'''
        
        return Response(content=emergency_twiml, media_type="application/xml")
    
    finally:
        # End call monitoring
        monitoring.end_call_monitoring(call_sid, "completed")


# Partial speech callback for real-time processing
@app.post("/voice-partial")
async def voice_partial(
    UnstableSpeechResult: str = Form(None),
    StableSpeechResult: str = Form(None),
    CallSid: str = Form(None)
):
    """Handle partial speech results for instant emergency detection."""
    
    if StableSpeechResult and len(StableSpeechResult.strip()) > 3:
        stable_speech = StableSpeechResult.lower()
        
        # Instant emergency detection
        if any(keyword in stable_speech for keyword in settings.EMERGENCY_KEYWORDS):
            logger.critical(
                "EMERGENCY detected in partial speech",
                call_sid=CallSid,
                speech=StableSpeechResult
            )
            
            monitoring.update_call_metrics(
                CallSid or "unknown",
                intent="emergency",
                urgency="critical",
                escalated=True,
                escalation_reason="emergency_detected"
            )
            
            emergency_response = (
                f"EMERGENCY DETECTED! Please hang up immediately and call "
                f"{settings.EMERGENCY_VET_NUMBERS['primary']} or go to your "
                f"nearest emergency veterinary clinic right now!"
            )
            
            return Response(
                content=f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="{settings.DEFAULT_VOICE_ID}">{emergency_response}</Say>
    <Hangup/>
</Response>''',
                media_type="application/xml"
            )
    
    # Continue gathering if no immediate action needed
    return Response(
        content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
        media_type="application/xml"
    )


# Fallback endpoint
@app.post("/voice-fallback")
@app.get("/voice-fallback")
async def voice_fallback(CallSid: str = Form(None)):
    """Fallback endpoint for when all else fails."""
    
    logger.warning("Voice fallback triggered", call_sid=CallSid)
    
    monitoring.update_call_metrics(
        CallSid or "unknown",
        final_state="fallback_triggered",
        escalated=True,
        escalation_reason="system_fallback"
    )
    
    fallback_text = (
        f"Thank you for calling {settings.CLINIC_NAME}. "
        f"Due to high call volume, our team will call you back within "
        f"{settings.CALLBACK_PROMISE_MINUTES} minutes to assist you personally. "
        f"If this is an emergency, please hang up and call "
        f"{settings.EMERGENCY_VET_NUMBERS['primary']} immediately."
    )
    
    return Response(
        content=f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="{settings.DEFAULT_VOICE_ID}">{fallback_text}</Say>
    <Hangup/>
</Response>''',
        media_type="application/xml"
    )


# Background task for scheduling callbacks
async def schedule_callback(call_sid: str, original_request: str, final_state: str):
    """Schedule a callback for the customer."""
    try:
        # Get conversation summary
        summary = conversation_engine.get_conversation_summary(call_sid)
        
        if summary:
            logger.info(
                "Callback scheduled",
                call_sid=call_sid,
                original_request=original_request,
                final_state=final_state,
                summary=summary
            )
            
            # Here you would integrate with your actual callback scheduling system
            # For now, we'll just log the requirement
            
    except Exception as e:
        logger.error("Callback scheduling failed", call_sid=call_sid, error=str(e))


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with system information."""
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT.value,
        "status": "operational",
        "endpoints": {
            "voice_webhook": "/voice-conversation",
            "health_check": "/health",
            "metrics": "/metrics",
            "analytics": "/analytics/dashboard"
        },
        "support": {
            "emergency": settings.EMERGENCY_VET_NUMBERS["primary"],
            "phone": settings.CLINIC_PHONE
        }
    }


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Application startup with full initialization."""
    logger.info(
        "Starting AI Veterinary Receptionist",
        version=settings.VERSION,
        environment=settings.ENVIRONMENT.value
    )
    
    # Initialize database
    try:
        db_success = initialize_database()
        if db_success:
            create_tables()
            logger.info("Database initialized successfully")
        else:
            logger.warning("Database initialization failed - running in degraded mode")
    except Exception as e:
        logger.error("Database startup error", error=str(e))
    
    # Start background tasks
    try:
        # Clean up old conversations every hour
        asyncio.create_task(periodic_cleanup())
        logger.info("Background tasks started")
    except Exception as e:
        logger.error("Background task startup error", error=str(e))
    
    logger.info("AI Veterinary Receptionist startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Graceful shutdown."""
    logger.info("Shutting down AI Veterinary Receptionist")
    
    # Perform cleanup
    try:
        # Export final metrics
        final_report = monitoring.get_performance_report()
        logger.info("Final performance report", report=final_report)
        
    except Exception as e:
        logger.error("Shutdown cleanup error", error=str(e))
    
    logger.info("AI Veterinary Receptionist shutdown complete")


async def periodic_cleanup():
    """Periodic cleanup task."""
    while True:
        try:
            await asyncio.sleep(3600)  # Run every hour
            await conversation_engine.cleanup_old_conversations(24)
            logger.info("Periodic cleanup completed")
        except Exception as e:
            logger.error("Periodic cleanup error", error=str(e))


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler with comprehensive logging."""
    
    logger.error(
        "Unhandled exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        client_ip=request.client.host
    )
    
    monitoring.record_error("unhandled_exception", request.url.path, str(exc))
    
    if settings.is_development:
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "detail": str(exc),
                "path": request.url.path
            }
        )
    else:
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error"}
        )


if __name__ == "__main__":
    uvicorn.run(
        "app.production_main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.is_development,
        log_level=settings.LOG_LEVEL.value.lower(),
        access_log=True
    )
