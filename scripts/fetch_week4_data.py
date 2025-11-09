"""
Fetch fresh data for FY2026 Week 4 testing (with 4-week average support)

Fetches:
- FY2026 Weeks 1-5 (current year - for 4W avg and Week 4/5 testing)
- FY2025 Weeks 1-5 (last year - for YoY comparison)
- FY2024 Weeks 1-5 (2 years ago - for extended comparisons)

This ensures we can test:
- Week 4 calculations
- Week 5 calculations
- 4-week rolling average (needs weeks 1-4)
- YoY variance (current vs last year)
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import polars as pl
from src.data.connector import get_db
from src.core.fiscal_calendar import get_week1_start
from datetime import timedelta

print("="*100)
print("FETCH FRESH DATA FOR WEEK 4+ TESTING")
print("="*100)

# Calculate date ranges for each fiscal year
fiscal_years = [2024, 2025, 2026]
weeks_to_fetch = [1, 2, 3, 4, 5]

print("\n[1] Calculating date ranges for fiscal weeks...")
date_ranges = {}
for fy in fiscal_years:
    week1_start = get_week1_start(fy)
    date_ranges[fy] = {}

    for week in weeks_to_fetch:
        # Week starts on Monday (week1_start is already a Monday)
        week_start = week1_start + timedelta(weeks=week-1)
        week_end = week_start + timedelta(days=6)  # Sunday
        date_ranges[fy][week] = (week_start, week_end)
        print(f"    FY{fy} Week {week}: {week_start} to {week_end}")

# Build SQL query
print("\n[2] Building SQL query...")

# Build WHERE clause with date ranges
conditions = []
for fy in fiscal_years:
    for week in weeks_to_fetch:
        start_date, end_date = date_ranges[fy][week]
        conditions.append(
            f"(\"Order_Date\" >= '{start_date}' AND \"Order_Date\" < '{end_date + timedelta(days=1)}')"
        )

where_clause = " OR ".join(conditions)

query = f"""
SELECT
    "Establishment",
    "Order_Number",
    "Order_Date",
    "Clean_Product_Name",
    "Clean_Class",
    "Total_Sales_Actual",
    "Net_Sales_Actual",
    "Product_Quantity",
    "Total_Product_Tax",
    "Eat_In_Or_Take_Away",
    "Product Type"
FROM public.mv_item_details
WHERE {where_clause}
ORDER BY "Order_Date", "Order_Number"
"""

print(f"\n[3] Executing query...")
print(f"    Fetching data for:")
print(f"    - FY2024 Weeks 1-5")
print(f"    - FY2025 Weeks 1-5")
print(f"    - FY2026 Weeks 1-5")

try:
    # Connect to database
    db = get_db()

    # Execute query and load into Polars
    with db.get_connection() as conn:
        df = pl.read_database(query, connection=conn)

    print(f"\n[OK] Fetched {len(df):,} rows")

    # Show summary
    print(f"\n[4] Data Summary:")
    print(f"    Unique orders: {df['Order_Number'].n_unique():,}")
    print(f"    Date range: {df['Order_Date'].min()} to {df['Order_Date'].max()}")
    print(f"    Establishments: {df['Establishment'].n_unique()}")
    print(f"    Total sales: £{df['Net_Sales_Actual'].sum():,.2f}")

    # Show establishments
    establishments = df.select('Establishment').unique().sort('Establishment')
    print(f"\n    Establishments in data:")
    for est in establishments['Establishment'].to_list():
        est_data = df.filter(pl.col('Establishment') == est)
        orders = est_data['Order_Number'].n_unique()
        sales = est_data['Net_Sales_Actual'].sum()
        print(f"        - {est}: {orders:,} orders, £{sales:,.2f}")

    # Export to CSV
    output_file = 'test_data_fy26_week4.csv'
    df.write_csv(output_file)
    print(f"\n[5] Exported to: {output_file}")

    # Verify fiscal week distribution
    print(f"\n[6] Verifying data can support testing...")
    from src.core.kpi_calculator import prepare_transaction_data

    prepared_df = prepare_transaction_data(df)

    fiscal_summary = prepared_df.group_by(['Fiscal_Year', 'Fiscal_Week']).agg([
        pl.col('Order_Number').n_unique().alias('Unique_Orders'),
        pl.col('Order_Net_Sales').sum().alias('Total_Sales')
    ]).sort(['Fiscal_Year', 'Fiscal_Week'])

    print(f"\n    Fiscal weeks in data:")
    for row in fiscal_summary.iter_rows(named=True):
        fy = row['Fiscal_Year']
        week = row['Fiscal_Week']
        orders = row['Unique_Orders']
        sales = row['Total_Sales']
        print(f"        FY{fy} Week {week:2d}: {orders:4,} orders, £{sales:,.2f}")

    # Check if we can test Week 4 and Week 5
    fy26_weeks = prepared_df.filter(pl.col('Fiscal_Year') == 2026)['Fiscal_Week'].unique().sort()
    print(f"\n[7] Testing Capability Check:")

    if 4 in fy26_weeks.to_list():
        print(f"    [OK] Can test FY26 Week 4 calculations")
    else:
        print(f"    [WARNING] FY26 Week 4 data not found")

    if 5 in fy26_weeks.to_list():
        print(f"    [OK] Can test FY26 Week 5 calculations")
    else:
        print(f"    [WARNING] FY26 Week 5 data not found")

    # Check 4-week average capability
    fy26_week_count = len(fy26_weeks)
    if fy26_week_count >= 4:
        print(f"    [OK] Can calculate 4-week average (have {fy26_week_count} weeks)")
    else:
        print(f"    [WARNING] Only {fy26_week_count} weeks - need 4+ for 4-week average")

    # Check YoY capability
    fy25_weeks = prepared_df.filter(pl.col('Fiscal_Year') == 2025)['Fiscal_Week'].unique().sort()
    if len(fy25_weeks) > 0:
        print(f"    [OK] Can calculate YoY variance (have FY25 data: weeks {list(fy25_weeks.to_list())})")
    else:
        print(f"    [WARNING] No FY25 data for YoY comparison")

    print("\n" + "="*100)
    print("DATA FETCH COMPLETE")
    print("="*100)
    print(f"\nNext step: Run test with new data:")
    print(f"    python scripts/test_weekly_report.py --data {output_file}")

except Exception as e:
    print(f"\n[ERROR] Failed to fetch data: {e}")
    import traceback
    traceback.print_exc()

    print("\n" + "="*100)
    print("TROUBLESHOOTING:")
    print("="*100)
    print("1. Check DATABASE_URL in .env file")
    print("2. Verify AWS RDS connection is working")
    print("3. Ensure mv_item_details has recent data")
    print("4. Check date ranges match fiscal calendar config")
