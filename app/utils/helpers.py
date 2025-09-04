"""Helper functions and utilities."""

import re
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import phonenumbers
from phonenumbers import NumberParseException


def parse_phone_number(phone_str: str, region: str = "US") -> Optional[str]:
    """Parse and format phone number."""
    try:
        parsed = phonenumbers.parse(phone_str, region)
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        return None
    except NumberParseException:
        return None


def extract_time_from_text(text: str) -> Optional[datetime]:
    """Extract time/date information from text."""
    # This is a simplified version - in production, you'd use a library like dateutil
    # or a more sophisticated NLP approach
    
    text_lower = text.lower()
    now = datetime.now()
    
    # Look for specific time patterns
    time_patterns = [
        (r'(\d{1,2}):(\d{2})\s*(am|pm)', 'time_12h'),
        (r'(\d{1,2})\s*(am|pm)', 'time_12h_no_minutes'),
        (r'(\d{1,2}):(\d{2})', 'time_24h'),
    ]
    
    for pattern, format_type in time_patterns:
        match = re.search(pattern, text_lower)
        if match:
            if format_type == 'time_12h':
                hour = int(match.group(1))
                minute = int(match.group(2))
                am_pm = match.group(3)
                
                if am_pm == 'pm' and hour != 12:
                    hour += 12
                elif am_pm == 'am' and hour == 12:
                    hour = 0
                    
                return now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            elif format_type == 'time_12h_no_minutes':
                hour = int(match.group(1))
                am_pm = match.group(2)
                
                if am_pm == 'pm' and hour != 12:
                    hour += 12
                elif am_pm == 'am' and hour == 12:
                    hour = 0
                    
                return now.replace(hour=hour, minute=0, second=0, microsecond=0)
    
    # Look for relative dates
    if 'tomorrow' in text_lower:
        return now + timedelta(days=1)
    elif 'next week' in text_lower:
        return now + timedelta(days=7)
    elif 'monday' in text_lower:
        days_ahead = 0 - now.weekday()  # 0 = Monday
        if days_ahead <= 0:
            days_ahead += 7
        return now + timedelta(days=days_ahead)
    # Add more day patterns as needed
    
    return None


def parse_business_hours(hours_json: str) -> Dict[str, Dict[str, str]]:
    """Parse business hours JSON string."""
    try:
        if hours_json:
            return json.loads(hours_json)
        else:
            # Default business hours
            return {
                "monday": {"open": "09:00", "close": "17:00"},
                "tuesday": {"open": "09:00", "close": "17:00"},
                "wednesday": {"open": "09:00", "close": "17:00"},
                "thursday": {"open": "09:00", "close": "17:00"},
                "friday": {"open": "09:00", "close": "17:00"},
                "saturday": {"open": "09:00", "close": "13:00"},
                "sunday": {"open": "closed", "close": "closed"}
            }
    except json.JSONDecodeError:
        return {}


def is_clinic_open(business_hours: Dict[str, Dict[str, str]], check_time: Optional[datetime] = None) -> bool:
    """Check if clinic is open at given time."""
    if not check_time:
        check_time = datetime.now()
    
    day_name = check_time.strftime("%A").lower()
    
    if day_name not in business_hours:
        return False
    
    day_hours = business_hours[day_name]
    
    if day_hours.get("open") == "closed" or day_hours.get("close") == "closed":
        return False
    
    try:
        open_time = datetime.strptime(day_hours["open"], "%H:%M").time()
        close_time = datetime.strptime(day_hours["close"], "%H:%M").time()
        current_time = check_time.time()
        
        return open_time <= current_time <= close_time
    except (ValueError, KeyError):
        return False


def calculate_sentiment(text: str) -> float:
    """Calculate basic sentiment score (-1 to 1)."""
    # This is a very basic sentiment analysis
    # In production, you'd use a proper sentiment analysis library
    
    positive_words = [
        'good', 'great', 'excellent', 'wonderful', 'amazing', 'fantastic',
        'happy', 'pleased', 'satisfied', 'thank', 'thanks', 'appreciate'
    ]
    
    negative_words = [
        'bad', 'terrible', 'awful', 'horrible', 'disappointed', 'angry',
        'upset', 'frustrated', 'emergency', 'urgent', 'hurt', 'pain',
        'sick', 'worried', 'concerned'
    ]
    
    text_lower = text.lower()
    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)
    
    total_words = len(text.split())
    if total_words == 0:
        return 0.0
    
    # Calculate score between -1 and 1
    sentiment_score = (positive_count - negative_count) / max(total_words, 1)
    return max(-1.0, min(1.0, sentiment_score))


