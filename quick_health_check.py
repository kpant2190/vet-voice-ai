#!/usr/bin/env python3
"""Quick Railway health check."""

import requests
import time

def check_railway_health():
    """Check if Railway app is responding."""
    
    url = "https://web-production-2b37.up.railway.app/health"
    
    print("🏥 Checking Railway Health...")
    print(f"URL: {url}")
    
    for attempt in range(3):
        try:
            print(f"\nAttempt {attempt + 1}/3...")
            response = requests.get(url, timeout=10)
            print(f"✅ Status: {response.status_code}")
            print(f"📝 Response: {response.text}")
            
            if response.status_code == 200:
                print("🎉 Railway app is healthy!")
                return True
            else:
                print(f"⚠️ Got status {response.status_code}")
                
        except requests.exceptions.Timeout:
            print("⏰ Timeout - app might still be starting")
        except requests.exceptions.ConnectionError:
            print("🔌 Connection failed - app not ready yet")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        if attempt < 2:
            print("⏳ Waiting 10 seconds...")
            time.sleep(10)
    
    return False

if __name__ == '__main__':
    check_railway_health()
