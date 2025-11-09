"""
KPI Calculator Module for CasualHero BI Platform

Translates Power BI DAX measures to Polars/DuckDB expressions.
Calculates business metrics for weekly and monthly reports.

Key Metrics:
    - Weekly Sales (Current Year, Last Year, YoY Variance)
    - 4-Week Average Sales (Current Year, Last Year, YoY Variance)
    - Order Volumes (Current Year, Last Year, YoY Variance)
    - Average Transaction Value - ATV (Current Year, Last Year, YoY Variance)

Business Rules Applied:
    - 7AM Cutoff: Transactions before 7am count as previous day
    - Fiscal Calendar: Oct 1 - Sep 30
    - Week Definition: Monday - Sunday
"""

import polars as pl
from datetime import date, timedelta
from typing import Optional, Dict, List, Tuple

from src.core.fiscal_calendar import get_fiscal_year, get_fiscal_week, adjust_for_cutoff


# ============================================================================
# Establishment to Company Mapping
# ============================================================================

# Based on Power BI report structure
COMPANY_MAPPING = {
    # SNOWFLAKE locations
    "Marble Arch House": "SNOWFLAKE",
    "South Kensington": "SNOWFLAKE",
    "The O2": "SNOWFLAKE",
    "The Orient, Trafford": "SNOWFLAKE",
    "Trafford - Fountain": "SNOWFLAKE",
    "Trafford - Next": "SNOWFLAKE",
    "Trafford - Zara": "SNOWFLAKE",
    "Westfield": "SNOWFLAKE",
    "Westgate": "SNOWFLAKE",
    "Westgate, Oxford": "SNOWFLAKE",
    "Trafford, Manchester": "SNOWFLAKE",

    # STRT SND locations
    "Soho": "STRT SND",
    "Westfield Stratford": "STRT SND",

    # SKYVIEW locations
    "Arndale, Manchester": "SKYVIEW",
    "Braehead, Glasgow": "SKYVIEW",
    "Lakeside, Thurrock Way": "SKYVIEW",
    "Meadowhall": "SKYVIEW",
    "Metrocentre, Newcastle": "SKYVIEW",
    "Metrocentre": "SKYVIEW",
}


def add_company_column(df: pl.DataFrame) -> pl.DataFrame:
    """
    Add Company column to DataFrame based on Establishment name.

    Args:
        df: Polars DataFrame with 'Establishment' column

    Returns:
        DataFrame with 'Company' column added

    Example:
        >>> df = pl.DataFrame({
        ...     'Establishment': ['The O2', 'Soho', 'Meadowhall']
        ... })
        >>> df = add_company_column(df)
        >>> print(df['Company'])
        ['SNOWFLAKE', 'STRT SND', 'SKYVIEW']
    """
    if 'Establishment' not in df.columns:
        raise ValueError("DataFrame must have 'Establishment' column")

    # Create mapping expression using replace
    return df.with_columns([
        pl.col('Establishment').replace(COMPANY_MAPPING, default="UNKNOWN").alias('Company')
    ])


# ============================================================================
# Data Preparation
# ============================================================================

