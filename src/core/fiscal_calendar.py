"""
Fiscal Calendar Module for CasualHero BI Platform

This module provides fiscal year and week calculations for Snowflake Gelato's
business intelligence reporting. All calculations are driven by configuration
data (fiscal_overrides.yaml) to ensure business rules are client-controlled.

Business Rules:
    - Fiscal Year: October 1 - September 30
    - Weeks: Monday - Sunday
    - Week 1 always starts on a Monday (configured per year)
    - 7AM Cutoff: Transactions before 7:00 AM count as the previous day

Key Functions:
    - adjust_for_cutoff: Apply 7AM cutoff rule to timestamps
    - get_week1_start: Get Week 1 start date for a fiscal year
    - get_fiscal_year: Determine fiscal year for any date
    - get_fiscal_week: Calculate fiscal week number (1-52/53)

Configuration:
    Fiscal year Week 1 start dates are defined in:
    config/fiscal_overrides.yaml
"""

from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, Optional
import yaml


# ============================================================================
# Configuration Loading
# ============================================================================

def _load_fiscal_config() -> Dict[int, date]:
    """
    Load fiscal year overrides from YAML configuration file.

    Returns:
        Dictionary mapping fiscal year (int) to Week 1 start date (date object)

    Raises:
        FileNotFoundError: If config/fiscal_overrides.yaml doesn't exist
        ValueError: If YAML is invalid or dates are malformed

    Example:
        >>> config = _load_fiscal_config()
        >>> config[2025]
        date(2024, 9, 30)
    """
    # Find config file relative to this module
    config_path = Path(__file__).parent.parent.parent / "config" / "fiscal_overrides.yaml"

    if not config_path.exists():
        raise FileNotFoundError(
            f"Fiscal calendar configuration not found: {config_path}\n"
            f"Please ensure config/fiscal_overrides.yaml exists."
        )

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in fiscal_overrides.yaml: {e}")

    if not data or 'fiscal_overrides' not in data:
        raise ValueError(
            "fiscal_overrides.yaml must contain 'fiscal_overrides' key"
        )

    # Convert string dates to date objects
    fiscal_overrides = {}
    for year_str, date_str in data['fiscal_overrides'].items():
        try:
            fiscal_year = int(year_str)
            week1_start = datetime.strptime(date_str, '%Y-%m-%d').date()

            # Validate it's a Monday
            if week1_start.weekday() != 0:  # 0 = Monday
                raise ValueError(
                    f"Week 1 start for FY{fiscal_year} must be a Monday. "
                    f"Got {date_str} which is a {week1_start.strftime('%A')}"
                )

            fiscal_overrides[fiscal_year] = week1_start
        except (ValueError, AttributeError) as e:
            raise ValueError(
                f"Invalid date format for fiscal year {year_str}: {date_str}. "
                f"Expected YYYY-MM-DD format. Error: {e}"
            )

    return fiscal_overrides


# Load configuration once at module import
_FISCAL_OVERRIDES: Dict[int, date] = _load_fiscal_config()


# ============================================================================
# Public API Functions
# ============================================================================

def adjust_for_cutoff(timestamp: datetime, cutoff_hour: int = 7) -> date:
    """
    Apply 7AM cutoff rule: transactions before cutoff count as previous day.

    Business Rule:
        Any transaction before 7:00 AM should be reported as part of the
        previous calendar day's business. This accounts for late-night
        operations that close after midnight.

    Args:
        timestamp: The transaction timestamp to adjust
        cutoff_hour: Hour of day for cutoff (default: 7 for 7:00 AM)

    Returns:
        Adjusted date for reporting purposes

    Examples:
        >>> # Monday 6:45 AM → Sunday
        >>> adjust_for_cutoff(datetime(2024, 10, 7, 6, 45))
        date(2024, 10, 6)

        >>> # Monday 7:01 AM → Monday
        >>> adjust_for_cutoff(datetime(2024, 10, 7, 7, 1))
        date(2024, 10, 7)

        >>> # Monday 12:01 AM → Sunday
        >>> adjust_for_cutoff(datetime(2024, 10, 7, 0, 1))
        date(2024, 10, 6)
    """
    if timestamp.hour < cutoff_hour:
        return (timestamp - timedelta(days=1)).date()
    return timestamp.date()


