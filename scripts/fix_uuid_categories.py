"""
Fix transactions that have UUIDs in category field instead of names.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.database import FinanceDatabase

DB_PATH = Path(__file__).parent.parent / "data" / "finance.db"


def main():
    db = FinanceDatabase(DB_PATH)

    print("=== FIXING UUID CATEGORIES ===\n")

    # Get all transactions and categories
    txns = db.get_transactions()
    categories = db.get_categories()

    # Create UUID -> Name mapping
    uuid_to_name = {cat.id: cat.name for cat in categories}

    # Find transactions with UUIDs
    fixed_count = 0
    uuid_transactions = []

    for txn in txns:
        if txn.category and len(txn.category) > 30 and '-' in txn.category:
            # Likely a UUID
            if txn.category in uuid_to_name:
                uuid_transactions.append((txn, uuid_to_name[txn.category]))

    print(f"Found {len(uuid_transactions)} transactions with UUID categories\n")

    if len(uuid_transactions) == 0:
        print("[OK] No UUID categories found. Database is clean!")
        return

    # Fix them
    for txn, category_name in uuid_transactions:
        try:
            db.update_transaction_category(
                transaction_id=txn.id,
                category=category_name,
                confirmed=txn.category_confirmed,
                confidence=txn.category_confidence
            )
            fixed_count += 1
            if fixed_count % 100 == 0:
                print(f"  Fixed {fixed_count}/{len(uuid_transactions)}...")
        except Exception as e:
            print(f"[ERROR] Failed to fix {txn.id}: {e}")

    print(f"\n[SUCCESS] Fixed {fixed_count} transactions")
    print("Categories are now displayed as NAMES instead of UUIDs")


if __name__ == "__main__":
    main()
