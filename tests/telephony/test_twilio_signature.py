"""Tests for Twilio signature validation middleware."""

import pytest
import hmac
import hashlib
import base64
from urllib.parse import urlencode
from unittest.mock import Mock, AsyncMock
from fastapi import HTTPException, Request
from fastapi.datastructures import FormData

from app.telephony.twilio_signature import (
    TwilioSignatureValidator,
    require_twilio_signature,
    validate_twilio_request_sync,
    create_signature_header,
    TwilioWebhookValidator
)


class TestTwilioSignatureValidator:
    """Test cases for Twilio signature validation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.auth_token = "test_auth_token_12345"
        self.validator = TwilioSignatureValidator(self.auth_token)
        self.test_url = "https://example.com/webhook"
        self.test_params = {
            "CallSid": "CA1234567890abcdef",
            "From": "+1234567890",
            "To": "+0987654321"
        }
    
    def _create_valid_signature(self, url: str, params: dict) -> str:
        """Create a valid Twilio signature for testing."""
        # Sort parameters and create query string
        sorted_params = sorted(params.items())
        query_string = urlencode(sorted_params)
        
        # Create signature base string
        signature_base = url + query_string
        
        # Compute HMAC-SHA1
        signature = hmac.new(
            self.auth_token.encode('utf-8'),
            signature_base.encode('utf-8'),
            hashlib.sha1
        ).digest()
        
        # Base64 encode
        return base64.b64encode(signature).decode('utf-8')
    
    def test_valid_signature(self):
        """Test validation of a correct signature."""
        valid_signature = self._create_valid_signature(self.test_url, self.test_params)
        
        result = self.validator.validate_signature(
            self.test_url,
            self.test_params,
            valid_signature
        )
        
        assert result is True
    
    def test_invalid_signature(self):
        """Test validation of an incorrect signature."""
        invalid_signature = "invalid_signature_12345"
        
        result = self.validator.validate_signature(
            self.test_url,
            self.test_params,
            invalid_signature
        )
        
        assert result is False
    
    def test_empty_signature(self):
        """Test validation with empty signature."""
        result = self.validator.validate_signature(
            self.test_url,
            self.test_params,
            ""
        )
        
        assert result is False
    
    def test_no_auth_token(self):
        """Test validator behavior without auth token."""
        validator = TwilioSignatureValidator(None)
        
        result = validator.validate_signature(
            self.test_url,
            self.test_params,
            "any_signature"
        )
        
        # Should return True in development mode when no token is provided
        assert result is True
    
    def test_different_parameters(self):
        """Test signature validation with different parameters."""
        different_params = {
            "CallSid": "CA9876543210fedcba",
            "From": "+5555555555",
            "To": "+4444444444",
            "CallStatus": "in-progress"
        }
        
        # Create signature for original params
        original_signature = self._create_valid_signature(self.test_url, self.test_params)
        
        # Should fail with different params
        result = self.validator.validate_signature(
            self.test_url,
            different_params,
            original_signature
        )
        
        assert result is False
    
    def test_different_url(self):
        """Test signature validation with different URL."""
        different_url = "https://example.com/different-webhook"
        
        # Create signature for original URL
        original_signature = self._create_valid_signature(self.test_url, self.test_params)
        
        # Should fail with different URL
        result = self.validator.validate_signature(
            different_url,
            self.test_params,
            original_signature
        )
        
        assert result is False
    
    def test_parameter_order_independence(self):
        """Test that parameter order doesn't affect validation."""
        # Same parameters in different order
        params_ordered_1 = {"A": "1", "B": "2", "C": "3"}
        params_ordered_2 = {"C": "3", "A": "1", "B": "2"}
        
        signature_1 = self._create_valid_signature(self.test_url, params_ordered_1)
        signature_2 = self._create_valid_signature(self.test_url, params_ordered_2)
        
        # Signatures should be identical
        assert signature_1 == signature_2
        
        # Both should validate with either parameter order
        assert self.validator.validate_signature(self.test_url, params_ordered_1, signature_1)
        assert self.validator.validate_signature(self.test_url, params_ordered_2, signature_1)
    
    def test_special_characters_in_params(self):
        """Test signature validation with special characters in parameters."""
        special_params = {
            "Message": "Hello, world! How are you?",
            "From": "+1 (555) 123-4567",
            "Body": "Test message with & special < characters > and spaces"
        }
        
        valid_signature = self._create_valid_signature(self.test_url, special_params)
        
        result = self.validator.validate_signature(
            self.test_url,
            special_params,
            valid_signature
        )
        
        assert result is True