def get_week1_start(fiscal_year: int) -> date:
    """
    Get the Week 1 start date for a specific fiscal year.

    This function looks up the configured Week 1 start date from the
    fiscal_overrides.yaml configuration file. No logic is applied -
    dates are purely configuration-driven.

    Args:
        fiscal_year: The fiscal year (e.g., 2025 for FY2025)

    Returns:
        Monday date when Week 1 starts for the given fiscal year

    Raises:
        ValueError: If fiscal year is not defined in configuration

    Examples:
        >>> get_week1_start(2025)
        date(2024, 9, 30)

        >>> get_week1_start(2024)
        date(2023, 10, 2)
    """
    if fiscal_year not in _FISCAL_OVERRIDES:
        available_years = sorted(_FISCAL_OVERRIDES.keys())
        raise ValueError(
            f"Fiscal year {fiscal_year} not configured in fiscal_overrides.yaml. "
            f"Available years: {available_years}. "
            f"Please add FY{fiscal_year} to the configuration."
        )

    return _FISCAL_OVERRIDES[fiscal_year]


def get_fiscal_year(target_date: date) -> int:
    """
    Determine the fiscal year for any given date.

    This function iterates through configured fiscal years to find which
    fiscal year the target date belongs to. It handles edge cases where
    Week 1 might start in late September.

    Algorithm:
        1. Check each configured fiscal year
        2. Find the year where target_date >= Week 1 start
        3. Verify target_date is before next fiscal year's Week 1
        4. Return the matching fiscal year

    Args:
        target_date: The date to look up

    Returns:
        Fiscal year (e.g., 2025 for FY2025)

    Raises:
        ValueError: If date falls outside all configured fiscal years

    Examples:
        >>> # Sep 30, 2024 is in FY2025 (Week 1 starts Sep 30)
        >>> get_fiscal_year(date(2024, 9, 30))
        2025

        >>> # Oct 1, 2023 is in FY2023 (Sunday before Week 1)
        >>> get_fiscal_year(date(2023, 10, 1))
        2023

        >>> # Jan 15, 2024 is in FY2024
        >>> get_fiscal_year(date(2024, 1, 15))
        2024
    """
    # Sort fiscal years to check from earliest to latest
    sorted_years = sorted(_FISCAL_OVERRIDES.keys())

    for i, fiscal_year in enumerate(sorted_years):
        week1_start = _FISCAL_OVERRIDES[fiscal_year]

        # Check if date is after this fiscal year's start
        if target_date >= week1_start:
            # Check if there's a next fiscal year
            if i + 1 < len(sorted_years):
                next_year = sorted_years[i + 1]
                next_week1_start = _FISCAL_OVERRIDES[next_year]

                # If date is before next fiscal year, it belongs to current
                if target_date < next_week1_start:
                    return fiscal_year
            else:
                # No next year configured, assume it's in this fiscal year
                return fiscal_year

    # Date is before all configured fiscal years
    available_years = sorted(_FISCAL_OVERRIDES.keys())
    raise ValueError(
        f"Date {target_date} falls outside all configured fiscal years. "
        f"Earliest configured: FY{available_years[0]} starting {_FISCAL_OVERRIDES[available_years[0]]}. "
        f"Please add earlier fiscal years to fiscal_overrides.yaml if needed."
    )


