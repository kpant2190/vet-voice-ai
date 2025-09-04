#!/usr/bin/env python3
"""Setup test clinic data for Railway deployment."""

import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.models.clinic import Clinic
from app.core.database import Base

def setup_test_clinic():
    """Create a test clinic with the Twilio phone number."""
    
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        return False
    
    print(f"🔗 Connecting to database...")
    
    try:
        # Create engine and session
        engine = create_engine(database_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine)
        
        db = SessionLocal()
        
        # Check if clinic already exists
        existing_clinic = db.query(Clinic).filter(Clinic.phone_number == "+61468017757").first()
        
        if existing_clinic:
            print(f"✅ Clinic already exists: {existing_clinic.name}")
            print(f"📞 Phone: {existing_clinic.phone_number}")
            return True
        
        # Create test clinic
        test_clinic = Clinic(
            name="AI Veterinary Clinic",
            email="contact@aivetclinic.com.au",
            phone_number="+61468017757",
            address="123 Pet Street, Sydney NSW 2000",
            business_hours="8 AM to 6 PM, Monday through Saturday",
            voice_greeting="Hello! Thank you for calling AI Veterinary Clinic. I'm your AI assistant. How can I help you and your pet today?",
            system_prompt="You are a helpful AI veterinary receptionist. Be professional, caring, and efficient. Help with appointments, general questions, and emergency triage."
        )
        
        db.add(test_clinic)
        db.commit()
        db.refresh(test_clinic)
        
        print(f"✅ Test clinic created successfully!")
        print(f"🏥 Name: {test_clinic.name}")
        print(f"📞 Phone: {test_clinic.phone_number}")
        print(f"📧 Email: {test_clinic.email}")
        print(f"🕒 Hours: {test_clinic.business_hours}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Error setting up test clinic: {e}")
        return False

if __name__ == "__main__":
    print("🏥 Setting up test clinic for Railway deployment...")
    success = setup_test_clinic()
    if success:
        print("🎉 Setup completed successfully!")
    else:
        print("💥 Setup failed!")
        sys.exit(1)
