"""
Test script to demonstrate CSV import pipeline.

This script:
1. Creates a sample NatWest CSV file
2. Imports it into SQLite database
3. Queries the database to verify data
4. Shows statistics
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.data.database import FinanceDatabase
from src.data.importer import TransactionImporter
from src.data.csv_parser import NatWestParser


def create_sample_csv(file_path: Path) -> None:
    """Create a sample NatWest CSV file for testing."""
    sample_data = """Date\tType\tDescription\tValue\tBalance\tAccount Name\tAccount Number
10-Jan-25\tPOS\tTESCO STORES 1234\t-45.67\t1954.33\tALIKHAN A\t757575-12344567
10-Jan-25\tPOS\tSTARBUCKS LONDON\t-4.50\t1949.83\tALIKHAN A\t757575-12344567
11-Jan-25\tDPC\tBRITISH GAS\t-120.00\t1829.83\tALIKHAN A\t757575-12344567
11-Jan-25\tBAC\tSALARY PAYMENT\t3000.00\t4829.83\tALIKHAN A\t757575-12344567
12-Jan-25\tPOS\tAMAZON.CO.UK\t-89.99\t4739.84\tALIKHAN A\t757575-12344567
12-Jan-25\tPOS\tUBER TRIP\t-12.50\t4727.34\tALIKHAN A\t757575-12344567
13-Jan-25\tPOS\tSAINSBURYS 5678\t-67.89\t4659.45\tALIKHAN A\t757575-12344567
13-Jan-25\tDPC\tBT GROUP PLC\t-45.00\t4614.45\tALIKHAN A\t757575-12344567
14-Jan-25\tPOS\tNETFLIX.COM\t-15.99\t4598.46\tALIKHAN A\t757575-12344567
15-Jan-25\tBAC\tREFUND AMAZON\t89.99\t4688.45\tALIKHAN A\t757575-12344567
"""

    file_path.write_text(sample_data)
    print(f"✓ Created sample CSV: {file_path}")


def main():
    """Run the import test."""

    print("=" * 70)
    print("PERSONAL FINANCE - CSV IMPORT TEST")
    print("=" * 70)
    print()

    # Setup
    test_dir = Path(__file__).parent / "test_data"
    test_dir.mkdir(exist_ok=True)

    csv_file = test_dir / "natwest_sample.csv"
    db_file = test_dir / "test_finance.db"

    # Clean up old test database
    if db_file.exists():
        db_file.unlink()
        print(f"✓ Cleaned up old database: {db_file}")

    # Step 1: Create sample CSV
    print("\n[1] Creating sample NatWest CSV file...")
    create_sample_csv(csv_file)

    # Step 2: Parse CSV
    print("\n[2] Parsing CSV file...")
    transactions = NatWestParser.parse_file(csv_file)
    print(f"✓ Parsed {len(transactions)} transactions")

    # Show first transaction
    if transactions:
        print("\nFirst transaction:")
        txn = transactions[0]
        print(f"  Date: {txn.date}")
        print(f"  Description: {txn.description}")
        print(f"  Amount: £{txn.amount}")
        print(f"  Balance: £{txn.balance}")
        print(f"  Account: {txn.account_name} ({txn.account_number})")
        print(f"  Type: {txn.transaction_type}")

    # Step 3: Import to database
    print("\n[3] Importing to SQLite database...")
    db = FinanceDatabase(db_file)
    importer = TransactionImporter(db)

    result = importer.import_natwest_csv(csv_file)
    print(f"✓ Import complete:")
    print(f"  Total parsed: {result['total_parsed']}")
    print(f"  Total inserted: {result['total_inserted']}")
    print(f"  Duplicates skipped: {result['duplicates_skipped']}")

    # Step 4: Query database
    print("\n[4] Querying database...")
    all_transactions = db.get_transactions()
    print(f"✓ Found {len(all_transactions)} transactions in database")

    # Show summary
    print("\n[5] Transaction Summary:")
    total_debit = sum(txn.amount for txn in all_transactions if txn.amount < 0)
    total_credit = sum(txn.amount for txn in all_transactions if txn.amount > 0)
    print(f"  Total Debits (spent): £{abs(total_debit):.2f}")
    print(f"  Total Credits (received): £{total_credit:.2f}")
    print(f"  Net: £{(total_credit + total_debit):.2f}")

    # Show statistics
    print("\n[6] Database Statistics:")
    stats = db.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Step 5: Test re-import (should skip duplicates)
    print("\n[7] Testing duplicate detection...")
    result2 = importer.import_natwest_csv(csv_file)
    print(f"✓ Re-import complete:")
    print(f"  Total parsed: {result2['total_parsed']}")
    print(f"  Total inserted: {result2['total_inserted']}")
    print(f"  Duplicates skipped: {result2['duplicates_skipped']}")

    print("\n" + "=" * 70)
    print("TEST COMPLETE!")
    print("=" * 70)
    print(f"\n✓ Database created at: {db_file}")
    print(f"✓ Sample CSV at: {csv_file}")
    print("\nYou can now use this database for further testing!")


if __name__ == "__main__":
    main()
