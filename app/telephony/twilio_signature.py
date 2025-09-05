"""Twilio webhook signature validation middleware."""

import hashlib
import hmac
import base64
from typing import Optional
from urllib.parse import urlencode
import logging
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer
import os

logger = logging.getLogger(__name__)

# Security bearer for webhook validation
security = HTTPBearer(auto_error=False)


class TwilioSignatureValidator:
    """Validates Twilio webhook signatures for security."""
    
    def __init__(self, auth_token: Optional[str] = None):
        """
        Initialize the signature validator.
        
        Args:
            auth_token: Twilio auth token for signature validation
        """
        self.auth_token = auth_token or os.getenv("TWILIO_AUTH_TOKEN")
        if not self.auth_token:
            logger.warning("No Twilio auth token provided - signature validation disabled")
    
    def validate_signature(self, url: str, post_vars: dict, signature: str) -> bool:
        """
        Validate Twilio webhook signature.
        
        Args:
            url: The full URL of the webhook
            post_vars: POST parameters from the request
            signature: X-Twilio-Signature header value
        
        Returns:
            True if signature is valid, False otherwise
        """
        if not self.auth_token:
            logger.warning("Signature validation skipped - no auth token")
            return True  # Allow in development
        
        try:
            # Sort parameters and create query string
            sorted_vars = sorted(post_vars.items())
            query_string = urlencode(sorted_vars)
            
            # Create the signature base string
            signature_base = url + query_string
            
            # Compute HMAC-SHA1
            expected_signature = hmac.new(
                self.auth_token.encode('utf-8'),
                signature_base.encode('utf-8'),
                hashlib.sha1
            ).digest()
            
            # Base64 encode
            expected_signature_b64 = base64.b64encode(expected_signature).decode('utf-8')
            
            # Compare signatures
            is_valid = hmac.compare_digest(signature, expected_signature_b64)
            
            if not is_valid:
                logger.error(
                    f"Invalid Twilio signature: url={url}, "
                    f"expected={expected_signature_b64[:10]}..., "
                    f"received={signature[:10] + '...' if signature else 'None'}"
                )
            else:
                logger.debug("Valid Twilio signature verified")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Error validating Twilio signature: {e}")
            return False


# Global validator instance
_validator = TwilioSignatureValidator()


async def require_twilio_signature(request: Request) -> None:
    """
    FastAPI dependency to validate Twilio webhook signatures.
    
    Args:
        request: FastAPI request object
        
    Raises:
        HTTPException: If signature validation fails
    """
    # Skip validation for development
    if os.getenv("ENVIRONMENT") == "development":
        logger.debug("Skipping signature validation in development")
        return
    
    # Get signature from headers
    signature = request.headers.get("X-Twilio-Signature")
    if not signature:
        logger.error("Missing X-Twilio-Signature header")
        raise HTTPException(
            status_code=401,
            detail="Missing Twilio signature"
        )
    
    # Get request URL
    url = str(request.url)
    
    # Get form data
    try:
        form_data = await request.form()
        post_vars = dict(form_data)
    except Exception as e:
        logger.error(f"Error reading form data: {e}")
        raise HTTPException(
            status_code=400,
            detail="Invalid form data"
        )
    
    # Validate signature
    if not _validator.validate_signature(url, post_vars, signature):
        raise HTTPException(
            status_code=401,
            detail="Invalid Twilio signature"
        )


async def require_twilio_signature_optional(request: Request) -> bool:
    """
    Optional Twilio signature validation that returns success status.
    
    Args:
        request: FastAPI request object
        
    Returns:
        True if signature is valid or validation is skipped, False otherwise
    """
    try:
        await require_twilio_signature(request)
        return True
    except HTTPException:
        return False


def validate_twilio_request_sync(url: str, post_vars: dict, signature: str) -> bool:
    """
    Synchronous signature validation for non-FastAPI contexts.
    
    Args:
        url: The full URL of the webhook
        post_vars: POST parameters from the request
        signature: X-Twilio-Signature header value
    
    Returns:
        True if signature is valid, False otherwise
    """
    return _validator.validate_signature(url, post_vars, signature)


class TwilioWebhookValidator:
    """Enhanced webhook validator with additional security features."""
    
    def __init__(self, auth_token: Optional[str] = None):
        self.validator = TwilioSignatureValidator(auth_token)
        self.rate_limits = {}  # Simple in-memory rate limiting
    
    async def validate_webhook(self, request: Request) -> dict:
        """
        Comprehensive webhook validation with rate limiting.
        
        Args:
            request: FastAPI request object
            
        Returns:
            Dictionary with validation results and request data
            
        Raises:
            HTTPException: If validation fails
        """
        client_ip = request.client.host if request.client else "unknown"
        
        # Basic rate limiting (simple implementation)
        current_time = time.time()
        if client_ip in self.rate_limits:
            if current_time - self.rate_limits[client_ip] < 1:  # 1 second between requests
                logger.warning(f"Rate limit exceeded for IP: {client_ip}")
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded"
                )
        self.rate_limits[client_ip] = current_time
        
        # Validate signature
        await require_twilio_signature(request)
        
        # Get form data
        form_data = await request.form()
        request_data = dict(form_data)
        
        # Log webhook details
        logger.info(
            "Validated Twilio webhook",
            client_ip=client_ip,
            call_sid=request_data.get("CallSid", "unknown"),
            from_number=request_data.get("From", "unknown")
        )
        
        return {
            "valid": True,
            "client_ip": client_ip,
            "data": request_data,
            "timestamp": current_time
        }


# Enhanced validator instance
webhook_validator = TwilioWebhookValidator()


def create_signature_header(url: str, post_vars: dict, auth_token: str) -> str:
    """
    Create Twilio signature for testing purposes.
    
    Args:
        url: The webhook URL
        post_vars: POST parameters
        auth_token: Twilio auth token
        
    Returns:
        Base64-encoded signature
    """
    # Sort parameters and create query string
    sorted_vars = sorted(post_vars.items())
    query_string = urlencode(sorted_vars)
    
    # Create the signature base string
    signature_base = url + query_string
    
    # Compute HMAC-SHA1
    signature = hmac.new(
        auth_token.encode('utf-8'),
        signature_base.encode('utf-8'),
        hashlib.sha1
    ).digest()
    
    # Base64 encode
    return base64.b64encode(signature).decode('utf-8')


# Import time for rate limiting
import time
