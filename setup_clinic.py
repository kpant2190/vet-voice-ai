#!/usr/bin/env python3
"""Setup script to create a clinic record for testing."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.clinic import Clinic

def setup_clinic():
    db = SessionLocal()
    try:
        # Check if clinic exists
        clinic = db.query(Clinic).filter(Clinic.phone_number == '+61468017757').first()
        if clinic:
            print(f'✅ Clinic already exists: {clinic.name}')
            return clinic
        
        # Create new clinic
        print('🏥 Creating clinic record...')
        new_clinic = Clinic(
            name='Sunny Paws Veterinary Clinic',
            phone_number='+61468017757',
            email='info@sunnypaws.com.au',
            address='123 Pet Street, Sydney, NSW 2000',
            business_hours='Monday-Friday: 8:00 AM - 6:00 PM, Saturday: 9:00 AM - 4:00 PM',
            voice_greeting='Hello! Thank you for calling Sunny Paws Veterinary Clinic. How can I help you and your pet today?',
            system_prompt='You are a helpful AI assistant for Sunny Paws Veterinary Clinic. Be professional, caring, and focus on pet health and scheduling appointments.'
        )
        db.add(new_clinic)
        db.commit()
        db.refresh(new_clinic)
        print(f'✅ Created clinic: {new_clinic.name}')
        return new_clinic
        
    except Exception as e:
        print(f'❌ Error: {e}')
        db.rollback()
    finally:
        db.close()

if __name__ == '__main__':
    setup_clinic()
