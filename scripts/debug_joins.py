"""
Debug join issues in KPI calculator
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import polars as pl
from src.core.kpi_calculator import (
    prepare_transaction_data,
    calculate_weekly_sales,
    calculate_4week_avg,
    calculate_order_volumes,
    calculate_atv
)

print("="*100)
print("DEBUG: Check columns returned by each metric function")
print("="*100)

# Load sample data
df = pl.read_csv('sample_data_100_rows.csv')
print(f"\n[1] Loaded {len(df)} rows")

# Prepare data
print("\n[2] Preparing transaction data...")
prepared_df = prepare_transaction_data(df)
print(f"    Columns after preparation: {prepared_df.columns}")

# Calculate each metric
print("\n[3] Calculating weekly sales...")
weekly_sales = calculate_weekly_sales(prepared_df, 2026, 4)
print(f"    Weekly sales columns: {weekly_sales.columns}")
print(f"    Weekly sales shape: {weekly_sales.shape}")

print("\n[4] Calculating 4-week avg...")
four_week_avg = calculate_4week_avg(prepared_df, 2026, 4)
print(f"    4-week avg columns: {four_week_avg.columns}")
print(f"    4-week avg shape: {four_week_avg.shape}")

print("\n[5] Calculating volumes...")
volumes = calculate_order_volumes(prepared_df, 2026, 4)
print(f"    Volumes columns: {volumes.columns}")
print(f"    Volumes shape: {volumes.shape}")

print("\n[6] Calculating ATV...")
atv = calculate_atv(prepared_df, 2026, 4)
print(f"    ATV columns: {atv.columns}")
print(f"    ATV shape: {atv.shape}")

# Try manual join
print("\n" + "="*100)
print("DEBUG: Try manual joins step by step")
print("="*100)

print("\n[7] Join 1: weekly_sales + four_week_avg")
result = weekly_sales
print(f"    Result before join: {result.columns}")

four_week_cols = [c for c in four_week_avg.columns if c not in ['Company', 'Establishment']]
print(f"    Four week cols to add: {four_week_cols}")
print(f"    Four week avg after select: {four_week_avg.select(['Company', 'Establishment'] + four_week_cols).columns}")

result = result.join(
    four_week_avg.select(['Company', 'Establishment'] + four_week_cols),
    on=['Company', 'Establishment'],
    how='left'
)
print(f"    Result after join 1: {result.columns}")

print("\n[8] Join 2: result + volumes")
print(f"    Result before join: {result.columns}")

volume_cols = [c for c in volumes.columns if c not in ['Company', 'Establishment']]
print(f"    Volume cols to add: {volume_cols}")
print(f"    Volumes after select: {volumes.select(['Company', 'Establishment'] + volume_cols).columns}")

try:
    result = result.join(
        volumes.select(['Company', 'Establishment'] + volume_cols),
        on=['Company', 'Establishment'],
        how='left'
    )
    print(f"    Result after join 2: {result.columns}")
except Exception as e:
    print(f"    [ERROR] Join 2 failed: {e}")
    print(f"    Result columns at failure: {result.columns}")
    print(f"    Volumes columns at failure: {volumes.select(['Company', 'Establishment'] + volume_cols).columns}")
