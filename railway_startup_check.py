"""Railway startup diagnostics - ensures app always starts."""

import os

def check_database_connection():
    """Check if database is available."""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ No DATABASE_URL found")
        return False
    
    if 'localhost' in database_url:
        print("❌ Database URL points to localhost (not Railway)")
        return False
    
    print(f"✅ DATABASE_URL configured: {database_url[:50]}...")
    return True

def check_environment_variables():
    """Check critical environment variables."""
    required_vars = [
        'OPENAI_API_KEY',
        'ELEVENLABS_API_KEY', 
        'TWILIO_ACCOUNT_SID',
        'TWILIO_AUTH_TOKEN',
        'SECRET_KEY'
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print(f"❌ Missing environment variables: {missing}")
        return False
    else:
        print(f"✅ All required environment variables found")
        return True

# Check environment on startup
print("🔍 Railway Startup Check")
print("=" * 50)

db_ok = check_database_connection()
env_ok = check_environment_variables()

if not db_ok or not env_ok:
    print("\n⚠️  WARNING: Some services may not work properly")
    print("📋 To fix:")
    if not db_ok:
        print("   1. Add PostgreSQL database in Railway dashboard")
        print("   2. Verify DATABASE_URL is automatically set")
    if not env_ok:
        print("   3. Add missing environment variables in Railway dashboard")

print("=" * 50)
print("🚀 Starting application...")
