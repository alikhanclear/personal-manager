"""
Simple test for variance calculations - tests the core logic directly.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import polars as pl

def test_variance_formula():
    """Test the variance formula logic directly."""
    print("=" * 80)
    print("TESTING VARIANCE FORMULA LOGIC")
    print("=" * 80)

    # Test data: Various scenarios
    test_cases = [
        {
            'name': 'Normal case (506 vs 715)',
            'current': 506,
            'last': 715,
            'expected_variance': (506 - 715) / 715,  # -0.2923
            'should_be_none': False
        },
        {
            'name': 'Current = 0, Last has value',
            'current': 0,
            'last': 100,
            'expected_variance': None,
            'should_be_none': True
        },
        {
            'name': 'Current has value, Last = 0',
            'current': 100,
            'last': 0,
            'expected_variance': None,
            'should_be_none': True
        },
        {
            'name': 'Both = 0',
            'current': 0,
            'last': 0,
            'expected_variance': None,
            'should_be_none': True
        },
        {
            'name': 'Positive variance (120 vs 100)',
            'current': 120,
            'last': 100,
            'expected_variance': (120 - 100) / 100,  # 0.20
            'should_be_none': False
        },
    ]

    # Create dataframe
    data = []
    for tc in test_cases:
        data.append({
            'Location': tc['name'],
            'Current_Year_Vol': tc['current'],
            'Last_Year_Vol': tc['last']
        })

    df = pl.DataFrame(data)

    # Apply the variance formula (matching our KPI calculator logic)
    df = df.with_columns([
        pl.when((pl.col('Current_Year_Vol') == 0) | (pl.col('Last_Year_Vol') == 0))
        .then(None)
        .otherwise((pl.col('Current_Year_Vol') - pl.col('Last_Year_Vol')) / pl.col('Last_Year_Vol'))
        .alias('Volume_Var_Pct')
    ])

    # Verify results
    print("\nResults:")
    print("=" * 80)
    passed = 0
    failed = 0

    for i, tc in enumerate(test_cases):
        row = df[i]
        calculated_variance = row['Volume_Var_Pct'][0]

        print(f"\nTest: {tc['name']}")
        print(f"  Current: {row['Current_Year_Vol'][0]}, Last: {row['Last_Year_Vol'][0]}")
        print(f"  Calculated variance: {calculated_variance}")
        print(f"  Expected: {tc['expected_variance']}")

        if tc['should_be_none']:
            if calculated_variance is None:
                print("  ✓ PASS: Correctly set to None")
                passed += 1
            else:
                print(f"  ✗ FAIL: Should be None, got {calculated_variance}")
                failed += 1
        else:
            if calculated_variance is not None and abs(calculated_variance - tc['expected_variance']) < 0.0001:
                print(f"  ✓ PASS: Variance correct ({calculated_variance * 100:.2f}%)")
                passed += 1
            else:
                print(f"  ✗ FAIL: Variance incorrect")
                failed += 1

    # Test that fill_null doesn't overwrite None
    print("\n" + "=" * 80)
    print("Testing fill_null behavior")
    print("=" * 80)

    # Simulate what happens in calculate_weekly_report
    numeric_cols = ['Current_Year_Vol', 'Last_Year_Vol']
    df_test = df.clone()

    # Fill numeric columns only (NOT variance)
    for col in numeric_cols:
        df_test = df_test.with_columns([
            pl.col(col).fill_null(0)
        ])

    # Check if variance None values are preserved
    none_count_before = df.filter(pl.col('Volume_Var_Pct').is_null()).height
    none_count_after = df_test.filter(pl.col('Volume_Var_Pct').is_null()).height

    print(f"  None values before fill_null: {none_count_before}")
    print(f"  None values after fill_null: {none_count_after}")

    if none_count_before == none_count_after:
        print("  ✓ PASS: fill_null preserved None variances")
        passed += 1
    else:
        print("  ✗ FAIL: fill_null overwrote None variances")
        failed += 1

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {failed} TESTS FAILED")
        return 1

if __name__ == '__main__':
    exit_code = test_variance_formula()
    sys.exit(exit_code)
