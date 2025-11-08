"""
Fetch 100 rows from mv_item_details materialized view
"""
import os
from dotenv import load_dotenv
from sqlalchemy import text
from src.data.connector import get_db
import polars as pl

# Load environment variables
load_dotenv()

print("Fetching 100 rows from mv_item_details...")
print("=" * 60)

try:
    # Simple query without ordering (avoid case sensitivity issues)
    query = "SELECT * FROM mv_item_details LIMIT 100"

    db = get_db()
    with db.get_connection() as conn:
        result = conn.execute(text(query))
        rows = [dict(row._mapping) for row in result]

    # Convert to Polars DataFrame
    df = pl.DataFrame(rows)

    print(f"\nSuccessfully fetched {len(df)} rows")
    print(f"Columns: {df.columns}")

    # Save to CSV
    output_file = "sample_data_100_rows.csv"
    df.write_csv(output_file)

    print(f"\nSaved to: {output_file}")
    print("\nFirst 5 rows:")
    print(df.head(5))

    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    print(f"Total rows: {len(df)}")
    print(f"Total columns: {len(df.columns)}")

    # Use correct case-sensitive column names
    if 'Order_Date' in df.columns:
        print(f"Date range: {df['Order_Date'].min()} to {df['Order_Date'].max()}")
    if 'Establishment' in df.columns:
        print(f"Establishments: {df['Establishment'].n_unique()} unique locations")
    if 'Total_Sales_Actual' in df.columns:
        total = df['Total_Sales_Actual'].sum()
        print(f"Total sales: £{total:,.2f}")

except Exception as e:
    print(f"\nERROR: {e}")
    print("\nCheck:")
    print("  1. Database connection (.env file)")
    print("  2. Materialized view name")
    print("  3. Database permissions")
