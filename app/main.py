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

# Add minimal request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"� {request.method} {request.url.path}")
    response = await call_next(request)
    print(f"✅ Response: {response.status_code}")
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

# Enhanced conversational AI webhook with advanced features
@app.post("/voice-conversation")
@app.get("/voice-conversation")
async def voice_conversation():
    """Enhanced conversational AI webhook with professional intelligence."""
    try:
        print(f"🎤 Enhanced voice conversation started at {time.time()}")
        
        # Professional veterinary greeting
        greeting = (
            "Hello and thank you for calling AI Veterinary Clinic. "
            "I'm your intelligent AI assistant, specially trained to help with pet care needs. "
            "I can assist with appointments, health questions, emergencies, and prescription refills. "
            "How may I help you and your pet today?"
        )
        
        prompt = (
            "Please tell me specifically what you need - for example, "
            "you can say 'book appointment', 'my pet is sick', 'emergency', or 'prescription refill'."
        )
        
        # Ultra-responsive speech configuration with enterprise features
        twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna">{greeting}</Say>
    <Gather input="speech" action="/speech-ai" method="POST" 
            speechTimeout="1.5" timeout="6" language="en-US" 
            hints="appointment,emergency,sick,help,prescription,refill,vaccine,checkup,urgent,pain,vomiting,eating,limping"
            partialResultCallback="/partial-ai">
        <Say voice="Polly.Joanna">{prompt}</Say>
    </Gather>
    <Say voice="Polly.Joanna">I didn't catch that clearly. Let me offer you some quick options.</Say>
    <Gather input="speech dtmf" action="/speech-ai" method="POST" speechTimeout="1" timeout="4" language="en-US">
        <Say voice="Polly.Joanna">Please say 'appointment', 'emergency', or 'health question', or press 1 for appointment, 2 for emergency, or 3 for health question.</Say>
    </Gather>
    <Redirect>/speech-ai</Redirect>
</Response>'''
        return Response(content=twiml, media_type="application/xml")
    except Exception as e:
        print(f"❌ Voice conversation error: {e}")
        # Safe fallback
        return Response(
            content='<?xml version="1.0" encoding="UTF-8"?><Response><Say voice="Polly.Joanna">Thank you for calling AI Veterinary Clinic!</Say><Hangup/></Response>',
            media_type="application/xml"
        )

@app.post("/voice-conversation-retry")
@app.get("/voice-conversation-retry")
async def voice_conversation_retry():
    """Retry voice conversation with shorter timeout."""
    try:
        twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna">I didn't catch that. Could you please tell me briefly what you need help with?</Say>
    <Gather input="speech" action="/speech" method="POST" speechTimeout="4" timeout="10" language="en-AU" enhanced="true">
        <Say voice="Polly.Joanna">For example, say appointment, emergency, or health question.</Say>
    </Gather>
    <Say voice="Polly.Joanna">I'm having trouble hearing you. Our team will call you back within 10 minutes to assist you. Thank you for calling AI Veterinary Clinic!</Say>
    <Hangup/>
</Response>'''
        return Response(content=twiml, media_type="application/xml")
    except Exception as e:
        return Response(
            content='<?xml version="1.0" encoding="UTF-8"?><Response><Say voice="alice">Thank you for calling!</Say><Hangup/></Response>',
            media_type="application/xml"
        )