def prepare_transaction_data(df: pl.DataFrame) -> pl.DataFrame:
    """
    Prepare transaction data for KPI calculations.

    Applies:
        - 7AM cutoff rule
        - Fiscal year and week calculations
        - Company mapping
        - Order-level aggregation

    Args:
        df: Raw transaction data from materialized view
            Required columns: Establishment, Order_Number, Order_Date,
                            Net_Sales_Actual, Product_Quantity

    Returns:
        DataFrame with fiscal calendar and order-level metrics

    Columns added:
        - Company: Company name (SNOWFLAKE, STRT SND, SKYVIEW)
        - Adjusted_Order_Date: Date after 7AM cutoff
        - Fiscal_Year: Fiscal year (e.g., 2025, 2026)
        - Fiscal_Week: Fiscal week number (1-52/53)
        - Order_Net_Sales: Total net sales for the order
        - Order_Item_Count: Number of items in the order
    """
    # Check if data is already prepared (idempotent operation)
    if 'Fiscal_Year' in df.columns and 'Adjusted_Order_Date' in df.columns:
        # Data already prepared, return as-is
        return df

    # Add Company column
    df = add_company_column(df)

    # Parse Order_Date as datetime if it's a string
    if df.schema['Order_Date'] == pl.Utf8:
        df = df.with_columns([
            pl.col('Order_Date').str.strptime(pl.Datetime, format='%Y-%m-%dT%H:%M:%S%.f')
        ])

    # Apply 7AM cutoff rule
    df = df.with_columns([
        pl.col('Order_Date').map_elements(
            lambda dt: adjust_for_cutoff(dt) if dt else None,
            return_dtype=pl.Date
        ).alias('Adjusted_Order_Date')
    ])

    # Add fiscal year and week
    df = df.with_columns([
        pl.col('Adjusted_Order_Date').map_elements(
            lambda d: get_fiscal_year(d) if d else None,
            return_dtype=pl.Int64
        ).alias('Fiscal_Year'),

        pl.col('Adjusted_Order_Date').map_elements(
            lambda d: get_fiscal_week(d) if d else None,
            return_dtype=pl.Int64
        ).alias('Fiscal_Week')
    ])

    # Aggregate to order level (one row per order)
    # Power BI measures calculate at order level, not line item level
    order_df = df.group_by([
        'Company', 'Establishment', 'Order_Number',
        'Adjusted_Order_Date', 'Fiscal_Year', 'Fiscal_Week'
    ]).agg([
        pl.col('Net_Sales_Actual').sum().alias('Order_Net_Sales'),
        pl.col('Product_Quantity').sum().alias('Order_Item_Count')
    ])

    return order_df


# ============================================================================
# Weekly Sales Calculations
# ============================================================================

def calculate_weekly_sales(
    df: pl.DataFrame,
    fiscal_year: int,
    fiscal_week: int
) -> pl.DataFrame:
    """
    Calculate weekly sales by Company and Establishment.

    Returns current year and last year sales with variance.

    Args:
        df: Prepared transaction data (from prepare_transaction_data)
        fiscal_year: Target fiscal year (e.g., 2026)
        fiscal_week: Target fiscal week (1-52/53)

    Returns:
        DataFrame with columns:
            - Company
            - Establishment
            - Current_Year_Sales: Sales for target week
            - Last_Year_Sales: Sales for same week last year
            - Weekly_Sales_Var_Pct: YoY variance percentage

    Example:
        >>> df = prepare_transaction_data(raw_df)
        >>> weekly = calculate_weekly_sales(df, 2026, 4)
        >>> print(weekly)
        Company      Establishment        Current_Year  Last_Year  Var%
        SNOWFLAKE    The O2              8737          10287      -15%
        SNOWFLAKE    Westfield           18629         15565       20%
    """
    # Filter to target week (current year)
    current_year_df = df.filter(
        (pl.col('Fiscal_Year') == fiscal_year) &
        (pl.col('Fiscal_Week') == fiscal_week)
    )

    # Filter to same week last year
    last_year_df = df.filter(
        (pl.col('Fiscal_Year') == fiscal_year - 1) &
        (pl.col('Fiscal_Week') == fiscal_week)
    )

    # Aggregate by Company and Establishment for current year
    current_year_sales = current_year_df.group_by(['Company', 'Establishment']).agg([
        pl.col('Order_Net_Sales').sum().alias('Current_Year_Sales')
    ])

    # Aggregate by Company and Establishment for last year
    last_year_sales = last_year_df.group_by(['Company', 'Establishment']).agg([
        pl.col('Order_Net_Sales').sum().alias('Last_Year_Sales')
    ])

    # Join current and last year
    result = current_year_sales.join(
        last_year_sales,
        on=['Company', 'Establishment'],
        how='outer',  # Keep all establishments even if no data in one year
        coalesce=True  # Merge join keys to avoid _right suffix columns
    ).fill_null(0)

    # Calculate variance percentage (safe division - avoid divide by zero)
    # Replace zeros with null to prevent division by zero
    result = result.with_columns([
        pl.when(pl.col('Last_Year_Sales') == 0)
        .then(None)
        .otherwise(pl.col('Last_Year_Sales'))
        .alias('Last_Year_Sales_Safe')
    ])

    result = result.with_columns([
        (
            (pl.col('Current_Year_Sales') - pl.col('Last_Year_Sales')) /
            pl.col('Last_Year_Sales_Safe')
        ).alias('Weekly_Sales_Var_Pct')
    ]).drop('Last_Year_Sales_Safe')

    return result


