"""
Test Weekly Report Generation - FY26 Week 4

Reproduces the Power BI Weekly Report (Page 2) using our KPI calculator.
Compares results against actual Power BI values.
"""

import polars as pl
from src.core.kpi_calculator import (
    calculate_weekly_report,
    add_company_totals,
    add_grand_total
)

print("="*100)
print("WEEKLY REPORT REPRODUCTION TEST - FY26 Week 4 (20 Oct - 26 Oct)")
print("="*100)

# Load sample data
print("\n[Step 1] Loading sample data...")
df = pl.read_csv('sample_data_100_rows.csv')
print(f"[OK] Loaded {len(df)} rows")
print(f"[OK] Columns: {df.columns}")

# Show sample (skipped to avoid Unicode box-drawing characters on Windows console)
# print("\nSample data (first 3 rows):")
# print(df.head(3))

# Calculate weekly report
print("\n" + "="*100)
print("[Step 2] Calculating Weekly Report Metrics...")
print("="*100)

try:
    # Calculate for FY26 Week 4
    report = calculate_weekly_report(df, fiscal_year=2026, fiscal_week=4)

    print(f"\n[OK] Calculated metrics for {len(report)} establishments")

    # Add totals
    report_with_totals = add_company_totals(report)
    final_report = add_grand_total(report_with_totals)

    print(f"[OK] Added company totals and grand total")
    print(f"[OK] Final report has {len(final_report)} rows")

    # Display the report
    print("\n" + "="*100)
    print("[Step 3] WEEKLY REPORT - FY26 Week 4")
    print("="*100)

    # Format for display (matching Power BI structure)
    display_df = final_report.select([
        'Company',
        'Establishment',
        'Current_Year_Sales',
        'Last_Year_Sales',
        'Weekly_Sales_Var_Pct',
        'Current_Year_4W_Avg',
        'Last_Year_4W_Avg',
        'FourWeek_Avg_Var_Pct',
        'Current_Year_Vol',
        'Last_Year_Vol',
        'Volume_Var_Pct',
        'Current_Year_ATV',
        'Last_Year_ATV',
        'ATV_Var_Pct'
    ])

    # Round numbers for readability
    display_df = display_df.with_columns([
        pl.col('Current_Year_Sales').round(0),
        pl.col('Last_Year_Sales').round(0),
        pl.col('Weekly_Sales_Var_Pct').round(2),
        pl.col('Current_Year_4W_Avg').round(0),
        pl.col('Last_Year_4W_Avg').round(0),
        pl.col('FourWeek_Avg_Var_Pct').round(2),
        pl.col('Current_Year_ATV').round(2),
        pl.col('Last_Year_ATV').round(2),
        pl.col('ATV_Var_Pct').round(2)
    ])

    # Skip full table display to avoid Unicode box-drawing characters
    # print("\n" + str(display_df))
    print(f"\n[Skipping table display - will show detailed comparisons below]")

    # Compare with Power BI values
    print("\n" + "="*100)
    print("[Step 4] COMPARISON WITH POWER BI REPORT")
    print("="*100)

    # Power BI values from PDF Page 2 for FY26 Week 4
    power_bi_values = {
        'Meadowhall': {
            'Current_Year_Sales': 8894,
            'Last_Year_Sales': 8080,
            'Weekly_Sales_Var_Pct': 0.10,  # 10%
            'Current_Year_4W_Avg': 9950,
            'Last_Year_4W_Avg': 7718,
            'Current_Year_Vol': 1155,
            'Last_Year_Vol': 1090,
            'Current_Year_ATV': 7.70,
            'Last_Year_ATV': 7.41
        },
        'The O2': {
            'Current_Year_Sales': 8737,
            'Last_Year_Sales': 10287,
            'Weekly_Sales_Var_Pct': -0.15,  # -15%
            'Current_Year_4W_Avg': 8755,
            'Last_Year_4W_Avg': 9015,
            'Current_Year_Vol': 933,
            'Last_Year_Vol': 1067,
            'Current_Year_ATV': 9.36,
            'Last_Year_ATV': 9.64
        },
        'Westfield': {
            'Current_Year_Sales': 18629,
            'Last_Year_Sales': 15565,
            'Weekly_Sales_Var_Pct': 0.20,  # 20%
            'Current_Year_4W_Avg': 16601,
            'Last_Year_4W_Avg': 14279,
            'Current_Year_Vol': 2282,
            'Last_Year_Vol': 1968,
            'Current_Year_ATV': 8.16,
            'Last_Year_ATV': 7.91
        }
    }

    print("\nChecking specific establishments:")
    print("-" * 100)

    for establishment, expected in power_bi_values.items():
        our_result = report.filter(pl.col('Establishment') == establishment)

        if len(our_result) > 0:
            print(f"\n{establishment}:")
            print(f"  Metric                     | Power BI | Our Calc | Diff    | Match?")
            print(f"  " + "-" * 80)

            row = our_result[0]

            # Weekly Sales
            our_sales = row['Current_Year_Sales'][0]
            exp_sales = expected['Current_Year_Sales']
            diff_sales = our_sales - exp_sales
            match_sales = "PASS" if abs(diff_sales) < 1 else "FAIL"
            print(f"  Current Year Sales         | {exp_sales:>8,.0f} | {our_sales:>8,.0f} | {diff_sales:>7,.0f} | {match_sales}")

            # Last Year Sales
            our_ly_sales = row['Last_Year_Sales'][0]
            exp_ly_sales = expected['Last_Year_Sales']
            diff_ly_sales = our_ly_sales - exp_ly_sales
            match_ly_sales = "PASS" if abs(diff_ly_sales) < 1 else "FAIL"
            print(f"  Last Year Sales            | {exp_ly_sales:>8,.0f} | {our_ly_sales:>8,.0f} | {diff_ly_sales:>7,.0f} | {match_ly_sales}")

            # Weekly Sales Variance
            our_var = row['Weekly_Sales_Var_Pct'][0]
            exp_var = expected['Weekly_Sales_Var_Pct']
            diff_var = our_var - exp_var
            match_var = "PASS" if abs(diff_var) < 0.01 else "FAIL"
            print(f"  Weekly Sales Var %         | {exp_var:>8.1%} | {our_var:>8.1%} | {diff_var:>7.1%} | {match_var}")

            # ATV
            our_atv = row['Current_Year_ATV'][0]
            exp_atv = expected['Current_Year_ATV']
            diff_atv = our_atv - exp_atv
            match_atv = "PASS" if abs(diff_atv) < 0.1 else "FAIL"
            print(f"  Current Year ATV           | {exp_atv:>8.2f} | {our_atv:>8.2f} | {diff_atv:>7.2f} | {match_atv}")

        else:
            print(f"\n{establishment}: [NOT FOUND] in our results")

    print("\n" + "="*100)
    print("[Step 5] SUMMARY")
    print("="*100)

    print("\nData Coverage:")
    print(f"  - Establishments in our data: {len(report)}")
    print(f"  - Companies: {report['Company'].n_unique()}")

    # Check if we have all companies
    companies_in_report = report['Company'].unique().to_list()
    print(f"  - Companies found: {', '.join(companies_in_report)}")

    # Check for missing establishments from Power BI
    power_bi_establishments = [
        'Marble Arch House', 'South Kensington', 'The O2', 'The Orient, Trafford',
        'Trafford - Fountain', 'Trafford - Next', 'Trafford - Zara', 'Westfield',
        'Westgate', 'Westgate, Oxford',  # SNOWFLAKE
        'Soho', 'Westfield Stratford',  # STRT SND
        'Arndale, Manchester', 'Braehead, Glasgow', 'Lakeside, Thurrock Way',
        'Meadowhall', 'Metrocentre, Newcastle'  # SKYVIEW
    ]

    our_establishments = report['Establishment'].to_list()
    missing = [e for e in power_bi_establishments if e not in our_establishments]

    if missing:
        print(f"\n[WARNING] Missing establishments (may not have data in sample):")
        for e in missing:
            print(f"     - {e}")

    print("\n" + "="*100)
    print("NOTES:")
    print("="*100)
    print("- Sample data only has 100 rows (may not include all establishments/weeks)")
    print("- Need full database connection to test against complete dataset")
    print("- Discrepancies may be due to:")
    print("  1. Incomplete sample data")
    print("  2. Different DAX logic in Power BI")
    print("  3. Fiscal week calculation differences")
    print("  4. Data filtering differences")
    print("\n[RECOMMENDATION] Get actual DAX measures from Power BI for precise validation")
    print("="*100)

except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()

    print("\n" + "="*100)
    print("TROUBLESHOOTING:")
    print("="*100)
    print("1. Check that sample_data_100_rows.csv exists")
    print("2. Verify fiscal calendar config has FY2026 defined")
    print("3. Ensure fiscal week 4 data exists in sample")
    print("4. Check column names match materialized view schema")
