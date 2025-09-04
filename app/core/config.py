"""Core configuration settings for the Vet Voice AI application."""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings."""
    
    # Project Info
    PROJECT_NAME: str = "Vet Voice AI"
    API_V1_STR: str = "/api"
    PORT: int = int(os.getenv("PORT", 8000))
    
    # Security
    SECRET_KEY: str = "temp_secret_key_change_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/vet_voice_ai"
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: Optional[str] = None
    
    # API Keys
    OPENAI_API_KEY: str = "temp_openai_key"
    ANTHROPIC_API_KEY: Optional[str] = None
    ELEVENLABS_API_KEY: str = "temp_elevenlabs_key"
    
    # Twilio Configuration
    TWILIO_ACCOUNT_SID: str = "temp_twilio_sid"
    TWILIO_AUTH_TOKEN: str = "temp_twilio_token"
    TWILIO_PHONE_NUMBER: str = "+1234567890"
    
    # Voice Settings
    DEFAULT_VOICE_ID: str = "temp_voice_id"
    SPEECH_MODEL: str = "whisper-1"
    
    # LLM Settings
    DEFAULT_LLM_PROVIDER: str = "openai"  # or "anthropic"
    GPT_MODEL: str = "gpt-4-1106-preview"
    CLAUDE_MODEL: str = "claude-3-sonnet-20240229"
    
    # Advanced Features Configuration
    PRESCRIPTION_REFILLS_ENABLED: bool = True
    EMERGENCY_TRIAGE_ENABLED: bool = True
    INSURANCE_VERIFICATION_ENABLED: bool = True
    SMS_NOTIFICATIONS_ENABLED: bool = True
    
    # Emergency Services
    ASPCA_POISON_CONTROL_NUMBER: str = "(888) 426-4435"
    EMERGENCY_TRANSFER_ENABLED: bool = True
    
    # Environment
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


def get_settings():
    """Create settings with error handling."""
    try:
        return Settings()
    except Exception as e:
        print(f"Warning: Error loading settings: {e}")
        print("Using fallback settings...")
        # Return settings with minimal configuration for Railway startup
        return Settings(
            SECRET_KEY="temp_secret_key_change_in_production",
            DATABASE_URL="postgresql://postgres:password@localhost:5432/vet_voice_ai",
            OPENAI_API_KEY="temp_openai_key",
            ELEVENLABS_API_KEY="temp_elevenlabs_key",
            TWILIO_ACCOUNT_SID="temp_twilio_sid",
            TWILIO_AUTH_TOKEN="temp_twilio_token",
            TWILIO_PHONE_NUMBER="+1234567890",
            DEFAULT_VOICE_ID="temp_voice_id"
        )


# Global settings instance
settings = get_settings()
