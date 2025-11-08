"""
List all materialized views in the database
"""
from dotenv import load_dotenv
from sqlalchemy import text
from src.data.connector import get_db

load_dotenv()

print("=" * 60)
print("Discovering Materialized Views")
print("=" * 60)

db = get_db()
with db.get_connection() as conn:
    # Query for materialized views
    result = conn.execute(text("""
        SELECT schemaname, matviewname
        FROM pg_matviews
        ORDER BY schemaname, matviewname
    """))

    views = result.fetchall()

    if views:
        print(f"\nFound {len(views)} materialized view(s):\n")
        for schema, view_name in views:
            print(f"  {schema}.{view_name}")
    else:
        print("\nNo materialized views found.")
        print("Checking for regular views...\n")

        # Try regular views instead
        result = conn.execute(text("""
            SELECT table_schema, table_name
            FROM information_schema.views
            WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
            ORDER BY table_schema, table_name
        """))

        regular_views = result.fetchall()

        if regular_views:
            print(f"Found {len(regular_views)} regular view(s):\n")
            for schema, view_name in regular_views:
                print(f"  {schema}.{view_name}")
        else:
            print("No views found.")

print("\n" + "=" * 60)
