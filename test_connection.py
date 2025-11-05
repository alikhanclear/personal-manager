"""
Quick test script to verify AWS database connection and discover schema
"""
import os
from dotenv import load_dotenv
from sqlalchemy import text
from src.data.connector import get_db
from src.data.queries import get_view_schema, get_sample_data

def test_connection():
    """Test database connection"""
    load_dotenv()

    print("=" * 60)
    print("Testing AWS PostgreSQL Connection")
    print("=" * 60)

    # Test 1: Basic connection
    print("\n[1/3] Testing database connection...")
    try:
        db = get_db()
        with db.get_connection() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print("[SUCCESS] Connected successfully!")
            print(f"PostgreSQL version: {version[:50]}...")
    except Exception as e:
        print(f"[FAILED] Connection failed: {e}")
        return False

    # Test 2: Discover materialized view schema
    print("\n[2/3] Discovering materialized view schema...")
    view_name = os.getenv("MATERIALIZED_VIEW_NAME")
    if not view_name:
        print("[FAILED] MATERIALIZED_VIEW_NAME not set in .env")
        return False

    print(f"Looking for view: {view_name}")
    try:
        schema = get_view_schema()
        if schema:
            print(f"[SUCCESS] Found view: {view_name}")
            print(f"\nColumns ({len(schema)} total):")
            for col_name, col_type in schema.items():
                print(f"  - {col_name}: {col_type}")
        else:
            print(f"[FAILED] View '{view_name}' not found in database")
            print("   Check: 1) View name is correct 2) View exists 3) User has permissions")
            return False
    except Exception as e:
        print(f"[FAILED] Schema discovery failed: {e}")
        return False

    # Test 3: Query sample data
    print("\n[3/3] Fetching sample data (5 rows)...")
    try:
        df = get_sample_data(limit=5)
        print(f"[SUCCESS] Retrieved {len(df)} rows")
        print(f"\nSample data:")
        print(df)
    except Exception as e:
        print(f"[FAILED] Query failed: {e}")
        return False

    print("\n" + "=" * 60)
    print("[SUCCESS] All tests passed!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    test_connection()
