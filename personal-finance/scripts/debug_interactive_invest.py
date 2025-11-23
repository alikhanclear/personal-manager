"""Debug script to check Interactive Investments rule matching."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.database import FinanceDatabase

DB_PATH = Path(__file__).parent.parent / "data" / "finance.db"

def main():
    db = FinanceDatabase(DB_PATH)

    print("=" * 80)
    print("INTERACTIVE INVESTMENTS DEBUG")
    print("=" * 80)

    # 1. Find all transactions with "Interactive" in description
    all_txns = db.get_transactions()
    interactive_txns = [t for t in all_txns if "INTERACTIVE" in t.description.upper()]

    print(f"\nFound {len(interactive_txns)} transactions with 'INTERACTIVE' in description:\n")

    for txn in interactive_txns[:10]:  # Show first 10
        print(f"ID: {txn.id[:8]}...")
        print(f"  Description: {txn.description}")
        print(f"  Category: {txn.category}")
        print(f"  Confidence: {txn.category_confidence}")
        print(f"  Confirmed: {txn.category_confirmed}")
        print()

    # 2. Find all rules with "Interactive" pattern
    all_rules = db.get_rules()
    interactive_rules = [r for r in all_rules if "INTERACTIVE" in r.pattern.upper()]

    print(f"\nFound {len(interactive_rules)} rules with 'INTERACTIVE' in pattern:\n")

    # Get category names
    categories = db.get_categories()
    cat_map = {c.id: c.name for c in categories}

    for rule in interactive_rules:
        print(f"Pattern: {rule.pattern}")
        print(f"  Category ID: {rule.category_id}")
        print(f"  Category Name: {cat_map.get(rule.category_id, 'UNKNOWN')}")
        print(f"  Priority: {rule.priority}")
        print()

    # 3. Test pattern matching
    if interactive_rules and interactive_txns:
        print("\n" + "=" * 80)
        print("PATTERN MATCHING TEST")
        print("=" * 80)

        rule = interactive_rules[0]
        txn = interactive_txns[0]

        print(f"\nRule pattern: '{rule.pattern}'")
        print(f"Transaction description: '{txn.description}'")
        print(f"\nPattern uppercase: '{rule.pattern.upper()}'")
        print(f"Description uppercase: '{txn.description.upper()}'")

        # Test substring match
        if rule.pattern.upper() in txn.description.upper():
            print("\n✓ MATCH: Pattern is substring of description")
        else:
            print("\n✗ NO MATCH: Pattern is NOT substring of description")

if __name__ == "__main__":
    main()