def calculate_4week_avg(
    df: pl.DataFrame,
    fiscal_year: int,
    fiscal_week: int
) -> pl.DataFrame:
    """
    Calculate 4-week rolling average sales by Company and Establishment.

    Calculates average for the 4 weeks ending with the target week.
    Crosses fiscal year boundaries when needed (e.g., Week 1-3).

    Args:
        df: Prepared transaction data
        fiscal_year: Target fiscal year
        fiscal_week: Target fiscal week

    Returns:
        DataFrame with columns:
            - Company
            - Establishment
            - Current_Year_4W_Avg: 4-week average for current year
            - Last_Year_4W_Avg: 4-week average for last year
            - FourWeek_Avg_Var_Pct: YoY variance percentage
    """
    # Calculate week range (last 4 weeks including target week)
    week_start = fiscal_week - 3
    week_end = fiscal_week

    # Handle cross-year boundaries (Week 1, 2, 3)
    if week_start < 1:
        # Need weeks from previous fiscal year
        weeks_needed_from_prev_fy = abs(week_start - 1) + 1  # How many weeks to pull from prev FY

        # Get max week number from previous FY (could be 52 or 53)
        prev_fy_max_week = df.filter(
            pl.col('Fiscal_Year') == fiscal_year - 1
        )['Fiscal_Week'].max()

        if prev_fy_max_week is None:
            prev_fy_max_week = 52  # Default to 52 if no data

        # Get weeks from previous FY (last N weeks)
        prev_fy_week_start = prev_fy_max_week - weeks_needed_from_prev_fy + 1

        # Current year: weeks 1 to target week
        current_year_df_this_fy = df.filter(
            (pl.col('Fiscal_Year') == fiscal_year) &
            (pl.col('Fiscal_Week') >= 1) &
            (pl.col('Fiscal_Week') <= week_end)
        )

        # Previous FY: last N weeks
        current_year_df_prev_fy = df.filter(
            (pl.col('Fiscal_Year') == fiscal_year - 1) &
            (pl.col('Fiscal_Week') >= prev_fy_week_start) &
            (pl.col('Fiscal_Week') <= prev_fy_max_week)
        )

        # Combine both
        current_year_df = pl.concat([current_year_df_prev_fy, current_year_df_this_fy])

        # Same logic for last year (fiscal_year - 1 becomes fiscal_year - 2)
        last_year_df_this_fy = df.filter(
            (pl.col('Fiscal_Year') == fiscal_year - 1) &
            (pl.col('Fiscal_Week') >= 1) &
            (pl.col('Fiscal_Week') <= week_end)
        )

        # Get max week from fiscal_year - 2
        two_years_ago_max_week = df.filter(
            pl.col('Fiscal_Year') == fiscal_year - 2
        )['Fiscal_Week'].max()

        if two_years_ago_max_week is None:
            two_years_ago_max_week = 52

        two_years_ago_week_start = two_years_ago_max_week - weeks_needed_from_prev_fy + 1

        last_year_df_prev_fy = df.filter(
            (pl.col('Fiscal_Year') == fiscal_year - 2) &
            (pl.col('Fiscal_Week') >= two_years_ago_week_start) &
            (pl.col('Fiscal_Week') <= two_years_ago_max_week)
        )

        last_year_df = pl.concat([last_year_df_prev_fy, last_year_df_this_fy])

    else:
        # Normal case: all 4 weeks within same fiscal year
        # Filter to last 4 weeks (current year)
        current_year_df = df.filter(
            (pl.col('Fiscal_Year') == fiscal_year) &
            (pl.col('Fiscal_Week') >= week_start) &
            (pl.col('Fiscal_Week') <= week_end)
        )

        # Filter to same 4 weeks last year
        last_year_df = df.filter(
            (pl.col('Fiscal_Year') == fiscal_year - 1) &
            (pl.col('Fiscal_Week') >= week_start) &
            (pl.col('Fiscal_Week') <= week_end)
        )

    # Aggregate by Company, Establishment, Week for current year
    current_year_weekly = current_year_df.group_by([
        'Company', 'Establishment', 'Fiscal_Week'
    ]).agg([
        pl.col('Order_Net_Sales').sum().alias('Weekly_Sales')
    ])

    # Calculate average across 4 weeks
    current_year_avg = current_year_weekly.group_by(['Company', 'Establishment']).agg([
        pl.col('Weekly_Sales').mean().alias('Current_Year_4W_Avg')
    ])

    # Same for last year
    last_year_weekly = last_year_df.group_by([
        'Company', 'Establishment', 'Fiscal_Week'
    ]).agg([
        pl.col('Order_Net_Sales').sum().alias('Weekly_Sales')
    ])

    last_year_avg = last_year_weekly.group_by(['Company', 'Establishment']).agg([
        pl.col('Weekly_Sales').mean().alias('Last_Year_4W_Avg')
    ])

    # Join current and last year
    result = current_year_avg.join(
        last_year_avg,
        on=['Company', 'Establishment'],
        how='outer',
        coalesce=True  # Merge join keys to avoid _right suffix columns
    ).fill_null(0)

    # Calculate variance (safe division - avoid divide by zero)
    result = result.with_columns([
        pl.when(pl.col('Last_Year_4W_Avg') == 0)
        .then(None)
        .otherwise(pl.col('Last_Year_4W_Avg'))
        .alias('Last_Year_4W_Avg_Safe')
    ])

    result = result.with_columns([
        (
            (pl.col('Current_Year_4W_Avg') - pl.col('Last_Year_4W_Avg')) /
            pl.col('Last_Year_4W_Avg_Safe')
        ).alias('FourWeek_Avg_Var_Pct')
    ]).drop('Last_Year_4W_Avg_Safe')

    return result


