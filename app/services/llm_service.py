"""LLM service for natural language processing and conversation handling."""

from typing import List, Dict, Optional, Any
import openai
import anthropic
from ..core.config import settings


class LLMService:
    """Handles LLM operations for conversation and intent detection."""
    
    def __init__(self):
        """Initialize the LLM service."""
        self.openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        if settings.ANTHROPIC_API_KEY:
            self.anthropic_client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        else:
            self.anthropic_client = None
    
    async def process_conversation(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        clinic_context: Dict[str, Any],
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process a conversation turn and generate response."""
        
        # Build system prompt
        system_message = system_prompt or self._build_system_prompt(clinic_context)
        
        # Prepare messages
        messages = [{"role": "system", "content": system_message}]
        messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_message})
        
        try:
            if settings.DEFAULT_LLM_PROVIDER == "openai":
                response = await self._call_openai(messages)
            elif settings.DEFAULT_LLM_PROVIDER == "anthropic" and self.anthropic_client:
                response = await self._call_anthropic(messages)
            else:
                response = await self._call_openai(messages)  # Fallback to OpenAI
            
            # Extract intent and entities
            intent = await self._detect_intent(user_message, response)
            entities = await self._extract_entities(user_message)
            
            return {
                "response": response,
                "intent": intent,
                "entities": entities,
                "confidence": 0.8  # Placeholder confidence score
            }
            
        except Exception as e:
            print(f"Error in LLM processing: {e}")
            return {
                "response": "I apologize, but I'm having trouble processing your request right now. Please hold while I connect you with our staff.",
                "intent": "error",
                "entities": {},
                "confidence": 0.0
            }
    
    async def _call_openai(self, messages: List[Dict[str, str]]) -> str:
        """Call OpenAI API."""
        response = self.openai_client.chat.completions.create(
            model=settings.GPT_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        return response.choices[0].message.content
    
    async def _call_anthropic(self, messages: List[Dict[str, str]]) -> str:
        """Call Anthropic API."""
        # Convert OpenAI format to Anthropic format
        system_message = ""
        user_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                user_messages.append(msg)
        
        response = self.anthropic_client.messages.create(
            model=settings.CLAUDE_MODEL,
            system=system_message,
            messages=user_messages,
            max_tokens=500,
            temperature=0.7
        )
        
        return response.content[0].text
    
    def _build_system_prompt(self, clinic_context: Dict[str, Any]) -> str:
        """Build system prompt based on clinic context."""
        clinic_name = clinic_context.get("name", "the veterinary clinic")
        business_hours = clinic_context.get("business_hours", "regular business hours")
        
        return f"""You are an AI receptionist for {clinic_name}, a veterinary clinic. 

Your responsibilities:
1. Greet callers warmly and professionally
2. Answer questions about services, hours, and general information
3. Schedule appointments for pet check-ups, vaccinations, and other services
4. Handle emergency situations by directing to appropriate resources
5. Collect necessary information (pet name, owner name, contact info, reason for visit)

Clinic Information:
- Name: {clinic_name}
- Hours: {business_hours}

Guidelines:
- Be empathetic, especially when pets are sick or injured
- If it's an emergency, prioritize getting them immediate help
- For appointments, collect: pet name, pet type, owner name, phone number, preferred date/time, reason for visit
- If you cannot help with something, offer to transfer to a staff member
- Keep responses concise but friendly
- Always confirm important details like appointment times and contact information

Remember: You are representing a caring veterinary practice. Be professional, empathetic, and helpful."""
    
    async def _detect_intent(self, user_message: str, ai_response: str) -> str:
        """Detect the main intent from the conversation."""
        # Simple keyword-based intent detection
        # In production, you might want to use a more sophisticated approach
        
        user_lower = user_message.lower()
        response_lower = ai_response.lower()
        
        if any(word in user_lower for word in ["appointment", "schedule", "book", "available"]):
            return "appointment_booking"
        elif any(word in user_lower for word in ["emergency", "urgent", "hurt", "injured", "bleeding"]):
            return "emergency"
        elif any(word in user_lower for word in ["hours", "open", "close", "when"]):
            return "business_hours"
        elif any(word in user_lower for word in ["price", "cost", "fee", "charge"]):
            return "pricing_inquiry"
        elif any(word in user_lower for word in ["cancel", "reschedule", "change"]):
            return "appointment_modification"
        else:
            return "general_inquiry"
    
    async def _extract_entities(self, text: str) -> Dict[str, Any]:
        """Extract entities from text (names, dates, phone numbers, etc.)."""
        entities = {}
        
        # Simple regex-based entity extraction
        # In production, you might want to use spaCy or a similar NLP library
        
        import re
        
        # Extract phone numbers
        phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        phones = re.findall(phone_pattern, text)
        if phones:
            entities["phone_numbers"] = phones
        
        # Extract potential pet names (capitalized words that aren't common words)
        name_pattern = r'\b[A-Z][a-z]+\b'
        potential_names = re.findall(name_pattern, text)
        common_words = {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"}
        pet_names = [name for name in potential_names if name not in common_words]
        if pet_names:
            entities["potential_names"] = pet_names
        
        return entities
