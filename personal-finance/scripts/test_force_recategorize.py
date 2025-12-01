"""
Test script to validate force re-categorize functionality.

This script will:
1. Show current categorization state
2. Simulate what happens when you force re-categorize
3. Help identify if caching is an issue
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data.database import FinanceDatabase
from src.core.categorizer import HybridCategorizer

def test_force_recategorize():
    """Test force re-categorize functionality."""

    print("="*80)
    print("TESTING FORCE RE-CATEGORIZE")
    print("="*80)

    # Connect to database
    db_path = "data/finance.db"
    db = FinanceDatabase(db_path)

    # Get all transactions
    all_transactions = db.get_transactions()
    print(f"\n1. Total transactions in database: {len(all_transactions)}")

    # Show current state
    confirmed = [t for t in all_transactions if t.category_confirmed]
    rule_matched = [t for t in all_transactions if t.category_confidence == 1.0 and not t.category_confirmed]
    ai_suggested = [t for t in all_transactions if t.category_confidence and t.category_confidence < 1.0]
    uncategorized = [t for t in all_transactions if not t.category or t.category == "Uncategorized"]

    print(f"\n2. Current categorization state:")
    print(f"   - Confirmed: {len(confirmed)}")
    print(f"   - Rule matched (confidence=1.0): {len(rule_matched)}")
    print(f"   - AI suggested (confidence<1.0): {len(ai_suggested)}")
    print(f"   - Uncategorized: {len(uncategorized)}")

    # Show rules
    rules = db.get_rules()
    print(f"\n3. Total rules in database: {len(rules)}")

    # Get all categories for lookup
    categories = db.get_categories()
    category_map = {cat.id: cat.name for cat in categories}

    # Show first 5 rules
    print(f"\n4. Sample rules:")
    for i, rule in enumerate(rules[:5], 1):
        # Get category name
        category_name = category_map.get(rule.category_id, "Unknown")
        print(f"   {i}. Pattern='{rule.pattern}' -> Category='{category_name}' (Priority={rule.priority})")

    # TEST 1: Normal mode (should skip confirmed)
    print(f"\n{'='*80}")
    print("TEST 1: Normal Mode (force_recategorize=False)")
    print("="*80)
    print("This should SKIP confirmed transactions...")

    # Create fresh categorizer
    categorizer = HybridCategorizer(db, enable_ai=False)

    # Re-categorize with force=False
    results = categorizer.categorize_batch(
        all_transactions,
        use_ai_fallback=False,
        force_recategorize=False
    )

    print(f"\nResults:")
    print(f"   - Total processed: {results['total']}")
    print(f"   - Already confirmed (skipped): {results['already_confirmed']}")
    print(f"   - Transaction type matched: {results['transaction_type_matched']}")
    print(f"   - Rule matched: {results['rule_matched']}")
    print(f"   - Uncategorized: {results['uncategorized']}")

    # TEST 2: Force mode (should re-categorize ALL)
    print(f"\n{'='*80}")
    print("TEST 2: Force Mode (force_recategorize=True)")
    print("="*80)
    print("This should RE-CATEGORIZE ALL transactions including confirmed...")

    # Reload transactions from database (fresh state)
    all_transactions = db.get_transactions()

    # Create fresh categorizer
    categorizer = HybridCategorizer(db, enable_ai=False)

    # Re-categorize with force=True
    results = categorizer.categorize_batch(
        all_transactions,
        use_ai_fallback=False,
        force_recategorize=True
    )

    print(f"\nResults:")
    print(f"   - Total processed: {results['total']}")
    print(f"   - Already confirmed (skipped): {results['already_confirmed']} (should be 0!)")
    print(f"   - Transaction type matched: {results['transaction_type_matched']}")
    print(f"   - Rule matched: {results['rule_matched']}")
    print(f"   - Uncategorized: {results['uncategorized']}")

    # Verify force mode worked
    if results['already_confirmed'] == 0:
        print(f"\n✓ PASS: Force mode correctly processed ALL transactions (none skipped)")
    else:
        print(f"\n✗ FAIL: Force mode should have skipped 0 transactions, but skipped {results['already_confirmed']}")

    print(f"\n{'='*80}")
    print("TEST COMPLETE")
    print("="*80)

    # Show example transactions
    print(f"\n5. Sample transactions after force re-categorize:")
    sample_txns = all_transactions[:5]
    for i, txn in enumerate(sample_txns, 1):
        print(f"   {i}. {txn.description[:40]:40s} -> {txn.category or 'Uncategorized':20s} (confidence={txn.category_confidence}, confirmed={txn.category_confirmed})")

if __name__ == "__main__":
    test_force_recategorize()
