"""Voice API endpoints for handling Twilio webhooks and voice processing."""

from fastapi import APIRouter, Request, Depends, HTTPException, Form, File, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import io
from datetime import datetime

from ..core.database import get_db
from ..services.twilio_service import TwilioService
from ..services.voice_processor import VoiceProcessor
from ..services.llm_service import LLMService
from ..services.appointment_service import AppointmentService
from ..services.prescription_service import PrescriptionRefillService
from ..services.emergency_service import EmergencyTriageService
from ..services.insurance_service import InsuranceVerificationService
from ..models.clinic import Clinic
from ..models.call_log import CallLog

router = APIRouter()

# Initialize services
twilio_service = TwilioService()
voice_processor = VoiceProcessor()
llm_service = LLMService()


@router.post("/webhook")
async def voice_webhook(
    request: Request,
    db: Session = Depends(get_db),
    CallSid: str = Form(...),
    From: str = Form(...),
    To: str = Form(...),
    CallStatus: str = Form(...),
    SpeechResult: Optional[str] = Form(None),
    Confidence: Optional[float] = Form(None)
):
    """Handle incoming Twilio voice webhooks with optimized response time."""
    
    try:
        # Fast response for Twilio - handle core logic first
        if CallStatus == "ringing":
            # Quick clinic lookup with timeout protection
            try:
                clinic = db.query(Clinic).filter(Clinic.phone_number == To).first()
                if not clinic:
                    # Fast fallback response
                    twiml = twilio_service.create_hangup_response(
                        "I'm sorry, this number is not configured for voice services."
                    )
                    return Response(content=twiml, media_type="application/xml")
                
                # Create minimal call log entry quickly
                call_log = CallLog(
                    clinic_id=clinic.id,
                    twilio_call_sid=CallSid,
                    caller_phone=From,
                    call_status=CallStatus,
                    call_direction="inbound",
                    call_started_at=datetime.utcnow()
                )
                db.add(call_log)
                db.commit()
                
                # Quick greeting response
                greeting = clinic.voice_greeting or f"Hello! Thank you for calling {clinic.name}. How can I help you today?"
                twiml = twilio_service.create_gather_response(
                    greeting,
                    f"/api/voice/process?call_sid={CallSid}"
                )
                
            except Exception as e:
                print(f"❌ Database error in webhook: {e}")
                # Fallback response without database
                twiml = twilio_service.create_gather_response(
                    "Hello! Thank you for calling. How can I help you today?",
                    f"/api/voice/process?call_sid={CallSid}"
                )
            
        elif SpeechResult:
            # For speech processing, use the lightweight process endpoint
            twiml = await process_speech_lightweight(
                speech_text=SpeechResult,
                call_sid=CallSid,
                db=db
            )
            
        else:
            # Fallback response
            twiml = twilio_service.create_gather_response(
                "I'm sorry, I didn't understand. Could you please repeat that?",
                f"/api/voice/process?call_sid={CallSid}"
            )
        
        return Response(content=twiml, media_type="application/xml")
        
    except Exception as e:
        print(f"❌ Critical error in webhook: {e}")
        # Emergency fallback response
        emergency_twiml = twilio_service.create_hangup_response(
            "I apologize, but I'm experiencing technical difficulties. Please call back in a moment or try our emergency line."
        )
        return Response(content=emergency_twiml, media_type="application/xml")


async def process_speech_lightweight(
    speech_text: str,
    call_sid: str,
    db: Session
) -> str:
    """Lightweight speech processing for fast webhook response."""
    
    try:
        # Quick database lookup with timeout protection
        call_log = db.query(CallLog).filter(CallLog.twilio_call_sid == call_sid).first()
        if not call_log:
            return twilio_service.create_hangup_response("Session expired. Please call back.")
        
        # Basic response without heavy LLM processing
        if any(word in speech_text.lower() for word in ["emergency", "urgent", "help", "dying"]):
            # Emergency response
            response_text = "This sounds urgent. Let me connect you with our emergency service right away. Please hold."
            twiml = twilio_service.create_hangup_response(response_text)
        elif any(word in speech_text.lower() for word in ["appointment", "book", "schedule"]):
            # Appointment response
            response_text = "I'd be happy to help you schedule an appointment. Let me connect you with our booking system."
            twiml = twilio_service.create_gather_response(
                response_text,
                f"/api/voice/process?call_sid={call_sid}"
            )
        else:
            # General response
            response_text = "I understand. Let me help you with that. One moment please."
            twiml = twilio_service.create_gather_response(
                response_text,
                f"/api/voice/process?call_sid={call_sid}"
            )
        
        # Quick transcript update
        call_log.transcript = f"{call_log.transcript or ''}\nUser: {speech_text}\nAI: {response_text}"
        db.commit()
        
        return twiml
        
    except Exception as e:
        print(f"❌ Error in lightweight processing: {e}")
        # Fallback response
        return twilio_service.create_gather_response(
            "I'm here to help. Could you please tell me what you need?",
            f"/api/voice/process?call_sid={call_sid}"
        )


