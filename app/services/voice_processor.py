"""Voice processing service for speech-to-text and text-to-speech."""

import io
import asyncio
from typing import Optional, BinaryIO
import openai
from elevenlabs import ElevenLabs
from ..core.config import settings


class VoiceProcessor:
    """Handles voice processing operations."""
    
    def __init__(self):
        """Initialize the voice processor."""
        self.openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.elevenlabs_client = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)
        
    async def speech_to_text(self, audio_file: BinaryIO) -> str:
        """Convert speech to text using OpenAI Whisper."""
        try:
            # Reset file pointer to beginning
            audio_file.seek(0)
            
            # Use OpenAI Whisper for transcription
            transcript = self.openai_client.audio.transcriptions.create(
                model=settings.SPEECH_MODEL,
                file=audio_file,
                response_format="text"
            )
            
            return transcript.strip()
            
        except Exception as e:
            print(f"Error in speech-to-text: {e}")
            return ""
    
    async def text_to_speech(self, text: str, voice_id: Optional[str] = None) -> bytes:
        """Convert text to speech using ElevenLabs."""
        try:
            # Use provided voice_id or default
            voice_id = voice_id or settings.DEFAULT_VOICE_ID
            
            # Generate audio using the new ElevenLabs API
            audio = self.elevenlabs_client.generate(
                text=text,
                voice=voice_id,
                model="eleven_monolingual_v1"
            )
            
            return audio
            
        except Exception as e:
            print(f"Error in text-to-speech: {e}")
            return b""
    
    async def text_to_speech_stream(self, text: str, voice_id: Optional[str] = None):
        """Stream text-to-speech for real-time playback."""
        try:
            voice_id = voice_id or settings.DEFAULT_VOICE_ID
            
            # For streaming, we'll generate in chunks
            # This is a simplified version - ElevenLabs streaming requires WebSocket
            audio = await self.text_to_speech(text, voice_id)
            
            # Yield in chunks for streaming
            chunk_size = 1024
            for i in range(0, len(audio), chunk_size):
                yield audio[i:i + chunk_size]
                await asyncio.sleep(0.01)  # Small delay for streaming effect
                
        except Exception as e:
            print(f"Error in text-to-speech streaming: {e}")
            yield b""
    
    def validate_audio_format(self, audio_file: BinaryIO) -> bool:
        """Validate that the audio file is in a supported format."""
        try:
            # Check file size (basic validation)
            audio_file.seek(0, 2)  # Seek to end
            file_size = audio_file.tell()
            audio_file.seek(0)  # Reset to beginning
            
            # Basic size check (between 1KB and 25MB)
            return 1024 <= file_size <= 25 * 1024 * 1024
            
        except Exception:
            return False
