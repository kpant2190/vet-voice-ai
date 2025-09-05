"""
Deep analysis of database connection issues for Railway deployment.
"""

import os
import sys

def analyze_database_config():
    """Analyze database configuration issues."""
    
    print("🔍 DEEP DATABASE CONNECTION ANALYSIS")
    print("=" * 60)
    
    # 1. Check environment variables
    print("\n1. ENVIRONMENT VARIABLES:")
    database_url = os.getenv('DATABASE_URL')
    print(f"   DATABASE_URL: {database_url}")
    
    if not database_url:
        print("   ❌ CRITICAL: DATABASE_URL not set!")
        return False
    
    # 2. Parse database URL
    print("\n2. DATABASE URL ANALYSIS:")
    if 'postgres.railway.internal' in database_url:
        print("   ✅ Using Railway internal postgres")
    elif 'localhost' in database_url:
        print("   ❌ PROBLEM: Using localhost (not Railway)")
        return False
    else:
        print(f"   ⚠️  Unknown database host: {database_url}")
    
    # 3. Check connection string format
    print("\n3. CONNECTION STRING FORMAT:")
    if database_url.startswith('postgresql://'):
        print("   ✅ Correct PostgreSQL URL format")
    elif database_url.startswith('postgres://'):
        print("   ⚠️  Legacy postgres:// format (might cause issues)")
    else:
        print("   ❌ Invalid database URL format")
        return False
    
    # 4. Test SQLAlchemy compatibility
    print("\n4. SQLALCHEMY COMPATIBILITY:")
    try:
        from sqlalchemy import create_engine
        print("   ✅ SQLAlchemy imported successfully")
        
        # Fix URL if needed
        if database_url.startswith('postgres://') and not database_url.startswith('postgresql://'):
            fixed_url = database_url.replace('postgres://', 'postgresql://', 1)
            print(f"   🔧 Fixed URL: postgres:// → postgresql://")
            os.environ['DATABASE_URL'] = fixed_url
            database_url = fixed_url
        
        # Test engine creation
        try:
            engine = create_engine(database_url, echo=False)
            print("   ✅ Engine created successfully")
            
            # Test connection
            try:
                with engine.connect() as conn:
                    result = conn.execute("SELECT 1")
                    result.fetchone()
                print("   ✅ Database connection successful!")
                return True
            except Exception as conn_err:
                print(f"   ❌ Connection failed: {conn_err}")
                return False
                
        except Exception as engine_err:
            print(f"   ❌ Engine creation failed: {engine_err}")
            return False
            
    except Exception as import_err:
        print(f"   ❌ SQLAlchemy import failed: {import_err}")
        return False

def recommend_fixes():
    """Recommend fixes for database issues."""
    
    print("\n" + "=" * 60)
    print("🔧 RECOMMENDED FIXES:")
    print("=" * 60)
    
    print("\n1. RAILWAY DASHBOARD FIXES:")
    print("   • Go to Railway dashboard → Your project")
    print("   • Check Postgres service is deployed and running")
    print("   • Verify DATABASE_URL variable is automatically set")
    print("   • Check service connectivity between web and postgres")
    
    print("\n2. CODE FIXES:")
    print("   • Update database.py to handle postgres:// vs postgresql://")
    print("   • Add better error handling for connection timeouts")
    print("   • Implement retry logic for database connections")
    
    print("\n3. ENVIRONMENT FIXES:")
    print("   • Ensure Railway sets DATABASE_URL automatically")
    print("   • Check if manual DATABASE_URL override is conflicting")
    print("   • Verify Railway internal networking is working")

if __name__ == "__main__":
    success = analyze_database_config()
    
    if not success:
        recommend_fixes()
        print("\n❌ Database connection analysis FAILED")
    else:
        print("\n✅ Database connection analysis PASSED")
        print("🎉 Database should be working correctly!")
