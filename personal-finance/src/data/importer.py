"""
CSV import pipeline for loading bank statements into database.
"""
from pathlib import Path
from typing import List

from .csv_parser import NatWestParser
from .database import FinanceDatabase
from .models import Transaction


class TransactionImporter:
    """Handles importing transactions from CSV files to database."""

    def __init__(self, database: FinanceDatabase):
        """
        Initialize importer with database connection.

        Args:
            database: FinanceDatabase instance
        """
        self.database = database

    def import_natwest_csv(
        self,
        file_path: str | Path,
        skip_duplicates: bool = True
    ) -> dict:
        """
        Import NatWest CSV file into database.

        Args:
            file_path: Path to CSV/TSV file
            skip_duplicates: If True, skip transactions with duplicate IDs

        Returns:
            Dictionary with import statistics
        """
        # Parse CSV file
        transactions = NatWestParser.parse_file(file_path)

        # Insert into database
        if skip_duplicates:
            inserted = self.database.insert_transactions_bulk(transactions)
        else:
            inserted = 0
            for txn in transactions:
                try:
                    self.database.insert_transaction(txn)
                    inserted += 1
                except Exception as e:
                    print(f"Failed to insert transaction {txn.id}: {e}")

        return {
            "file": str(file_path),
            "total_parsed": len(transactions),
            "total_inserted": inserted,
            "duplicates_skipped": len(transactions) - inserted,
        }

    def import_multiple_files(
        self,
        file_paths: List[str | Path],
        skip_duplicates: bool = True
    ) -> dict:
        """
        Import multiple CSV files into database.

        Args:
            file_paths: List of file paths to import
            skip_duplicates: If True, skip duplicate transactions

        Returns:
            Dictionary with aggregate import statistics
        """
        results = []
        total_parsed = 0
        total_inserted = 0

        for file_path in file_paths:
            try:
                result = self.import_natwest_csv(file_path, skip_duplicates)
                results.append(result)
                total_parsed += result["total_parsed"]
                total_inserted += result["total_inserted"]
            except Exception as e:
                print(f"Failed to import {file_path}: {e}")
                continue

        return {
            "files_processed": len(results),
            "total_parsed": total_parsed,
            "total_inserted": total_inserted,
            "duplicates_skipped": total_parsed - total_inserted,
            "details": results,
        }


def quick_import(file_path: str | Path, db_path: str = "finance.db") -> dict:
    """
    Quick helper to import a single CSV file.

    Args:
        file_path: Path to CSV/TSV file
        db_path: Path to SQLite database

    Returns:
        Import statistics
    """
    db = FinanceDatabase(db_path)
    importer = TransactionImporter(db)
    return importer.import_natwest_csv(file_path)
