"""ElevenLabs TTS service for high-quality voice synthesis."""

import os
import requests
import tempfile
from typing import Optional
import base64
import hashlib

class ElevenLabsService:
    """Service for generating high-quality speech using ElevenLabs."""
    
    def __init__(self):
        self.api_key = os.getenv('ELEVENLABS_API_KEY')
        self.voice_id = os.getenv('DEFAULT_VOICE_ID', 'cgSgspJ2msm6clMCkdW9')
        self.base_url = "https://api.elevenlabs.io/v1"
        
    def generate_speech_url(self, text: str, voice_id: Optional[str] = None) -> Optional[str]:
        """Generate speech and return a URL for Twilio to use."""
        try:
            if not self.api_key or not self.api_key.startswith('sk_'):
                print(f"⚠️ ElevenLabs API key invalid: {self.api_key[:10]}...")
                return None
                
            use_voice_id = voice_id or self.voice_id
            print(f"🎤 Generating ElevenLabs speech for: '{text[:50]}...'")
            
            url = f"{self.base_url}/text-to-speech/{use_voice_id}/stream"
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }
            
            data = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.6,
                    "similarity_boost": 0.8,
                    "style": 0.2,
                    "use_speaker_boost": True
                }
            }
            
            response = requests.post(url, json=data, headers=headers, stream=True)
            
            if response.status_code == 200:
                # Create a unique filename
                text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
                filename = f"speech_{text_hash}.mp3"
                
                # Save audio temporarily (in production, upload to CDN)
                audio_content = response.content
                print(f"✅ ElevenLabs speech generated: {len(audio_content)} bytes")
                
                # For now, return None to use Polly (ElevenLabs needs file hosting)
                # In production: upload to S3/CloudFlare and return public URL
                return None
            else:
                print(f"❌ ElevenLabs error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ ElevenLabs service error: {e}")
            return None

# Global instance
elevenlabs_service = ElevenLabsService()

def get_best_voice_say_tag(text: str) -> str:
    """Get the best possible voice Say tag for the text."""
    # Try ElevenLabs first
    elevenlabs_url = elevenlabs_service.generate_speech_url(text)
    
    if elevenlabs_url:
        # Use ElevenLabs audio
        return f'<Play>{elevenlabs_url}</Play>'
    else:
        # Fall back to best Twilio voice
        return f'<Say voice="Polly.Joanna">{text}</Say>'