def calculate_order_volumes(
    df: pl.DataFrame,
    fiscal_year: int,
    fiscal_week: int
) -> pl.DataFrame:
    """
    Calculate order volumes (number of orders) by Company and Establishment.

    Args:
        df: Prepared transaction data
        fiscal_year: Target fiscal year
        fiscal_week: Target fiscal week

    Returns:
        DataFrame with columns:
            - Company
            - Establishment
            - Current_Year_Vol: Order count for current year
            - Last_Year_Vol: Order count for last year
            - Volume_Var_Pct: YoY variance percentage
    """
    # Filter to target week (current year)
    current_year_df = df.filter(
        (pl.col('Fiscal_Year') == fiscal_year) &
        (pl.col('Fiscal_Week') == fiscal_week)
    )

    # Filter to same week last year
    last_year_df = df.filter(
        (pl.col('Fiscal_Year') == fiscal_year - 1) &
        (pl.col('Fiscal_Week') == fiscal_week)
    )

    # Count orders (not line items)
    current_year_vol = current_year_df.group_by(['Company', 'Establishment']).agg([
        pl.col('Order_Number').n_unique().alias('Current_Year_Vol')
    ])

    last_year_vol = last_year_df.group_by(['Company', 'Establishment']).agg([
        pl.col('Order_Number').n_unique().alias('Last_Year_Vol')
    ])

    # Join
    result = current_year_vol.join(
        last_year_vol,
        on=['Company', 'Establishment'],
        how='outer',
        coalesce=True  # Merge join keys to avoid _right suffix columns
    ).fill_null(0)

    # Calculate variance (safe division - avoid divide by zero)
    result = result.with_columns([
        pl.when(pl.col('Last_Year_Vol') == 0)
        .then(None)
        .otherwise(pl.col('Last_Year_Vol'))
        .alias('Last_Year_Vol_Safe')
    ])

    result = result.with_columns([
        (
            (pl.col('Current_Year_Vol') - pl.col('Last_Year_Vol')) /
            pl.col('Last_Year_Vol_Safe')
        ).alias('Volume_Var_Pct')
    ]).drop('Last_Year_Vol_Safe')

    return result