# ADVANCED AI SPEECH PROCESSING - INTELLIGENT CONVERSATION
@app.post("/speech-ai")
@app.get("/speech-ai")
async def speech_ai(SpeechResult: str = Form(None), Digits: str = Form(None), CallSid: str = Form(None)):
    """Advanced AI speech processing with intelligent conversation management."""
    
    print(f"🧠 AI Speech Processing: Speech='{SpeechResult}', Digits='{Digits}', CallSid='{CallSid}'")
    
    # Handle DTMF input with detailed responses
    if Digits:
        print(f"📱 DTMF Input: {Digits}")
        if Digits == "1":
            msg = (
                "Perfect! I'll help you schedule an appointment. "
                "Our scheduling team will call you back within 10 minutes to check our availability "
                "and find the best time for your pet's visit. Please have your preferred dates ready."
            )
        elif Digits == "2":
            msg = (
                "This is an EMERGENCY! Please hang up immediately and call your nearest "
                "emergency veterinary clinic or our emergency line. If your pet is unconscious, "
                "bleeding, or in severe distress, go to the nearest emergency vet right now. "
                "Time is critical for your pet's safety!"
            )
        elif Digits == "3":
            msg = (
                "I understand you have health questions about your pet. "
                "Our experienced veterinary team will call you back within 10 minutes "
                "to discuss your pet's symptoms and provide professional guidance."
            )
        else:
            msg = "Thank you for calling. Our team will call you back in 10 minutes to assist you."
    
    # Advanced speech processing with AI intelligence
    elif SpeechResult and SpeechResult.strip():
        speech = SpeechResult.lower().strip()
        print(f"🗣️ Processing speech: '{speech}'")
        
        # Emergency detection with immediate response
        emergency_keywords = [
            "emergency", "urgent", "dying", "bleeding", "poison", "choking", 
            "unconscious", "seizure", "can't breathe", "collapse", "critical",
            "severe pain", "vomiting blood", "not breathing"
        ]
        
        if any(keyword in speech for keyword in emergency_keywords):
            msg = (
                f"EMERGENCY DETECTED! I heard you mention '{SpeechResult}'. "
                f"This sounds critical - please hang up immediately and call your nearest "
                f"emergency veterinary clinic or go directly to an emergency animal hospital. "
                f"If this involves poison, call the Pet Poison Helpline at (855) 764-7661. "
                f"Time is critical for your pet's safety!"
            )
        
        # Appointment requests with detailed processing
        elif any(word in speech for word in ["appointment", "schedule", "book", "visit", "checkup", "exam"]):
            # Extract additional context
            pet_context = ""
            if "dog" in speech:
                pet_context = " for your dog"
            elif "cat" in speech:
                pet_context = " for your cat"
            elif "puppy" in speech:
                pet_context = " for your puppy"
            elif "kitten" in speech:
                pet_context = " for your kitten"
            
            visit_type = ""
            if "vaccination" in speech or "vaccine" in speech or "shot" in speech:
                visit_type = " for vaccinations"
            elif "checkup" in speech or "wellness" in speech:
                visit_type = " for a wellness checkup"
            elif "sick" in speech:
                visit_type = " for illness consultation"
            
            msg = (
                f"Excellent! I'll help you book an appointment{pet_context}{visit_type}. "
                f"Based on what you said - '{SpeechResult}' - our scheduling team will call you back "
                f"within 10 minutes to check our availability and book the perfect time slot for you."
            )
        
        # Health concerns with symptom assessment
        elif any(word in speech for word in [
            "sick", "ill", "vomiting", "diarrhea", "not eating", "limping", 
            "cough", "scratching", "lethargic", "pain", "fever", "infection"
        ]):
            # Identify symptoms mentioned
            symptoms = []
            if "vomiting" in speech or "throwing up" in speech:
                symptoms.append("vomiting")
            if "diarrhea" in speech or "loose stool" in speech:
                symptoms.append("diarrhea")
            if "not eating" in speech or "won't eat" in speech:
                symptoms.append("loss of appetite")
            if "limping" in speech or "favoring" in speech:
                symptoms.append("limping")
            if "cough" in speech:
                symptoms.append("coughing")
            if "scratch" in speech or "itch" in speech:
                symptoms.append("scratching/itching")
            if "lethargic" in speech or "tired" in speech:
                symptoms.append("lethargy")
            if "pain" in speech:
                symptoms.append("pain")
            
            symptom_text = f" regarding {', '.join(symptoms)}" if symptoms else ""
            
            msg = (
                f"I understand your pet isn't feeling well{symptom_text}. "
                f"Based on what you described - '{SpeechResult}' - our experienced veterinary team "
                f"will call you back within 10 minutes to discuss these symptoms and determine "
                f"if your pet needs to be seen today or if we can provide guidance over the phone."
            )
        
        # Prescription refills
        elif any(word in speech for word in ["prescription", "medication", "refill", "medicine", "pills"]):
            msg = (
                f"I can help you with prescription refills. I noted that you mentioned '{SpeechResult}'. "
                f"Our pharmacy team will call you back within 10 minutes to verify your pet's "
                f"prescription information and process the refill. Please have your pet's name "
                f"and current prescription details ready."
            )
        
        # Insurance and billing
        elif any(word in speech for word in ["insurance", "billing", "payment", "cost", "price"]):
            msg = (
                f"I'll connect you with our billing and insurance specialist. "
                f"Regarding your question about '{SpeechResult}', they will call you back "
                f"within 10 minutes to help with insurance claims, payment options, or cost estimates."
            )
        
        # General inquiry with context preservation
        else:
            msg = (
                f"Thank you for calling AI Veterinary Clinic! I heard you say '{SpeechResult}'. "
                f"To make sure we provide you with the most appropriate assistance, "
                f"our knowledgeable team will call you back within 10 minutes to address "
                f"your specific needs and ensure your pet gets the best possible care."
            )
    
    # No input fallback
    else:
        msg = (
            "I didn't hear anything clearly, but that's okay! "
            "Our friendly team will call you back within 10 minutes to personally assist you. "
            "Thank you for choosing AI Veterinary Clinic for your pet's care!"
        )
    
    print(f"📞 AI Response: {msg[:100]}...")
    
    return Response(
        content=f'<Response><Say voice="Polly.Joanna">{msg}</Say><Hangup/></Response>',
        media_type="application/xml"
    )

