"""Twilio routes for voice, webhooks, and media streaming."""

from fastapi import APIRouter, Request, WebSocket, Form, Depends, HTTPException
from fastapi.responses import Response
from typing import Optional, Dict, Any
import logging
from datetime import datetime
import json
import os

from app.telephony.twilio_twiml import (
    voice_entry,
    generate_dtmf_response,
    generate_error_response,
    generate_transfer_twiml
)
from app.telephony.twilio_signature import (
    require_twilio_signature,
    webhook_validator
)
from app.telephony.media_server import media_server

logger = logging.getLogger(__name__)

# Create router for Twilio endpoints
router = APIRouter(prefix="/twilio", tags=["twilio"])


@router.post("/voice")
async def voice_webhook(
    request: Request,
    CallSid: str = Form(...),
    From: str = Form(...),
    To: str = Form(...),
    CallStatus: str = Form(...),
    AccountSid: str = Form(...),
    _: None = Depends(require_twilio_signature)
):
    """
    Twilio voice webhook endpoint.
    
    Handles incoming calls and returns TwiML for voice response.
    """
    logger.info(
        "Incoming voice call",
        call_sid=CallSid,
        from_number=From,
        to_number=To,
        status=CallStatus
    )
    
    try:
        # Determine clinic context based on To number
        clinic_id = _get_clinic_id_from_number(To)
        clinic_context = _get_clinic_context(clinic_id)
        
        # Build WebSocket URL for media streaming
        base_url = str(request.base_url).rstrip('/')
        ws_url = f"wss://{request.url.hostname}/twilio/ws?callSid={CallSid}&fromNumber={From}&clinicId={clinic_id}"
        
        if request.url.hostname == "localhost":
            ws_url = f"ws://localhost:8000/twilio/ws?callSid={CallSid}&fromNumber={From}&clinicId={clinic_id}"
        
        # Prepare call context
        call_context = {
            "call_sid": CallSid,
            "from_number": From,
            "to_number": To,
            "clinic_id": clinic_id,
            "ws_url": ws_url,
            "greeting": clinic_context.get("greeting", "Hello! How can I help you with your pet today?"),
            "consent_required": clinic_context.get("consent_required", False),
            "consent_text": clinic_context.get("consent_text", ""),
            "dtmf_instructions": clinic_context.get(
                "dtmf_instructions",
                "You can press 1 for appointments, 2 for emergencies, or 3 for general questions."
            ),
            "fallback_message": clinic_context.get(
                "fallback_message",
                "Thank you for calling. Our team will call you back shortly."
            )
        }
        
        # Generate TwiML response
        twiml = voice_entry(call_context)
        
        logger.debug("Generated TwiML", call_sid=CallSid, twiml=twiml[:200])
        
        return Response(content=twiml, media_type="application/xml")
        
    except Exception as e:
        logger.error(f"Voice webhook error: {e}", call_sid=CallSid)
        
        # Return error TwiML
        error_twiml = generate_error_response("system")
        return Response(content=error_twiml, media_type="application/xml")


@router.post("/dtmf")
async def dtmf_webhook(
    request: Request,
    CallSid: str = Form(...),
    From: str = Form(...),
    Digits: str = Form(...),
    _: None = Depends(require_twilio_signature)
):
    """
    Twilio DTMF webhook endpoint.
    
    Handles DTMF digit input and returns appropriate TwiML response.
    """
    logger.info(
        "DTMF input received",
        call_sid=CallSid,
        from_number=From,
        digits=Digits
    )
    
    try:
        # Determine clinic context
        clinic_id = _get_clinic_id_from_number(request.form().get("To", ""))
        clinic_context = _get_clinic_context(clinic_id)
        
        # Handle special cases
        if Digits == "2":  # Emergency
            logger.warning(
                "Emergency DTMF selected",
                call_sid=CallSid,
                from_number=From
            )
        
        # Generate DTMF response
        twiml = generate_dtmf_response(Digits, clinic_context)
        
        return Response(content=twiml, media_type="application/xml")
        
    except Exception as e:
        logger.error(f"DTMF webhook error: {e}", call_sid=CallSid)
        
        error_twiml = generate_error_response("general")
        return Response(content=error_twiml, media_type="application/xml")


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    callSid: str,
    fromNumber: str,
    clinicId: str = "default"
):
    """
    WebSocket endpoint for Twilio Media Streams.
    
    Handles real-time audio streaming with barge-in functionality.
    """
    logger.info(
        "WebSocket connection requested",
        call_sid=callSid,
        from_number=fromNumber,
        clinic_id=clinicId
    )
    
    try:
        await media_server.handle_websocket(websocket, callSid, fromNumber, clinicId)
        
    except Exception as e:
        logger.error(f"WebSocket error: {e}", call_sid=callSid)


