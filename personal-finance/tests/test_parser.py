"""
Unit tests for parser.py

Tests the NatWest CSV parsing logic.
"""

import pytest
from io import StringIO
from datetime import datetime
from src.data.parser import parse_natwest_csv, Transaction


@pytest.mark.unit
class TestNatWestParser:
    """Test suite for NatWest CSV parser."""

    def test_parse_comma_delimited(self, sample_csv_content):
        """Test parsing comma-delimited CSV."""
        result = parse_natwest_csv(StringIO(sample_csv_content))

        assert len(result) == 3
        assert isinstance(result[0], Transaction)

    def test_parse_semicolon_delimited(self):
        """Test parsing semicolon-delimited CSV."""
        csv_content = """Date;Description;Amount;Balance;Account Number
01/01/2025;TESCO STORES;-45.67;1000.00;12345678
"""
        result = parse_natwest_csv(StringIO(csv_content))

        assert len(result) == 1
        assert result[0].description == "TESCO STORES"

    def test_transaction_fields(self, sample_csv_content):
        """Test that all transaction fields are parsed correctly."""
        result = parse_natwest_csv(StringIO(sample_csv_content))
        txn = result[0]

        assert isinstance(txn.date, datetime)
        assert txn.description == "TESCO STORES 1234"
        assert txn.amount == -45.67
        assert txn.balance == 1000.00
        assert txn.account_number == "12345678"

    def test_deterministic_transaction_id(self, sample_csv_content):
        """Test that transaction IDs are deterministic (same input = same ID)."""
        result1 = parse_natwest_csv(StringIO(sample_csv_content))
        result2 = parse_natwest_csv(StringIO(sample_csv_content))

        # Same transaction should have same ID
        assert result1[0].id == result2[0].id

    def test_different_transactions_different_ids(self):
        """Test that different transactions have different IDs."""
        csv1 = """Date,Description,Amount,Balance,Account Number
01/01/2025,TESCO STORES,-45.67,1000.00,12345678
"""
        csv2 = """Date,Description,Amount,Balance,Account Number
02/01/2025,AMAZON PRIME,-8.99,991.01,12345678
"""

        result1 = parse_natwest_csv(StringIO(csv1))
        result2 = parse_natwest_csv(StringIO(csv2))

        assert result1[0].id != result2[0].id

    def test_empty_csv(self):
        """Test parsing empty CSV."""
        csv_content = """Date,Description,Amount,Balance,Account Number
"""
        result = parse_natwest_csv(StringIO(csv_content))
        assert len(result) == 0

    def test_date_formats(self):
        """Test different date formats."""
        test_cases = [
            ("01/01/2025", datetime(2025, 1, 1)),
            ("31/12/2024", datetime(2024, 12, 31)),
            ("15/06/2025", datetime(2025, 6, 15)),
        ]

        for date_str, expected_date in test_cases:
            csv_content = f"""Date,Description,Amount,Balance,Account Number
{date_str},TEST TRANSACTION,-10.00,100.00,12345678
"""
            result = parse_natwest_csv(StringIO(csv_content))
            assert result[0].date.date() == expected_date.date()

    def test_positive_and_negative_amounts(self):
        """Test parsing positive (credits) and negative (debits) amounts."""
        csv_content = """Date,Description,Amount,Balance,Account Number
01/01/2025,EXPENSE,-50.00,950.00,12345678
02/01/2025,INCOME,100.00,1050.00,12345678
"""
        result = parse_natwest_csv(StringIO(csv_content))

        assert result[0].amount == -50.00  # Expense
        assert result[1].amount == 100.00  # Income

    def test_decimal_precision(self):
        """Test that decimal amounts are parsed with correct precision."""
        csv_content = """Date,Description,Amount,Balance,Account Number
01/01/2025,TESCO,-45.67,1000.33,12345678
"""
        result = parse_natwest_csv(StringIO(csv_content))

        assert result[0].amount == -45.67
        assert result[0].balance == 1000.33

    @pytest.mark.parametrize("invalid_csv", [
        "",  # Completely empty
        "Invalid CSV",  # No headers
        "Date,Description\n01/01/2025,TEST",  # Missing columns
    ])
    def test_invalid_csv_formats(self, invalid_csv):
        """Test handling of invalid CSV formats."""
        with pytest.raises(Exception):  # Should raise parsing error
            parse_natwest_csv(StringIO(invalid_csv))
