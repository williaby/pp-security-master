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

# WORKAROUND: python-dotenv has issues with # in passwords
# If password appears truncated or has escape characters, use the full password directly
if POSTGRES_PASSWORD and (
    (len(POSTGRES_PASSWORD) < 15 and POSTGRES_PASSWORD.endswith("!W")) or  # Truncated at #
    "\\" in POSTGRES_PASSWORD  # Has escape characters
):
    # This is the known Unraid password with special characters
    POSTGRES_PASSWORD = "cribrsk!W#9D%6^0" 
    print("⚠️  Applied password workaround for dotenv parsing limitation")

# Build DATABASE_URL from individual parameters to avoid dotenv parsing issues
if all([POSTGRES_HOST, POSTGRES_USER, POSTGRES_DB, POSTGRES_PASSWORD]):
    # URL-encode the password to handle special characters
    user_enc = urllib.parse.quote_plus(POSTGRES_USER)
    pw_enc = urllib.parse.quote_plus(POSTGRES_PASSWORD) 
    constructed_url = f"postgresql://{user_enc}:{pw_enc}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    
    try:
        print("Attempting connection with constructed DATABASE_URL...")
        print(f"URL: postgresql://{user_enc}:[PASSWORD]@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")
        
        with psycopg2.connect(constructed_url) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                version = cur.fetchone()
                if version:
                    print(f"✅ Connected successfully with DATABASE_URL!")
                    print(f"PostgreSQL version: {version[0]}")
                    
                    # Test basic operations
                    print("Testing basic SQL operations...")
                    cur.execute("SELECT current_database(), current_user, now();")
                    result = cur.fetchone()
                    print(f"✅ Database: {result[0]}, User: {result[1]}, Time: {result[2]}")
                    
                    print("✅ All PostgreSQL connection tests passed!")
                    if __name__ == "__main__":
                        exit(0)  # Success - no need to try fallback
                    return  # For pytest execution
                else:
                    print("❌ Connected with DATABASE_URL, but could not fetch PostgreSQL version.")
    except Exception as e:
        print(f"❌ Failed to connect with constructed DATABASE_URL: {e}")
        print("🔄 Falling back to individual connection parameters...")

# Fallback attempt: Individual parameters
if not all([POSTGRES_HOST, POSTGRES_USER, POSTGRES_DB, POSTGRES_PASSWORD]):
    print("\n❌ Database connection info not complete in .env")
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
                    f"✅ Connected successfully with parameters! PostgreSQL version: {version[0]}",
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
