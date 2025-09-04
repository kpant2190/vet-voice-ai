"""Clinic model for veterinary clinic information."""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..core.database import Base


class Clinic(Base):
    """Veterinary clinic model."""
    
    __tablename__ = "clinics"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    phone_number = Column(String(20), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    address = Column(Text)
    
    # Business hours (stored as JSON string or separate fields)
    business_hours = Column(Text)  # JSON format: {"monday": {"open": "08:00", "close": "18:00"}, ...}
    
    # Settings
    ai_enabled = Column(Boolean, default=True)
    auto_booking_enabled = Column(Boolean, default=True)
    
    # Voice settings
    voice_id = Column(String(100))  # ElevenLabs voice ID
    voice_greeting = Column(Text)   # Custom greeting message
    
    # AI behavior settings
    llm_provider = Column(String(50), default="openai")  # "openai" or "anthropic"
    system_prompt = Column(Text)    # Custom system prompt for the AI
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    appointments = relationship("Appointment", back_populates="clinic")
    call_logs = relationship("CallLog", back_populates="clinic")
    
    def __repr__(self):
        return f"<Clinic(id={self.id}, name='{self.name}')>"
