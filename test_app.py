#!/usr/bin/env python3

try:
    from app.main import app
    print("SUCCESS: FastAPI app import OK")
    print(f"App title: {app.title}")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
