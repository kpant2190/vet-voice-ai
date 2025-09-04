#!/bin/bash

# Test Twilio webhook endpoint
curl -X POST https://web-production-2b37.up.railway.app/api/voice/webhook \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "From=%2B1234567890&To=%2B61468017757&CallSid=test123&AccountSid=test"
