"""
Debug script to check categorization setup and test matching.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.data.database import FinanceDatabase
from src.core.categorizer import HybridCategorizer
from src.core.rule_engine import RuleEngine

# Initialize
DB_PATH = Path(__file__).parent / "data" / "finance.db"
db = FinanceDatabase(DB_PATH)

print("=" * 80)
print("CATEGORIZATION DEBUG")
print("=" * 80)

# Check database stats
stats = db.get_statistics()
print(f"\n[Database Stats]")
print(f"  Total transactions: {stats['total_transactions']}")
print(f"  Total categories: {stats['total_categories']}")
print(f"  Total rules: {stats['total_rules']}")
print(f"  Categorized transactions: {stats['categorized_transactions']}")

# Get some sample transactions
transactions = db.get_transactions(limit=10)
print(f"\n[Sample Transactions]")
for i, txn in enumerate(transactions[:5], 1):
    print(f"\n{i}. Description: '{txn.description}'")
    print(f"   Amount: £{txn.amount}")
    print(f"   Category: {txn.category or 'NONE'}")
    print(f"   Confirmed: {txn.category_confirmed}")

# Get some rules
rules = db.get_rules()
print(f"\n[Sample Rules (first 10)]")
for i, rule in enumerate(rules[:10], 1):
    print(f"{i}. Pattern: '{rule.pattern}' → {rule.category_id} (priority: {rule.priority})")

# Test rule matching
if transactions and rules:
    print(f"\n[Testing Rule Matching]")
    rule_engine = RuleEngine(rules)

    for txn in transactions[:5]:
        print(f"\nTransaction: '{txn.description}'")
        match = rule_engine.match_transaction(txn)
        if match:
            category_id, pattern, priority = match
            print(f"  ✓ MATCHED: Pattern '{pattern}' → {category_id}")
        else:
            print(f"  ✗ NO MATCH")

            # Check what patterns are in the description
            desc_upper = txn.description.upper()
            matching_keywords = []
            for rule in rules[:20]:  # Check first 20 rules
                if rule.pattern.upper() in desc_upper:
                    matching_keywords.append(rule.pattern)

            if matching_keywords:
                print(f"  💡 Found keywords in description: {matching_keywords}")

print("\n" + "=" * 80)
