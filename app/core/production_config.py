"""Production-ready configuration for AI Veterinary Receptionist."""

import os
from typing import Optional, List, Dict, Any
from pydantic import BaseSettings, validator
from enum import Enum
import secrets


class Environment(str, Enum):
    """Environment types."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    """Logging levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class VoiceProvider(str, Enum):
    """Voice synthesis providers."""
    TWILIO = "twilio"
    ELEVENLABS = "elevenlabs"
    POLLY = "polly"


class LLMProvider(str, Enum):
    """Large Language Model providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure_openai"


class ProductionSettings(BaseSettings):
    """Production-ready settings with validation and security."""
    
    # Application Info
    PROJECT_NAME: str = "AI Veterinary Receptionist"
    VERSION: str = "2.0.0"
    DESCRIPTION: str = "Enterprise AI Receptionist for Veterinary Clinics"
    ENVIRONMENT: Environment = Environment.PRODUCTION
    DEBUG: bool = False
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    API_V2_STR: str = "/api/v2"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    RATE_LIMIT_PER_MINUTE: int = 60
    MAX_CALL_DURATION_SECONDS: int = 600  # 10 minutes max
    
    # Database
    DATABASE_URL: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 30
    
    # Twilio Configuration
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_PHONE_NUMBER: str
    TWILIO_WEBHOOK_URL: Optional[str] = None
    TWILIO_FALLBACK_URL: Optional[str] = None
    
    # AI/ML Configuration
    OPENAI_API_KEY: str
    ANTHROPIC_API_KEY: Optional[str] = None
    ELEVENLABS_API_KEY: Optional[str] = None
    
    # Voice Configuration
    PRIMARY_VOICE_PROVIDER: VoiceProvider = VoiceProvider.POLLY
    FALLBACK_VOICE_PROVIDER: VoiceProvider = VoiceProvider.TWILIO
    DEFAULT_VOICE_ID: str = "Polly.Joanna"
    SPEECH_TIMEOUT_SECONDS: float = 1.0
    TOTAL_TIMEOUT_SECONDS: float = 4.0
    SPEECH_LANGUAGE: str = "en-US"
    
    # LLM Configuration
    LLM_PROVIDER: LLMProvider = LLMProvider.OPENAI
    GPT_MODEL: str = "gpt-4"
    CLAUDE_MODEL: str = "claude-3-sonnet-20240229"
    MAX_TOKENS: int = 500
    TEMPERATURE: float = 0.7
    
    # Business Logic
    CLINIC_NAME: str = "AI Veterinary Clinic"
    CLINIC_PHONE: str = "+1-800-VET-CARE"
    CLINIC_ADDRESS: str = "123 Pet Care Ave, Animal City, AC 12345"
    EMERGENCY_TRANSFER_ENABLED: bool = True
    CALLBACK_PROMISE_MINUTES: int = 10
    
    # Emergency Configuration
    EMERGENCY_KEYWORDS: List[str] = [
        "emergency", "urgent", "dying", "bleeding", "poison", "choking",
        "unconscious", "seizure", "trauma", "accident", "critical"
    ]
    EMERGENCY_VET_NUMBERS: Dict[str, str] = {
        "primary": "+1-800-EMERGENCY",
        "secondary": "+1-800-VET-URGENT",
        "poison_control": "(888) 426-4435"
    }
    
    # Appointment Configuration
    APPOINTMENT_KEYWORDS: List[str] = [
        "appointment", "schedule", "book", "visit", "checkup",
        "vaccination", "vaccine", "wellness", "exam"
    ]
    APPOINTMENT_TYPES: Dict[str, int] = {
        "wellness": 30,
        "vaccination": 15,
        "consultation": 45,
        "surgery": 120,
        "emergency": 60
    }
    
    # Health Keywords
    HEALTH_KEYWORDS: List[str] = [
        "sick", "ill", "vomiting", "diarrhea", "not eating", "limping",
        "cough", "scratching", "lethargic", "pain", "fever", "infection"
    ]
    
    # Monitoring & Observability
    LOG_LEVEL: LogLevel = LogLevel.INFO
    ENABLE_METRICS: bool = True
    ENABLE_TRACING: bool = True
    METRICS_ENDPOINT: str = "/metrics"
    HEALTH_ENDPOINT: str = "/health"
    
    # Feature Flags
    ENABLE_SMS_NOTIFICATIONS: bool = True
    ENABLE_EMAIL_NOTIFICATIONS: bool = True
    ENABLE_CALLBACK_SCHEDULING: bool = True
    ENABLE_PRESCRIPTION_REFILLS: bool = True
    ENABLE_INSURANCE_VERIFICATION: bool = True
    ENABLE_MULTILINGUAL_SUPPORT: bool = False
    ENABLE_VOICE_BIOMETRICS: bool = False
    
    # Rate Limiting & Performance
    MAX_CONCURRENT_CALLS: int = 100
    RESPONSE_TIMEOUT_SECONDS: float = 30.0
    RETRY_ATTEMPTS: int = 3
    CIRCUIT_BREAKER_THRESHOLD: int = 5
    
    # Compliance & Privacy
    ENABLE_CALL_RECORDING: bool = False
    DATA_RETENTION_DAYS: int = 365
    ENABLE_HIPAA_COMPLIANCE: bool = True
    ENABLE_GDPR_COMPLIANCE: bool = True
    PCI_COMPLIANCE_ENABLED: bool = False
    
    # Notification Configuration
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    
    # Cache Configuration
    REDIS_URL: Optional[str] = None
    CACHE_TTL_SECONDS: int = 300
    
    @validator("ENVIRONMENT", pre=True)
    def validate_environment(cls, v):
        """Validate environment setting."""
        if isinstance(v, str):
            return Environment(v.lower())
        return v
    
    @validator("DATABASE_URL")
    def validate_database_url(cls, v):
        """Validate database URL format."""
        if not v.startswith(("postgresql://", "postgres://")):
            raise ValueError("DATABASE_URL must be a PostgreSQL connection string")
        return v
    
    @validator("TWILIO_PHONE_NUMBER")
    def validate_phone_number(cls, v):
        """Validate Twilio phone number format."""
        if not v.startswith("+"):
            raise ValueError("Phone number must include country code (e.g., +1)")
        return v
    
    @validator("SECRET_KEY")
    def validate_secret_key(cls, v):
        """Ensure secret key is sufficiently strong."""
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v
    
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.ENVIRONMENT == Environment.PRODUCTION
    
    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.ENVIRONMENT == Environment.DEVELOPMENT
    
    @property
    def webhook_base_url(self) -> str:
        """Get the base webhook URL."""
        if self.TWILIO_WEBHOOK_URL:
            return self.TWILIO_WEBHOOK_URL
        return f"https://your-domain.com{self.API_V1_STR}"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
production_settings = ProductionSettings()


def get_settings() -> ProductionSettings:
    """Get production settings instance."""
    return production_settings
