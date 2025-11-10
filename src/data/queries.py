"""
Database Queries Module for CasualHero BI Platform

Provides functions to query the AWS PostgreSQL materialized view
and return data as Polars DataFrames for analysis.

Phase 1 Strategy:
    - Query existing materialized view (black box approach)
    - Return Polars DataFrames for downstream processing
    - Apply fiscal calendar transformations in Python (not SQL)
    - No need to understand underlying table structure

Future Migration:
    - Phase 2: Reverse engineer view logic
    - Phase 3: Migrate to Neon and implement logic in application

Schema Note:
    The actual materialized view schema needs to be provided by the client.
    This module contains template functions that will be updated once we
    receive the schema information.
"""

import os
from datetime import date, datetime
from typing import Optional, List, Dict, Any

import polars as pl
from sqlalchemy import text

from src.data.connector import get_db
from src.core.fiscal_calendar import adjust_for_cutoff, get_fiscal_year, get_fiscal_week


# ============================================================================
# Configuration
# ============================================================================

# Materialized view name (from environment or default)
MV_NAME = os.getenv('MATERIALIZED_VIEW_NAME', 'orders_view')  # Update with actual name from client


# ============================================================================
# Base Query Functions
# ============================================================================

def get_raw_data(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: Optional[int] = None
) -> pl.DataFrame:
    """
    Fetch raw data from the materialized view.

    This is the foundation query - all other queries build on this.
    Returns data as a Polars DataFrame for high-performance processing.

    Args:
        start_date: Filter records from this date onwards (optional)
        end_date: Filter records up to this date (optional)
        limit: Limit number of rows returned (optional, for testing)

    Returns:
        Polars DataFrame with raw transaction data

    Example:
        >>> # Get all data
        >>> df = get_raw_data()
        >>>
        >>> # Get data for specific date range
        >>> df = get_raw_data(
        ...     start_date=date(2024, 1, 1),
        ...     end_date=date(2024, 12, 31)
        ... )
        >>>
        >>> # Get sample for testing (first 100 rows)
        >>> df = get_raw_data(limit=100)

    Note:
        This query needs to be updated once we receive the actual
        materialized view schema from the client.
    """
    # Build query dynamically based on parameters
    query_parts = [f"SELECT * FROM {MV_NAME}"]
    params = {}

    # Add WHERE clauses if filters provided
    where_clauses = []
    if start_date:
        where_clauses.append("order_date >= :start_date")
        params['start_date'] = start_date
    if end_date:
        where_clauses.append("order_date <= :end_date")
        params['end_date'] = end_date

    if where_clauses:
        query_parts.append("WHERE " + " AND ".join(where_clauses))

    # Add ORDER BY for consistent results
    query_parts.append("ORDER BY order_date, order_id")

    # Add LIMIT if specified
    if limit:
        query_parts.append(f"LIMIT {limit}")

    query = " ".join(query_parts)

    # Execute query
    db = get_db()
    with db.get_connection() as conn:
        result = conn.execute(text(query), params)

        # Convert to list of dicts
        rows = [dict(row._mapping) for row in result]

    # Convert to Polars DataFrame
    if not rows:
        # Return empty DataFrame with expected schema (update schema as needed)
        return pl.DataFrame()

    df = pl.DataFrame(rows)

    return df


def get_data_with_fiscal_calendar(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    apply_cutoff: bool = True
) -> pl.DataFrame:
    """
    Fetch data and apply fiscal calendar transformations.

    This function:
    1. Queries the materialized view
    2. Applies 7AM cutoff rule (if enabled)
    3. Adds fiscal year and week columns
    4. Returns enhanced DataFrame ready for analysis

    Args:
        start_date: Filter records from this date onwards (optional)
        end_date: Filter records up to this date (optional)
        apply_cutoff: Apply 7AM cutoff rule (default: True)

    Returns:
        Polars DataFrame with fiscal calendar columns added:
            - adjusted_order_date: Date after applying 7AM cutoff
            - fiscal_year: Fiscal year (e.g., 2024)
            - fiscal_week: Fiscal week number (1-52/53)

    Example:
        >>> df = get_data_with_fiscal_calendar(
        ...     start_date=date(2024, 1, 1),
        ...     end_date=date(2024, 12, 31)
        ... )
        >>> print(df.columns)
        ['order_id', 'order_date', 'adjusted_order_date', 'fiscal_year', 'fiscal_week', ...]
    """
    # Get raw data
    df = get_raw_data(start_date, end_date)

    if df.is_empty():
        return df

    # Apply fiscal calendar transformations
    # NOTE: Column names need to be updated based on actual schema

    # Step 1: Apply 7AM cutoff rule if timestamp column exists
    if apply_cutoff and 'order_timestamp' in df.columns:
        # Apply cutoff to each timestamp
        df = df.with_columns([
            pl.col('order_timestamp').map_elements(
                lambda ts: adjust_for_cutoff(ts),
                return_dtype=pl.Date
            ).alias('adjusted_order_date')
        ])
    elif 'order_date' in df.columns:
        # No timestamp, use order_date as-is
        df = df.with_columns([
            pl.col('order_date').alias('adjusted_order_date')
        ])

    # Step 2: Add fiscal year
    if 'adjusted_order_date' in df.columns:
        df = df.with_columns([
            pl.col('adjusted_order_date').map_elements(
                lambda d: get_fiscal_year(d),
                return_dtype=pl.Int32
            ).alias('fiscal_year')
        ])

        # Step 3: Add fiscal week
        df = df.with_columns([
            pl.col('adjusted_order_date').map_elements(
                lambda d: get_fiscal_week(d),
                return_dtype=pl.Int32
            ).alias('fiscal_week')
        ])

    return df


