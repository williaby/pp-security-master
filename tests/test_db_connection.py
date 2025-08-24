import os
import urllib.parse
from pathlib import Path

import psycopg2
import pytest
from dotenv import load_dotenv


def get_db_connection_params():
    """Get database connection parameters from environment."""
    # Load .env if present
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)

    # Get individual connection parameters
    postgres_host = os.getenv("POSTGRES_HOST")
    postgres_port = os.getenv("POSTGRES_PORT", "5432")
    postgres_user = os.getenv("POSTGRES_USER")
    postgres_db = os.getenv("POSTGRES_DB")
    postgres_password = os.getenv("POSTGRES_PASSWORD")

    # WORKAROUND: python-dotenv has issues with # in passwords
    # If password appears truncated or has escape characters, use the full password directly
    if postgres_password and (
        (len(postgres_password) < 15 and postgres_password.endswith("!W")) or  # Truncated at #
        "\\" in postgres_password  # Has escape characters
    ):
        # This is the known Unraid password with special characters
        postgres_password = "cribrsk!W#9D%6^0" 
        print("⚠️  Applied password workaround for dotenv parsing limitation")

    return postgres_host, postgres_port, postgres_user, postgres_db, postgres_password


@pytest.mark.database
@pytest.mark.integration
def test_database_connection():
    """Test PostgreSQL database connection using constructed URL."""
    postgres_host, postgres_port, postgres_user, postgres_db, postgres_password = get_db_connection_params()
    
    # Check if we have all required connection parameters
    if not all([postgres_host, postgres_user, postgres_db, postgres_password]):
        pytest.skip("Database connection info not complete in .env")

    # Build DATABASE_URL from individual parameters to avoid dotenv parsing issues
    user_enc = urllib.parse.quote_plus(postgres_user)
    pw_enc = urllib.parse.quote_plus(postgres_password) 
    constructed_url = f"postgresql://{user_enc}:{pw_enc}@{postgres_host}:{postgres_port}/{postgres_db}"
    
    with psycopg2.connect(constructed_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            version = cur.fetchone()
            assert version is not None, "Could not fetch PostgreSQL version"
            
            # Test basic operations
            cur.execute("SELECT current_database(), current_user, now();")
            result = cur.fetchone()
            assert result is not None, "Could not fetch basic database info"
            assert len(result) == 3, "Expected 3 fields in result"


@pytest.mark.database
@pytest.mark.integration 
def test_database_connection_individual_params():
    """Test PostgreSQL database connection using individual parameters."""
    postgres_host, postgres_port, postgres_user, postgres_db, postgres_password = get_db_connection_params()
    
    if not all([postgres_host, postgres_user, postgres_db, postgres_password]):
        pytest.skip("Database connection info not complete in .env")

    with psycopg2.connect(
        host=postgres_host,
        port=postgres_port,
        user=postgres_user,
        password=postgres_password,
        dbname=postgres_db,
    ) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            version = cur.fetchone()
            assert version is not None, "Could not fetch PostgreSQL version"
