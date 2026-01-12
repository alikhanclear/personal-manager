"""Check what duplicates exist in the database."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.database import FinanceDatabase

db = FinanceDatabase('data/finance.db')

# Get all duplicates
duplicates = db.get_potential_duplicates()

print(f"\n{'='*80}")
print(f"DUPLICATE ANALYSIS")
print(f"{'='*80}")
print(f"\nTotal duplicates: {len(duplicates)}")

if duplicates:
    print(f"\nFirst 10 duplicates:")
    print(f"{'-'*80}")
    for i, dup in enumerate(duplicates[:10], 1):
        print(f"\n{i}. Date: {dup.date}")
        print(f"   Description: {dup.description[:60]}")
        print(f"   Amount: £{dup.amount:.2f}")
        print(f"   Account: {dup.account_name}")
        print(f"   Detected: {dup.detected_at}")
        print(f"   Transaction ID: {dup.transaction_id}")

    # Check if these transaction IDs actually exist in transactions table
    print(f"\n{'-'*80}")
    print(f"Checking if corresponding transactions exist...")
    print(f"{'-'*80}")

    for i, dup in enumerate(duplicates[:5], 1):
        txn = db.get_transaction(dup.transaction_id)
        if txn:
            print(f"{i}. Transaction {dup.transaction_id[:8]}... EXISTS in database")
        else:
            print(f"{i}. Transaction {dup.transaction_id[:8]}... NOT FOUND in database")

print(f"\n{'='*80}")