class TestRequireTwilioSignature:
    """Test cases for the FastAPI dependency function."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.auth_token = "test_auth_token_12345"
    
    @pytest.mark.asyncio
    async def test_valid_request(self, monkeypatch):
        """Test dependency with valid signature."""
        # Mock environment
        monkeypatch.setenv("TWILIO_AUTH_TOKEN", self.auth_token)
        monkeypatch.setenv("ENVIRONMENT", "production")
        
        # Create mock request
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.__str__ = Mock(return_value="https://example.com/webhook")
        request.headers = {"X-Twilio-Signature": "valid_signature"}
        
        # Mock form data
        form_data = FormData([
            ("CallSid", "CA1234567890abcdef"),
            ("From", "+1234567890")
        ])
        request.form = AsyncMock(return_value=form_data)
        
        # Mock the validator to return True
        monkeypatch.setattr(
            "app.telephony.twilio_signature._validator.validate_signature",
            lambda url, params, sig: True
        )
        
        # Should not raise exception
        await require_twilio_signature(request)
    
    @pytest.mark.asyncio
    async def test_missing_signature_header(self):
        """Test dependency with missing signature header."""
        # Create mock request without signature header
        request = Mock(spec=Request)
        request.headers = {}
        
        # Should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await require_twilio_signature(request)
        
        assert exc_info.value.status_code == 401
        assert "Missing Twilio signature" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_development_environment(self, monkeypatch):
        """Test dependency in development environment."""
        # Mock development environment
        monkeypatch.setenv("ENVIRONMENT", "development")
        
        # Create mock request
        request = Mock(spec=Request)
        
        # Should not raise exception in development
        await require_twilio_signature(request)
    
    @pytest.mark.asyncio
    async def test_invalid_signature(self, monkeypatch):
        """Test dependency with invalid signature."""
        # Mock environment
        monkeypatch.setenv("TWILIO_AUTH_TOKEN", self.auth_token)
        monkeypatch.setenv("ENVIRONMENT", "production")
        
        # Create mock request
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.__str__ = Mock(return_value="https://example.com/webhook")
        request.headers = {"X-Twilio-Signature": "invalid_signature"}
        
        # Mock form data
        form_data = FormData([("CallSid", "CA1234567890abcdef")])
        request.form = AsyncMock(return_value=form_data)
        
        # Mock the validator to return False
        monkeypatch.setattr(
            "app.telephony.twilio_signature._validator.validate_signature",
            lambda url, params, sig: False
        )
        
        # Should raise HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await require_twilio_signature(request)
        
        assert exc_info.value.status_code == 401
        assert "Invalid Twilio signature" in str(exc_info.value.detail)


class TestValidateTwilioRequestSync:
    """Test cases for synchronous validation function."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.auth_token = "test_auth_token_12345"
    
    def test_sync_validation(self, monkeypatch):
        """Test synchronous validation function."""
        # Mock auth token
        monkeypatch.setenv("TWILIO_AUTH_TOKEN", self.auth_token)
        
        url = "https://example.com/webhook"
        params = {"CallSid": "CA1234567890abcdef"}
        
        # Create valid signature
        validator = TwilioSignatureValidator(self.auth_token)
        valid_signature = validator.validate_signature(url, params, "dummy")
        
        # Mock the global validator
        monkeypatch.setattr(
            "app.telephony.twilio_signature._validator.validate_signature",
            lambda u, p, s: True
        )
        
        result = validate_twilio_request_sync(url, params, "test_signature")
        
        assert result is True


class TestCreateSignatureHeader:
    """Test cases for signature creation function."""
    
    def test_create_signature(self):
        """Test signature creation for testing purposes."""
        auth_token = "test_auth_token"
        url = "https://example.com/webhook"
        params = {"param1": "value1", "param2": "value2"}
        
        signature = create_signature_header(url, params, auth_token)
        
        # Should return a base64-encoded string
        assert isinstance(signature, str)
        assert len(signature) > 0
        
        # Should be valid base64
        try:
            base64.b64decode(signature)
        except Exception:
            pytest.fail("Signature is not valid base64")
    
    def test_signature_consistency(self):
        """Test that signature creation is consistent."""
        auth_token = "test_auth_token"
        url = "https://example.com/webhook"
        params = {"param1": "value1", "param2": "value2"}
        
        signature1 = create_signature_header(url, params, auth_token)
        signature2 = create_signature_header(url, params, auth_token)
        
        # Should be identical
        assert signature1 == signature2


class TestTwilioWebhookValidator:
    """Test cases for enhanced webhook validator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.auth_token = "test_auth_token_12345"
        self.validator = TwilioWebhookValidator(self.auth_token)
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test basic rate limiting functionality."""
        # Create mock request
        request = Mock(spec=Request)
        request.client = Mock()
        request.client.host = "192.168.1.1"
        request.url = Mock()
        request.url.__str__ = Mock(return_value="https://example.com/webhook")
        request.headers = {"X-Twilio-Signature": "test_signature"}
        
        # Mock form data
        form_data = FormData([("CallSid", "CA1234567890abcdef")])
        request.form = AsyncMock(return_value=form_data)
        
        # Mock signature validation to pass
        self.validator.validator.validate_signature = Mock(return_value=True)
        
        # First request should pass
        result1 = await self.validator.validate_webhook(request)
        assert result1["valid"] is True
        
        # Immediate second request should fail (rate limited)
        with pytest.raises(HTTPException) as exc_info:
            await self.validator.validate_webhook(request)
        
        assert exc_info.value.status_code == 429
