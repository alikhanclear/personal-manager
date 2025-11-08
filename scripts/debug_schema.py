"""
Debug - check what's in information_schema
"""
from dotenv import load_dotenv
from sqlalchemy import text
from src.data.connector import get_db

load_dotenv()

db = get_db()
with db.get_connection() as conn:
    print("Searching for 'mv_item_details' in information_schema...")
    print("=" * 60)

    # Check all tables/views with similar names
    result = conn.execute(text("""
        SELECT table_schema, table_name, table_type
        FROM information_schema.tables
        WHERE table_name LIKE '%item%'
        ORDER BY table_schema, table_name
    """))

    tables = result.fetchall()

    if tables:
        print(f"\nFound {len(tables)} table(s) matching 'item':\n")
        for schema, name, ttype in tables:
            print(f"  {schema}.{name} ({ttype})")
    else:
        print("\nNo tables found matching 'item'")

    print("\n" + "=" * 60)
    print("\nTrying direct query on mv_item_details...")

    try:
        result = conn.execute(text("SELECT * FROM mv_item_details LIMIT 1"))
        row = result.fetchone()
        if row:
            print("[SUCCESS] Can query mv_item_details directly!")
            print(f"Columns: {result.keys()}")
        else:
            print("Query succeeded but no data")
    except Exception as e:
        print(f"[FAILED] {e}")
