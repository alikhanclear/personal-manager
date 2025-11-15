"""
CSV parser for NatWest bank statements.
"""
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import List

import polars as pl

from .models import Transaction


class NatWestParser:
    """Parser for NatWest bank CSV/TSV files."""

    # NatWest date format: "10-Jan-25"
    DATE_FORMAT = "%d-%b-%y"

    # Expected columns in NatWest export
    EXPECTED_COLUMNS = [
        "Date",
        "Type",
        "Description",
        "Value",
        "Balance",
        "Account Name",
        "Account Number",
    ]

    @classmethod
    def parse_file(cls, file_path: str | Path) -> List[Transaction]:
        """
        Parse NatWest CSV/TSV file into Transaction objects.

        Args:
            file_path: Path to CSV/TSV file

        Returns:
            List of Transaction objects

        Raises:
            ValueError: If file format is invalid
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Try reading with auto-detected separator (comma or tab)
        df = None
        last_error = None

        # Try comma-separated first (more common)
        for separator in [",", "\t"]:
            try:
                df = pl.read_csv(
                    file_path,
                    separator=separator,
                    has_header=True,
                    infer_schema_length=1000,
                )
                # Check if we got the expected columns
                if set(cls.EXPECTED_COLUMNS).issubset(set(df.columns)):
                    break  # Success!
                else:
                    df = None  # Wrong separator, try next
            except Exception as e:
                last_error = e
                continue

        if df is None:
            raise ValueError(
                f"Failed to parse CSV/TSV file. Tried both comma and tab separators. "
                f"Last error: {last_error}"
            )

        # Validate columns
        cls._validate_columns(df.columns)

        # Convert to transactions
        transactions = []
        for row in df.iter_rows(named=True):
            try:
                transaction = cls._parse_row(row)
                transactions.append(transaction)
            except Exception as e:
                # Log but don't fail on individual row errors
                print(f"Warning: Failed to parse row: {row}. Error: {e}")
                continue

        return transactions

    @classmethod
    def _validate_columns(cls, columns: List[str]) -> None:
        """Validate that CSV has expected columns."""
        missing = set(cls.EXPECTED_COLUMNS) - set(columns)
        if missing:
            raise ValueError(
                f"Missing required columns: {missing}. "
                f"Expected: {cls.EXPECTED_COLUMNS}. "
                f"Found: {columns}"
            )

    @classmethod
    def _parse_row(cls, row: dict) -> Transaction:
        """Parse a single CSV row into Transaction object."""

        # Parse date: "10-Jan-25" -> date object
        date_str = row["Date"]
        parsed_date = datetime.strptime(date_str, cls.DATE_FORMAT).date()

        # Parse amount (Value column)
        # Negative = debit (money out), Positive = credit (money in)
        amount = Decimal(str(row["Value"]))

        # Parse balance (optional, may be None)
        balance = None
        if row.get("Balance") is not None and row["Balance"] != "":
            balance = Decimal(str(row["Balance"]))

        # Clean account number (remove any formatting)
        account_number = str(row["Account Number"]).replace("-", "").strip()

        return Transaction(
            date=parsed_date,
            description=str(row["Description"]).strip(),
            amount=amount,
            balance=balance,
            account_name=str(row["Account Name"]).strip(),
            account_number=account_number,
            transaction_type=str(row["Type"]).strip(),
        )

    @classmethod
    def parse_multiple_files(cls, file_paths: List[str | Path]) -> List[Transaction]:
        """
        Parse multiple CSV files and combine into single transaction list.

        Useful for importing multiple accounts or multiple statement periods.

        Args:
            file_paths: List of file paths to parse

        Returns:
            Combined list of transactions from all files
        """
        all_transactions = []

        for file_path in file_paths:
            try:
                transactions = cls.parse_file(file_path)
                all_transactions.extend(transactions)
                print(f"✓ Parsed {len(transactions)} transactions from {file_path}")
            except Exception as e:
                print(f"✗ Failed to parse {file_path}: {e}")
                continue

        return all_transactions


# Convenience function for quick parsing
def parse_natwest_csv(file_path: str | Path) -> List[Transaction]:
    """
    Quick helper to parse a NatWest CSV file.

    Args:
        file_path: Path to CSV/TSV file

    Returns:
        List of Transaction objects
    """
    return NatWestParser.parse_file(file_path)
