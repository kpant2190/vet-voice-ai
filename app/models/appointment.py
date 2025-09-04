"""Appointment model for managing veterinary appointments."""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from enum import Enum
from ..core.database import Base


class AppointmentStatus(Enum):
    """Appointment status enumeration."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"


class AppointmentType(Enum):
    """Appointment type enumeration."""
    CHECKUP = "checkup"
    VACCINATION = "vaccination"
    SURGERY = "surgery"
    EMERGENCY = "emergency"
    CONSULTATION = "consultation"
    GROOMING = "grooming"
    OTHER = "other"


class Appointment(Base):
    """Appointment model."""
    
    __tablename__ = "appointments"
    
    id = Column(Integer, primary_key=True, index=True)
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=False)
    
    # Pet and owner information
    pet_name = Column(String(100), nullable=False)
    pet_type = Column(String(50))  # dog, cat, bird, etc.
    owner_name = Column(String(255), nullable=False)
    owner_phone = Column(String(20), nullable=False)
    owner_email = Column(String(255))
    
    # Appointment details
    appointment_date = Column(DateTime(timezone=True), nullable=False)
    appointment_type = Column(SQLEnum(AppointmentType), default=AppointmentType.CHECKUP)
    status = Column(SQLEnum(AppointmentStatus), default=AppointmentStatus.PENDING)
    
    # Additional information
    reason = Column(Text)  # Reason for visit
    notes = Column(Text)   # Additional notes
    
    # AI-generated information
    ai_summary = Column(Text)  # Summary of the conversation that led to this appointment
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    clinic = relationship("Clinic", back_populates="appointments")
    
    def __repr__(self):
        return f"<Appointment(id={self.id}, pet_name='{self.pet_name}', owner_name='{self.owner_name}')>"