def get_fiscal_week_summary(
    fiscal_year: int,
    fiscal_week: Optional[int] = None
) -> pl.DataFrame:
    """
    Get aggregated data for a specific fiscal week or entire year.

    Returns summary metrics:
    - Net sales
    - Gross sales
    - Order count
    - Items sold
    - Average transaction value (ATV)

    Args:
        fiscal_year: The fiscal year (e.g., 2024)
        fiscal_week: Specific week number (optional, None = entire year)

    Returns:
        Polars DataFrame with aggregated metrics

    Example:
        >>> # Get FY2024 Week 15 summary
        >>> df = get_fiscal_week_summary(2024, 15)
        >>>
        >>> # Get entire FY2024 summary
        >>> df = get_fiscal_week_summary(2024)

    Note:
        Column names and aggregation logic need to be updated
        based on actual materialized view schema.
    """
    # Get data with fiscal calendar
    df = get_data_with_fiscal_calendar()

    if df.is_empty():
        return pl.DataFrame()

    # Filter by fiscal year
    df = df.filter(pl.col('fiscal_year') == fiscal_year)

    # Filter by fiscal week if specified
    if fiscal_week is not None:
        df = df.filter(pl.col('fiscal_week') == fiscal_week)

    # Aggregate (update column names based on actual schema)
    # This is a template - actual aggregation depends on schema
    summary = df.group_by(['fiscal_year', 'fiscal_week']).agg([
        # pl.col('net_sales').sum().alias('total_net_sales'),
        # pl.col('gross_sales').sum().alias('total_gross_sales'),
        # pl.col('order_id').n_unique().alias('order_count'),
        # pl.col('items_sold').sum().alias('total_items'),
        # (pl.col('net_sales').sum() / pl.col('order_id').n_unique()).alias('atv')
        pl.count().alias('record_count')  # Placeholder until we know schema
    ])

    return summary


def get_establishment_summary(
    fiscal_year: int,
    establishment_id: Optional[int] = None
) -> pl.DataFrame:
    """
    Get aggregated data by establishment (location).

    Args:
        fiscal_year: The fiscal year (e.g., 2024)
        establishment_id: Specific establishment (optional, None = all)

    Returns:
        Polars DataFrame with establishment-level metrics

    Example:
        >>> # Get all establishments for FY2024
        >>> df = get_establishment_summary(2024)
        >>>
        >>> # Get specific establishment
        >>> df = get_establishment_summary(2024, establishment_id=5)

    Note:
        Column names need to be updated based on actual schema.
    """
    # Get data with fiscal calendar
    df = get_data_with_fiscal_calendar()

    if df.is_empty():
        return pl.DataFrame()

    # Filter by fiscal year
    df = df.filter(pl.col('fiscal_year') == fiscal_year)

    # Filter by establishment if specified
    if establishment_id is not None and 'establishment_id' in df.columns:
        df = df.filter(pl.col('establishment_id') == establishment_id)

    # Aggregate by establishment (update based on actual schema)
    summary = df.group_by(['establishment_id']).agg([
        pl.count().alias('record_count')  # Placeholder
    ])

    return summary


# ============================================================================
# Schema Discovery Functions
# ============================================================================

def get_view_schema() -> Dict[str, str]:
    """
    Discover the schema of the materialized view.

    Returns:
        Dictionary mapping column names to data types

    Example:
        >>> schema = get_view_schema()
        >>> print(schema)
        {'order_id': 'integer', 'order_date': 'date', 'net_sales': 'numeric', ...}
    """
    # First try: Query information_schema
    query = f"""
        SELECT
            column_name,
            data_type
        FROM information_schema.columns
        WHERE table_name = :table_name
        AND table_schema = 'public'
        ORDER BY ordinal_position
    """

    db = get_db()
    with db.get_connection() as conn:
        result = conn.execute(text(query), {'table_name': MV_NAME})
        rows = result.fetchall()

        # If no results, query the view directly to get column names and types
        if not rows:
            # Query one row to get column names and infer types
            result = conn.execute(text(f"SELECT * FROM {MV_NAME} LIMIT 1"))

            # Get column names from result keys
            columns = result.keys()

            # Get data types from the result description
            # PostgreSQL type codes to names mapping
            type_map = {
                23: 'integer',
                25: 'text',
                1043: 'character varying',
                1082: 'date',
                1114: 'timestamp without time zone',
                1700: 'numeric',
                701: 'double precision',
                16: 'boolean'
            }

            schema = {}
            for idx, col_name in enumerate(columns):
                # Get the type from cursor description
                type_code = result.cursor.description[idx].type_code
                data_type = type_map.get(type_code, f'unknown({type_code})')
                schema[col_name] = data_type

            return schema

    schema = {row[0]: row[1] for row in rows}
    return schema


