"""Database configuration and connection management."""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from .config import settings

# Create Base class first
Base = declarative_base()

# Create database engine with Railway-optimized settings
engine = None
SessionLocal = None

def initialize_database():
    """Initialize database connection with proper error handling."""
    global engine, SessionLocal
    
    try:
        print(f"🔗 Connecting to database...")
        print(f"🔗 Database host: {settings.DATABASE_URL.split('@')[1].split('/')[0] if '@' in settings.DATABASE_URL else 'localhost'}")
        
        # Simplified connection settings for Railway compatibility
        engine = create_engine(
            settings.DATABASE_URL,
            echo=settings.DEBUG,
            # Basic connection pool for Railway
            pool_size=3,
            max_overflow=5,
            pool_pre_ping=True,
            pool_recycle=1800,  # 30 minutes
            # Simplified connection args
            connect_args={
                "connect_timeout": 30,
                "application_name": "vet-voice-ai"
            }
        )
        
        # Test connection immediately
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
            print("✅ Database connection successful!")
        
        # Create session factory
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print(f"🔍 DATABASE_URL: {settings.DATABASE_URL[:50]}...")
        engine = None
        SessionLocal = None
        return False

def get_db():
    """Dependency to get database session."""
    if not SessionLocal:
        raise Exception("Database not initialized - call initialize_database() first")
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create all tables in the database."""
    if not engine:
        print("⚠️ No database engine available - skipping table creation")
        return False
    
    try:
        # Import all models to ensure they're registered with Base
        from ..models import clinic, appointment, call_log
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("📊 Database tables created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        return False
