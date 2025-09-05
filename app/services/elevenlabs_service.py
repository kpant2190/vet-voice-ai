"""ElevenLabs TTS service for high-quality voice synthesis."""

import os
import requests
import tempfile
from typing import Optional
import base64

class ElevenLabsService:
    """Service for generating high-quality speech using ElevenLabs."""
    
    def __init__(self):
        self.api_key = os.getenv('ELEVENLABS_API_KEY')
        self.voice_id = os.getenv('DEFAULT_VOICE_ID', 'cgSgspJ2msm6clMCkdW9')
        self.base_url = "https://api.elevenlabs.io/v1"
        
    def generate_speech(self, text: str, voice_id: Optional[str] = None) -> Optional[str]:
        """Generate speech and return a publicly accessible URL."""
        try:
            if not self.api_key:
                print("❌ ElevenLabs API key not found")
                return None
                
            use_voice_id = voice_id or self.voice_id
            
            url = f"{self.base_url}/text-to-speech/{use_voice_id}"
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }
            
            data = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                    "style": 0.0,
                    "use_speaker_boost": True
                }
            }
            
            response = requests.post(url, json=data, headers=headers)
            
            if response.status_code == 200:
                # For now, return None to fall back to Twilio voice
                # In production, you'd upload this to a CDN and return the URL
                print(f"✅ ElevenLabs speech generated successfully")
                return None  # Fallback to Twilio for now
            else:
                print(f"❌ ElevenLabs error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ ElevenLabs service error: {e}")
            return None
    
    def get_voice_url(self, text: str) -> Optional[str]:
        """Get a publicly accessible URL for the generated speech."""
        # For now, return None to use Twilio's voice
        # This would need to be implemented with file hosting
        return None

# Global instance
elevenlabs_service = ElevenLabsService()
