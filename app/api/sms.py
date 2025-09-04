"""SMS API endpoints for handling Twilio SMS webhooks."""

from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from ..core.database import get_db
from ..services.twilio_service import TwilioService
from ..services.llm_service import LLMService
from ..models.clinic import Clinic
from ..models.call_log import CallLog

router = APIRouter()

# Initialize services
twilio_service = TwilioService()
llm_service = LLMService()


@router.post("/webhook")
async def sms_webhook(
    request: Request,
    db: Session = Depends(get_db),
    MessageSid: str = Form(...),
    From: str = Form(...),
    To: str = Form(...),
    Body: str = Form(...),
    NumMedia: Optional[str] = Form("0")
):
    """Handle incoming Twilio SMS webhooks."""
    
    # Find the clinic based on the number
    clinic = db.query(Clinic).filter(Clinic.phone_number == To).first()
    if not clinic:
        # Default response if clinic not found
        twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>Thank you for your message. This number is not configured for SMS services.</Message>
</Response>"""
        return Response(content=twiml, media_type="application/xml")
    
    # Create a call log entry for the SMS (reusing the same table)
    sms_log = CallLog(
        clinic_id=clinic.id,
        twilio_call_sid=MessageSid,
        caller_phone=From,
        call_status="completed",
        call_direction="inbound",
        call_started_at=datetime.utcnow(),
        call_ended_at=datetime.utcnow(),
        transcript=f"SMS: {Body}"
    )
    db.add(sms_log)
    db.commit()
    db.refresh(sms_log)
    
    # Process the SMS message
    clinic_context = {
        "name": clinic.name,
        "business_hours": clinic.business_hours or "9 AM to 5 PM, Monday through Friday",
        "phone": clinic.phone_number,
        "email": clinic.email
    }
    
    # Process with LLM
    llm_response = await llm_service.process_conversation(
        user_message=Body,
        conversation_history=[],
        clinic_context=clinic_context,
        system_prompt=f"You are {clinic.name}'s SMS assistant. Respond helpfully and concisely to text messages. Keep responses under 160 characters when possible."
    )
    
    response_text = llm_response["response"]
    
    # Update SMS log
    sms_log.intent_detected = llm_response["intent"]
    sms_log.confidence_score = llm_response["confidence"]
    sms_log.transcript = f"SMS: {Body}\nReply: {response_text}"
    db.commit()
    
    # Create TwiML response
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{response_text}</Message>
</Response>"""
    
    return Response(content=twiml, media_type="application/xml")


@router.post("/status-callback")
async def sms_status_callback(
    request: Request,
    db: Session = Depends(get_db),
    MessageSid: str = Form(...),
    MessageStatus: str = Form(...),
    From: str = Form(...),
    To: str = Form(...)
):
    """Handle Twilio SMS status callbacks."""
    
    try:
        # Find the SMS log entry
        sms_log = db.query(CallLog).filter(CallLog.twilio_call_sid == MessageSid).first()
        
        if sms_log:
            # Update status
            sms_log.call_status = MessageStatus
            db.commit()
            
            print(f"SMS {MessageSid} status updated: {MessageStatus}")
        
        return {"status": "success", "message": "SMS status updated"}
        
    except Exception as e:
        print(f"Error updating SMS status: {e}")
        return {"status": "error", "message": str(e)}
