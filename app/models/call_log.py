"""Call log model for tracking voice calls and conversations."""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..core.database import Base


class CallLog(Base):
    """Call log model for tracking voice interactions."""
    
    __tablename__ = "call_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=False)
    
    # Call information
    twilio_call_sid = Column(String(50), unique=True, nullable=False, index=True)
    caller_phone = Column(String(20), nullable=False)
    call_duration = Column(Float)  # Duration in seconds
    
    # Call status and outcome
    call_status = Column(String(20))  # answered, busy, no-answer, cancelled, completed, failed
    call_direction = Column(String(20))  # inbound, outbound
    
    # Conversation data
    transcript = Column(Text)  # Full conversation transcript
    ai_summary = Column(Text)  # AI-generated summary of the call
    intent_detected = Column(String(100))  # Main intent (appointment, information, emergency, etc.)
    
    # Appointment related
    appointment_created = Column(Boolean, default=False)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    
    # Audio files (stored URLs or file paths)
    recording_url = Column(String(500))
    
    # AI performance metrics
    confidence_score = Column(Float)  # Overall AI confidence in handling the call
    sentiment_score = Column(Float)   # Caller sentiment (-1 to 1)
    
    # Timestamps
    call_started_at = Column(DateTime(timezone=True))
    call_ended_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    clinic = relationship("Clinic", back_populates="call_logs")
    appointment = relationship("Appointment")
    
    def __repr__(self):
        return f"<CallLog(id={self.id}, twilio_call_sid='{self.twilio_call_sid}', caller_phone='{self.caller_phone}')>"
