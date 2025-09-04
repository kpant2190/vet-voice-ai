#!/usr/bin/env python3

try:
    from app.services.voice_processor import VoiceProcessor
    print("SUCCESS: Voice processor import OK")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
