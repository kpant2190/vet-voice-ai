"""Prescription refill service for handling medication requests."""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..models.clinic import Clinic
from ..models.appointment import Appointment
from ..core.database import get_db


class PrescriptionRefillService:
    """Handles prescription refill requests and automation."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def process_refill_request(
        self,
        pet_name: str,
        owner_phone: str,
        medication_name: str,
        clinic_id: int
    ) -> Dict[str, Any]:
        """Process a prescription refill request from voice call."""
        
        # Find pet's previous appointments and medications
        previous_appointments = self.db.query(Appointment).filter(
            Appointment.clinic_id == clinic_id,
            Appointment.owner_phone == owner_phone,
            Appointment.pet_name.ilike(f"%{pet_name}%")
        ).order_by(Appointment.appointment_date.desc()).limit(5).all()
        
        if not previous_appointments:
            return {
                "status": "not_found",
                "message": f"I couldn't find any previous appointments for {pet_name}. Please provide your pet's full name and your phone number.",
                "requires_verification": True
            }
        
        # Check if medication was previously prescribed
        medication_history = await self._check_medication_history(
            previous_appointments, medication_name
        )
        
        if medication_history["found"]:
            # Create refill request
            refill_request = await self._create_refill_request(
                pet_name=pet_name,
                owner_phone=owner_phone,
                medication_name=medication_name,
                clinic_id=clinic_id,
                last_prescription_date=medication_history["last_prescribed"]
            )
            
            return {
                "status": "success",
                "message": f"I've submitted a refill request for {pet_name}'s {medication_name}. The veterinarian will review it and you'll receive a confirmation within 2 hours. You can pick it up at your preferred pharmacy.",
                "refill_id": refill_request["id"],
                "estimated_ready_time": "2 hours",
                "requires_approval": True
            }
        else:
            return {
                "status": "verification_needed",
                "message": f"I need to verify the medication details with our veterinarian. Could you please spell the medication name and tell me when it was last prescribed for {pet_name}?",
                "requires_human_review": True
            }
    
    async def _check_medication_history(
        self, appointments: List[Appointment], medication_name: str
    ) -> Dict[str, Any]:
        """Check if medication was previously prescribed."""
        
        # This would integrate with practice management software
        # For now, we'll use a simple keyword search in appointment notes
        
        medication_keywords = medication_name.lower().split()
        
        for appointment in appointments:
            if appointment.notes:
                notes_lower = appointment.notes.lower()
                if any(keyword in notes_lower for keyword in medication_keywords):
                    return {
                        "found": True,
                        "last_prescribed": appointment.appointment_date,
                        "prescription_notes": appointment.notes
                    }
        
        return {"found": False}
    
    async def _create_refill_request(
        self,
        pet_name: str,
        owner_phone: str,
        medication_name: str,
        clinic_id: int,
        last_prescription_date: datetime
    ) -> Dict[str, Any]:
        """Create a refill request for veterinarian approval."""
        
        # In a real implementation, this would integrate with:
        # - Practice management software
        # - Electronic prescription systems
        # - Pharmacy networks
        
        refill_request = {
            "id": f"RX{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "pet_name": pet_name,
            "owner_phone": owner_phone,
            "medication_name": medication_name,
            "clinic_id": clinic_id,
            "last_prescription_date": last_prescription_date,
            "request_date": datetime.now(),
            "status": "pending_approval",
            "estimated_ready": datetime.now() + timedelta(hours=2)
        }
        
        # TODO: Save to database and send to practice management system
        
        return refill_request
    
    async def detect_refill_intent(self, user_message: str) -> Dict[str, Any]:
        """Detect if the caller is requesting a prescription refill."""
        
        refill_keywords = [
            "refill", "prescription", "medication", "medicine", "pills",
            "tablets", "antibiotics", "heartworm", "flea", "tick",
            "pain medication", "thyroid", "diabetes", "insulin"
        ]
        
        message_lower = user_message.lower()
        
        # Check for refill intent
        has_refill_keywords = any(keyword in message_lower for keyword in refill_keywords)
        
        if has_refill_keywords:
            # Extract potential medication names
            potential_medications = await self._extract_medication_names(user_message)
            
            return {
                "is_refill_request": True,
                "confidence": 0.9 if len(potential_medications) > 0 else 0.7,
                "potential_medications": potential_medications,
                "requires_information": ["pet_name", "medication_name", "owner_phone"]
            }
        
        return {"is_refill_request": False, "confidence": 0.0}
    
    async def _extract_medication_names(self, text: str) -> List[str]:
        """Extract potential medication names from text."""
        
        # Common vet medications (simplified list)
        common_vet_medications = [
            "carprofen", "rimadyl", "metacam", "previcox", "deramaxx",
            "heartgard", "nexgard", "bravecto", "seresto", "frontline",
            "advantage", "revolution", "comfortis", "trifexis",
            "amoxicillin", "cephalexin", "clindamycin", "enrofloxacin",
            "metronidazole", "prednisone", "gabapentin", "tramadol",
            "insulin", "levothyroxine", "enalapril", "furosemide"
        ]
        
        text_lower = text.lower()
        found_medications = []
        
        for medication in common_vet_medications:
            if medication in text_lower:
                found_medications.append(medication.title())
        
        return found_medications
    
    def generate_refill_response(self, refill_result: Dict[str, Any]) -> str:
        """Generate appropriate response based on refill request result."""
        
        if refill_result["status"] == "success":
            return refill_result["message"]
        
        elif refill_result["status"] == "not_found":
            return (
                "I couldn't find any previous appointments in our system. "
                "Let me transfer you to our staff who can help verify your pet's "
                "information and process your refill request."
            )
        
        elif refill_result["status"] == "verification_needed":
            return refill_result["message"]
        
        else:
            return (
                "I'm having trouble processing your refill request right now. "
                "Let me connect you with our staff who can help you immediately."
            )
