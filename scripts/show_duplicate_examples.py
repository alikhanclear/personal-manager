"""Show concrete examples of transactions and their duplicates."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.database import FinanceDatabase
from collections import defaultdict

db = FinanceDatabase('data/finance.db')

print("\n" + "="*80)
print("DUPLICATE INVESTIGATION")
print("="*80)

# Get all duplicates
duplicates = db.get_potential_duplicates()
print(f"\nTotal duplicates flagged: {len(duplicates)}")

# Group duplicates by transaction ID
dup_by_id = defaultdict(list)
for dup in duplicates:
    dup_by_id[dup.transaction_id].append(dup)

print(f"Unique transaction IDs: {len(dup_by_id)}")

# Show detection timestamps
if duplicates:
    print(f"\nWhen were these detected?")
    print(f"-" * 80)
    for dup in sorted(duplicates, key=lambda d: d.detected_at)[:5]:
        print(f"  {dup.detected_at} - {dup.description[:50]}")

# Find transaction IDs with multiple duplicate entries
multi_dups = {tid: dups for tid, dups in dup_by_id.items() if len(dups) > 1}

if multi_dups:
    print(f"\n[ALERT] Transaction IDs with MULTIPLE duplicate entries: {len(multi_dups)}")
    for tid, dups in multi_dups.items():
        print(f"  - {tid[:12]}... has {len(dups)} duplicate entries")

# Show detailed examples
print(f"\n" + "="*80)
print("DETAILED EXAMPLES (First 3 cases)")
print("="*80)

for i, (txn_id, dups) in enumerate(list(dup_by_id.items())[:3], 1):
    print(f"\n--- Example {i} ---")

    # Get the actual transaction from main table
    txn = db.get_transaction(txn_id)

    if txn:
        print(f"\nACTUAL TRANSACTION (in transactions table):")
        print(f"  ID: {txn.id}")
        print(f"  Date: {txn.date}")
        print(f"  Description: {txn.description}")
        print(f"  Amount: {txn.amount}")
        print(f"  Balance: {txn.balance}")
        print(f"  Account: {txn.account_name}")
        print(f"  Created: {txn.created_at if hasattr(txn, 'created_at') else 'N/A'}")
    else:
        print(f"\n[ERROR] Transaction {txn_id} NOT FOUND in transactions table!")
        print(f"This means the duplicate was flagged, but the original is missing.")

    print(f"\nDUPLICATE ENTRIES (in potential_duplicates table): {len(dups)}")
    for j, dup in enumerate(dups, 1):
        print(f"\n  Duplicate #{j}:")
        print(f"    Date: {dup.date}")
        print(f"    Description: {dup.description}")
        print(f"    Amount: {dup.amount}")
        print(f"    Balance: {dup.balance}")
        print(f"    Account: {dup.account_name}")
        print(f"    Detected at: {dup.detected_at}")

        # Compare with actual transaction
        if txn:
            if (dup.date == txn.date and
                dup.description == txn.description and
                float(dup.amount) == float(txn.amount)):
                print(f"    [MATCH] This IS an exact duplicate of the transaction")
            else:
                print(f"    [MISMATCH] This does NOT match the transaction!")

print("\n" + "="*80)
