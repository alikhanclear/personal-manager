"""
Debug script - check what's being read from .env
"""
import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("Environment Variables Check")
print("=" * 60)

# Check individual variables
host = os.getenv('DB_HOST', 'NOT SET')
port = os.getenv('DB_PORT', 'NOT SET')
database = os.getenv('DB_NAME', 'NOT SET')
user = os.getenv('DB_USER', 'NOT SET')
password = os.getenv('DB_PASSWORD', 'NOT SET')
view = os.getenv('MATERIALIZED_VIEW_NAME', 'NOT SET')

print(f"\nDB_HOST: {host}")
print(f"DB_PORT: {port}")
print(f"DB_NAME: {database}")
print(f"DB_USER: {user}")
print(f"DB_PASSWORD: {'*' * len(password) if password != 'NOT SET' else 'NOT SET'}")
print(f"DB_PASSWORD length: {len(password) if password != 'NOT SET' else 0} characters")
print(f"MATERIALIZED_VIEW_NAME: {view}")

# Check for DATABASE_URL
db_url = os.getenv('DATABASE_URL', 'NOT SET')
print(f"\nDATABASE_URL: {'SET' if db_url != 'NOT SET' else 'NOT SET'}")

print("\n" + "=" * 60)
print("Verify these match your credentials!")
print("=" * 60)
