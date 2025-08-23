import os
import urllib.parse
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

# Load .env if present
env_path = Path(".env")
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

# Get individual connection parameters
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")

# Skip DATABASE_URL due to dotenv parsing issues with special characters
# Use individual parameters directly
if not all([POSTGRES_HOST, POSTGRES_USER, POSTGRES_DB, POSTGRES_PASSWORD]):
    print("Database connection info not complete in .env")
    print(f"  POSTGRES_HOST: {'✓' if POSTGRES_HOST else '✗'}")
    print(f"  POSTGRES_USER: {'✓' if POSTGRES_USER else '✗'}")
    print(f"  POSTGRES_DB: {'✓' if POSTGRES_DB else '✗'}")
    print(f"  POSTGRES_PASSWORD: {'✓' if POSTGRES_PASSWORD else '✗'}")
    exit(1)

try:
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
                    f"✅ Connected successfully! PostgreSQL version: {version[0]}",
                )
                
                # Test basic operations
                print("Testing basic SQL operations...")
                cur.execute("SELECT current_database(), current_user, now();")
                result = cur.fetchone()
                print(f"✅ Database: {result[0]}, User: {result[1]}, Time: {result[2]}")
                
                print("✅ All PostgreSQL connection tests passed!")
            else:
                print("❌ Connected, but could not fetch PostgreSQL version.")
except Exception as e:
    print(f"❌ Failed to connect to PostgreSQL: {e}")
    print("\n🔧 Troubleshooting steps:")
    print("1. Verify PostgreSQL container is running in Unraid")
    print("2. Check container logs for authentication issues") 
    print("3. Confirm credentials in Unraid container environment")
    print("4. Verify firewall/network connectivity on port 5436")
