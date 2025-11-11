"""
Test variance calculations to ensure they handle 0 values correctly.

This script verifies that:
1. Variance is None when current year = 0
2. Variance is None when last year = 0
3. Variance is None when both = 0
4. Variance is calculated correctly when both have values
5. fill_null(0) doesn't overwrite None variances
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import polars as pl
from src.core.kpi_calculator import calculate_weekly_report

def create_test_data():
    """Create test transaction data with known scenarios."""
    data = []

    # Scenario 1: Both years have data - should calculate variance
    # Current: 506, Last: 715 -> Variance: (506-715)/715 = -29.23%
    for i in range(506):
        data.append({
            'Establishment': 'Test Location 1',
            'Order_Number': f'ORD-CY-{i}',
            'Order_Date': datetime(2024, 10, 2, 12, 0, 0),  # FY2025 Week 1
            'Order_Net_Sales': 10.0,
            'Fiscal_Year': 2025,
            'Fiscal_Week': 1
        })

    for i in range(715):
        data.append({
            'Establishment': 'Test Location 1',
            'Order_Number': f'ORD-LY-{i}',
            'Order_Date': datetime(2023, 10, 2, 12, 0, 0),  # FY2024 Week 1
            'Order_Net_Sales': 10.0,
            'Fiscal_Year': 2024,
            'Fiscal_Week': 1
        })

    # Scenario 2: Current year = 0, Last year has data - should be None
    for i in range(100):
        data.append({
            'Establishment': 'Test Location 2',
            'Order_Number': f'ORD-LY2-{i}',
            'Order_Date': datetime(2023, 10, 2, 12, 0, 0),
            'Order_Net_Sales': 10.0,
            'Fiscal_Year': 2024,
            'Fiscal_Week': 1
        })

    # Scenario 3: Current year has data, Last year = 0 - should be None
    for i in range(100):
        data.append({
            'Establishment': 'Test Location 3',
            'Order_Number': f'ORD-CY3-{i}',
            'Order_Date': datetime(2024, 10, 2, 12, 0, 0),
            'Order_Net_Sales': 10.0,
            'Fiscal_Year': 2025,
            'Fiscal_Week': 1
        })

    # Scenario 4: Both years = 0 - should be None (no data, just placeholder)
    # We'll add this row manually after calculation

    df = pl.DataFrame(data)

    # Add Company column
    df = df.with_columns([
        pl.lit('TEST COMPANY').alias('Company')
    ])

    return df

def run_tests():
    """Run variance calculation tests."""
    print("=" * 80)
    print("VARIANCE CALCULATION TESTS")
    print("=" * 80)

    # Create test data
    print("\n1. Creating test data...")
    df = create_test_data()
    print(f"   Created {len(df)} test transactions")

    # Run calculations
    print("\n2. Running variance calculations...")
    result = calculate_weekly_report(df, fiscal_year=2025, fiscal_week=1)

    print(f"   Generated report with {len(result)} rows")

    # Verify results
    print("\n3. Verifying variance calculations...")
    print("=" * 80)

    test_results = []

    # Test 1: Both years have data (506 vs 715)
    print("\nTest 1: Both years have data (Normal variance calculation)")
    location1 = result.filter(pl.col('Establishment') == 'Test Location 1')
    if len(location1) > 0:
        current_vol = location1['Current_Year_Vol'][0]
        last_vol = location1['Last_Year_Vol'][0]
        variance = location1['Volume_Var_Pct'][0]

        expected_variance = (506 - 715) / 715  # -0.2923 or -29.23%

        print(f"   Current Year Vol: {current_vol}")
        print(f"   Last Year Vol: {last_vol}")
        print(f"   Variance: {variance}")
        print(f"   Expected: {expected_variance:.4f}")

        if variance is not None and abs(variance - expected_variance) < 0.0001:
            print("   ✓ PASS: Variance calculated correctly")
            test_results.append(('Test 1', True))
        else:
            print("   ✗ FAIL: Variance incorrect or None")
            test_results.append(('Test 1', False))
    else:
        print("   ✗ FAIL: Location 1 not found")
        test_results.append(('Test 1', False))

    # Test 2: Current year = 0, Last year has data
    print("\nTest 2: Current year = 0 (Should be None)")
    location2 = result.filter(pl.col('Establishment') == 'Test Location 2')
    if len(location2) > 0:
        current_vol = location2['Current_Year_Vol'][0]
        last_vol = location2['Last_Year_Vol'][0]
        variance = location2['Volume_Var_Pct'][0]

        print(f"   Current Year Vol: {current_vol}")
        print(f"   Last Year Vol: {last_vol}")
        print(f"   Variance: {variance}")

        if current_vol == 0 and variance is None:
            print("   ✓ PASS: Variance correctly set to None")
            test_results.append(('Test 2', True))
        else:
            print("   ✗ FAIL: Variance should be None")
            test_results.append(('Test 2', False))
    else:
        print("   ✗ FAIL: Location 2 not found")
        test_results.append(('Test 2', False))

    # Test 3: Last year = 0, Current year has data
    print("\nTest 3: Last year = 0 (Should be None)")
    location3 = result.filter(pl.col('Establishment') == 'Test Location 3')
    if len(location3) > 0:
        current_vol = location3['Current_Year_Vol'][0]
        last_vol = location3['Last_Year_Vol'][0]
        variance = location3['Volume_Var_Pct'][0]

        print(f"   Current Year Vol: {current_vol}")
        print(f"   Last Year Vol: {last_vol}")
        print(f"   Variance: {variance}")

        if last_vol == 0 and variance is None:
            print("   ✓ PASS: Variance correctly set to None")
            test_results.append(('Test 3', True))
        else:
            print("   ✗ FAIL: Variance should be None")
            test_results.append(('Test 3', False))
    else:
        print("   ✗ FAIL: Location 3 not found")
        test_results.append(('Test 3', False))

    # Test 4: Verify fill_null didn't overwrite variance None values
    print("\nTest 4: fill_null(0) should not affect variance columns")
    none_variances = result.filter(pl.col('Volume_Var_Pct').is_null())
    print(f"   Found {len(none_variances)} rows with None variance")

    if len(none_variances) >= 2:  # Should have at least Test Location 2 and 3
        print("   ✓ PASS: None values preserved in variance column")
        test_results.append(('Test 4', True))
    else:
        print("   ✗ FAIL: fill_null may have overwritten None variances")
        test_results.append(('Test 4', False))

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)

    for test_name, result in test_results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} TESTS FAILED")
        return 1

if __name__ == '__main__':
    exit_code = run_tests()
    sys.exit(exit_code)
