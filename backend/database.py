from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import logging
from urllib.parse import urlparse, urlunparse
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def is_running_in_docker() -> bool:
    """Heuristic to detect if running inside a container."""
    if os.path.exists("/.dockerenv"):
        return True
    if os.getenv("CONTAINER") or os.getenv("CONTAINERIZED"):
        return True
    return False


def normalize_database_url(raw_url: str | None) -> str:
    """Normalize DATABASE_URL for local/dev/docker environments.

    - Falls back to DEV_DATABASE_URL if DATABASE_URL is unset
    - Rewrites host.docker.internal -> 127.0.0.1 when not inside Docker
    - Leaves docker-compose service hosts (e.g., db) untouched
    """
    fallback = os.getenv("DEV_DATABASE_URL") or "postgresql://postgres:postgres@127.0.0.1:5432/movies"
    if not raw_url or raw_url.strip() == "":
        logger.warning("DATABASE_URL not set; using DEV_DATABASE_URL/default for local dev")
        return fallback

    try:
        parsed = urlparse(raw_url)
        hostname = parsed.hostname or ""
        if hostname.lower() == "host.docker.internal" and not is_running_in_docker():
            # Replace with localhost when running directly on host
            new_netloc = parsed.netloc.replace("host.docker.internal", "127.0.0.1")
            parsed = parsed._replace(netloc=new_netloc)
            fixed = urlunparse(parsed)
            logger.info("Rewrote DATABASE_URL host.docker.internal -> 127.0.0.1 for local runtime")
            return fixed
        return raw_url
    except Exception as e:
        logger.warning(f"Could not parse DATABASE_URL; using fallback. Error: {e}")
        return fallback


# Get DATABASE_URL from environment
DATABASE_URL = normalize_database_url(os.getenv("DATABASE_URL"))

# Log database connection info (without password)
if DATABASE_URL:
    try:
        parsed = urlparse(DATABASE_URL)
        safe_url = f"{parsed.scheme}://{parsed.username}:***@{parsed.hostname}:{parsed.port}{parsed.path}"
        logger.info(f"Using database: {safe_url}")
    except:
        logger.info(f"Using database: {DATABASE_URL[:50]}...")

# Create engine with connection pooling and error handling
try:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # Verify connections before use
        pool_recycle=300,    # Recycle connections every 5 minutes
        echo=False           # Set to True for SQL debugging
    )
    logger.info("Database engine created successfully")
except Exception as e:
    logger.error(f"Failed to create database engine: {e}")
    raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_connection():
    """Test database connection."""
    try:
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            logger.info("Database connection test successful")
            return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False