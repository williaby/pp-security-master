"""Database connection and session management for Security Master."""

import os
import urllib.parse
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from .models import Base

# Load environment variables
env_path = Path(".env")
if env_path.exists():
    load_dotenv(dotenv_path=env_path)


def get_database_url() -> str:
    """Get database URL from environment variables.

    Returns:
        str: SQLAlchemy database URL

    Raises:
        ValueError: If required environment variables are not set
    """
    # Try DATABASE_URL first
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url

    # Build from individual components
    postgres_host = os.getenv("POSTGRES_HOST")
    postgres_port = os.getenv("POSTGRES_PORT", "5432")
    postgres_user = os.getenv("POSTGRES_USER")
    postgres_db = os.getenv("POSTGRES_DB")
    postgres_password = os.getenv("POSTGRES_PASSWORD")

    if not all([postgres_host, postgres_user, postgres_db, postgres_password]):
        raise ValueError(
            "Database connection not configured. "
            "Set DATABASE_URL or POSTGRES_HOST, POSTGRES_USER, POSTGRES_DB, POSTGRES_PASSWORD"
        )

    # URL-encode credentials to handle special characters
    user_enc = urllib.parse.quote_plus(postgres_user)
    pw_enc = urllib.parse.quote_plus(postgres_password)

    return f"postgresql://{user_enc}:{pw_enc}@{postgres_host}:{postgres_port}/{postgres_db}"


# Create database engine (lazy initialization)
_engine: Engine | None = None
_SessionLocal: type[Session] | None = None


def get_engine() -> Engine:
    """Get or create database engine."""
    global _engine
    if _engine is None:
        database_url = get_database_url()
        _engine = create_engine(
            database_url,
            pool_pre_ping=True,  # Verify connections before using
            pool_size=10,
            max_overflow=20,
            connect_args={"connect_timeout": 10},
            echo=os.getenv("DB_ECHO", "false").lower() == "true",
        )
    return _engine


def get_session_factory() -> type[Session]:
    """Get or create session factory."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=get_engine()
        )
    return _SessionLocal


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Provide a transactional scope for database operations.

    Yields:
        Session: SQLAlchemy database session

    Example:
        with get_db_session() as session:
            security = session.query(SecurityMaster).first()
    """
    SessionLocal = get_session_factory()
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# Alias for compatibility with CLI
get_session = get_db_session


def test_connection() -> dict[str, Any]:
    """Test database connection and return connection info.

    Returns:
        dict: Connection information including host, port, database, user, version

    Raises:
        Exception: If connection fails
    """
    engine = get_engine()

    with engine.connect() as conn:
        # Get PostgreSQL version
        result = conn.execute(text("SELECT version();"))
        version_row = result.fetchone()
        version = version_row[0] if version_row else "Unknown"

        # Get connection info
        result = conn.execute(
            text(
                "SELECT current_database(), current_user, "
                "inet_server_addr(), inet_server_port();"
            )
        )
        db_info = result.fetchone()

        return {
            "host": str(db_info[2]) if db_info[2] else "localhost",
            "port": str(db_info[3]) if db_info[3] else "5432",
            "database": db_info[0],
            "user": db_info[1],
            "version": version.split(",")[0] if version else "Unknown",
        }


def create_tables(engine: Engine | None = None) -> None:
    """Create all tables in the database.

    Args:
        engine: SQLAlchemy engine (uses default if not provided)
    """
    if engine is None:
        engine = get_engine()

    Base.metadata.create_all(bind=engine)


def drop_tables(engine: Engine | None = None) -> None:
    """Drop all tables in the database.

    Args:
        engine: SQLAlchemy engine (uses default if not provided)

    Warning:
        This will delete all data in the database!
    """
    if engine is None:
        engine = get_engine()

    Base.metadata.drop_all(bind=engine)
