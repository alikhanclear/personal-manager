"""
Debug CLEARTHREAD matching with LIVE rule engine test.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.database import FinanceDatabase
from src.core.rule_engine import RuleEngine
from src.data.models import Transaction
from datetime import datetime

# Initialize
db = FinanceDatabase("data/finance.db")
rule_engine = RuleEngine(db)

print("=" * 80)
print("LIVE RULE ENGINE TEST")
print("=" * 80)

# Get a real CLEARTHREAD transaction
all_transactions = db.get_transactions()
clearthread_txn = next((t for t in all_transactions if 'CLEARTHREAD STARLI' in t.description.upper()), None)

if not clearthread_txn:
    print("\nERROR: No CLEARTHREAD transaction found!")
    sys.exit(1)

print(f"\nTest Transaction:")
print(f"  ID: {clearthread_txn.id}")
print(f"  Description: '{clearthread_txn.description}'")
print(f"  Category: {clearthread_txn.category}")
print(f"  Confidence: {clearthread_txn.category_confidence}")

# Test rule matching with LIVE rule engine
print(f"\n{'='*80}")
print("CALLING LIVE RULE ENGINE")
print("=" * 80)

match_result = rule_engine.match_transaction(clearthread_txn)

if match_result:
    category_id, pattern, priority = match_result
    print(f"\n✓ MATCH FOUND!")
    print(f"  Category ID: {category_id}")
    print(f"  Pattern: '{pattern}'")
    print(f"  Priority: {priority}")

    # Look up category name
    categories = db.get_categories()
    category = next((c for c in categories if c.id == category_id), None)
    if category:
        print(f"  Category Name: {category.name}")
    else:
        print(f"  ❌ ERROR: Category ID '{category_id}' NOT FOUND in categories table!")
        print(f"\n  Available categories:")
        for c in categories[:10]:
            print(f"    - {c.id}: {c.name}")
else:
    print(f"\n❌ NO MATCH FOUND!")
    print(f"\nDEBUGGING WHY...")

    # Get all rules and test manually
    all_rules = db.get_rules()
    print(f"\nTotal rules in database: {len(all_rules)}")

    clearthread_rules = [r for r in all_rules if 'CLEARTHREAD' in r.pattern.upper()]
    print(f"CLEARTHREAD rules: {len(clearthread_rules)}")

    for rule in clearthread_rules:
        print(f"\n  Testing rule: '{rule.pattern}'")
        print(f"    Category ID: {rule.category_id}")
        print(f"    Priority: {rule.priority}")

        # Check if category exists
        categories = db.get_categories()
        category = next((c for c in categories if c.id == rule.category_id), None)
        if category:
            print(f"    Category Name: {category.name}")
        else:
            print(f"    ❌ BROKEN: Category ID '{rule.category_id}' does not exist!")

print("\n" + "=" * 80)
