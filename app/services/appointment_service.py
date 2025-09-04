"""Appointment service for managing veterinary appointments."""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..models.appointment import Appointment, AppointmentStatus, AppointmentType
from ..models.clinic import Clinic


class AppointmentService:
    """Service for managing appointments."""
    
    def __init__(self, db: Session):
        """Initialize the appointment service."""
        self.db = db
    
    async def create_appointment(
        self,
        clinic_id: int,
        pet_name: str,
        pet_type: str,
        owner_name: str,
        owner_phone: str,
        appointment_date: datetime,
        appointment_type: AppointmentType = AppointmentType.CHECKUP,
        reason: Optional[str] = None,
        owner_email: Optional[str] = None,
        ai_summary: Optional[str] = None
    ) -> Appointment:
        """Create a new appointment."""
        
        appointment = Appointment(
            clinic_id=clinic_id,
            pet_name=pet_name,
            pet_type=pet_type,
            owner_name=owner_name,
            owner_phone=owner_phone,
            owner_email=owner_email,
            appointment_date=appointment_date,
            appointment_type=appointment_type,
            reason=reason,
            ai_summary=ai_summary,
            status=AppointmentStatus.PENDING
        )
        
        self.db.add(appointment)
        self.db.commit()
        self.db.refresh(appointment)
        
        return appointment
    
    async def get_available_slots(
        self,
        clinic_id: int,
        date: datetime,
        duration_minutes: int = 30
    ) -> List[datetime]:
        """Get available appointment slots for a given date."""
        
        # Get clinic business hours
        clinic = self.db.query(Clinic).filter(Clinic.id == clinic_id).first()
        if not clinic:
            return []
        
        # For simplicity, assume 9 AM to 5 PM with 30-minute slots
        # In production, you'd parse the clinic's business_hours JSON
        start_hour = 9
        end_hour = 17
        slot_duration = timedelta(minutes=duration_minutes)
        
        # Generate all possible slots for the date
        slots = []
        current_slot = date.replace(hour=start_hour, minute=0, second=0, microsecond=0)
        end_time = date.replace(hour=end_hour, minute=0, second=0, microsecond=0)
        
        while current_slot < end_time:
            slots.append(current_slot)
            current_slot += slot_duration
        
        # Get existing appointments for this date
        existing_appointments = self.db.query(Appointment).filter(
            Appointment.clinic_id == clinic_id,
            Appointment.appointment_date >= date.replace(hour=0, minute=0, second=0),
            Appointment.appointment_date < date.replace(hour=23, minute=59, second=59),
            Appointment.status.in_([AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED])
        ).all()
        
        # Remove slots that are already booked
        booked_slots = {apt.appointment_date for apt in existing_appointments}
        available_slots = [slot for slot in slots if slot not in booked_slots]
        
        return available_slots
    
    async def find_next_available_slot(
        self,
        clinic_id: int,
        preferred_date: Optional[datetime] = None,
        days_ahead: int = 7
    ) -> Optional[datetime]:
        """Find the next available appointment slot."""
        
        start_date = preferred_date or datetime.now()
        
        for day_offset in range(days_ahead):
            check_date = start_date + timedelta(days=day_offset)
            
            # Skip weekends (basic business logic)
            if check_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
                continue
                
            available_slots = await self.get_available_slots(clinic_id, check_date)
            if available_slots:
                return available_slots[0]  # Return first available slot
        
        return None
    
    async def update_appointment_status(
        self,
        appointment_id: int,
        status: AppointmentStatus
    ) -> Optional[Appointment]:
        """Update appointment status."""
        
        appointment = self.db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if appointment:
            appointment.status = status
            self.db.commit()
            self.db.refresh(appointment)
        
        return appointment
    
    async def get_appointments_by_phone(
        self,
        clinic_id: int,
        phone_number: str
    ) -> List[Appointment]:
        """Get appointments by phone number."""
        
        return self.db.query(Appointment).filter(
            Appointment.clinic_id == clinic_id,
            Appointment.owner_phone == phone_number
        ).order_by(Appointment.appointment_date.desc()).all()
    
    async def parse_appointment_request(
        self,
        conversation_text: str,
        entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse appointment information from conversation text and entities."""
        
        appointment_info = {}
        
        # Extract pet name
        if "potential_names" in entities and entities["potential_names"]:
            appointment_info["pet_name"] = entities["potential_names"][0]
        
        # Extract phone number
        if "phone_numbers" in entities and entities["phone_numbers"]:
            appointment_info["owner_phone"] = entities["phone_numbers"][0]
        
        # Simple keyword matching for pet type
        text_lower = conversation_text.lower()
        if "dog" in text_lower:
            appointment_info["pet_type"] = "dog"
        elif "cat" in text_lower:
            appointment_info["pet_type"] = "cat"
        elif "bird" in text_lower:
            appointment_info["pet_type"] = "bird"
        elif "rabbit" in text_lower:
            appointment_info["pet_type"] = "rabbit"
        
        # Detect appointment type
        if any(word in text_lower for word in ["checkup", "check-up", "routine", "wellness"]):
            appointment_info["appointment_type"] = AppointmentType.CHECKUP
        elif any(word in text_lower for word in ["vaccination", "vaccine", "shot"]):
            appointment_info["appointment_type"] = AppointmentType.VACCINATION
        elif any(word in text_lower for word in ["surgery", "operation", "spay", "neuter"]):
            appointment_info["appointment_type"] = AppointmentType.SURGERY
        elif any(word in text_lower for word in ["emergency", "urgent", "hurt", "injured"]):
            appointment_info["appointment_type"] = AppointmentType.EMERGENCY
        elif any(word in text_lower for word in ["grooming", "bath", "nail", "trim"]):
            appointment_info["appointment_type"] = AppointmentType.GROOMING
        else:
            appointment_info["appointment_type"] = AppointmentType.CONSULTATION
        
        return appointment_info
