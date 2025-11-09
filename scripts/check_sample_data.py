"""
Check what fiscal weeks are in the sample data
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import polars as pl
from src.core.kpi_calculator import prepare_transaction_data

print("="*100)
print("SAMPLE DATA ANALYSIS")
print("="*100)

# Load sample data
df = pl.read_csv('sample_data_100_rows.csv')
print(f"\n[1] Loaded {len(df)} rows")
print(f"    Columns: {df.columns}")

# Prepare data (adds fiscal calendar columns)
prepared_df = prepare_transaction_data(df)
print(f"\n[2] After preparation:")
print(f"    Columns: {prepared_df.columns}")

# Show unique fiscal years and weeks
fiscal_summary = prepared_df.group_by(['Fiscal_Year', 'Fiscal_Week']).agg([
    pl.col('Order_Number').n_unique().alias('Unique_Orders'),
    pl.col('Order_Net_Sales').sum().alias('Total_Sales')
]).sort(['Fiscal_Year', 'Fiscal_Week'])

print(f"\n[3] Fiscal weeks in sample data:")
for row in fiscal_summary.iter_rows(named=True):
    print(f"    FY{row['Fiscal_Year']} Week {row['Fiscal_Week']:2d}: {row['Unique_Orders']:4d} orders, Sales: £{row['Total_Sales']:,.2f}")

# Show establishments
establishments = prepared_df.select('Establishment').unique().sort('Establishment')
print(f"\n[4] Establishments in sample ({len(establishments)} total):")
for est in establishments['Establishment'].to_list():
    print(f"    - {est}")

# Check specifically for FY26 Week 4
fy26_w4 = prepared_df.filter(
    (pl.col('Fiscal_Year') == 2026) &
    (pl.col('Fiscal_Week') == 4)
)
print(f"\n[5] FY2026 Week 4 data:")
print(f"    Rows: {len(fy26_w4)}")
if len(fy26_w4) > 0:
    print(f"    Orders: {fy26_w4['Order_Number'].n_unique()}")
    print(f"    Total Sales: £{fy26_w4['Order_Net_Sales'].sum():.2f}")
else:
    print("    [WARNING] No data for FY26 Week 4!")

print("\n" + "="*100)
print("RECOMMENDATION:")
print("="*100)
if len(fy26_w4) == 0:
    print("Sample data doesn't include FY26 Week 4.")
    print("Options:")
    print("  1. Fetch larger sample with recent weeks from database")
    print("  2. Test with whatever weeks ARE in the sample")
    print("  3. Use full database connection for testing")