def extract_pet_info(text: str) -> Dict[str, Any]:
    """Extract pet information from text."""
    pet_info = {}
    text_lower = text.lower()
    
    # Pet types
    pet_types = {
        'dog': ['dog', 'puppy', 'canine'],
        'cat': ['cat', 'kitten', 'feline'],
        'bird': ['bird', 'parrot', 'cockatiel', 'budgie'],
        'rabbit': ['rabbit', 'bunny'],
        'hamster': ['hamster', 'gerbil'],
        'guinea pig': ['guinea pig'],
        'fish': ['fish', 'goldfish'],
        'reptile': ['snake', 'lizard', 'gecko', 'iguana', 'turtle']
    }
    
    for pet_type, keywords in pet_types.items():
        if any(keyword in text_lower for keyword in keywords):
            pet_info['type'] = pet_type
            break
    
    # Extract potential pet names (capitalized words that aren't common words)
    name_pattern = r'\b[A-Z][a-z]+\b'
    potential_names = re.findall(name_pattern, text)
    
    # Filter out common words that aren't names
    common_words = {
        'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday',
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December',
        'Doctor', 'Veterinarian', 'Clinic', 'Hospital', 'Emergency'
    }
    
    pet_names = [name for name in potential_names if name not in common_words]
    if pet_names:
        pet_info['potential_names'] = pet_names
    
    return pet_info


def format_appointment_confirmation(appointment_data: Dict[str, Any]) -> str:
    """Format appointment confirmation message."""
    pet_name = appointment_data.get('pet_name', 'your pet')
    appointment_date = appointment_data.get('appointment_date')
    owner_name = appointment_data.get('owner_name', '')
    
    if isinstance(appointment_date, datetime):
        date_str = appointment_date.strftime('%A, %B %d at %I:%M %p')
    else:
        date_str = str(appointment_date)
    
    confirmation = f"Perfect! I've scheduled an appointment for {pet_name} on {date_str}."
    
    if owner_name:
        confirmation += f" The appointment is under the name {owner_name}."
    
    confirmation += " You should receive a confirmation call or text message shortly. Is there anything else I can help you with today?"
    
    return confirmation


def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent injection attacks."""
    # Remove potentially dangerous characters
    text = re.sub(r'[<>"\']', '', text)
    
    # Limit length
    text = text[:1000]
    
    # Strip whitespace
    text = text.strip()
    
    return text


def generate_call_summary(transcript: str, intent: str, entities: Dict[str, Any]) -> str:
    """Generate a summary of the call."""
    summary_parts = []
    
    # Add intent
    if intent:
        intent_descriptions = {
            'appointment_booking': 'Caller requested to schedule an appointment',
            'emergency': 'Emergency call requiring immediate attention',
            'business_hours': 'Caller inquired about business hours',
            'pricing_inquiry': 'Caller asked about pricing or costs',
            'appointment_modification': 'Caller wanted to modify an existing appointment',
            'general_inquiry': 'General inquiry about services'
        }
        summary_parts.append(intent_descriptions.get(intent, f'Intent: {intent}'))
    
    # Add key entities
    if entities.get('phone_numbers'):
        summary_parts.append(f"Phone: {entities['phone_numbers'][0]}")
    
    if entities.get('potential_names'):
        summary_parts.append(f"Names mentioned: {', '.join(entities['potential_names'])}")
    
    # Add sentiment context
    sentiment = calculate_sentiment(transcript)
    if sentiment < -0.2:
        summary_parts.append("Caller seemed concerned or upset")
    elif sentiment > 0.2:
        summary_parts.append("Caller was positive and satisfied")
    
    return ". ".join(summary_parts) if summary_parts else "Call completed"
