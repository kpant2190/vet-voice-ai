import os
import requests

# Set Railway DATABASE_URL for the script
os.environ['DATABASE_URL'] = 'postgresql://postgres:utfvyCEEcOSjrwzAoJhYvDakypRvmOrz@postgres.railway.internal:5432/railway'

print("🏥 Setting up test clinic in Railway database...")

try:
    # Import after setting environment variable
    import sys
    sys.path.append('app')
    
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    
    # Create engine
    engine = create_engine(os.environ['DATABASE_URL'])
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    print("✅ Connected to Railway database")
    
    # Test connection
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("✅ Database connection working")
    
    # Create session and insert clinic data
    db = SessionLocal()
    
    # Insert clinic data directly with SQL
    insert_sql = """
    INSERT INTO clinics (name, email, phone_number, address, business_hours, voice_greeting, system_prompt, created_at, updated_at)
    VALUES (
        'AI Veterinary Clinic',
        'contact@aivetclinic.com.au',
        '+61468017757',
        '123 Pet Street, Sydney NSW 2000',
        '8 AM to 6 PM, Monday through Saturday',
        'Hello! Thank you for calling AI Veterinary Clinic. I am your AI assistant. How can I help you and your pet today?',
        'You are a helpful AI veterinary receptionist. Be professional, caring, and efficient. Help with appointments, general questions, and emergency triage.',
        NOW(),
        NOW()
    )
    ON CONFLICT (phone_number) DO UPDATE SET
        name = EXCLUDED.name,
        updated_at = NOW()
    """
    
    with engine.connect() as conn:
        conn.execute(text(insert_sql))
        conn.commit()
        print("✅ Test clinic created/updated successfully")
    
    # Verify clinic exists
    with engine.connect() as conn:
        result = conn.execute(text("SELECT name, phone_number FROM clinics WHERE phone_number = '+61468017757'"))
        clinic = result.fetchone()
        if clinic:
            print(f"✅ Clinic verified: {clinic[0]} - {clinic[1]}")
        else:
            print("❌ Clinic not found after insert")
    
    print("🎉 Setup completed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
