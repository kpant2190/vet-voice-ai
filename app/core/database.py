"""Database configuration and connection management."""

from sqlalchemy import create_engine
try:
    from sqlalchemy.ext.declarative import declarative_base
except ImportError:
    from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

# Create database engine with optimized settings for Railway
try:
    engine = create_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        # Optimized connection pool settings for Railway PostgreSQL
        pool_size=5,                    # Smaller pool for webhook performance
        max_overflow=10,                # Allow burst connections
        pool_pre_ping=True,            # Test connections before use
        pool_recycle=3600,             # Recycle connections every hour
        # Faster connection timeouts for webhook responsiveness
        connect_args={
            "connect_timeout": 10,      # Reduced from 60 to 10 seconds
            "application_name": "vet-voice-ai",
            "options": "-c statement_timeout=30s"  # 30 second query timeout
        }
    )
    print(f"🔗 Database engine created for: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'localhost'}")
except Exception as e:
    print(f"⚠️  Warning: Could not create database engine: {e}")
    # Create a dummy engine for now
    engine = None

# Create SessionLocal class
if engine:
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
else:
    SessionLocal = None

# Create Base class for declarative models
Base = declarative_base()


def get_db():
    """Dependency to get database session."""
    if not SessionLocal:
        raise Exception("Database not available - SessionLocal is None")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all tables in the database."""
    if not engine:
        raise Exception("Database engine not available - cannot create tables")
    try:
        Base.metadata.create_all(bind=engine)
        print("📊 Database tables created successfully")
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        raise  # Re-raise the exception for the startup handler
