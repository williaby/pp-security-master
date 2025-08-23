import os
import psycopg
import urllib.parse
from pathlib import Path
from dotenv import load_dotenv

# Load .env if present
env_path = Path(".") / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)


# Try DATABASE_URL first, else build from POSTGRES_* variables
DB_URL = os.getenv("DATABASE_URL")
if not DB_URL:
    POSTGRES_URL = os.getenv("POSTGRES_URL")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_USER = os.getenv("POSTGRES_USER")
    POSTGRES_DB = os.getenv("POSTGRES_DB")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    if all([POSTGRES_URL, POSTGRES_USER, POSTGRES_DB]):
        # URL-encode username and password, handle None
        user_enc = urllib.parse.quote_plus(POSTGRES_USER or "")
        pw_enc = urllib.parse.quote_plus(POSTGRES_PASSWORD or "")
        DB_URL = f"postgresql://{user_enc}:{pw_enc}@{POSTGRES_URL}:{POSTGRES_PORT}/{POSTGRES_DB}"
    else:
        print("Database connection info not set in .env")
        exit(1)

try:
    with psycopg.connect(DB_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            version = cur.fetchone()
            if version:
                print(f"Connected successfully! PostgreSQL version: {version[0]}")
            else:
                print("Connected, but could not fetch PostgreSQL version.")
except Exception as e:
    print(f"Failed to connect to PostgreSQL: {e}")
