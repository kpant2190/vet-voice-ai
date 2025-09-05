"""Tests for Twilio TwiML generation functionality."""

import pytest
from app.telephony.twilio_twiml import (
    voice_entry,
    generate_dtmf_response,
    generate_error_response,
    generate_transfer_twiml
)


class TestTwilioTwiML:
    """Test cases for TwiML generation functions."""
    
    def test_voice_entry_basic(self):
        """Test basic voice entry TwiML generation."""
        call_context = {
            "call_sid": "CA1234567890abcdef",
            "from_number": "+1234567890",
            "clinic_id": "test_clinic",
            "ws_url": "ws://localhost:8000/twilio/ws"
        }
        
        twiml = voice_entry(call_context)
        
        assert "<?xml version=" in twiml
        assert "<Response>" in twiml
        assert "<Say voice=\"Polly.Joanna\">" in twiml
        assert "<Start>" in twiml
        assert "<Stream" in twiml
        assert call_context["ws_url"] in twiml
        assert "<Gather" in twiml
        assert "</Response>" in twiml
    
    def test_voice_entry_with_consent(self):
        """Test voice entry with consent message."""
        call_context = {
            "call_sid": "CA1234567890abcdef",
            "from_number": "+1234567890",
            "clinic_id": "test_clinic",
            "ws_url": "ws://localhost:8000/twilio/ws",
            "consent_required": True,
            "consent_text": "This call may be recorded for quality purposes."
        }
        
        twiml = voice_entry(call_context)
        
        assert call_context["consent_text"] in twiml
        assert "<Pause length=\"1\"/>" in twiml
    
    def test_voice_entry_custom_greeting(self):
        """Test voice entry with custom greeting."""
        custom_greeting = "Welcome to Test Vet Clinic!"
        call_context = {
            "call_sid": "CA1234567890abcdef",
            "from_number": "+1234567890",
            "clinic_id": "test_clinic",
            "ws_url": "ws://localhost:8000/twilio/ws",
            "greeting": custom_greeting
        }
        
        twiml = voice_entry(call_context)
        
        assert custom_greeting in twiml
    
    def test_dtmf_response_appointment(self):
        """Test DTMF response for appointment (digit 1)."""
        twiml = generate_dtmf_response("1")
        
        assert "<?xml version=" in twiml
        assert "<Response>" in twiml
        assert "<Say voice=\"Polly.Joanna\">" in twiml
        assert "appointment" in twiml.lower()
        assert "<Hangup/>" in twiml
    
    def test_dtmf_response_emergency(self):
        """Test DTMF response for emergency (digit 2)."""
        twiml = generate_dtmf_response("2")
        
        assert "EMERGENCY" in twiml
        assert "hang up immediately" in twiml
        assert "emergency veterinary clinic" in twiml
    
    def test_dtmf_response_with_clinic_context(self):
        """Test DTMF response with clinic context."""
        clinic_context = {"name": "Happy Paws Vet Clinic"}
        twiml = generate_dtmf_response("1", clinic_context)
        
        assert "Happy Paws Vet Clinic" in twiml
    
    def test_dtmf_response_unknown_digit(self):
        """Test DTMF response for unknown digit."""
        twiml = generate_dtmf_response("9")
        
        assert "Thank you for calling" in twiml
        assert "assist you shortly" in twiml
    
    def test_error_response_general(self):
        """Test general error response."""
        twiml = generate_error_response("general")
        
        assert "<?xml version=" in twiml
        assert "<Response>" in twiml
        assert "technical difficulties" in twiml
        assert "<Hangup/>" in twiml
    
    def test_error_response_timeout(self):
        """Test timeout error response."""
        twiml = generate_error_response("timeout")
        
        assert "didn't receive a response" in twiml
        assert "call you back" in twiml
    
    def test_transfer_twiml(self):
        """Test call transfer TwiML generation."""
        transfer_number = "+1234567890"
        twiml = generate_transfer_twiml(transfer_number)
        
        assert "<?xml version=" in twiml
        assert "<Dial" in twiml
        assert f"<Number>{transfer_number}</Number>" in twiml
        assert "connect you to a team member" in twiml
    
    def test_transfer_twiml_with_clinic_context(self):
        """Test call transfer with clinic context."""
        transfer_number = "+1234567890"
        clinic_context = {"name": "Best Pet Clinic"}
        twiml = generate_transfer_twiml(transfer_number, clinic_context)
        
        assert "Best Pet Clinic" in twiml
    
    def test_voice_entry_parameter_handling(self):
        """Test voice entry with all parameters."""
        call_context = {
            "call_sid": "CA1234567890abcdef",
            "from_number": "+1234567890",
            "clinic_id": "test_clinic",
            "ws_url": "wss://example.com/ws",
            "greeting": "Custom greeting",
            "consent_required": True,
            "consent_text": "Custom consent text",
            "dtmf_instructions": "Custom DTMF instructions",
            "fallback_message": "Custom fallback message"
        }
        
        twiml = voice_entry(call_context)
        
        # Check all custom elements are included
        assert call_context["greeting"] in twiml
        assert call_context["consent_text"] in twiml
        assert call_context["dtmf_instructions"] in twiml
        assert call_context["fallback_message"] in twiml
        assert call_context["ws_url"] in twiml
        
        # Check parameter values in stream
        assert f'value="{call_context["call_sid"]}"' in twiml
        assert f'value="{call_context["from_number"]}"' in twiml
        assert f'value="{call_context["clinic_id"]}"' in twiml
    
    def test_twiml_xml_validity(self):
        """Test that generated TwiML is valid XML structure."""
        call_context = {
            "call_sid": "CA1234567890abcdef",
            "from_number": "+1234567890",
            "clinic_id": "test_clinic",
            "ws_url": "ws://localhost:8000/twilio/ws"
        }
        
        twiml = voice_entry(call_context)
        
        # Check XML declaration and structure
        assert twiml.startswith('<?xml version="1.0" encoding="UTF-8"?>')
        assert twiml.count("<Response>") == 1
        assert twiml.count("</Response>") == 1
        assert twiml.endswith("</Response>")
        
        # Check that all opened tags are closed
        assert twiml.count("<Start>") == twiml.count("</Start>")
        assert twiml.count("<Stream") == twiml.count("</Stream>")
        assert twiml.count("<Gather") == twiml.count("</Gather>")
    
    def test_special_characters_in_context(self):
        """Test handling of special characters in call context."""
        call_context = {
            "call_sid": "CA1234567890abcdef",
            "from_number": "+1234567890",
            "clinic_id": "test_clinic",
            "ws_url": "ws://localhost:8000/twilio/ws",
            "greeting": "Welcome to Dr. Smith's & Associates Veterinary Clinic!"
        }
        
        twiml = voice_entry(call_context)
        
        # Should handle special characters properly
        assert "&" in twiml or "&amp;" in twiml
        assert "Dr. Smith's" in twiml
    
    @pytest.mark.parametrize("digit,expected_keyword", [
        ("1", "appointment"),
        ("2", "EMERGENCY"),
        ("3", "questions"),
        ("0", "main office"),
        ("*", "main menu"),
        ("#", "wonderful day")
    ])
    def test_dtmf_responses_coverage(self, digit, expected_keyword):
        """Test DTMF responses for all supported digits."""
        twiml = generate_dtmf_response(digit)
        
        assert expected_keyword.lower() in twiml.lower()
        assert "<Hangup/>" in twiml
    
    @pytest.mark.parametrize("error_type,expected_keyword", [
        ("general", "technical difficulties"),
        ("timeout", "didn't receive"),
        ("system", "updating"),
        ("overload", "high call volume")
    ])
    def test_error_responses_coverage(self, error_type, expected_keyword):
        """Test error responses for all supported types."""
        twiml = generate_error_response(error_type)
        
        assert expected_keyword in twiml
        assert "<Hangup/>" in twiml
