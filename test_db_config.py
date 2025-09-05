"""Test database configuration locally."""

import os
import sys

# Add the app directory to the path
sys.path.append('app')

# Set a test DATABASE_URL
os.environ['DATABASE_URL'] = 'postgresql://postgres:password@localhost:5432/test_db'

try:
    from app.core.database import initialize_database, create_tables, engine
    from app.core.config import settings
    
    print("🔍 Testing database configuration...")
    print(f"DATABASE_URL: {settings.DATABASE_URL}")
    
    # Test initialization
    print("\n1. Testing database initialization...")
    success = initialize_database()
    print(f"Initialization result: {success}")
    
    if success:
        print("\n2. Testing table creation...")
        tables_success = create_tables()
        print(f"Table creation result: {tables_success}")
        
        if engine:
            print("\n3. Testing connection...")
            from sqlalchemy import text
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                print(f"Connection test: {result.fetchone()}")
            print("✅ All tests passed!")
        else:
            print("❌ Engine is None")
    else:
        print("❌ Database initialization failed")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
