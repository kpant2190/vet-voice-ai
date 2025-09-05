"""Railway-optimized database configuration and connection management."""

import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from .config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Base class first
Base = declarative_base()

# Global database variables
engine = None
SessionLocal = None

def get_railway_database_url():
    """Get Railway-compatible database URL."""
    
    database_url = settings.DATABASE_URL
    
    # Check if we're using Railway PostgreSQL
    if 'railway.app' in database_url:
        logger.info("Using Railway PostgreSQL database")
        return database_url
    
    # For local development, use localhost
    if 'localhost' in database_url:
        logger.warning("Using localhost database (development mode)")
        return database_url
    
    # Try to detect other cloud PostgreSQL providers
    if any(provider in database_url for provider in ['amazonaws.com', 'digitalocean.com', 'render.com']):
        logger.info("Using cloud PostgreSQL database")
        return database_url
    
    logger.info(f"Using database URL: {database_url[:50]}...")
    return database_url

def create_railway_engine():
    """Create SQLAlchemy engine optimized for Railway."""
    
    database_url = get_railway_database_url()
    
    try:
        # Railway-optimized connection settings
        engine = create_engine(
            database_url,
            # Connection pool settings for Railway
            pool_size=3,              # Small pool for Railway limits
            max_overflow=7,           # Allow some overflow connections
            pool_timeout=30,          # Wait 30s for connection
            pool_recycle=1800,        # Recycle connections every 30 minutes
            pool_pre_ping=True,       # Test connections before use
            
            # Disable echo in production for performance
            echo=settings.DEBUG and 'localhost' in database_url,
            
            # Connection arguments
            connect_args={
                "connect_timeout": 10,           # 10 second connection timeout
                "application_name": "vet_voice_ai",
                "options": "-c timezone=UTC"     # Set timezone
            }
        )
        
        # Test the connection immediately
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            db_version = result.fetchone()[0]
            logger.info(f"Database connected: {db_version[:50]}...")
        
        return engine
        
    except Exception as e:
        logger.error(f"Failed to create database engine: {e}")
        return None

def initialize_database():
    """Initialize database connection with Railway compatibility."""
    global engine, SessionLocal
    
    logger.info("Initializing database connection for Railway...")
    
    try:
        # Create the engine
        engine = create_railway_engine()
        if not engine:
            logger.error("Failed to create database engine")
            return False
        
        # Create session factory
        SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )
        
        # Test session creation
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            logger.info("Database session test successful")
        finally:
            db.close()
        
        logger.info("Database initialization completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        engine = None
        SessionLocal = None
        return False

def get_db():
    """Dependency to get database session with error handling."""
    if not SessionLocal:
        logger.error("Database not initialized - call initialize_database() first")
        raise Exception("Database not initialized")
    
    db = SessionLocal()
    try:
        # Test the connection
        db.execute(text("SELECT 1"))
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def create_tables():
    """Create all tables in the database with error handling."""
    if not engine:
        logger.warning("No database engine available - skipping table creation")
        return False
    
    try:
        # Import all models to ensure they're registered with Base
        from ..models import clinic, appointment, call_log
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        # Verify table creation
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            tables = [row[0] for row in result.fetchall()]
            logger.info(f"Created tables: {', '.join(tables)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        return False

def check_database_health():
    """Check database connection health for monitoring."""
    global engine
    
    if not engine:
        return {
            "status": "not_initialized", 
            "message": "Database engine not created",
            "database": "not_initialized"
        }
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        
        return {
            "status": "ok",
            "message": "Database connection healthy",
            "database": "connected"
        }
        
    except Exception as e:
        return {
            "status": "degraded",
            "message": f"Database connection error: {str(e)}",
            "database": "error"
        }
