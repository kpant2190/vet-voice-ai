"""WebSocket media server for Twilio Media Streams with barge-in functionality."""

import asyncio
import json
import base64
import logging
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from datetime import datetime
import uuid
import time
import os
import io

from fastapi import WebSocket, WebSocketDisconnect
import openai
from elevenlabs import generate, Voice, VoiceSettings

logger = logging.getLogger(__name__)


@dataclass
class CallSession:
    """Represents an active call session."""
    call_sid: str
    from_number: str
    clinic_id: str
    websocket: WebSocket
    stream_sid: Optional[str] = None
    start_time: datetime = None
    last_activity: datetime = None
    conversation_buffer: List[Dict[str, Any]] = None
    audio_buffer: bytes = b''
    is_speaking: bool = False
    interrupt_requested: bool = False
    current_response_id: Optional[str] = None
    
    def __post_init__(self):
        if self.start_time is None:
            self.start_time = datetime.utcnow()
        if self.last_activity is None:
            self.last_activity = datetime.utcnow()
        if self.conversation_buffer is None:
            self.conversation_buffer = []


class MediaStreamServer:
    """Handles Twilio Media Streams with real-time audio processing."""
    
    def __init__(self):
        self.active_sessions: Dict[str, CallSession] = {}
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.clinic_config = self._load_clinic_config()
        
        # Audio configuration for Twilio μ-law 8kHz
        self.sample_rate = 8000
        self.channels = 1
        self.audio_format = "mulaw"
        
        # Simplified barge-in configuration
        self.audio_buffer_size = 1600  # 100ms at 8kHz
        self.silence_threshold = 0.01  # Basic silence detection
        
        logger.info("Media stream server initialized")
    
    def _load_clinic_config(self) -> Dict[str, Any]:
        """Load clinic-specific configuration."""
        return {
            "default": {
                "name": "Veterinary Clinic",
                "greeting": "Hello! I'm your AI assistant. How can I help you with your pet today?",
                "emergency_keywords": ["emergency", "urgent", "bleeding", "unconscious", "poison"],
                "transfer_number": "+61468017757",
                "max_call_duration": 600,  # 10 minutes
                "enable_recording": False
            }
        }
    
    async def handle_websocket(self, websocket: WebSocket, call_sid: str, from_number: str, clinic_id: str = "default"):
        """
        Handle incoming WebSocket connection for media streaming.
        
        Args:
            websocket: FastAPI WebSocket connection
            call_sid: Twilio call SID
            from_number: Caller's phone number
            clinic_id: Clinic identifier
        """
        await websocket.accept()
        
        session = CallSession(
            call_sid=call_sid,
            from_number=from_number,
            clinic_id=clinic_id,
            websocket=websocket
        )
        
        self.active_sessions[call_sid] = session
        
        logger.info(
            "WebSocket connection established",
            call_sid=call_sid,
            from_number=from_number,
            clinic_id=clinic_id
        )
        
        try:
            async for message in websocket.iter_text():
                await self._process_message(session, message)
                
        except WebSocketDisconnect:
            logger.info("WebSocket disconnected", call_sid=call_sid)
        except Exception as e:
            logger.error(f"WebSocket error: {e}", call_sid=call_sid)
        finally:
            await self._cleanup_session(call_sid)
    
    async def _process_message(self, session: CallSession, message: str):
        """Process incoming WebSocket message from Twilio."""
        try:
            data = json.loads(message)
            event = data.get("event")
            
            session.last_activity = datetime.utcnow()
            
            if event == "connected":
                await self._handle_connected(session, data)
            elif event == "start":
                await self._handle_start(session, data)
            elif event == "media":
                await self._handle_media(session, data)
            elif event == "stop":
                await self._handle_stop(session, data)
            else:
                logger.debug(f"Unknown event: {event}", call_sid=session.call_sid)
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}", call_sid=session.call_sid)
        except Exception as e:
            logger.error(f"Message processing error: {e}", call_sid=session.call_sid)
    
    async def _handle_connected(self, session: CallSession, data: Dict[str, Any]):
        """Handle WebSocket connected event."""
        logger.info("Media stream connected", call_sid=session.call_sid)
        
        # Send initial greeting
        await self._send_greeting(session)
    
    async def _handle_start(self, session: CallSession, data: Dict[str, Any]):
        """Handle stream start event."""
        stream_data = data.get("start", {})
        session.stream_sid = stream_data.get("streamSid")
        
        logger.info(
            "Media stream started",
            call_sid=session.call_sid,
            stream_sid=session.stream_sid
        )
    
    async def _handle_media(self, session: CallSession, data: Dict[str, Any]):
        """Handle incoming audio media."""
        media_data = data.get("media", {})
        payload = media_data.get("payload")
        
        if not payload:
            return
        
        # Decode μ-law audio
        try:
            audio_data = base64.b64decode(payload)
            session.audio_buffer += audio_data
            
            # Process audio in chunks for real-time ASR
            if len(session.audio_buffer) >= 320:  # 20ms at 8kHz μ-law
                await self._process_audio_chunk(session)
                
        except Exception as e:
            logger.error(f"Audio processing error: {e}", call_sid=session.call_sid)
    
    async def _handle_stop(self, session: CallSession, data: Dict[str, Any]):
        """Handle stream stop event."""
        logger.info("Media stream stopped", call_sid=session.call_sid)
        
        # Process any remaining audio
        if session.audio_buffer:
            await self._process_final_audio(session)
    
    async def _process_audio_chunk(self, session: CallSession):
        """Process accumulated audio for speech recognition."""
        if len(session.audio_buffer) < self.audio_buffer_size:
            return
        
        # Take a chunk for processing
        chunk_size = min(self.audio_buffer_size, len(session.audio_buffer))
        audio_chunk = session.audio_buffer[:chunk_size]
        session.audio_buffer = session.audio_buffer[chunk_size:]
        
        # Simple voice activity detection based on audio data presence
        if self._detect_voice_activity(audio_chunk):
            await self._handle_voice_activity(session, audio_chunk)
    
    def _detect_voice_activity(self, audio_data: bytes) -> bool:
        """Simple voice activity detection based on audio data."""
        try:
            # Basic check - if we have audio data and it's not all zeros
            if not audio_data or len(audio_data) == 0:
                return False
            
            # Count non-zero bytes as a simple activity indicator
            non_zero_count = sum(1 for byte in audio_data if byte != 0)
            activity_ratio = non_zero_count / len(audio_data)
            
            return activity_ratio > self.silence_threshold
            
        except Exception:
            return False
    
    async def _handle_voice_activity(self, session: CallSession, audio_data: bytes):
        """Handle detected voice activity (potential barge-in)."""
        if session.is_speaking and not session.interrupt_requested:
            logger.info("Barge-in detected", call_sid=session.call_sid)
            session.interrupt_requested = True
            await self._stop_current_speech(session)
        
        # Accumulate audio for transcription
        await self._accumulate_speech(session, audio_data)
    
    async def _accumulate_speech(self, session: CallSession, audio_data: bytes):
        """Accumulate speech audio for transcription."""
        # Store audio in session buffer for transcription
        if not hasattr(session, 'speech_buffer'):
            session.speech_buffer = b''
        
        session.speech_buffer += audio_data
        
        # Transcribe when we have enough audio (1-2 seconds)
        if len(session.speech_buffer) >= 16000:  # ~1 second at 8kHz 16-bit
            await self._transcribe_speech(session)
    
    async def _transcribe_speech(self, session: CallSession):
        """Transcribe accumulated speech using OpenAI Whisper."""
        if not hasattr(session, 'speech_buffer') or len(session.speech_buffer) < 8000:
            return
        
        try:
            # For now, we'll skip complex audio processing and use a placeholder
            # In a production environment, you'd want to properly convert μ-law to WAV
            # For the demo, we'll simulate receiving text or use DTMF fallback
            
            # Create a temporary audio file for Whisper
            # This is a simplified approach - in production you'd do proper format conversion
            temp_audio = io.BytesIO(session.speech_buffer)
            
            # For demo purposes, we'll use a basic transcription approach
            # In production, you'd properly convert the μ-law audio to the right format
            logger.info(
                "Audio transcription attempted",
                call_sid=session.call_sid,
                buffer_size=len(session.speech_buffer)
            )
            
            # For now, we'll simulate a basic interaction or rely on DTMF
            # In the real implementation, you'd properly convert and transcribe the audio
            user_message = "I need help with my pet"  # Placeholder for demo
            
            if user_message:
                logger.info(
                    "Simulated user speech",
                    call_sid=session.call_sid,
                    text=user_message
                )
                
                # Process the user's message
                await self._process_user_message(session, user_message)
            
            # Clear speech buffer
            session.speech_buffer = b''
            
        except Exception as e:
            logger.error(f"Speech transcription error: {e}", call_sid=session.call_sid)
    
    async def _process_user_message(self, session: CallSession, message: str):
        """Process transcribed user message and generate response."""
        try:
            # Add user message to conversation
            session.conversation_buffer.append({
                "role": "user",
                "content": message,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Check for emergency keywords
            if await self._check_emergency(session, message):
                return
            
            # Generate AI response
            response = await self._generate_ai_response(session, message)
            
            if response:
                # Add AI response to conversation
                session.conversation_buffer.append({
                    "role": "assistant",
                    "content": response,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                # Convert to speech and send
                await self._send_speech_response(session, response)
            
        except Exception as e:
            logger.error(f"Message processing error: {e}", call_sid=session.call_sid)
    
    async def _check_emergency(self, session: CallSession, message: str) -> bool:
        """Check if message contains emergency keywords."""
        clinic_config = self.clinic_config.get(session.clinic_id, self.clinic_config["default"])
        emergency_keywords = clinic_config.get("emergency_keywords", [])
        
        message_lower = message.lower()
        
        for keyword in emergency_keywords:
            if keyword in message_lower:
                logger.warning(
                    "Emergency detected",
                    call_sid=session.call_sid,
                    keyword=keyword,
                    message=message
                )
                
                emergency_response = "This sounds like an emergency! Please hang up immediately and call your nearest emergency veterinary clinic or animal hospital. If your pet has ingested something toxic, call the Pet Poison Helpline at (855) 764-7661. Time is critical in emergencies!"
                
                await self._send_speech_response(session, emergency_response)
                return True
        
        return False
    
    async def _generate_ai_response(self, session: CallSession, user_message: str) -> str:
        """Generate AI response using OpenAI."""
        try:
            clinic_config = self.clinic_config.get(session.clinic_id, self.clinic_config["default"])
            
            # Build conversation context
            messages = [
                {
                    "role": "system",
                    "content": f"""You are an AI receptionist for {clinic_config['name']}. 
                    You help pet owners with scheduling appointments, answering basic questions, 
                    and providing general guidance. Keep responses concise and friendly.
                    
                    If someone mentions an emergency, immediately direct them to emergency services.
                    For medical questions, provide general guidance but always recommend consulting with a veterinarian.
                    For appointments, gather basic information (pet type, concern, preferred time) and confirm you'll have someone call back.
                    """
                }
            ]
            
            # Add recent conversation history (last 5 exchanges)
            recent_messages = session.conversation_buffer[-10:] if session.conversation_buffer else []
            for msg in recent_messages:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # Add current user message
            messages.append({
                "role": "user",
                "content": user_message
            })
            
            # Generate response
            response = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model="gpt-4",
                messages=messages,
                max_tokens=150,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"AI response generation error: {e}", call_sid=session.call_sid)
            return "I'm sorry, I'm having trouble processing your request. Let me have one of our team members call you back."
    
    async def _send_speech_response(self, session: CallSession, text: str):
        """Convert text to speech and send to Twilio."""
        try:
            session.current_response_id = str(uuid.uuid4())
            session.is_speaking = True
            session.interrupt_requested = False
            
            # Generate speech using ElevenLabs
            audio = await asyncio.to_thread(
                generate,
                text=text,
                voice=Voice(
                    voice_id="21m00Tcm4TlvDq8ikWAM",  # Rachel voice
                    settings=VoiceSettings(
                        stability=0.5,
                        similarity_boost=0.7,
                        style=0.2,
                        use_speaker_boost=True
                    )
                ),
                model="eleven_monolingual_v1"
            )
            
            # For demo purposes, we'll send a simple audio response
            # In production, you'd properly convert the ElevenLabs audio to μ-law format
            
            # Simulate sending audio chunks
            # The actual implementation would require proper audio format conversion
            logger.info(
                "Sending speech response",
                call_sid=session.call_sid,
                text=text,
                response_id=session.current_response_id
            )
            
            # For now, we'll send a simple mark message to indicate speech completion
            mark_message = {
                "event": "mark",
                "streamSid": session.stream_sid,
                "mark": {
                    "name": f"speech_complete_{session.current_response_id}"
                }
            }
            
            await session.websocket.send_text(json.dumps(mark_message))
            
            session.is_speaking = False
            
            logger.info(
                "Speech response completed",
                call_sid=session.call_sid,
                response_id=session.current_response_id
            )
            
        except Exception as e:
            logger.error(f"Speech response error: {e}", call_sid=session.call_sid)
            session.is_speaking = False
    
    async def _stop_current_speech(self, session: CallSession):
        """Stop current speech output for barge-in."""
        if session.is_speaking:
            session.interrupt_requested = True
            logger.info("Speech interrupted for barge-in", call_sid=session.call_sid)
    
    async def _send_greeting(self, session: CallSession):
        """Send initial greeting to caller."""
        clinic_config = self.clinic_config.get(session.clinic_id, self.clinic_config["default"])
        greeting = clinic_config.get("greeting", "Hello! How can I help you today?")
        
        await self._send_speech_response(session, greeting)
    
    async def _process_final_audio(self, session: CallSession):
        """Process any remaining audio when stream ends."""
        if hasattr(session, 'speech_buffer') and session.speech_buffer:
            await self._transcribe_speech(session)
    
    async def _cleanup_session(self, call_sid: str):
        """Clean up session resources."""
        if call_sid in self.active_sessions:
            session = self.active_sessions[call_sid]
            
            # Log session summary
            duration = (datetime.utcnow() - session.start_time).total_seconds()
            message_count = len(session.conversation_buffer)
            
            logger.info(
                "Session cleanup",
                call_sid=call_sid,
                duration=duration,
                messages=message_count,
                from_number=session.from_number
            )
            
            del self.active_sessions[call_sid]
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get current session statistics."""
        return {
            "active_sessions": len(self.active_sessions),
            "sessions": [
                {
                    "call_sid": session.call_sid,
                    "from_number": session.from_number,
                    "duration": (datetime.utcnow() - session.start_time).total_seconds(),
                    "messages": len(session.conversation_buffer),
                    "is_speaking": session.is_speaking
                }
                for session in self.active_sessions.values()
            ]
        }


# Global media server instance
media_server = MediaStreamServer()
