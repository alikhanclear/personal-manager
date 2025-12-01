"""
Debug script to identify why transactions aren't matching rules.

Shows:
1. All uncategorized transactions
2. All rules in database
3. Tests if rules SHOULD match but aren't (token matching issue)
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data.database import FinanceDatabase
from src.core.rule_engine import RuleEngine
from src.data.models import Transaction

def debug_unmatched_transactions():
    """Debug why transactions aren't matching rules."""

    print("="*80)
    print("DEBUGGING UNMATCHED TRANSACTIONS")
    print("="*80)

    # Connect to database
    db_path = "data/finance.db"
    db = FinanceDatabase(db_path)

    # Get all transactions
    all_transactions = db.get_transactions()
    print(f"\n1. Total transactions: {len(all_transactions)}")

    # Filter uncategorized (after force re-categorize)
    uncategorized = [t for t in all_transactions if not t.category or t.category == "Uncategorized"]
    print(f"2. Uncategorized transactions: {len(uncategorized)}")

    # Get all rules
    rules = db.get_rules()
    print(f"3. Total rules in database: {len(rules)}")

    # Get categories for display
    categories = db.get_categories()
    category_map = {cat.id: cat.name for cat in categories}

    # Initialize rule engine
    rule_engine = RuleEngine(rules)

    # Show first 20 uncategorized transactions and test matching
    print(f"\n{'='*80}")
    print(f"ANALYZING FIRST 20 UNCATEGORIZED TRANSACTIONS")
    print(f"{'='*80}\n")

    for i, txn in enumerate(uncategorized[:20], 1):
        print(f"{i}. Description: '{txn.description}'")
        print(f"   Amount: £{txn.amount:.2f}")
        print(f"   Date: {txn.date}")

        # Test if any rule matches
        match = rule_engine.match_transaction(txn)

        if match:
            category_id, pattern, priority = match
            category_name = category_map.get(category_id, "Unknown")
            print(f"   *** SHOULD MATCH: Pattern='{pattern}' -> Category='{category_name}' (Priority={priority})")
            print(f"   *** BUG DETECTED: Rule exists but didn't categorize! ***")
        else:
            print(f"   -> No rule matches (genuinely uncategorized)")

        print()

    # Show all rules for reference
    print(f"\n{'='*80}")
    print(f"ALL RULES IN DATABASE (Total: {len(rules)})")
    print(f"{'='*80}\n")

    for i, rule in enumerate(rules[:50], 1):  # Show first 50 rules
        category_name = category_map.get(rule.category_id, "Unknown")
        print(f"{i}. Pattern='{rule.pattern}' -> Category='{category_name}' (Priority={rule.priority})")

    if len(rules) > 50:
        print(f"\n... and {len(rules) - 50} more rules")

    # Group uncategorized by common patterns
    print(f"\n{'='*80}")
    print(f"COMMON PATTERNS IN UNCATEGORIZED TRANSACTIONS")
    print(f"{'='*80}\n")

    # Extract first words from descriptions
    first_words = {}
    for txn in uncategorized:
        # Get first word/token
        words = txn.description.split()
        if words:
            first_word = words[0].upper()
            if first_word not in first_words:
                first_words[first_word] = []
            first_words[first_word].append(txn)

    # Show top 20 most common first words
    sorted_patterns = sorted(first_words.items(), key=lambda x: len(x[1]), reverse=True)

    print("Top 20 most common patterns (first word in description):\n")
    for i, (pattern, txns) in enumerate(sorted_patterns[:20], 1):
        print(f"{i}. '{pattern}' - {len(txns)} transactions")
        # Show example
        example = txns[0]
        print(f"   Example: '{example.description}' (£{example.amount:.2f})")
        print()

    print(f"\n{'='*80}")
    print(f"RECOMMENDATIONS")
    print(f"{'='*80}\n")

    print("Based on the analysis above:")
    print("1. Check if any uncategorized transactions SHOULD match a rule but don't")
    print("   - This indicates a token-matching bug")
    print("2. Check the common patterns list")
    print("   - These are candidates for new rules")
    print("3. Verify token-based matching is working correctly")
    print("   - Pattern tokens must match whole words in description")

if __name__ == "__main__":
    debug_unmatched_transactions()
