"""
Debug script to investigate Netflix transaction categorization issue.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.database import FinanceDatabase

DB_PATH = Path(__file__).parent.parent / "data" / "finance.db"

def main():
    print("=" * 80)
    print("Netflix Transaction Debug")
    print("=" * 80)

    db = FinanceDatabase(DB_PATH)

    # Get all transactions
    all_txns = db.get_transactions()

    # Filter Netflix transactions
    netflix_txns = [t for t in all_txns if 'netflix' in t.description.lower()]

    print(f"\nFound {len(netflix_txns)} Netflix transactions:\n")

    for i, txn in enumerate(netflix_txns, 1):
        print(f"{i}. Transaction ID: {txn.id}")
        print(f"   Date: {txn.date}")
        print(f"   Description: {txn.description}")
        print(f"   Amount: £{txn.amount}")
        print(f"   Category: {txn.category}")
        print(f"   Confidence: {txn.category_confidence}")
        print(f"   Confirmed: {txn.category_confirmed}")
        print()

    # Check for PAYPAL rules
    print("=" * 80)
    print("Checking for PAYPAL and NETFLIX rules:")
    print("=" * 80)

    rules = db.get_rules()

    paypal_rules = [r for r in rules if 'paypal' in r.pattern.lower()]
    netflix_rules = [r for r in rules if 'netflix' in r.pattern.lower()]

    print(f"\nPAYPAL rules ({len(paypal_rules)}):")
    for rule in paypal_rules:
        print(f"  - Pattern: '{rule.pattern}' -> Category: {rule.category_id}, Priority: {rule.priority}")

    print(f"\nNETFLIX rules ({len(netflix_rules)}):")
    for rule in netflix_rules:
        print(f"  - Pattern: '{rule.pattern}' -> Category: {rule.category_id}, Priority: {rule.priority}")

    # Check what categories exist
    print("\n" + "=" * 80)
    print("Checking category IDs:")
    print("=" * 80)

    categories = db.get_categories()
    cat_lookup = {cat.id: cat.name for cat in categories}

    print("\nRelevant categories:")
    for cat_id, cat_name in cat_lookup.items():
        if 'streaming' in cat_name.lower() or 'transport' in cat_name.lower():
            print(f"  {cat_name}: {cat_id}")

    # Now translate rule category_ids to names
    if paypal_rules:
        print("\n" + "=" * 80)
        print("PAYPAL rules with category names:")
        print("=" * 80)
        for rule in paypal_rules:
            cat_name = cat_lookup.get(rule.category_id, "UNKNOWN")
            print(f"  Pattern: '{rule.pattern}' -> {cat_name} (Priority: {rule.priority})")

    if netflix_rules:
        print("\n" + "=" * 80)
        print("NETFLIX rules with category names:")
        print("=" * 80)
        for rule in netflix_rules:
            cat_name = cat_lookup.get(rule.category_id, "UNKNOWN")
            print(f"  Pattern: '{rule.pattern}' -> {cat_name} (Priority: {rule.priority})")

if __name__ == '__main__':
    main()
