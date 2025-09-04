"""Emergency triage service for handling urgent pet situations."""

from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime


class EmergencyLevel(Enum):
    """Emergency severity levels."""
    CRITICAL = "critical"        # Immediate veterinary attention
    URGENT = "urgent"           # Same day appointment needed
    MODERATE = "moderate"       # Next day appointment acceptable
    NON_EMERGENCY = "non_emergency"  # Regular appointment fine


class EmergencyTriageService:
    """Handles emergency assessment and triage for pet calls."""
    
    def __init__(self):
        self.critical_symptoms = [
            "not breathing", "unconscious", "seizure", "bleeding heavily",
            "can't walk", "hit by car", "poisoned", "choking",
            "difficulty breathing", "collapsed", "severe trauma",
            "bloated stomach", "pale gums", "blue tongue", "convulsions"
        ]
        
        self.urgent_symptoms = [
            "vomiting blood", "diarrhea with blood", "not eating for 2 days",
            "difficulty urinating", "straining to defecate", "limping badly",
            "eye injury", "excessive drooling", "distended abdomen",
            "rapid breathing", "weakness", "hiding", "crying in pain"
        ]
        
        self.poison_keywords = [
            "chocolate", "grapes", "raisins", "onions", "garlic", "xylitol",
            "antifreeze", "rat poison", "cleaning products", "medications",
            "plants", "mushrooms", "insecticide", "fertilizer"
        ]
    
    async def assess_emergency_level(self, caller_description: str) -> Dict[str, Any]:
        """Assess the emergency level based on caller's description."""
        
        description_lower = caller_description.lower()
        
        # Check for critical symptoms
        critical_found = [symptom for symptom in self.critical_symptoms 
                         if symptom in description_lower]
        
        if critical_found:
            return {
                "level": EmergencyLevel.CRITICAL,
                "confidence": 0.95,
                "symptoms_detected": critical_found,
                "action": "immediate_emergency",
                "message": "This sounds like a critical emergency. Please bring your pet to our emergency clinic immediately or call our emergency hotline.",
                "estimated_wait_time": "immediate"
            }
        
        # Check for urgent symptoms
        urgent_found = [symptom for symptom in self.urgent_symptoms 
                       if symptom in description_lower]
        
        if urgent_found:
            return {
                "level": EmergencyLevel.URGENT,
                "confidence": 0.85,
                "symptoms_detected": urgent_found,
                "action": "same_day_appointment",
                "message": "This requires urgent attention. Let me find you an appointment today.",
                "estimated_wait_time": "within 4 hours"
            }
        
        # Check for poison exposure
        poison_found = [poison for poison in self.poison_keywords 
                       if poison in description_lower]
        
        if poison_found and any(word in description_lower for word in ["ate", "ingested", "swallowed", "consumed"]):
            return await self._handle_poison_exposure(poison_found, description_lower)
        
        # Default to moderate if symptoms mentioned but not critical/urgent
        if any(word in description_lower for word in ["sick", "hurt", "pain", "problem", "wrong"]):
            return {
                "level": EmergencyLevel.MODERATE,
                "confidence": 0.6,
                "symptoms_detected": [],
                "action": "schedule_soon",
                "message": "I'd like to get your pet seen soon. Let me check our availability for today or tomorrow.",
                "estimated_wait_time": "within 24 hours"
            }
        
        return {
            "level": EmergencyLevel.NON_EMERGENCY,
            "confidence": 0.8,
            "symptoms_detected": [],
            "action": "regular_appointment",
            "message": "Let me help you schedule a regular appointment for your pet.",
            "estimated_wait_time": "within a week"
        }
    
    async def _handle_poison_exposure(self, poisons_found: List[str], description: str) -> Dict[str, Any]:
        """Handle specific poison exposure cases."""
        
        critical_poisons = ["antifreeze", "rat poison", "xylitol", "grapes", "raisins"]
        
        if any(poison in poisons_found for poison in critical_poisons):
            return {
                "level": EmergencyLevel.CRITICAL,
                "confidence": 0.98,
                "symptoms_detected": poisons_found,
                "action": "immediate_poison_emergency",
                "message": f"This is a poison emergency! Your pet has ingested {', '.join(poisons_found)} which can be fatal. Please call the ASPCA Poison Control at (888) 426-4435 immediately and bring your pet to our emergency clinic right now.",
                "estimated_wait_time": "immediate",
                "poison_control_number": "(888) 426-4435",
                "additional_instructions": "Do NOT induce vomiting unless instructed by poison control."
            }
        
        # Less critical but still urgent poisons
        return {
            "level": EmergencyLevel.URGENT,
            "confidence": 0.9,
            "symptoms_detected": poisons_found,
            "action": "poison_consultation",
            "message": f"Your pet has ingested {', '.join(poisons_found)}. Let me connect you with our veterinarian immediately for guidance. Please have the product packaging ready.",
            "estimated_wait_time": "within 30 minutes",
            "poison_control_number": "(888) 426-4435"
        }
    
    def generate_emergency_response(self, assessment: Dict[str, Any]) -> str:
        """Generate appropriate response based on emergency assessment."""
        
        level = assessment["level"]
        message = assessment["message"]
        
        if level == EmergencyLevel.CRITICAL:
            response = f"🚨 EMERGENCY: {message}"
            
            if "poison_control_number" in assessment:
                response += f" The ASPCA Poison Control number is {assessment['poison_control_number']}."
            
            if "additional_instructions" in assessment:
                response += f" Important: {assessment['additional_instructions']}"
            
            response += " I'm also notifying our emergency veterinarian right now."
            
        elif level == EmergencyLevel.URGENT:
            response = f"⚠️ URGENT: {message} I'm checking for the earliest available appointment now."
            
        elif level == EmergencyLevel.MODERATE:
            response = f"📅 {message} I can check our schedule for the next day or two."
            
        else:
            response = message
        
        return response
    
    async def get_emergency_instructions(self, emergency_type: str) -> Dict[str, Any]:
        """Provide first aid instructions for common emergencies."""
        
        instructions = {
            "choking": {
                "immediate_steps": [
                    "Open your pet's mouth carefully",
                    "Look for visible objects and try to remove with tweezers",
                    "Do NOT stick your finger down their throat",
                    "If object is visible but stuck, come to emergency clinic immediately"
                ],
                "warning": "Do not attempt to remove objects that are firmly lodged"
            },
            
            "bleeding": {
                "immediate_steps": [
                    "Apply direct pressure with clean cloth or towel",
                    "Do not remove the cloth if it becomes soaked - add more layers",
                    "Elevate the injured area if possible",
                    "Keep your pet calm and still"
                ],
                "warning": "Severe bleeding requires immediate veterinary attention"
            },
            
            "seizure": {
                "immediate_steps": [
                    "Do NOT put anything in your pet's mouth",
                    "Keep your pet away from stairs and furniture",
                    "Time the seizure",
                    "Stay calm and speak softly",
                    "Note what happened before the seizure"
                ],
                "warning": "Seizures lasting more than 2 minutes require immediate emergency care"
            },
            
            "heatstroke": {
                "immediate_steps": [
                    "Move your pet to a cool, shaded area",
                    "Apply cool (not cold) water to paw pads and ears",
                    "Offer small amounts of cool water to drink",
                    "Use fans to increase air circulation"
                ],
                "warning": "Heatstroke can be fatal - seek immediate veterinary care"
            }
        }
        
        return instructions.get(emergency_type, {
            "immediate_steps": ["Keep your pet calm", "Come to the clinic immediately"],
            "warning": "When in doubt, seek immediate veterinary attention"
        })
    
    def get_emergency_contacts(self, clinic_id: int) -> Dict[str, str]:
        """Get emergency contact information for the clinic."""
        
        # This would be pulled from the clinic database
        return {
            "emergency_line": "+1-555-VET-HELP",
            "after_hours_clinic": "24/7 Emergency Animal Hospital",
            "poison_control": "(888) 426-4435",
            "emergency_address": "123 Emergency Vet Blvd, City, State 12345"
        }
    
    async def should_transfer_immediately(self, assessment: Dict[str, Any]) -> bool:
        """Determine if call should be transferred to emergency vet immediately."""
        
        return (
            assessment["level"] == EmergencyLevel.CRITICAL or
            (assessment["level"] == EmergencyLevel.URGENT and 
             assessment["confidence"] > 0.9)
        )