@router.post("/process")
async def process_speech(
    call_sid: str,
    db: Session = Depends(get_db),
    SpeechResult: str = Form(...),
    Confidence: Optional[float] = Form(None)
):
    """Process speech input from Twilio with full AI processing."""
    
    # Get call log and clinic
    call_log = db.query(CallLog).filter(CallLog.twilio_call_sid == call_sid).first()
    if not call_log:
        twiml = twilio_service.create_hangup_response("Session expired. Please call back.")
        return Response(content=twiml, media_type="application/xml")
    
    clinic = db.query(Clinic).filter(Clinic.id == call_log.clinic_id).first()
    
    # Process the speech with full AI capabilities
    twiml = await process_speech_input(
        speech_text=SpeechResult,
        call_sid=call_sid,
        clinic=clinic,
        call_log=call_log,
        db=db
    )
    
    return Response(content=twiml, media_type="application/xml")


async def process_speech_input(
    speech_text: str,
    call_sid: str,
    clinic: Clinic,
    call_log: CallLog,
    db: Session
) -> str:
    """Process speech input and generate appropriate response with advanced features."""
    
    # Initialize advanced services
    prescription_service = PrescriptionRefillService(db)
    emergency_service = EmergencyTriageService()
    insurance_service = InsuranceVerificationService()
    
    # Build conversation history from call log
    conversation_history = []
    if call_log.transcript:
        conversation_history = [
            {"role": "assistant", "content": "Hello! How can I help you today?"},
            {"role": "user", "content": call_log.transcript}
        ]
    
    # 🚨 PRIORITY 1: Emergency Detection
    emergency_assessment = await emergency_service.assess_emergency_level(speech_text)
    
    if emergency_assessment["level"].value in ["critical", "urgent"]:
        # Update call log with emergency status
        call_log.intent_detected = "emergency"
        call_log.confidence_score = emergency_assessment["confidence"]
        
        response_text = emergency_service.generate_emergency_response(emergency_assessment)
        
        # For critical emergencies, immediate transfer
        if await emergency_service.should_transfer_immediately(emergency_assessment):
            twiml = twilio_service.create_hangup_response(
                f"{response_text} I'm connecting you with our emergency veterinarian right now. Please hold."
            )
            db.commit()
            return twiml
    
    # 💊 PRIORITY 2: Prescription Refill Detection
    refill_intent = await prescription_service.detect_refill_intent(speech_text)
    
    if refill_intent["is_refill_request"]:
        # Process refill request
        # Extract pet name and medication from speech
        entities = await llm_service._extract_entities(speech_text)
        
        # Try to process refill if we have enough information
        if entities.get("potential_names") and refill_intent.get("potential_medications"):
            refill_result = await prescription_service.process_refill_request(
                pet_name=entities["potential_names"][0],
                owner_phone=call_log.caller_phone,
                medication_name=refill_intent["potential_medications"][0],
                clinic_id=clinic.id
            )
            
            response_text = prescription_service.generate_refill_response(refill_result)
            call_log.intent_detected = "prescription_refill"
        else:
            response_text = "I'd be happy to help with a prescription refill. Could you please tell me your pet's name and which medication you need refilled?"
            call_log.intent_detected = "prescription_refill_incomplete"
    
    # 💳 PRIORITY 3: Insurance/Cost Inquiry Detection
    else:
        insurance_intent = await insurance_service.detect_insurance_inquiry(speech_text)
        
        if insurance_intent["is_insurance_inquiry"]:
            # Handle insurance and cost questions
            response_text = "I'd be happy to help with insurance and cost information. What service are you interested in, and do you have pet insurance?"
            call_log.intent_detected = "insurance_inquiry"
        
        # 📅 PRIORITY 4: Regular LLM Processing for Appointments
        else:
            # Build clinic context
            clinic_context = {
                "name": clinic.name,
                "business_hours": clinic.business_hours or "9 AM to 5 PM, Monday through Friday",
                "phone": clinic.phone_number,
                "email": clinic.email
            }
            
            # Process with LLM
            llm_response = await llm_service.process_conversation(
                user_message=speech_text,
                conversation_history=conversation_history,
                clinic_context=clinic_context,
                system_prompt=clinic.system_prompt
            )
            
            response_text = llm_response["response"]
            call_log.intent_detected = llm_response["intent"]
            call_log.confidence_score = llm_response["confidence"]
            
            # Handle appointment booking
            if llm_response["intent"] == "appointment_booking":
                appointment_service = AppointmentService(db)
                appointment_info = await appointment_service.parse_appointment_request(
                    speech_text, 
                    llm_response["entities"]
                )
                
                # If we have enough information, try to book appointment
                if all(key in appointment_info for key in ["pet_name", "owner_phone"]):
                    try:
                        next_slot = await appointment_service.find_next_available_slot(clinic.id)
                        
                        if next_slot:
                            appointment = await appointment_service.create_appointment(
                                clinic_id=clinic.id,
                                pet_name=appointment_info["pet_name"],
                                pet_type=appointment_info.get("pet_type", ""),
                                owner_name=appointment_info.get("owner_name", ""),
                                owner_phone=appointment_info["owner_phone"],
                                appointment_date=next_slot,
                                appointment_type=appointment_info.get("appointment_type"),
                                reason=speech_text,
                                ai_summary=llm_response["response"]
                            )
                            
                            call_log.appointment_created = True
                            call_log.appointment_id = appointment.id
                            
                            response_text = f"Perfect! I've scheduled an appointment for {appointment_info['pet_name']} on {next_slot.strftime('%A, %B %d at %I:%M %p')}. You'll receive a confirmation text message shortly. Is there anything else I can help you with?"
                        else:
                            response_text = "I'm sorry, we don't have any available appointments in the next week. Let me transfer you to our staff to help you schedule something further out."
                    except Exception as e:
                        response_text = "I'm having trouble accessing our appointment system right now. Let me transfer you to our staff."
    
    # Update call log with transcript
    updated_transcript = f"{call_log.transcript or ''}\nUser: {speech_text}\nAI: {response_text}"
    call_log.transcript = updated_transcript
    
    # Determine call flow
    if any(phrase in response_text.lower() for phrase in ["goodbye", "thank you for calling", "have a great day"]):
        twiml = twilio_service.create_hangup_response(response_text)
    elif "transfer" in response_text.lower():
        twiml = twilio_service.create_hangup_response(
            f"{response_text} Please hold while we connect you."
        )
    else:
        # Continue conversation
        twiml = twilio_service.create_gather_response(
            response_text,
            f"/api/voice/process?call_sid={call_sid}"
        )
    
    # Save call log updates
    db.commit()
    
    return twiml


