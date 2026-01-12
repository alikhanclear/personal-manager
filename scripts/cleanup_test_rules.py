"""
Clean up any test rules left over from failed test runs.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.database import FinanceDatabase

def cleanup_test_rules():
    """Remove all test rules from database."""
    db = FinanceDatabase(db_path="data/finance.db")

    rules = db.get_rules()
    deleted = 0

    for rule in rules:
        if rule.pattern.startswith('TEST_'):
            print(f"Deleting test rule: {rule.pattern}")
            db.delete_rule(rule.id)
            deleted += 1

    print(f"\nTotal test rules deleted: {deleted}")
    print(f"Remaining rules: {len(db.get_rules())}")

if __name__ == "__main__":
    cleanup_test_rules()
