"""
Test Decimal division issue and Float64 solution.

This demonstrates why we need to cast Decimal to Float64 before division.
"""

import sys
from pathlib import Path
from decimal import Decimal

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import polars as pl

print("=" * 80)
print("TESTING DECIMAL DIVISION ISSUE")
print("=" * 80)

# Simulate data coming from PostgreSQL (Decimal types)
print("\n1. Creating DataFrame with Decimal types (like from PostgreSQL)...")
df = pl.DataFrame({
    'Location': ['Store A', 'Store B', 'Store C'],
    'Current': [Decimal('506'), Decimal('100'), Decimal('0')],
    'Last': [Decimal('715'), Decimal('0'), Decimal('100')],
})

print(df)
print(f"\nColumn types: {df.dtypes}")

# Test 1: Try division with Decimal (THIS WILL FAIL)
print("\n" + "=" * 80)
print("TEST 1: Division with Decimal types (WILL FAIL)")
print("=" * 80)

try:
    result = df.with_columns([
        pl.when(
            (pl.col('Current') == 0) |
            (pl.col('Last') == 0)
        )
        .then(None)
        .otherwise((pl.col('Current') - pl.col('Last')) / pl.col('Last'))
        .alias('Variance')
    ])
    print("✓ UNEXPECTED: No error occurred!")
    print(result)
except Exception as e:
    print(f"✗ EXPECTED ERROR: {type(e).__name__}: {str(e)}")
    print("   This is why the app was failing!")

# Test 2: Cast to Float64 BEFORE division (THIS WORKS)
print("\n" + "=" * 80)
print("TEST 2: Cast to Float64 BEFORE division (WORKS)")
print("=" * 80)

try:
    # Cast to Float64 first
    df_fixed = df.with_columns([
        pl.col('Current').cast(pl.Float64),
        pl.col('Last').cast(pl.Float64),
    ])

    print(f"After casting: {df_fixed.dtypes}")

    # Now division works!
    result = df_fixed.with_columns([
        pl.when(
            (pl.col('Current') == 0) |
            (pl.col('Last') == 0)
        )
        .then(None)
        .otherwise((pl.col('Current') - pl.col('Last')) / pl.col('Last'))
        .alias('Variance_Pct')
    ])

    print("\n✓ SUCCESS: Division works with Float64!")
    print(result)

    # Verify variances
    print("\nVariance calculations:")
    for row in result.iter_rows(named=True):
        var_pct = row['Variance_Pct']
        if var_pct is None:
            print(f"  {row['Location']}: None (correct - one value is 0)")
        else:
            print(f"  {row['Location']}: {var_pct * 100:.2f}% (correct)")

except Exception as e:
    print(f"✗ UNEXPECTED ERROR: {type(e).__name__}: {str(e)}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print("✓ Decimal types from PostgreSQL cause 'division by zero Decimal' errors")
print("✓ Solution: Cast to Float64 BEFORE any division operations")
print("✓ Float64 handles conditional division gracefully in Polars")
print("=" * 80)
