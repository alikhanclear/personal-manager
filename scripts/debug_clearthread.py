"""
Debug CLEARTHREAD rule matching issue.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.database import FinanceDatabase
from src.core.rule_engine import RuleEngine

# Initialize database
db = FinanceDatabase("data/finance.db")

# Search for CLEARTHREAD rules
print("=" * 80)
print("SEARCHING FOR CLEARTHREAD RULES")
print("=" * 80)

all_rules = db.get_rules()
clearthread_rules = [r for r in all_rules if 'CLEARTHREAD' in r.pattern.upper()]

print(f"\nFound {len(clearthread_rules)} rules matching 'CLEARTHREAD':")
for rule in clearthread_rules:
    print(f"\n  Pattern: '{rule.pattern}'")
    print(f"  Category ID: {rule.category_id}")
    print(f"  Priority: {rule.priority}")

    # Get category name
    categories = db.get_categories()
    category = next((c for c in categories if c.id == rule.category_id), None)
    if category:
        print(f"  Category Name: {category.name}")
    else:
        print(f"  WARNING: Category ID '{rule.category_id}' not found in database!")

# Search for CLEARTHREAD transactions
print("\n" + "=" * 80)
print("SEARCHING FOR CLEARTHREAD TRANSACTIONS")
print("=" * 80)

all_transactions = db.get_transactions()
clearthread_txns = [t for t in all_transactions if 'CLEARTHREAD' in t.description.upper()]

print(f"\nFound {len(clearthread_txns)} transactions with 'CLEARTHREAD':")
for txn in clearthread_txns[:5]:  # Show first 5
    print(f"\n  Description: '{txn.description}'")
    print(f"  Category: {txn.category or 'None'}")
    print(f"  Confidence: {txn.category_confidence}")
    print(f"  Confirmed: {txn.category_confirmed}")

# Test rule matching
if clearthread_rules and clearthread_txns:
    print("\n" + "=" * 80)
    print("TESTING RULE MATCHING")
    print("=" * 80)

    rule_engine = RuleEngine(db)
    test_description = "CLEARTHREAD STARLI, INITIAL PAYMENT , VIA MOBILE -..."

    print(f"\nTest Description: '{test_description}'")
    print("\nTokens extracted:")

    # Show how tokens are extracted
    import re
    tokens = [t.strip() for t in re.split(r'[\s,*\-./\\|()]+', test_description.upper()) if t.strip()]
    for i, token in enumerate(tokens, 1):
        print(f"  {i}. '{token}'")

    print("\nTesting each CLEARTHREAD rule:")
    for rule in clearthread_rules:
        pattern_upper = rule.pattern.upper()
        pattern_tokens = [t.strip() for t in re.split(r'[\s,*\-./\\|()]+', pattern_upper) if t.strip()]

        print(f"\n  Rule Pattern: '{rule.pattern}'")
        print(f"  Pattern Tokens: {pattern_tokens}")

        # Check if all pattern tokens exist in description tokens
        matches = all(pt in tokens for pt in pattern_tokens)
        print(f"  Would Match: {matches}")

        if not matches:
            print(f"  Missing tokens: {[pt for pt in pattern_tokens if pt not in tokens]}")

print("\n" + "=" * 80)
