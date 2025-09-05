"""Twilio TwiML generation for voice entry and media streaming."""

from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


def voice_entry(call_context: Dict[str, Any]) -> str:
    """
    Generate TwiML for voice entry with Media Streams and DTMF fallback.
    
    Args:
        call_context: Dictionary containing call information
            - call_sid: Twilio call SID
            - from_number: Caller's phone number
            - clinic_id: Clinic identifier for multi-tenancy
            - ws_url: WebSocket URL for media streaming
            - consent_required: Whether to play consent message
            - consent_text: Clinic-specific consent text
    
    Returns:
        TwiML string for Twilio voice response
    """
    call_sid = call_context.get("call_sid", "unknown")
    from_number = call_context.get("from_number", "unknown")
    clinic_id = call_context.get("clinic_id", "default")
    ws_url = call_context.get("ws_url", "/twilio/ws")
    consent_required = call_context.get("consent_required", False)
    consent_text = call_context.get("consent_text", "")
    
    logger.info(
        f"Generating TwiML for voice entry: call_sid={call_sid}, from_number={from_number}, clinic_id={clinic_id}"
    )
    
    # Base greeting for the clinic
    greeting = call_context.get(
        "greeting",
        "Hello and thank you for calling. I'm your AI assistant here to help with your pet care needs."
    )
    
    # Build TwiML with media streaming and DTMF fallback
    twiml_parts = ['<?xml version="1.0" encoding="UTF-8"?>', '<Response>']
    
    # Add consent message if required
    if consent_required and consent_text:
        twiml_parts.extend([
            f'<Say voice="Polly.Joanna">{consent_text}</Say>',
            '<Pause length="1"/>'
        ])
    
    # Initial greeting
    twiml_parts.append(f'<Say voice="Polly.Joanna">{greeting}</Say>')
    
    # Start media streaming to WebSocket endpoint
    twiml_parts.extend([
        '<Start>',
        f'    <Stream url="{ws_url}" track="inbound_track">',
        f'        <Parameter name="callSid" value="{call_sid}"/>',
        f'        <Parameter name="fromNumber" value="{from_number}"/>',
        f'        <Parameter name="clinicId" value="{clinic_id}"/>',
        '    </Stream>',
        '</Start>'
    ])
    
    # Gather for DTMF fallback with extended timeout to allow streaming
    dtmf_instructions = call_context.get(
        "dtmf_instructions",
        "If you prefer, you can also press 1 for appointments, 2 for emergencies, or 3 for general questions."
    )
    
    twiml_parts.extend([
        '<Gather input="dtmf" action="/twilio/dtmf" method="POST" timeout="30" numDigits="1">',
        f'    <Say voice="Polly.Joanna">{dtmf_instructions}</Say>',
        f'    <Pause length="25"/>',  # Allow time for voice interaction
        '</Gather>'
    ])
    
    # Fallback if no input received
    fallback_message = call_context.get(
        "fallback_message",
        "I didn't receive any input. Our team will call you back shortly. Thank you for calling."
    )
    
    twiml_parts.extend([
        f'<Say voice="Polly.Joanna">{fallback_message}</Say>',
        '<Hangup/>'
    ])
    
    twiml_parts.append('</Response>')
    
    twiml = '\n'.join(twiml_parts)
    
    logger.debug(f"Generated TwiML: {twiml}")
    
    return twiml


def generate_dtmf_response(digit: str, clinic_context: Optional[Dict[str, Any]] = None) -> str:
    """
    Generate TwiML response for DTMF input.
    
    Args:
        digit: DTMF digit pressed (1, 2, 3, etc.)
        clinic_context: Optional clinic-specific context
    
    Returns:
        TwiML string for DTMF response
    """
    clinic_context = clinic_context or {}
    clinic_name = clinic_context.get("name", "our veterinary clinic")
    
    logger.info(f"Generating DTMF response for digit: {digit}")
    
    # Define responses for each digit
    responses = {
        "1": f"Thank you for choosing to schedule an appointment. Our scheduling team will call you back within 10 minutes to book the perfect time for your pet at {clinic_name}.",
        "2": f"This is an EMERGENCY! Please hang up immediately and call your nearest emergency veterinary clinic. If this is a poison emergency, call the Pet Poison Helpline at (855) 764-7661. Time is critical!",
        "3": f"I understand you have questions about your pet's health. Our experienced veterinary team will call you back within 10 minutes to provide professional guidance.",
        "0": f"Connecting you to our main office. Please hold while we transfer your call.",
        "*": f"Returning to the main menu. Please listen to the options again.",
        "#": f"Thank you for calling {clinic_name}. Have a wonderful day!"
    }
    
    message = responses.get(digit, f"Thank you for calling {clinic_name}. Our team will assist you shortly.")
    
    twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna">{message}</Say>
    <Hangup/>
</Response>'''
    
    logger.debug(f"Generated DTMF TwiML for digit {digit}: {twiml}")
    
    return twiml


def generate_error_response(error_type: str = "general") -> str:
    """
    Generate TwiML for error conditions.
    
    Args:
        error_type: Type of error (general, timeout, system, etc.)
    
    Returns:
        TwiML string for error response
    """
    logger.warning(f"Generating error response: {error_type}")
    
    error_messages = {
        "general": "We're experiencing technical difficulties. Please call back in a few minutes or our team will call you back shortly.",
        "timeout": "I didn't receive a response. Our team will call you back within 10 minutes to assist you.",
        "system": "Our system is currently updating. Please call back in a few minutes for the best service.",
        "overload": "We're experiencing high call volume. Please hold for the next available representative or we'll call you back shortly."
    }
    
    message = error_messages.get(error_type, error_messages["general"])
    
    twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna">{message}</Say>
    <Hangup/>
</Response>'''
    
    return twiml


def generate_transfer_twiml(transfer_number: str, clinic_context: Optional[Dict[str, Any]] = None) -> str:
    """
    Generate TwiML for transferring calls to human staff.
    
    Args:
        transfer_number: Phone number to transfer to
        clinic_context: Optional clinic-specific context
    
    Returns:
        TwiML string for call transfer
    """
    clinic_context = clinic_context or {}
    clinic_name = clinic_context.get("name", "our veterinary clinic")
    
    logger.info(f"Generating transfer TwiML to: {transfer_number}")
    
    twiml = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna">Please hold while I connect you to a team member at {clinic_name}.</Say>
    <Dial timeout="30" callerId="+61468017757">
        <Number>{transfer_number}</Number>
    </Dial>
    <Say voice="Polly.Joanna">I'm sorry, our team is currently unavailable. We'll call you back within 10 minutes.</Say>
    <Hangup/>
</Response>'''
    
    return twiml


def generate_recording_twiml(call_context: Dict[str, Any]) -> str:
    """
    Generate TwiML for call recording (when enabled and consented).
    
    Args:
        call_context: Call context with recording preferences
    
    Returns:
        TwiML string with recording configuration
    """
    record_calls = call_context.get("record_calls", False)
    recording_url = call_context.get("recording_url", "/twilio/recording")
    
    if not record_calls:
        return ""
    
    logger.info("Adding call recording to TwiML")
    
    recording_twiml = f'''
    <Record action="{recording_url}" method="POST" maxLength="600" timeout="5" transcribe="true" transcribeCallback="/twilio/transcription"/>'''
    
    return recording_twiml
