"""Twilio service for handling voice calls and webhooks."""

from typing import Optional, Dict, Any
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
from ..core.config import settings


class TwilioService:
    """Service for Twilio voice operations."""
    
    def __init__(self):
        """Initialize the Twilio service."""
        self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        self.phone_number = settings.TWILIO_PHONE_NUMBER
    
    def create_voice_response(self, message: str, action_url: Optional[str] = None) -> str:
        """Create a TwiML voice response."""
        response = VoiceResponse()
        
        # Add the message
        response.say(message, voice='alice', language='en-US')
        
        # If action URL is provided, gather input
        if action_url:
            gather = response.gather(
                input='speech',
                action=action_url,
                method='POST',
                speech_timeout='auto',
                language='en-US'
            )
            gather.say("Please speak after the tone.", voice='alice')
            
            # Fallback if no input is received
            response.say("I didn't hear anything. Please call back.", voice='alice')
        
        return str(response)
    
    def create_gather_response(
        self,
        message: str,
        action_url: str,
        timeout: int = 5,
        max_speech_time: int = 30
    ) -> str:
        """Create a TwiML response that gathers speech input."""
        response = VoiceResponse()
        
        gather = response.gather(
            input='speech',
            action=action_url,
            method='POST',
            timeout=timeout,
            speech_timeout='auto',
            max_speech_time=max_speech_time,
            language='en-US'
        )
        
        gather.say(message, voice='alice', language='en-US')
        
        # Fallback if no input
        response.say("I didn't receive any input. Goodbye!", voice='alice')
        response.hangup()
        
        return str(response)
    
    def create_recording_response(
        self,
        message: str,
        action_url: str,
        max_length: int = 120,
        play_beep: bool = True
    ) -> str:
        """Create a TwiML response that records audio."""
        response = VoiceResponse()
        
        response.say(message, voice='alice', language='en-US')
        
        response.record(
            action=action_url,
            method='POST',
            max_length=max_length,
            play_beep=play_beep,
            timeout=10,
            transcribe=False  # We'll use Whisper instead
        )
        
        return str(response)
    
    def create_redirect_response(self, url: str) -> str:
        """Create a TwiML response that redirects to another URL."""
        response = VoiceResponse()
        response.redirect(url, method='POST')
        return str(response)
    
    def create_hangup_response(self, message: Optional[str] = None) -> str:
        """Create a TwiML response that hangs up the call."""
        response = VoiceResponse()
        
        if message:
            response.say(message, voice='alice', language='en-US')
        
        response.hangup()
        return str(response)
    
    async def make_outbound_call(
        self,
        to_number: str,
        webhook_url: str,
        from_number: Optional[str] = None
    ) -> Optional[str]:
        """Make an outbound call."""
        try:
            call = self.client.calls.create(
                to=to_number,
                from_=from_number or self.phone_number,
                url=webhook_url,
                method='POST'
            )
            return call.sid
        except Exception as e:
            print(f"Error making outbound call: {e}")
            return None
    
    async def get_call_details(self, call_sid: str) -> Optional[Dict[str, Any]]:
        """Get details about a specific call."""
        try:
            call = self.client.calls(call_sid).fetch()
            return {
                "sid": call.sid,
                "status": call.status,
                "duration": call.duration,
                "from": call.from_,
                "to": call.to,
                "start_time": call.start_time,
                "end_time": call.end_time,
                "price": call.price,
                "direction": call.direction
            }
        except Exception as e:
            print(f"Error fetching call details: {e}")
            return None
    
    async def get_recording_url(self, call_sid: str) -> Optional[str]:
        """Get the recording URL for a call."""
        try:
            recordings = self.client.recordings.list(call_sid=call_sid)
            if recordings:
                recording = recordings[0]
                return f"https://api.twilio.com{recording.uri.replace('.json', '.mp3')}"
            return None
        except Exception as e:
            print(f"Error fetching recording: {e}")
            return None
    
    def parse_webhook_data(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Twilio webhook data."""
        return {
            "call_sid": form_data.get("CallSid"),
            "account_sid": form_data.get("AccountSid"),
            "from": form_data.get("From"),
            "to": form_data.get("To"),
            "call_status": form_data.get("CallStatus"),
            "direction": form_data.get("Direction"),
            "speech_result": form_data.get("SpeechResult"),
            "confidence": form_data.get("Confidence"),
            "recording_url": form_data.get("RecordingUrl"),
            "recording_duration": form_data.get("RecordingDuration"),
            "digits": form_data.get("Digits")
        }
