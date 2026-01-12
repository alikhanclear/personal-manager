#!/usr/bin/env python3
"""
Test CSV upload process (mimics what the app does).
"""
import sys
from pathlib import Path
from src.data.database import FinanceDatabase
from src.data.csv_parser import NatWestParser
from src.data.importer import TransactionImporter

if len(sys.argv) < 2:
    print("Usage: python test_upload.py <path_to_csv_file>")
    print("\nExample: python test_upload.py ~/Downloads/transactions.csv")
    sys.exit(1)

csv_file = Path(sys.argv[1])

if not csv_file.exists():
    print(f"❌ File not found: {csv_file}")
    sys.exit(1)

print("=" * 80)
print("TESTING CSV UPLOAD")
print("=" * 80)

DB_PATH = Path("data/finance.db")
db = FinanceDatabase(DB_PATH)

print(f"\n1. DATABASE STATE (BEFORE):")
transactions_before = db.get_transactions()
print(f"   Transactions: {len(transactions_before)}")

print(f"\n2. PARSING CSV:")
print(f"   File: {csv_file}")
print(f"   Size: {csv_file.stat().st_size:,} bytes")

try:
    parser = NatWestParser()
    transactions = parser.parse_file(csv_file)
    print(f"   ✓ Parsed: {len(transactions)} transactions")

    # Show first transaction
    if transactions:
        t = transactions[0]
        print(f"\n   Sample transaction:")
        print(f"   - Date: {t.date}")
        print(f"   - Description: {t.description}")
        print(f"   - Amount: £{t.amount}")
        print(f"   - Account: {t.account_name}")

except Exception as e:
    print(f"   ❌ Parse error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print(f"\n3. IMPORTING TO DATABASE:")
try:
    importer = TransactionImporter(db)
    inserted = db.insert_transactions_bulk(transactions)
    print(f"   ✓ Inserted: {inserted} transactions")
except Exception as e:
    print(f"   ❌ Import error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print(f"\n4. DATABASE STATE (AFTER):")
transactions_after = db.get_transactions()
print(f"   Transactions: {len(transactions_after)}")

# Get stats
uncategorized = [t for t in transactions_after if not t.category or t.category == "Uncategorized"]
print(f"   Uncategorized: {len(uncategorized)}")

print("\n" + "=" * 80)
print("✓ UPLOAD TEST COMPLETE!")
print("=" * 80)
print(f"\nNext steps:")
print(f"1. Run: python debug_database.py  (to verify data)")
print(f"2. Run: python app.py  (to start the app)")
print(f"3. Go to Review tab and check if transactions appear")
