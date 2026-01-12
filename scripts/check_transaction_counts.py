"""Check transaction and duplicate counts."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.database import FinanceDatabase

db = FinanceDatabase('data/finance.db')

# Get statistics
stats = db.get_statistics()

print(f"\n{'='*80}")
print(f"DATABASE STATUS")
print(f"{'='*80}")
print(f"\nTransactions in database: {stats['total_transactions']}")
print(f"Potential duplicates flagged: {len(db.get_potential_duplicates())}")

# Get all duplicates and check for patterns
duplicates = db.get_potential_duplicates()

if duplicates:
    # Count how many unique transaction IDs
    unique_ids = set(d.transaction_id for d in duplicates)
    print(f"\nUnique transaction IDs in duplicates: {len(unique_ids)}")
    print(f"Total duplicate records: {len(duplicates)}")

    if len(duplicates) > len(unique_ids):
        print(f"\n⚠️ ISSUE DETECTED:")
        print(f"Some transaction IDs appear multiple times in duplicates table!")
        print(f"This suggests your CSV file has internal duplicates.")

        # Find which IDs appear multiple times
        from collections import Counter
        id_counts = Counter(d.transaction_id for d in duplicates)
        multi_ids = {id: count for id, count in id_counts.items() if count > 1}

        if multi_ids:
            print(f"\nTransaction IDs appearing multiple times:")
            for txn_id, count in multi_ids.items():
                # Find the duplicate
                dup_examples = [d for d in duplicates if d.transaction_id == txn_id]
                if dup_examples:
                    d = dup_examples[0]
                    print(f"  - {txn_id[:12]}... appears {count}x: {d.description[:50]}")

print(f"\n{'='*80}")
