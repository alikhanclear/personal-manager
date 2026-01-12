"""Debug script to check Yahya Ali Khan rule and matching."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.database import FinanceDatabase
from src.core.rule_engine import RuleEngine

db = FinanceDatabase(Path(__file__).parent.parent / "data" / "finance.db")

print("=" * 60)
print("Checking Yahya Ali Khan Rule")
print("=" * 60)

# Get all rules
rules = db.get_rules()
print(f"\nTotal rules in database: {len(rules)}")

# Find Yahya-related rules
yahya_rules = [r for r in rules if 'yahya' in r.pattern.lower() or 'ali khan' in r.pattern.lower()]

print(f"\nRules matching 'yahya' or 'ali khan': {len(yahya_rules)}")
print("-" * 60)

if not yahya_rules:
    print("NO YAHYA ALI KHAN RULES FOUND!")
    print("\nSearching for 'kids' category rules...")

    # Get categories
    categories = db.get_categories()
    cat_map = {c.id: c.name for c in categories}

    kids_cat = [c for c in categories if c.name.lower() == 'kids']
    if kids_cat:
        kids_id = kids_cat[0].id
        print(f"Kids category ID: {kids_id}")

        kids_rules = [r for r in rules if r.category_id == kids_id]
        print(f"\nAll rules for 'Kids' category: {len(kids_rules)}")
        for r in kids_rules:
            print(f"  Pattern: '{r.pattern}' | Priority: {r.priority}")
    else:
        print("Kids category not found!")
else:
    # Get categories
    categories = db.get_categories()
    cat_map = {c.id: c.name for c in categories}

    for rule in yahya_rules:
        category_name = cat_map.get(rule.category_id, "UNKNOWN")
        print(f"\nPattern: '{rule.pattern}'")
        print(f"Category: {category_name}")
        print(f"Priority: {rule.priority}")

# Check actual transactions
print("\n" + "=" * 60)
print("Checking Transactions")
print("=" * 60)

transactions = db.get_transactions()
yahya_txns = [t for t in transactions if 'yahya' in t.description.lower() or 'ali khan' in t.description.lower()]

print(f"\nTransactions matching 'yahya' or 'ali khan': {len(yahya_txns)}")
print("-" * 60)

if yahya_txns:
    for t in yahya_txns[:10]:  # Show first 10
        print(f"\nDescription: '{t.description}'")
        print(f"Amount: £{t.amount:.2f}")
        print(f"Date: {t.date}")
        print(f"Current Category: {t.category or 'NONE'}")
        print(f"Confidence: {t.category_confidence}")
else:
    print("NO TRANSACTIONS FOUND with 'yahya' or 'ali khan' in description")

    # Show some sample transaction descriptions
    print("\nSample transaction descriptions (first 10):")
    for t in transactions[:10]:
        print(f"  '{t.description}'")

# Test rule matching
if yahya_rules and yahya_txns:
    print("\n" + "=" * 60)
    print("Testing Rule Matching")
    print("=" * 60)

    rule_engine = RuleEngine(db)

    for txn in yahya_txns[:5]:  # Test first 5 transactions
        print(f"\nTesting: '{txn.description}'")

        for rule in yahya_rules:
            # CORRECT parameter order: description, pattern
            matched = rule_engine._matches_pattern(txn.description, rule.pattern)
            print(f"  Pattern '{rule.pattern}': {matched}")

            if matched:
                print(f"  -> Should categorize as: {cat_map.get(rule.category_id, 'UNKNOWN')}")
