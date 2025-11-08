"""
Fresh test - discover schema and sample data
"""
import os
from dotenv import load_dotenv
from sqlalchemy import text
import polars as pl
from src.data.connector import get_db

# Load environment
load_dotenv()

view_name = os.getenv('MATERIALIZED_VIEW_NAME')

print("=" * 60)
print("Materialized View Schema Discovery")
print("=" * 60)
print(f"\nView: {view_name}\n")

db = get_db()
with db.get_connection() as conn:
    # Query one row to get schema
    result = conn.execute(text(f"SELECT * FROM {view_name} LIMIT 5"))

    # Get column names and types
    columns = result.keys()

    # PostgreSQL type codes to names
    type_map = {
        23: 'integer',
        25: 'text',
        1043: 'character varying',
        1082: 'date',
        1114: 'timestamp without time zone',
        1700: 'numeric',
        701: 'double precision',
        16: 'boolean',
        20: 'bigint'
    }

    print(f"Columns ({len(columns)} total):")
    print("-" * 60)
    for idx, col_name in enumerate(columns):
        type_code = result.cursor.description[idx].type_code
        data_type = type_map.get(type_code, f'unknown({type_code})')
        print(f"  {col_name:<30} {data_type}")

    print("\n" + "=" * 60)
    print("Sample Data (5 rows)")
    print("=" * 60)

    # Fetch the data
    rows = [dict(row._mapping) for row in result]

    if rows:
        df = pl.DataFrame(rows)
        print(df)
    else:
        print("No data in view")

print("\n" + "=" * 60)
print("[SUCCESS] Schema discovered!")
print("=" * 60)
