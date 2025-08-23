import os
import urllib.parse
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

# Load .env if present
env_path = Path(".env")
if env_path.exists():
    load_dotenv(dotenv_path=env_path)


# Try DATABASE_URL first, else build from POSTGRES_* variables
DB_URL = os.getenv("DATABASE_URL")
if not DB_URL:
    POSTGRES_HOST = os.getenv("POSTGRES_HOST")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_USER = os.getenv("POSTGRES_USER")
    POSTGRES_DB = os.getenv("POSTGRES_DB")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    if all([POSTGRES_HOST, POSTGRES_USER, POSTGRES_DB]):
        # URL-encode username and password, handle None
        user_enc = urllib.parse.quote_plus(POSTGRES_USER or "")
        pw_enc = urllib.parse.quote_plus(POSTGRES_PASSWORD or "")
        DB_URL = f"postgresql://{user_enc}:{pw_enc}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
        print(
            f"Constructed DB_URL: postgresql://{user_enc}:[PASSWORD]@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}",
        )
    else:
        print("Database connection info not set in .env")
        exit(1)

try:
    # Try connecting using the constructed URL first
    if DB_URL:
        print("Attempting connection with URL...")
        with psycopg2.connect(DB_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                version = cur.fetchone()
                if version:
                    print(f"Connected successfully! PostgreSQL version: {version[0]}")
                else:
                    print("Connected, but could not fetch PostgreSQL version.")
except Exception as e:
    print(f"Failed to connect with URL: {e}")
    # Try connecting with individual parameters as fallback
    try:
        POSTGRES_HOST = os.getenv("POSTGRES_HOST")
        POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
        POSTGRES_USER = os.getenv("POSTGRES_USER")
        POSTGRES_DB = os.getenv("POSTGRES_DB")
        POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")

        print(
            f"Attempting connection with parameters: host={POSTGRES_HOST}, port={POSTGRES_PORT}, user={POSTGRES_USER}, dbname={POSTGRES_DB}",
        )
        with psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            dbname=POSTGRES_DB,
        ) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                version = cur.fetchone()
                if version:
                    print(
                        f"Connected successfully with parameters! PostgreSQL version: {version[0]}",
                    )
                else:
                    print(
                        "Connected with parameters, but could not fetch PostgreSQL version.",
                    )
    except Exception as e2:
        print(f"Failed to connect with parameters: {e2}")
