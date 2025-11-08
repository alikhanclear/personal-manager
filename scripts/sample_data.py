"""
Extract and display sample records from materialized view
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
print(f"Sample Data from {view_name}")
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

        print(f"\nTotal records fetched: {len(df)}")
        print("\nColumns: " + ", ".join(df.columns))
        print("\n" + "=" * 80)

        # Display full dataframe
        with pl.Config(
            set_tbl_rows=10,
            set_tbl_cols=20,
            set_fmt_str_lengths=50,
            set_tbl_width_chars=200
        ):
            print(df)

        print("\n" + "=" * 80)
        print("Data Summary:")
        print("=" * 80)
        print(f"Date range: {df['Order_Date'].min()} to {df['Order_Date'].max()}")
        print(f"Establishments: {df['Establishment'].unique().to_list()}")
        print(f"Total sales (10 records): £{df['Net_Sales_Actual'].sum():.2f}")
        print(f"Total items sold: {df['Product_Quantity'].sum()}")
    else:
        print("No data found in view")

print("\n" + "=" * 80)