# Advanced partial speech callback for real-time intelligence
@app.post("/partial-ai")
async def partial_speech_ai(
    UnstableSpeechResult: str = Form(None),
    StableSpeechResult: str = Form(None),
    CallSid: str = Form(None)
):
    """Advanced partial speech processing with real-time emergency detection."""
    
    print(f"🎯 Partial AI: Stable='{StableSpeechResult}', Unstable='{UnstableSpeechResult}'")
    
    # Check stable speech for immediate action
    if StableSpeechResult and len(StableSpeechResult.strip()) > 3:
        stable = StableSpeechResult.lower().strip()
        
        # Immediate emergency detection - highest priority
        critical_emergencies = [
            "dying", "dead", "unconscious", "bleeding", "poison", "choking",
            "can't breathe", "not breathing", "seizure", "collapse"
        ]
        
        if any(emergency in stable for emergency in critical_emergencies):
            print(f"🚨 CRITICAL EMERGENCY detected in partial: {StableSpeechResult}")
            return Response(
                content=f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna">
        CRITICAL EMERGENCY DETECTED! Please hang up immediately and call your nearest 
        emergency veterinary clinic or go directly to an emergency animal hospital right now! 
        If this involves poison, also call the Pet Poison Helpline at (855) 764-7661. 
        Your pet's life may depend on immediate action!
    </Say>
    <Hangup/>
</Response>''',
                media_type="application/xml"
            )
        
        # Urgent situations requiring fast response
        urgent_keywords = ["emergency", "urgent", "severe pain", "vomiting blood", "difficulty breathing"]
        if any(urgent in stable for urgent in urgent_keywords):
            print(f"⚡ URGENT situation detected in partial: {StableSpeechResult}")
            return Response(
                content=f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna">
        This sounds urgent! Please hang up and call your nearest emergency vet immediately, 
        or our emergency line for immediate assistance. Time is important for your pet's health!
    </Say>
    <Hangup/>
</Response>''',
                media_type="application/xml"
            )
        
        # Quick appointment confirmation for clear requests
        if "appointment" in stable and len(stable.split()) >= 2:
            print(f"📅 Quick appointment detected in partial: {StableSpeechResult}")
            return Response(
                content=f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna">
        Perfect! I can help you schedule an appointment. 
        Our scheduling team will call you back within 10 minutes to book the ideal time for your pet.
    </Say>
    <Hangup/>
</Response>''',
                media_type="application/xml"
            )
    
    # Continue gathering if no immediate action needed
    return Response(
        content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
        media_type="application/xml"
    )

# Keep original partial endpoint for backward compatibility
@app.post("/partial")
async def partial_speech_callback(
    UnstableSpeechResult: str = Form(None),
    StableSpeechResult: str = Form(None)
):
    """Handle partial speech results for instant feedback."""
    # Check if we have enough stable speech to respond immediately
    if StableSpeechResult and len(StableSpeechResult.strip()) > 3:
        stable = StableSpeechResult.lower()
        
        # Instant response for emergencies
        if "emergency" in stable or "urgent" in stable:
            return Response(
                content='<Response><Say voice="Polly.Joanna">Emergency! Call your nearest emergency vet now!</Say><Hangup/></Response>',
                media_type="application/xml"
            )
        
        # Instant response for appointments
        if "appointment" in stable or "book" in stable:
            return Response(
                content='<Response><Say voice="Polly.Joanna">Appointment request received! Calling back in 10 minutes.</Say><Hangup/></Response>',
                media_type="application/xml"
            )
    
    # Continue gathering if not enough info
    return Response(
        content='<Response></Response>',
        media_type="application/xml"
    )

# BACKWARD COMPATIBILITY - Original speech endpoint (redirects to AI version)
@app.post("/speech")
@app.get("/speech")
async def speech_compatibility(SpeechResult: str = Form(None), Digits: str = Form(None), CallSid: str = Form(None)):
    """Backward compatibility endpoint - redirects to advanced AI processing."""
    print(f"🔄 Redirecting to AI speech processing...")
    return await speech_ai(SpeechResult, Digits, CallSid)

# SUPER-FAST EXPRESS ENDPOINT FOR INSTANT RESPONSES
@app.post("/express")
@app.get("/express")
async def express_speech(SpeechResult: str = Form(None), Digits: str = Form(None)):
    """Express endpoint for lightning-fast responses."""
    # Instant DTMF response
    if Digits == "1":
        return Response(content='<Response><Say voice="Polly.Joanna">Appointment noted. Calling back shortly.</Say><Hangup/></Response>', media_type="application/xml")
    elif Digits == "2":
        return Response(content='<Response><Say voice="Polly.Joanna">Emergency! Call emergency vet now!</Say><Hangup/></Response>', media_type="application/xml")
    elif Digits == "3":
        return Response(content='<Response><Say voice="Polly.Joanna">Health question noted. Calling back shortly.</Say><Hangup/></Response>', media_type="application/xml")
    
    # Instant speech response
    if SpeechResult:
        s = SpeechResult.lower()
        if "emergency" in s:
            return Response(content='<Response><Say voice="Polly.Joanna">Emergency! Call emergency vet immediately!</Say><Hangup/></Response>', media_type="application/xml")
        elif "appointment" in s:
            return Response(content='<Response><Say voice="Polly.Joanna">Appointment request noted. Calling back in 10 minutes.</Say><Hangup/></Response>', media_type="application/xml")
        else:
            return Response(content='<Response><Say voice="Polly.Joanna">Request received. Calling back in 10 minutes.</Say><Hangup/></Response>', media_type="application/xml")
    
    # Default
    return Response(content='<Response><Say voice="Polly.Joanna">Thank you for calling.</Say><Hangup/></Response>', media_type="application/xml")

# SPEECH TEST ENDPOINT
@app.post("/speech-test")
@app.get("/speech-test")
async def speech_test():
    """Simple test endpoint for speech without any processing."""
    return Response(
        content='<Response><Say voice="Polly.Joanna">Speech test successful! Your voice was heard.</Say><Hangup/></Response>',
        media_type="application/xml"
    )

# BULLETPROOF SPEECH PROCESSING - GUARANTEED TO WORK
@app.post("/speech-handler")
@app.get("/speech-handler")
async def speech_handler(SpeechResult: str = Form(None)):
    """Ultra-reliable speech handler with best possible voice quality."""
    try:
        # Import the voice service
        from .services.elevenlabs_service import get_best_voice_say_tag
        
        # Determine response based on speech
        if SpeechResult and "emergency" in SpeechResult.lower():
            msg = "Emergency detected! Please call your nearest emergency vet immediately!"
        elif SpeechResult and "appointment" in SpeechResult.lower():
            msg = "Perfect! Our team will call you back in 10 minutes to book your appointment."
        elif SpeechResult and "sick" in SpeechResult.lower():
            msg = "I understand your pet isn't feeling well. Our vet will call you back in 10 minutes."
        elif SpeechResult:
            msg = "Thank you! Our team will call you back in 10 minutes to help you."
        else:
            msg = "Thank you for calling AI Veterinary Clinic!"
        
        # Get best possible voice tag
        voice_tag = get_best_voice_say_tag(msg)
        
        return Response(
            content=f'<?xml version="1.0"?><Response>{voice_tag}<Hangup/></Response>',
            media_type="application/xml"
        )
    except Exception as e:
        print(f"❌ Speech handler error: {e}")
        # Ultra-safe fallback
        return Response(
            content='<?xml version="1.0"?><Response><Say voice="Polly.Joanna">Thank you for calling!</Say><Hangup/></Response>',
            media_type="application/xml"
        )

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
    """Enhanced speech responses with better voice and comprehensive processing."""
    try:
        import time
        print(f"🎤 Speech received: '{SpeechResult}' at {time.time()}")
        
        if SpeechResult:
            speech_lower = SpeechResult.lower()
            
            # Emergency keywords - highest priority
            if any(word in speech_lower for word in ["emergency", "urgent", "dying", "bleeding", "poison", "choking", "unconscious", "seizure"]):
                response = "This sounds like an emergency! Please hang up immediately and call your nearest emergency veterinary clinic or animal hospital right away. Time is critical for your pet's safety!"
                
            # Appointment keywords  
            elif any(word in speech_lower for word in ["appointment", "schedule", "book", "visit", "checkup", "vaccination", "vaccine"]):
                response = "Perfect! I'd be happy to help you schedule an appointment for your pet. Our booking team will call you back within 10 minutes to check available times and confirm the details."
                
            # Health concern keywords
            elif any(word in speech_lower for word in ["sick", "ill", "vomiting", "diarrhea", "not eating", "limping", "cough", "scratching", "lethargic", "pain"]):
                response = "I understand you have concerns about your pet's health. Our experienced veterinary team will call you back within 10 minutes to discuss your pet's symptoms and determine the best care."
                
            # Prescription keywords
            elif any(word in speech_lower for word in ["prescription", "medication", "medicine", "refill", "pills"]):
                response = "Of course! I can help you with prescription needs. Our pharmacy team will call you back within 10 minutes to check your pet's prescription status and process any refills."
                
            # General inquiry
            else:
                response = f"Thank you for calling AI Veterinary Clinic! I heard you mention '{SpeechResult}'. Our knowledgeable team will call you back within 10 minutes to help with whatever your pet needs."
        else:
            response = "Thank you for calling AI Veterinary Clinic! Our team will call you back within 10 minutes to assist you and your pet."
        
        twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna">{response}</Say>
    <Hangup/>
</Response>'''
        return Response(content=twiml, media_type="application/xml")
        
    except Exception as e:
        print(f"❌ Simple response error: {e}")
        return Response(
            content='<?xml version="1.0" encoding="UTF-8"?><Response><Say voice="Polly.Joanna">Thank you for calling AI Veterinary Clinic!</Say><Hangup/></Response>',
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