def calculate_atv(
    df: pl.DataFrame,
    fiscal_year: int,
    fiscal_week: int
) -> pl.DataFrame:
    """
    Calculate Average Transaction Value (ATV) by Company and Establishment.

    ATV = Total Net Sales / Number of Orders

    Args:
        df: Prepared transaction data
        fiscal_year: Target fiscal year
        fiscal_week: Target fiscal week

    Returns:
        DataFrame with columns:
            - Company
            - Establishment
            - Current_Year_ATV: ATV for current year
            - Last_Year_ATV: ATV for last year
            - ATV_Var_Pct: YoY variance percentage
    """
    # Filter to target week (current year)
    current_year_df = df.filter(
        (pl.col('Fiscal_Year') == fiscal_year) &
        (pl.col('Fiscal_Week') == fiscal_week)
    )

    # Filter to same week last year
    last_year_df = df.filter(
        (pl.col('Fiscal_Year') == fiscal_year - 1) &
        (pl.col('Fiscal_Week') == fiscal_week)
    )

    # Calculate ATV = Total Sales / Order Count
    current_year_atv = current_year_df.group_by(['Company', 'Establishment']).agg([
        (pl.col('Order_Net_Sales').sum() / pl.col('Order_Number').n_unique()).alias('Current_Year_ATV')
    ])

    last_year_atv = last_year_df.group_by(['Company', 'Establishment']).agg([
        (pl.col('Order_Net_Sales').sum() / pl.col('Order_Number').n_unique()).alias('Last_Year_ATV')
    ])

    # Join
    result = current_year_atv.join(
        last_year_atv,
        on=['Company', 'Establishment'],
        how='outer',
        coalesce=True  # Merge join keys to avoid _right suffix columns
    ).fill_null(0)

    # Calculate variance (safe division - avoid divide by zero)
    result = result.with_columns([
        pl.when(pl.col('Last_Year_ATV') == 0)
        .then(None)
        .otherwise(pl.col('Last_Year_ATV'))
        .alias('Last_Year_ATV_Safe')
    ])

    result = result.with_columns([
        (
            (pl.col('Current_Year_ATV') - pl.col('Last_Year_ATV')) /
            pl.col('Last_Year_ATV_Safe')
        ).alias('ATV_Var_Pct')
    ]).drop('Last_Year_ATV_Safe')

    return result


# ============================================================================
# Combined Weekly Report Data
# ============================================================================

def calculate_weekly_report(
    df: pl.DataFrame,
    fiscal_year: int,
    fiscal_week: int
) -> pl.DataFrame:
    """
    Calculate all metrics for the Weekly Report (Page 2 of Power BI).

    Combines:
        - Weekly Sales
        - 4-Week Average
        - Order Volumes
        - ATV

    All with YoY comparisons and variances.

    Args:
        df: Raw transaction data from materialized view
        fiscal_year: Target fiscal year (e.g., 2026)
        fiscal_week: Target fiscal week (e.g., 4)

    Returns:
        DataFrame with all metrics combined, ready for display

    Columns:
        - Company
        - Establishment
        - Current_Year_Sales, Last_Year_Sales, Weekly_Sales_Var_Pct
        - Current_Year_4W_Avg, Last_Year_4W_Avg, FourWeek_Avg_Var_Pct
        - Current_Year_Vol, Last_Year_Vol, Volume_Var_Pct
        - Current_Year_ATV, Last_Year_ATV, ATV_Var_Pct

    Example:
        >>> report = calculate_weekly_report(df, 2026, 4)
        >>> print(report.columns)
        ['Company', 'Establishment', 'Current_Year_Sales', ...]
    """
    # Prepare data
    prepared_df = prepare_transaction_data(df)

    # Calculate each metric
    weekly_sales = calculate_weekly_sales(prepared_df, fiscal_year, fiscal_week)
    four_week_avg = calculate_4week_avg(prepared_df, fiscal_year, fiscal_week)
    volumes = calculate_order_volumes(prepared_df, fiscal_year, fiscal_week)
    atv = calculate_atv(prepared_df, fiscal_year, fiscal_week)

    # Join all metrics together
    # Start with weekly sales as base
    result = weekly_sales

    # Join 4-week avg
    # NOTE: All metric functions use coalesce=True in their internal joins,
    # so no _right suffix columns exist. Direct join is clean.
    result = result.join(
        four_week_avg,
        on=['Company', 'Establishment'],
        how='left'
    )

    # Join volumes
    result = result.join(
        volumes,
        on=['Company', 'Establishment'],
        how='left'
    )

    # Join ATV
    result = result.join(
        atv,
        on=['Company', 'Establishment'],
        how='left'
    )

    # Fill nulls with 0
    result = result.fill_null(0)

    # Sort by Company then Establishment
    result = result.sort(['Company', 'Establishment'])

    return result


# ============================================================================
# Aggregation Functions (Company Totals, Grand Total)
# ============================================================================

