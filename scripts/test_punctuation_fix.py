"""
Test script to validate the trailing punctuation fix.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.rule_engine import RuleEngine
from src.data.models import Rule, Transaction
from datetime import datetime, date

def test_punctuation_fix():
    """Test that trailing punctuation doesn't break matching."""

    print("="*80)
    print("TESTING TRAILING PUNCTUATION FIX")
    print("="*80)

    # Create test rules
    rules = [
        Rule(pattern="CLEARTHREAD STARLI", category_id="clearthread-cat", priority=15),
        Rule(pattern="FOA PEACE IN PALESTINE", category_id="charity-cat", priority=15),
        Rule(pattern="AMAZON", category_id="shopping-cat", priority=10),
        Rule(pattern="CO-OP", category_id="groceries-cat", priority=10),
        Rule(pattern="APPLE.COM/BILL", category_id="subscriptions-cat", priority=10),
    ]

    # Initialize rule engine
    engine = RuleEngine(rules)

    # Test cases
    test_cases = [
        # (description, expected_pattern_match, test_name)
        # PRIMARY FIX TEST - FOA PEACE IN PALESTINE
        ("5001 11NOV25 , FOA PEACE IN , PALESTINE , LEICESTER GB", "FOA PEACE IN PALESTINE", "FOA PEACE IN PALESTINE - Main fix"),
        ("FOA PEACE IN , PALESTINE , LEICESTER", "FOA PEACE IN PALESTINE", "FOA PEACE IN PALESTINE - Commas between words"),

        # Trailing punctuation tests
        ("CLEARTHREAD STARLI, INITIAL PAYMENT", "CLEARTHREAD STARLI", "Trailing comma"),
        ("CLEARTHREAD STARLI; PAYMENT", "CLEARTHREAD STARLI", "Trailing semicolon"),
        ("CLEARTHREAD STARLI. PAYMENT", "CLEARTHREAD STARLI", "Trailing period"),

        # Preserved special characters
        ("CO-OP FOOD STORE", "CO-OP", "CO-OP with hyphen preserved"),
        ("APPLE.COM/BILL SUBSCRIPTION", "APPLE.COM/BILL", "Apple with dot/slash preserved"),

        # Baseline tests
        ("CLEARTHREAD STARLI PAYMENT", "CLEARTHREAD STARLI", "No punctuation"),
        ("NETFLIX, INC.", None, "No matching rule"),
    ]

    print("\nRunning tests:\n")

    passed = 0
    failed = 0

    for description, expected_pattern, test_name in test_cases:
        # Create test transaction
        txn = Transaction(
            id="test-" + str(passed + failed),
            date=date.today(),
            description=description,
            amount=-10.0,
            balance=100.0,
            account_number="12345678",
            account_name="Test Account"
        )

        # Test matching
        match = engine.match_transaction(txn)

        if expected_pattern is None:
            # Expecting no match
            if match is None:
                print(f"[PASS] {test_name}")
                print(f"       '{description}'")
                print(f"       -> No match (as expected)")
                passed += 1
            else:
                print(f"[FAIL] {test_name}")
                print(f"       '{description}'")
                print(f"       -> Matched '{match[1]}' but expected no match")
                failed += 1
        else:
            # Expecting a match
            if match and match[1] == expected_pattern:
                print(f"[PASS] {test_name}")
                print(f"       '{description}'")
                print(f"       -> Matched '{match[1]}'")
                passed += 1
            elif match:
                print(f"[FAIL] {test_name}")
                print(f"       '{description}'")
                print(f"       -> Matched '{match[1]}' but expected '{expected_pattern}'")
                failed += 1
            else:
                print(f"[FAIL] {test_name}")
                print(f"       '{description}'")
                print(f"       -> No match (expected '{expected_pattern}')")
                failed += 1

        print()

    print("="*80)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*80)

    return failed == 0

if __name__ == "__main__":
    success = test_punctuation_fix()
    exit(0 if success else 1)