def get_sample_data(limit: int = 10) -> pl.DataFrame:
    """
    Get sample data from materialized view for schema inspection.

    Args:
        limit: Number of sample rows (default: 10)

    Returns:
        Polars DataFrame with sample data

    Example:
        >>> sample = get_sample_data(5)
        >>> print(sample)
    """
    return get_raw_data(limit=limit)


# ============================================================================
# Production Query Functions (Phase 1 - AWS PostgreSQL)
# ============================================================================

def query_all_transactions(db, years: int = 5) -> pl.DataFrame:
    """
    Query all transaction data from mv_item_details for the last N years.

    This is the main function for loading data in production.
    Used by Streamlit app with 24-hour caching.

    Args:
        db: Database connection instance from get_db()
        years: Number of fiscal years to load (default: 5)

    Returns:
        Polars DataFrame with transaction-level data

    Example:
        >>> from src.data.connector import get_db
        >>> db = get_db()
        >>> df = query_all_transactions(db, years=5)
        >>> print(f"Loaded {len(df):,} rows")
    """
    from datetime import datetime, timedelta
    from src.core.fiscal_calendar import get_fiscal_year, get_week1_start

    # Calculate date range
    # Get current fiscal year
    today = datetime.now().date()
    current_fy = get_fiscal_year(today)

    # Go back N years
    oldest_fy = current_fy - years + 1

    # Get start date (Week 1 of oldest fiscal year)
    start_date = get_week1_start(oldest_fy)

    # Get end date (today)
    end_date = today

    # Strategy: Split queries to avoid AWS timeout (Power BI logic in Polars)

    print(f"  [Strategy] Loading data in 2 queries + join in Polars (faster than SQL JOIN)")

    # Query 1: Get all transactions (fast - simple query)
    transactions_query = """
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
        WHERE "Order_Date" >= :start_date
          AND "Order_Date" <= :end_date
    """

    # Query 2: Get payment statuses (fast - small table)
    payments_query = """
        SELECT DISTINCT
            "Order Id" as "Order_Number",
            "Status"
        FROM public."PaymentDetails"
    """

    with db.get_connection() as conn:
        print(f"  [Query 1/2] Fetching {(end_date - start_date).days / 365:.1f} years from mv_item_details...")
        transactions_df = pl.read_database(
            transactions_query,
            connection=conn,
            execute_options={"parameters": {"start_date": start_date, "end_date": end_date}}
        )
        print(f"  [Query 1/2] ✓ Got {len(transactions_df):,} transactions")

        print(f"  [Query 2/2] Fetching payment statuses...")
        payments_df = pl.read_database(payments_query, connection=conn)
        print(f"  [Query 2/2] ✓ Got {len(payments_df):,} payment records")

    # Apply Power BI logic in Polars (much faster than SQL)
    print(f"  [Filter] Applying Power BI filters (exclude denied, keep captured/authorized)...")

    # LEFT JOIN + filter (matches Power BI exactly)
    df = transactions_df.join(
        payments_df,
        on="Order_Number",
        how="left"
    ).filter(
        # Exclude denied + only keep captured/authorized (Power BI logic)
        (pl.col("Status").str.to_lowercase() != "denied") &
        (pl.col("Status").str.to_lowercase().is_in(["captured", "authorized"]))
    )

    print(f"  [Filter] ✓ Filtered to {len(df):,} valid transactions")

    return df


# ============================================================================
# Module Testing
# ============================================================================

if __name__ == "__main__":
    print("Database Queries Module - Schema Discovery")
    print("=" * 60)

    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("Loaded .env file")
    except ImportError:
        print("python-dotenv not installed")

    print(f"\nMaterialized View: {MV_NAME}")
    print("=" * 60)

    try:
        # Discover schema
        print("\nDiscovering Schema...")
        schema = get_view_schema()

        if schema:
            print(f"\nFound {len(schema)} columns:")
            for col_name, col_type in schema.items():
                print(f"  {col_name:<30} {col_type}")
        else:
            print(f"Could not find view '{MV_NAME}' in database")
            print("Check MV_NAME environment variable or view permissions")

    except Exception as e:
        print(f"\nERROR: {e}")
        print("\nTroubleshooting:")
        print("  1. Ensure DATABASE_URL is set correctly")
        print("  2. Verify materialized view exists")
        print("  3. Check database user has SELECT permissions")
        print("  4. Update MV_NAME environment variable if needed")

    print("\n" + "=" * 60)
    print("Next Steps:")
    print("=" * 60)
    print("1. Get materialized view name from client")
    print("2. Set MV_NAME environment variable")
    print("3. Run this script to discover schema")
    print("4. Update query functions with actual column names")
    print("5. Test with get_sample_data()")
    print("=" * 60)