def get_fiscal_week(target_date: date) -> int:
    """
    Calculate the fiscal week number (1-52 or 1-53) for any given date.

    Week Calculation:
        - Week 1 starts on the configured Monday for each fiscal year
        - Weeks are Monday-Sunday
        - Week number = floor((days since Week 1 start) / 7) + 1
        - Most years have 52 weeks, some have 53

    Args:
        target_date: The date to calculate the week for

    Returns:
        Fiscal week number (1-52 or 1-53)

    Raises:
        ValueError: If date falls outside configured fiscal years

    Examples:
        >>> # Oct 2, 2023 is FY2024 Week 1 Day 1
        >>> get_fiscal_week(date(2023, 10, 2))
        1

        >>> # Oct 8, 2023 is FY2024 Week 1 Day 7 (Sunday)
        >>> get_fiscal_week(date(2023, 10, 8))
        1

        >>> # Oct 9, 2023 is FY2024 Week 2 Day 1
        >>> get_fiscal_week(date(2023, 10, 9))
        2

        >>> # Sep 30, 2024 is FY2025 Week 1 Day 1
        >>> get_fiscal_week(date(2024, 9, 30))
        1
    """
    fiscal_year = get_fiscal_year(target_date)
    week1_start = get_week1_start(fiscal_year)

    # Calculate days since Week 1 started
    days_since_week1 = (target_date - week1_start).days

    # Week number (1-indexed)
    week_number = (days_since_week1 // 7) + 1

    return week_number


def get_fiscal_info(target_date: date) -> Dict[str, any]:
    """
    Get comprehensive fiscal calendar information for a date.

    Convenience function that returns all fiscal calendar attributes
    for a given date in a single call.

    Args:
        target_date: The date to analyze

    Returns:
        Dictionary containing:
            - fiscal_year: The fiscal year (int)
            - fiscal_week: The week number (int)
            - week1_start: Week 1 start date for this fiscal year (date)
            - calendar_date: The input date (date)

    Example:
        >>> get_fiscal_info(date(2024, 9, 30))
        {
            'fiscal_year': 2025,
            'fiscal_week': 1,
            'week1_start': date(2024, 9, 30),
            'calendar_date': date(2024, 9, 30)
        }
    """
    fiscal_year = get_fiscal_year(target_date)
    fiscal_week = get_fiscal_week(target_date)
    week1_start = get_week1_start(fiscal_year)

    return {
        'fiscal_year': fiscal_year,
        'fiscal_week': fiscal_week,
        'week1_start': week1_start,
        'calendar_date': target_date
    }


# ============================================================================
# Module Info
# ============================================================================

def get_configured_years() -> list[int]:
    """
    Get list of all fiscal years currently configured.

    Useful for validation and reporting purposes.

    Returns:
        Sorted list of fiscal years with configured Week 1 start dates

    Example:
        >>> get_configured_years()
        [2024, 2025, 2026]
    """
    return sorted(_FISCAL_OVERRIDES.keys())


if __name__ == "__main__":
    # Quick validation when run directly
    print("Fiscal Calendar Module - Configuration Check")
    print("=" * 60)
    print(f"\nConfigured Fiscal Years: {get_configured_years()}")
    print("\nFiscal Year Week 1 Start Dates:")
    for fy in get_configured_years():
        week1 = get_week1_start(fy)
        print(f"  FY{fy}: {week1.strftime('%Y-%m-%d (%A)')}")

    print("\n" + "=" * 60)
    print("7AM Cutoff Rule Examples:")
    print("=" * 60)
    examples = [
        datetime(2024, 10, 7, 6, 45),  # Monday 6:45 AM
        datetime(2024, 10, 7, 7, 1),   # Monday 7:01 AM
        datetime(2024, 10, 7, 0, 1),   # Monday 12:01 AM
    ]
    for ts in examples:
        adjusted = adjust_for_cutoff(ts)
        print(f"{ts.strftime('%A %I:%M %p')} -> {adjusted.strftime('%A %Y-%m-%d')}")

    print("\n" + "=" * 60)
    print("FY2024 Test Examples:")
    print("=" * 60)

    test_dates = [
        date(2023, 10, 1),   # Sunday before Week 1
        date(2023, 10, 2),   # Week 1 Day 1 (Monday)
        date(2023, 10, 8),   # Week 1 Day 7 (Sunday)
        date(2023, 10, 9),   # Week 2 Day 1 (Monday)
        date(2024, 1, 15),   # Mid-year date
        date(2024, 9, 29),   # Last day of FY2024
    ]

    for test_date in test_dates:
        try:
            info = get_fiscal_info(test_date)
            print(f"{test_date.strftime('%Y-%m-%d (%A)')}: "
                  f"FY{info['fiscal_year']} Week {info['fiscal_week']}")
        except ValueError as e:
            print(f"{test_date.strftime('%Y-%m-%d (%A)')}: {e}")

    print("\n" + "=" * 60)
    print("Configuration loaded successfully!")
    print("=" * 60)
