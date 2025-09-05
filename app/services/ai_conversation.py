"""Advanced AI Conversation Engine for Veterinary Receptionist."""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

import openai
from anthropic import Anthropic

from ..core.production_config import get_settings


class ConversationState(str, Enum):
    """Conversation state tracking."""
    GREETING = "greeting"
    LISTENING = "listening"
    EMERGENCY = "emergency"
    APPOINTMENT = "appointment"
    HEALTH_INQUIRY = "health_inquiry"
    PRESCRIPTION = "prescription"
    INSURANCE = "insurance"
    CALLBACK_SCHEDULED = "callback_scheduled"
    ESCALATION = "escalation"
    COMPLETED = "completed"


class Intent(str, Enum):
    """Conversation intents."""
    EMERGENCY = "emergency"
    APPOINTMENT_NEW = "appointment_new"
    APPOINTMENT_MODIFY = "appointment_modify"
    HEALTH_QUESTION = "health_question"
    PRESCRIPTION_REFILL = "prescription_refill"
    INSURANCE_INQUIRY = "insurance_inquiry"
    GENERAL_INFO = "general_info"
    CALLBACK_REQUEST = "callback_request"
    UNKNOWN = "unknown"


class Urgency(str, Enum):
    """Urgency levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ConversationContext:
    """Context for ongoing conversation."""
    call_sid: str
    phone_number: str
    state: ConversationState
    intent: Optional[Intent]
    urgency: Urgency
    pet_info: Dict[str, Any]
    customer_info: Dict[str, Any]
    conversation_history: List[Dict[str, str]]
    extracted_data: Dict[str, Any]
    start_time: datetime
    last_activity: datetime
    escalation_reason: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "call_sid": self.call_sid,
            "phone_number": self.phone_number,
            "state": self.state.value,
            "intent": self.intent.value if self.intent else None,
            "urgency": self.urgency.value,
            "pet_info": self.pet_info,
            "customer_info": self.customer_info,
            "conversation_history": self.conversation_history,
            "extracted_data": self.extracted_data,
            "start_time": self.start_time.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "escalation_reason": self.escalation_reason
        }


class AIConversationEngine:
    """Advanced AI conversation engine with context awareness."""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = logging.getLogger(__name__)
        self.conversations: Dict[str, ConversationContext] = {}
        
        # Initialize AI clients
        if self.settings.LLM_PROVIDER.value == "openai":
            self.openai_client = openai.OpenAI(api_key=self.settings.OPENAI_API_KEY)
        elif self.settings.LLM_PROVIDER.value == "anthropic":
            self.anthropic_client = Anthropic(api_key=self.settings.ANTHROPIC_API_KEY)
    
    async def start_conversation(self, call_sid: str, phone_number: str) -> ConversationContext:
        """Start a new conversation."""
        context = ConversationContext(
            call_sid=call_sid,
            phone_number=phone_number,
            state=ConversationState.GREETING,
            intent=None,
            urgency=Urgency.LOW,
            pet_info={},
            customer_info={},
            conversation_history=[],
            extracted_data={},
            start_time=datetime.now(),
            last_activity=datetime.now()
        )
        
        self.conversations[call_sid] = context
        self.logger.info(f"Started conversation for {call_sid} from {phone_number}")
        return context
    
    async def process_speech(self, call_sid: str, speech_text: str) -> Tuple[str, ConversationState]:
        """Process speech input and return response with new state."""
        context = self.conversations.get(call_sid)
        if not context:
            context = await self.start_conversation(call_sid, "unknown")
        
        # Update conversation history
        context.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "speaker": "caller",
            "text": speech_text,
            "intent": await self._classify_intent(speech_text)
        })
        
        # Classify intent and urgency
        intent = await self._classify_intent(speech_text)
        urgency = await self._assess_urgency(speech_text, intent)
        
        context.intent = intent
        context.urgency = urgency
        context.last_activity = datetime.now()
        
        # Generate response based on intent
        response_text, new_state = await self._generate_response(context, speech_text)
        
        # Update conversation history with AI response
        context.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "speaker": "ai",
            "text": response_text,
            "state": new_state.value
        })
        
        context.state = new_state
        
        return response_text, new_state
    
    async def _classify_intent(self, speech_text: str) -> Intent:
        """Classify the intent of the speech using AI."""
        speech_lower = speech_text.lower()
        
        # Emergency detection (highest priority)
        if any(keyword in speech_lower for keyword in self.settings.EMERGENCY_KEYWORDS):
            return Intent.EMERGENCY
        
        # Appointment-related
        if any(keyword in speech_lower for keyword in self.settings.APPOINTMENT_KEYWORDS):
            if any(word in speech_lower for word in ["change", "cancel", "reschedule", "move"]):
                return Intent.APPOINTMENT_MODIFY
            return Intent.APPOINTMENT_NEW
        
        # Health questions
        if any(keyword in speech_lower for keyword in self.settings.HEALTH_KEYWORDS):
            return Intent.HEALTH_QUESTION
        
        # Prescription refills
        if any(word in speech_lower for word in ["prescription", "medication", "refill", "medicine"]):
            return Intent.PRESCRIPTION_REFILL
        
        # Insurance
        if any(word in speech_lower for word in ["insurance", "coverage", "claim", "billing"]):
            return Intent.INSURANCE_INQUIRY
        
        # Callback request
        if any(word in speech_lower for word in ["call back", "callback", "call me", "phone me"]):
            return Intent.CALLBACK_REQUEST
        
        return Intent.UNKNOWN
    
    async def _assess_urgency(self, speech_text: str, intent: Intent) -> Urgency:
        """Assess the urgency of the request."""
        speech_lower = speech_text.lower()
        
        # Critical urgency indicators
        critical_words = [
            "dying", "dead", "unconscious", "bleeding", "poison", "choking",
            "seizure", "can't breathe", "collapse", "emergency"
        ]
        if any(word in speech_lower for word in critical_words):
            return Urgency.CRITICAL
        
        # High urgency indicators
        high_words = [
            "urgent", "asap", "immediately", "right now", "can't wait",
            "severe pain", "vomiting blood", "difficulty breathing"
        ]
        if any(word in speech_lower for word in high_words):
            return Urgency.HIGH
        
        # Intent-based urgency
        if intent == Intent.EMERGENCY:
            return Urgency.CRITICAL
        elif intent == Intent.HEALTH_QUESTION:
            return Urgency.MEDIUM
        elif intent == Intent.APPOINTMENT_NEW:
            return Urgency.LOW
        
        return Urgency.LOW
    
    async def _generate_response(self, context: ConversationContext, speech_text: str) -> Tuple[str, ConversationState]:
        """Generate AI response based on context and intent."""
        
        # Emergency handling
        if context.intent == Intent.EMERGENCY or context.urgency == Urgency.CRITICAL:
            response = await self._handle_emergency(context, speech_text)
            return response, ConversationState.EMERGENCY
        
        # Appointment handling
        elif context.intent in [Intent.APPOINTMENT_NEW, Intent.APPOINTMENT_MODIFY]:
            response = await self._handle_appointment(context, speech_text)
            return response, ConversationState.APPOINTMENT
        
        # Health inquiry handling
        elif context.intent == Intent.HEALTH_QUESTION:
            response = await self._handle_health_inquiry(context, speech_text)
            return response, ConversationState.HEALTH_INQUIRY
        
        # Prescription handling
        elif context.intent == Intent.PRESCRIPTION_REFILL:
            response = await self._handle_prescription(context, speech_text)
            return response, ConversationState.PRESCRIPTION
        
        # Insurance handling
        elif context.intent == Intent.INSURANCE_INQUIRY:
            response = await self._handle_insurance(context, speech_text)
            return response, ConversationState.INSURANCE
        
        # Default handling
        else:
            response = await self._handle_general_inquiry(context, speech_text)
            return response, ConversationState.LISTENING
    
    async def _handle_emergency(self, context: ConversationContext, speech_text: str) -> str:
        """Handle emergency situations."""
        self.logger.critical(f"EMERGENCY detected: {speech_text} from {context.phone_number}")
        
        # Extract emergency details using AI
        emergency_details = await self._extract_emergency_details(speech_text)
        context.extracted_data.update(emergency_details)
        
        if "poison" in speech_text.lower():
            return (
                f"This is a POISON EMERGENCY! Please hang up immediately and call "
                f"the ASPCA Poison Control Hotline at {self.settings.EMERGENCY_VET_NUMBERS['poison_control']} "
                f"right now! They are available 24/7. Time is critical!"
            )
        
        return (
            f"This is an EMERGENCY! Please hang up immediately and call your nearest "
            f"emergency veterinary hospital or our emergency line at "
            f"{self.settings.EMERGENCY_VET_NUMBERS['primary']}. "
            f"If your pet is unconscious or in severe distress, go to the nearest "
            f"emergency vet clinic immediately. Time is critical for your pet's safety!"
        )
    
    async def _handle_appointment(self, context: ConversationContext, speech_text: str) -> str:
        """Handle appointment requests."""
        # Extract appointment details
        appointment_details = await self._extract_appointment_details(speech_text)
        context.extracted_data.update(appointment_details)
        
        if context.intent == Intent.APPOINTMENT_MODIFY:
            return (
                f"I understand you need to modify an existing appointment. "
                f"Our scheduling team will call you back within {self.settings.CALLBACK_PROMISE_MINUTES} "
                f"minutes at {context.phone_number} to help you reschedule. "
                f"Please have your appointment confirmation number ready if you have it."
            )
        
        pet_type = appointment_details.get("pet_type", "pet")
        reason = appointment_details.get("reason", "checkup")
        
        return (
            f"Perfect! I'll help you schedule an appointment for your {pet_type}. "
            f"I've noted that you mentioned {reason}. Our scheduling team will call you "
            f"back within {self.settings.CALLBACK_PROMISE_MINUTES} minutes at "
            f"{context.phone_number} to check our availability and book the best time for you."
        )
    
    async def _handle_health_inquiry(self, context: ConversationContext, speech_text: str) -> str:
        """Handle health-related questions."""
        # Extract health details
        health_details = await self._extract_health_details(speech_text)
        context.extracted_data.update(health_details)
        
        symptoms = health_details.get("symptoms", [])
        pet_type = health_details.get("pet_type", "pet")
        
        if context.urgency == Urgency.HIGH:
            return (
                f"I understand your {pet_type} is showing concerning symptoms. "
                f"Based on what you've described, this sounds like it needs prompt attention. "
                f"One of our experienced veterinarians will call you back within "
                f"{self.settings.CALLBACK_PROMISE_MINUTES} minutes to discuss the symptoms "
                f"and determine if you need to bring your {pet_type} in today."
            )
        
        return (
            f"I understand you have questions about your {pet_type}'s health. "
            f"Our veterinary team will call you back within "
            f"{self.settings.CALLBACK_PROMISE_MINUTES} minutes to discuss your concerns "
            f"and provide professional guidance on the best care for your {pet_type}."
        )
    
    async def _handle_prescription(self, context: ConversationContext, speech_text: str) -> str:
        """Handle prescription refill requests."""
        return (
            f"I can help you with prescription refills. Our pharmacy team will call you "
            f"back within {self.settings.CALLBACK_PROMISE_MINUTES} minutes to verify "
            f"your pet's prescription information and process the refill. Please have "
            f"your pet's information and current prescription details ready."
        )
    
    async def _handle_insurance(self, context: ConversationContext, speech_text: str) -> str:
        """Handle insurance-related inquiries."""
        return (
            f"I'll connect you with our insurance specialist who can help with coverage "
            f"questions, claims, and billing. They will call you back within "
            f"{self.settings.CALLBACK_PROMISE_MINUTES} minutes to assist you with "
            f"your insurance needs."
        )
    
    async def _handle_general_inquiry(self, context: ConversationContext, speech_text: str) -> str:
        """Handle general inquiries."""
        return (
            f"Thank you for calling {self.settings.CLINIC_NAME}! I want to make sure "
            f"I understand exactly how we can help you and your pet. Our team will "
            f"call you back within {self.settings.CALLBACK_PROMISE_MINUTES} minutes "
            f"to discuss your needs and provide the best possible care."
        )
    
    async def _extract_emergency_details(self, speech_text: str) -> Dict[str, Any]:
        """Extract emergency details using AI."""
        # This would use the LLM to extract structured data
        # For now, return basic extraction
        return {
            "emergency_type": "general",
            "symptoms": [],
            "timestamp": datetime.now().isoformat()
        }
    
    async def _extract_appointment_details(self, speech_text: str) -> Dict[str, Any]:
        """Extract appointment details using AI."""
        # Basic extraction - would be enhanced with LLM
        details = {
            "pet_type": "pet",
            "reason": "checkup",
            "preferred_time": None,
            "timestamp": datetime.now().isoformat()
        }
        
        speech_lower = speech_text.lower()
        
        # Extract pet type
        if "dog" in speech_lower:
            details["pet_type"] = "dog"
        elif "cat" in speech_lower:
            details["pet_type"] = "cat"
        elif "bird" in speech_lower:
            details["pet_type"] = "bird"
        elif "rabbit" in speech_lower:
            details["pet_type"] = "rabbit"
        
        # Extract reason
        if any(word in speech_lower for word in ["vaccination", "vaccine", "shot"]):
            details["reason"] = "vaccination"
        elif any(word in speech_lower for word in ["checkup", "check up", "wellness", "exam"]):
            details["reason"] = "wellness exam"
        elif any(word in speech_lower for word in ["sick", "ill", "not feeling well"]):
            details["reason"] = "illness consultation"
        
        return details
    
    async def _extract_health_details(self, speech_text: str) -> Dict[str, Any]:
        """Extract health-related details using AI."""
        details = {
            "pet_type": "pet",
            "symptoms": [],
            "duration": None,
            "severity": "unknown",
            "timestamp": datetime.now().isoformat()
        }
        
        speech_lower = speech_text.lower()
        
        # Extract symptoms
        symptom_keywords = {
            "vomiting": ["vomiting", "throwing up", "puking"],
            "diarrhea": ["diarrhea", "loose stool", "runny stool"],
            "lethargy": ["lethargic", "tired", "sleepy", "no energy"],
            "loss_of_appetite": ["not eating", "won't eat", "no appetite"],
            "limping": ["limping", "favoring leg", "won't put weight"],
            "coughing": ["coughing", "cough", "hacking"],
            "scratching": ["scratching", "itching", "itchy"]
        }
        
        for symptom, keywords in symptom_keywords.items():
            if any(keyword in speech_lower for keyword in keywords):
                details["symptoms"].append(symptom)
        
        return details
    
    def get_conversation_summary(self, call_sid: str) -> Optional[Dict[str, Any]]:
        """Get conversation summary for reporting."""
        context = self.conversations.get(call_sid)
        if not context:
            return None
        
        return {
            "call_sid": call_sid,
            "duration_minutes": (datetime.now() - context.start_time).total_seconds() / 60,
            "final_state": context.state.value,
            "intent": context.intent.value if context.intent else None,
            "urgency": context.urgency.value,
            "interactions": len(context.conversation_history),
            "extracted_data": context.extracted_data,
            "escalation_reason": context.escalation_reason
        }
    
    async def cleanup_old_conversations(self, hours: int = 24):
        """Clean up conversations older than specified hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        expired_conversations = [
            call_sid for call_sid, context in self.conversations.items()
            if context.last_activity < cutoff_time
        ]
        
        for call_sid in expired_conversations:
            del self.conversations[call_sid]
        
        self.logger.info(f"Cleaned up {len(expired_conversations)} old conversations")


# Global conversation engine instance
conversation_engine = AIConversationEngine()
