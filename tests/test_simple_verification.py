"""
Simple verification tests to ensure pytest is working correctly.

These tests verify basic Python functionality and pytest setup.
No external dependencies or complex setup required.
"""

import pytest
from datetime import datetime
from decimal import Decimal


@pytest.mark.unit
class TestPytestSetup:
    """Verify pytest is working correctly."""

    def test_basic_assertion(self):
        """Test that basic assertions work."""
        assert 1 + 1 == 2

    def test_string_operations(self):
        """Test string operations."""
        text = "TESCO STORES"
        assert "TESCO" in text
        assert text.upper() == "TESCO STORES"

    def test_list_operations(self):
        """Test list operations."""
        items = [1, 2, 3, 4, 5]
        assert len(items) == 5
        assert 3 in items
        assert sum(items) == 15

    def test_decimal_precision(self):
        """Test decimal arithmetic (important for finance)."""
        amount = Decimal("10.50")
        tax = Decimal("1.05")
        total = amount + tax
        assert total == Decimal("11.55")

    def test_datetime_operations(self):
        """Test datetime handling."""
        date = datetime(2025, 1, 15)
        assert date.year == 2025
        assert date.month == 1
        assert date.day == 15


@pytest.mark.unit
class TestImports:
    """Verify we can import our modules."""

    def test_import_models(self):
        """Test importing data models."""
        from src.data.models import Transaction, Category, Rule
        # If this doesn't raise ImportError, imports work
        assert Transaction is not None
        assert Category is not None
        assert Rule is not None

    def test_import_rule_engine(self):
        """Test importing rule engine."""
        from src.core.rule_engine import RuleEngine
        assert RuleEngine is not None

    def test_import_parser(self):
        """Test importing CSV parser."""
        from src.data.csv_parser import NatWestParser
        assert NatWestParser is not None

    def test_import_database(self):
        """Test importing database manager."""
        from src.data.database import FinanceDatabase
        assert FinanceDatabase is not None


@pytest.mark.unit
@pytest.mark.parametrize("input,expected", [
    (100, 100),
    (0, 0),
    (-50, -50),
    (99.99, 99.99),
])
def test_parameterized_example(input, expected):
    """Example of parameterized test."""
    result = input
    assert result == expected


@pytest.mark.unit
class TestFixtures:
    """Test that pytest fixtures are available."""

    def test_clean_db_fixture(self, clean_db):
        """Test that clean_db fixture works."""
        # clean_db should be a string path
        assert isinstance(clean_db, str)
        assert "test_finance.db" in clean_db

    def test_sample_categories_fixture(self, clean_db, sample_categories):
        """Test that sample_categories fixture works."""
        # sample_categories should be a list of dicts
        assert isinstance(sample_categories, list)
        assert len(sample_categories) == 5

        # Check first category has expected structure
        first_cat = sample_categories[0]
        assert "id" in first_cat
        assert "name" in first_cat
        assert "description" in first_cat

    def test_sample_transactions_fixture(self, clean_db, sample_transactions):
        """Test that sample_transactions fixture works."""
        assert isinstance(sample_transactions, list)
        assert len(sample_transactions) == 3

        # Check first transaction structure
        first_txn = sample_transactions[0]
        assert "id" in first_txn
        assert "description" in first_txn
        assert "amount" in first_txn


@pytest.mark.unit
def test_exception_handling():
    """Test that pytest can catch exceptions."""
    with pytest.raises(ValueError):
        raise ValueError("Expected error")


@pytest.mark.unit
def test_approximate_comparison():
    """Test approximate float comparison."""
    result = 0.1 + 0.2
    expected = 0.3
    assert result == pytest.approx(expected)


# Summary function
def pytest_report_header(config):
    """Add custom header to pytest output."""
    return "Personal Manager - Test Suite Verification"