@router.post("/upload-audio")
async def upload_audio(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload and process audio file for transcription."""
    
    if not file.content_type.startswith('audio/'):
        raise HTTPException(status_code=400, detail="File must be an audio file")
    
    try:
        # Read file content
        audio_content = await file.read()
        audio_file = io.BytesIO(audio_content)
        
        # Validate audio format
        if not voice_processor.validate_audio_format(audio_file):
            raise HTTPException(status_code=400, detail="Invalid audio format or file too large")
        
        # Process with speech-to-text
        transcript = await voice_processor.speech_to_text(audio_file)
        
        return {"transcript": transcript}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing audio: {str(e)}")


@router.post("/text-to-speech")
async def text_to_speech(
    text: str,
    voice_id: Optional[str] = None
):
    """Convert text to speech."""
    
    try:
        audio_content = await voice_processor.text_to_speech(text, voice_id)
        
        return Response(
            content=audio_content,
            media_type="audio/mpeg",
            headers={"Content-Disposition": "attachment; filename=speech.mp3"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating speech: {str(e)}")


@router.post("/status-callback")
async def call_status_callback(
    request: Request,
    db: Session = Depends(get_db),
    CallSid: str = Form(...),
    CallStatus: str = Form(...),
    CallDuration: Optional[str] = Form(None),
    From: str = Form(...),
    To: str = Form(...)
):
    """Handle Twilio call status callbacks for tracking and analytics."""
    
    try:
        # Find the call log entry
        call_log = db.query(CallLog).filter(CallLog.twilio_call_sid == CallSid).first()
        
        if call_log:
            # Update call status and duration
            call_log.call_status = CallStatus
            
            if CallDuration:
                call_log.call_duration = float(CallDuration)
            
            # Set end time for completed calls
            if CallStatus in ["completed", "busy", "failed", "no-answer", "canceled"]:
                call_log.call_ended_at = datetime.utcnow()
            
            db.commit()
            
            # Log for analytics
            print(f"Call {CallSid} status updated: {CallStatus}, Duration: {CallDuration}s")
        
        return {"status": "success", "message": "Status updated"}
        
    except Exception as e:
        print(f"Error updating call status: {e}")
        return {"status": "error", "message": str(e)}
