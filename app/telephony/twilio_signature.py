"""Twilio webhook signature validation middleware."""

import hashlib
import hmac
import base64
from typing import Optional, Dict, Any
from urllib.parse import urlencode, quote
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
        self.environment = os.getenv("ENVIRONMENT", "production")
        self.railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN")
        
        if not self.auth_token:
            logger.error("CRITICAL: No Twilio auth token provided - webhooks will be insecure!")
        else:
            logger.info("Twilio signature validation initialized successfully")
    
    def validate_signature(self, url: str, post_vars: Dict[str, Any], signature: str) -> bool:
        """
        Validate Twilio webhook signature using proper URL and parameter handling.
        
        Args:
            url: The full URL of the webhook
            post_vars: POST parameters from the request
            signature: X-Twilio-Signature header value
        
        Returns:
            True if signature is valid, False otherwise
        """
        if not self.auth_token:
            logger.error("Cannot validate signature - no auth token available")
            return False
        
        if not signature:
            logger.error("Cannot validate signature - no signature provided")
            return False
        
        try:
            # Ensure URL uses https in production
            if self.railway_domain and self.railway_domain in url:
                if not url.startswith('https://'):
                    url = url.replace('http://', 'https://')
                    logger.debug(f"Corrected URL to HTTPS: {url}")
            
            # Sort parameters by key (Twilio requirement)
            sorted_params = sorted(post_vars.items())
            
            # Build the signature string exactly as Twilio does
            signature_string = url
            for key, value in sorted_params:
                # Handle both string and list values
                if isinstance(value, list):
                    value = value[0] if value else ""
                signature_string += f"{key}{value}"
            
            logger.debug(f"Signature string (first 100 chars): {signature_string[:100]}...")
            
            # Compute HMAC-SHA1
            computed_signature = hmac.new(
                self.auth_token.encode('utf-8'),
                signature_string.encode('utf-8'),
                hashlib.sha1
            ).digest()
            
            # Base64 encode
            expected_signature = base64.b64encode(computed_signature).decode('utf-8')
            
            # Compare signatures using constant-time comparison
            is_valid = hmac.compare_digest(signature, expected_signature)
            
            if not is_valid:
                logger.error(
                    "Signature validation failed",
                    extra={
                        "url": url,
                        "expected_signature": expected_signature[:20] + "...",
                        "received_signature": signature[:20] + "...",
                        "params_count": len(post_vars)
                    }
                )
            else:
                logger.info("Signature validation successful")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Error validating Twilio signature: {e}", exc_info=True)
            return False


# Global validator instance
_validator = TwilioSignatureValidator()


async def require_twilio_signature(request: Request) -> Dict[str, Any]:
    """
    FastAPI dependency to validate Twilio webhook signatures and return form data.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Dictionary containing the validated form data
        
    Raises:
        HTTPException: If signature validation fails
    """
    # In development with no auth token, log warning but allow
    if _validator.environment == "development" and not _validator.auth_token:
        logger.warning("Development mode with no auth token - allowing request")
        try:
            form_data = await request.form()
            return dict(form_data)
        except Exception as e:
            logger.error(f"Error reading form data in dev mode: {e}")
            raise HTTPException(status_code=400, detail="Invalid form data")
    
    # Production mode requires auth token
    if not _validator.auth_token:
        logger.error("Production deployment missing TWILIO_AUTH_TOKEN")
        raise HTTPException(
            status_code=500,
            detail="Server configuration error - missing auth token"
        )
    
    # Get signature from headers
    signature = request.headers.get("X-Twilio-Signature")
    if not signature:
        logger.error("Missing X-Twilio-Signature header in webhook request")
        raise HTTPException(
            status_code=401,
            detail="Missing Twilio signature header"
        )
    
    # Get the full URL exactly as Twilio sees it
    url = str(request.url)
    
    # Handle Railway URL schemes properly
    if _validator.railway_domain and _validator.railway_domain in url:
        # Ensure HTTPS for Railway deployments
        if url.startswith('http://'):
            url = url.replace('http://', 'https://')
    
    # Parse form data
    try:
        form_data = await request.form()
        post_vars = {}
        
        # Handle multipart form data properly
        for key, value in form_data.items():
            if hasattr(value, 'read'):  # File upload
                post_vars[key] = await value.read().decode('utf-8')
            else:
                post_vars[key] = str(value)
        
        logger.debug(f"Parsed {len(post_vars)} form parameters for signature validation")
        
    except Exception as e:
        logger.error(f"Error parsing form data: {e}")
        raise HTTPException(
            status_code=400,
            detail="Invalid form data format"
        )
    
    # Validate signature
    try:
        is_valid = _validator.validate_signature(url, post_vars, signature)
        if not is_valid:
            logger.error(
                "Twilio signature validation failed",
                extra={
                    "url": url,
                    "from": post_vars.get("From", "unknown"),
                    "call_sid": post_vars.get("CallSid", "unknown")
                }
            )
            raise HTTPException(
                status_code=401,
                detail="Invalid Twilio signature"
            )
        
        logger.info(
            "Twilio webhook validated successfully",
            extra={
                "from": post_vars.get("From", "unknown"),
                "call_sid": post_vars.get("CallSid", "unknown"),
                "endpoint": request.url.path
            }
        )
        
        return post_vars
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during signature validation: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Signature validation error"
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


def validate_twilio_request_sync(url: str, post_vars: Dict[str, Any], signature: str) -> bool:
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


def create_signature_header(url: str, post_vars: Dict[str, Any], auth_token: str) -> str:
    """
    Create Twilio signature for testing purposes.
    
    Args:
        url: The webhook URL
        post_vars: POST parameters
        auth_token: Twilio auth token
        
    Returns:
        Base64-encoded signature
    """
    # Sort parameters by key (Twilio requirement)
    sorted_params = sorted(post_vars.items())
    
    # Build the signature string exactly as Twilio does
    signature_string = url
    for key, value in sorted_params:
        # Handle both string and list values
        if isinstance(value, list):
            value = value[0] if value else ""
        signature_string += f"{key}{value}"
    
    # Compute HMAC-SHA1
    signature = hmac.new(
        auth_token.encode('utf-8'),
        signature_string.encode('utf-8'),
        hashlib.sha1
    ).digest()
    
    # Base64 encode
    return base64.b64encode(signature).decode('utf-8')
