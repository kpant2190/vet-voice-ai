"""Enterprise Telephony Package for AI Veterinary Receptionist.

This package provides production-ready telephony capabilities including:
- Twilio Voice integration with Media Streams
- Real-time WebSocket audio processing with barge-in
- DTMF fallback menu support
- Webhook security validation
- Multi-tenant clinic configuration
"""

from .twilio_twiml import voice_entry, generate_dtmf_response, generate_error_response
from .twilio_signature import require_twilio_signature, TwilioSignatureValidator
from .media_server import MediaStreamServer, media_server

__version__ = "1.0.0"
__all__ = [
    "voice_entry",
    "generate_dtmf_response", 
    "generate_error_response",
    "require_twilio_signature",
    "TwilioSignatureValidator",
    "MediaStreamServer",
    "media_server"
]