def add_company_totals(df: pl.DataFrame) -> pl.DataFrame:
    """
    Add company-level total rows to the report.

    Inserts subtotal rows after each company's establishments.

    Args:
        df: Weekly report DataFrame

    Returns:
        DataFrame with company total rows added
    """
    # Calculate company totals
    company_totals = df.group_by('Company').agg([
        # Weekly Sales
        pl.col('Current_Year_Sales').sum(),
        pl.col('Last_Year_Sales').sum(),

        # 4-Week Avg
        pl.col('Current_Year_4W_Avg').sum(),
        pl.col('Last_Year_4W_Avg').sum(),

        # Volumes
        pl.col('Current_Year_Vol').sum(),
        pl.col('Last_Year_Vol').sum(),

        # ATV - weighted average (total sales / total orders)
        (pl.col('Current_Year_Sales').sum() / pl.col('Current_Year_Vol').sum()).alias('Current_Year_ATV'),
        (pl.col('Last_Year_Sales').sum() / pl.col('Last_Year_Vol').sum()).alias('Last_Year_ATV'),
    ])

    # Recalculate variances for totals
    company_totals = company_totals.with_columns([
        ((pl.col('Current_Year_Sales') - pl.col('Last_Year_Sales')) / pl.col('Last_Year_Sales')).alias('Weekly_Sales_Var_Pct'),
        ((pl.col('Current_Year_4W_Avg') - pl.col('Last_Year_4W_Avg')) / pl.col('Last_Year_4W_Avg')).alias('FourWeek_Avg_Var_Pct'),
        ((pl.col('Current_Year_Vol') - pl.col('Last_Year_Vol')) / pl.col('Last_Year_Vol')).alias('Volume_Var_Pct'),
        ((pl.col('Current_Year_ATV') - pl.col('Last_Year_ATV')) / pl.col('Last_Year_ATV')).alias('ATV_Var_Pct'),
    ])

    # Add "Total" as Establishment name
    company_totals = company_totals.with_columns([
        pl.lit("Total").alias('Establishment')
    ])

    # Reorder columns to match original DataFrame
    company_totals = company_totals.select(df.columns)

    # Combine with original data
    result = pl.concat([df, company_totals]).sort(['Company', 'Establishment'])

    return result


def add_grand_total(df: pl.DataFrame) -> pl.DataFrame:
    """
    Add grand total row to the report.

    Args:
        df: Weekly report DataFrame (ideally with company totals already added)

    Returns:
        DataFrame with grand total row appended
    """
    # Calculate grand totals
    grand_total = df.group_by(pl.lit(1).alias('_dummy')).agg([
        pl.col('Current_Year_Sales').sum(),
        pl.col('Last_Year_Sales').sum(),
        pl.col('Current_Year_4W_Avg').sum(),
        pl.col('Last_Year_4W_Avg').sum(),
        pl.col('Current_Year_Vol').sum(),
        pl.col('Last_Year_Vol').sum(),
        (pl.col('Current_Year_Sales').sum() / pl.col('Current_Year_Vol').sum()).alias('Current_Year_ATV'),
        (pl.col('Last_Year_Sales').sum() / pl.col('Last_Year_Vol').sum()).alias('Last_Year_ATV'),
    ]).drop('_dummy')

    # Recalculate variances
    grand_total = grand_total.with_columns([
        ((pl.col('Current_Year_Sales') - pl.col('Last_Year_Sales')) / pl.col('Last_Year_Sales')).alias('Weekly_Sales_Var_Pct'),
        ((pl.col('Current_Year_4W_Avg') - pl.col('Last_Year_4W_Avg')) / pl.col('Last_Year_4W_Avg')).alias('FourWeek_Avg_Var_Pct'),
        ((pl.col('Current_Year_Vol') - pl.col('Last_Year_Vol')) / pl.col('Last_Year_Vol')).alias('Volume_Var_Pct'),
        ((pl.col('Current_Year_ATV') - pl.col('Last_Year_ATV')) / pl.col('Last_Year_ATV')).alias('ATV_Var_Pct'),
    ])

    # Add "Total" labels
    grand_total = grand_total.with_columns([
        pl.lit("Total").alias('Company'),
        pl.lit("").alias('Establishment')
    ])

    # Reorder columns to match original DataFrame
    grand_total = grand_total.select(df.columns)

    # Append to result
    result = pl.concat([df, grand_total])

    return result