@router.post("/status")
async def call_status_webhook(
    request: Request,
    CallSid: str = Form(...),
    CallStatus: str = Form(...),
    From: str = Form(None),
    To: str = Form(None),
    Duration: str = Form(None),
    _: None = Depends(require_twilio_signature)
):
    """
    Twilio call status webhook endpoint.
    
    Handles call status updates (completed, failed, etc.).
    """
    logger.info(
        "Call status update",
        call_sid=CallSid,
        status=CallStatus,
        duration=Duration,
        from_number=From
    )
    
    try:
        # Log call completion
        if CallStatus == "completed":
            duration_seconds = int(Duration) if Duration else 0
            logger.info(
                "Call completed",
                call_sid=CallSid,
                duration=duration_seconds,
                from_number=From
            )
        
        elif CallStatus in ["failed", "busy", "no-answer"]:
            logger.warning(
                "Call not completed",
                call_sid=CallSid,
                status=CallStatus,
                from_number=From
            )
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Status webhook error: {e}", call_sid=CallSid)
        return {"status": "error", "message": str(e)}


@router.post("/recording")
async def recording_webhook(
    request: Request,
    CallSid: str = Form(...),
    RecordingUrl: str = Form(...),
    RecordingSid: str = Form(...),
    RecordingDuration: str = Form(...),
    _: None = Depends(require_twilio_signature)
):
    """
    Twilio recording webhook endpoint.
    
    Handles recording completion events.
    """
    logger.info(
        "Recording completed",
        call_sid=CallSid,
        recording_sid=RecordingSid,
        duration=RecordingDuration,
        url=RecordingUrl
    )
    
    try:
        # Store recording information
        recording_data = {
            "call_sid": CallSid,
            "recording_sid": RecordingSid,
            "recording_url": RecordingUrl,
            "duration": int(RecordingDuration),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Here you would typically store this in a database
        logger.debug("Recording data", **recording_data)
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Recording webhook error: {e}", call_sid=CallSid)
        return {"status": "error", "message": str(e)}


@router.post("/transcription")
async def transcription_webhook(
    request: Request,
    CallSid: str = Form(...),
    TranscriptionText: str = Form(...),
    TranscriptionStatus: str = Form(...),
    TranscriptionSid: str = Form(...),
    _: None = Depends(require_twilio_signature)
):
    """
    Twilio transcription webhook endpoint.
    
    Handles transcription completion events.
    """
    logger.info(
        "Transcription completed",
        call_sid=CallSid,
        transcription_sid=TranscriptionSid,
        status=TranscriptionStatus
    )
    
    try:
        if TranscriptionStatus == "completed":
            logger.debug(
                "Call transcription",
                call_sid=CallSid,
                text=TranscriptionText[:200] + "..." if len(TranscriptionText) > 200 else TranscriptionText
            )
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Transcription webhook error: {e}", call_sid=CallSid)
        return {"status": "error", "message": str(e)}


@router.get("/health")
async def health_check():
    """Health check endpoint for Twilio webhooks."""
    session_stats = media_server.get_session_stats()
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "active_sessions": session_stats["active_sessions"],
        "version": "1.0.0"
    }


@router.get("/sessions")
async def get_active_sessions():
    """Get information about active call sessions."""
    return media_server.get_session_stats()


@router.post("/transfer")
async def transfer_call(
    request: Request,
    CallSid: str = Form(...),
    From: str = Form(...),
    TransferTo: str = Form(...),
    _: None = Depends(require_twilio_signature)
):
    """
    Transfer call to human staff.
    
    Generates TwiML to transfer the call to specified number.
    """
    logger.info(
        "Call transfer requested",
        call_sid=CallSid,
        from_number=From,
        transfer_to=TransferTo
    )
    
    try:
        clinic_id = _get_clinic_id_from_number(request.form().get("To", ""))
        clinic_context = _get_clinic_context(clinic_id)
        
        twiml = generate_transfer_twiml(TransferTo, clinic_context)
        
        return Response(content=twiml, media_type="application/xml")
        
    except Exception as e:
        logger.error(f"Transfer webhook error: {e}", call_sid=CallSid)
        
        error_twiml = generate_error_response("general")
        return Response(content=error_twiml, media_type="application/xml")


def _get_clinic_id_from_number(phone_number: str) -> str:
    """
    Determine clinic ID based on phone number.
    
    Args:
        phone_number: Phone number that was called
        
    Returns:
        Clinic identifier
    """
    # Map phone numbers to clinic IDs
    number_mapping = {
        "+61468017757": "default",
        # Add more mappings as needed
    }
    
    return number_mapping.get(phone_number, "default")


def _get_clinic_context(clinic_id: str) -> Dict[str, Any]:
    """
    Get clinic-specific configuration.
    
    Args:
        clinic_id: Clinic identifier
        
    Returns:
        Dictionary with clinic configuration
    """
    # This would typically come from a database
    clinic_configs = {
        "default": {
            "name": "Veterinary Clinic",
            "greeting": "Hello! I'm your AI assistant. How can I help you with your pet today?",
            "consent_required": False,
            "consent_text": "",
            "dtmf_instructions": "You can press 1 for appointments, 2 for emergencies, or 3 for general questions.",
            "fallback_message": "Thank you for calling. Our team will call you back shortly.",
            "transfer_number": "+61468017757",
            "emergency_keywords": ["emergency", "urgent", "bleeding", "unconscious", "poison"]
        }
    }
    
    return clinic_configs.get(clinic_id, clinic_configs["default"])
