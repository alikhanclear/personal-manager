"""
Export sample records to CSV for viewing
"""
import os
from dotenv import load_dotenv
from sqlalchemy import text
import polars as pl
from src.data.connector import get_db

# Load environment
load_dotenv()

view_name = os.getenv('MATERIALIZED_VIEW_NAME')

print("=" * 80)
print(f"Extracting sample data from {view_name}")
print("=" * 80)

db = get_db()
with db.get_connection() as conn:
    # Query 10 records
    result = conn.execute(text(f"SELECT * FROM {view_name} ORDER BY \"Order_Date\" DESC LIMIT 10"))

    # Convert to list of dicts
    rows = [dict(row._mapping) for row in result]

    if rows:
        # Create Polars DataFrame
        df = pl.DataFrame(rows)

        print(f"\n[SUCCESS] Fetched {len(df)} records")
        print(f"Columns: {len(df.columns)}")
        print(f"Date range: {df['Order_Date'].min()} to {df['Order_Date'].max()}")

        # Save to CSV
        output_file = "sample_data_10_records.csv"
        df.write_csv(output_file)

        print(f"\n[SUCCESS] Data exported to: {output_file}")
        print("\nColumn Summary:")
        print("-" * 80)

        for col in df.columns:
            print(f"  - {col:<30} ({df[col].dtype})")

        print("\n" + "=" * 80)
        print("Data Statistics:")
        print("=" * 80)
        print(f"Total Net Sales: £{df['Net_Sales_Actual'].sum():.2f}")
        print(f"Total Items Sold: {df['Product_Quantity'].sum()}")
        print(f"Unique Establishments: {df['Establishment'].n_unique()}")
        print(f"Unique Products: {df['Clean_Product_Name'].n_unique()}")

        print("\n" + "=" * 80)
        print(f"Open {output_file} in Excel or a text editor to view the data")
        print("=" * 80)
    else:
        print("[FAILED] No data found in view")
