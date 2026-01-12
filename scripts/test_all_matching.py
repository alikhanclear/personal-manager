"""
Comprehensive regression tests for rule matching after adding dot delimiter.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.rule_engine import RuleEngine
from src.data.models import Rule, Transaction
from datetime import datetime

# Test cases: (transaction_description, pattern, should_match, test_name)
TEST_CASES = [
    # NEW: Dot delimiter tests
    ("8430 02NOV25 D , BOLT.EUO2511021744, LONDON GB", "BOLT", True, "BOLT with dot suffix"),
    ("PAYPAL *NETFLIX.COM", "NETFLIX", True, "NETFLIX with .COM domain"),
    ("AMAZON.CO.UK PURCHASE", "AMAZON", True, "AMAZON with .CO.UK domain"),
    ("APPLE.COM/BILL SUBSCRIPTION", "APPLE", True, "APPLE with .COM/BILL"),
    ("SPORTSDIRECT.COM ONLINE", "SPORTSDIRECT", True, "SPORTSDIRECT with .COM"),

    # PRESERVED: Original token matching (no regressions)
    ("TFL TRAVEL LONDON", "TFL", True, "TFL as whole word"),
    ("NETFLIX SUBSCRIPTION", "TFL", False, "TFL should NOT match NETFLIX"),
    ("CO-OP FOOD STORE", "CO-OP", True, "CO-OP with hyphen preserved"),
    ("M&S SIMPLY FOOD", "M&S", True, "M&S with ampersand"),

    # PRESERVED: Multi-word patterns
    ("PAYPAL *AMAZON PRIME", "AMAZON PRIME", True, "Multi-word pattern AMAZON PRIME"),
    ("CLEARTHREAD STARLI, INITIAL PAYMENT", "CLEARTHREAD STARLI", True, "Multi-word with trailing comma"),

    # PRESERVED: Trailing punctuation stripping
    ("FOA PEACE IN , PALESTINE , LEICESTER", "FOA PEACE IN PALESTINE", True, "Pattern with commas ignored"),

    # EDGE CASES
    ("BOLT SCOOTERS LONDON", "BOLT", True, "BOLT as standalone word"),
    ("THUNDERBOLT PAYMENTS", "BOLT", False, "BOLT should NOT match THUNDERBOLT"),
    ("F1 GRAND PRIX", "F1", True, "Short pattern F1"),
    ("BNA LTD PAYMENT", "BNA", True, "Short pattern BNA"),
]

def run_tests():
    """Run all test cases."""
    print("\n" + "=" * 80)
    print("COMPREHENSIVE RULE MATCHING REGRESSION TESTS")
    print("=" * 80)

    passed = 0
    failed = 0
    test_results = []

    for description, pattern, expected_match, test_name in TEST_CASES:
        # Create transaction
        txn = Transaction(
            id=f"test-{passed+failed}",
            date=datetime(2025, 11, 2),
            description=description,
            amount=-10.00,
            balance=1000.00,
            account_number="12345678",
            account_name="Test Account"
        )

        # Create rule
        rule = Rule(
            id="test-rule",
            pattern=pattern,
            category_id="test-category",
            priority=10
        )

        # Test matching
        engine = RuleEngine([rule])
        result = engine.match_transaction(txn)
        actual_match = result is not None

        # Check result
        if actual_match == expected_match:
            status = "[PASS]"
            passed += 1
        else:
            status = "[FAIL]"
            failed += 1

        test_results.append({
            'status': status,
            'test_name': test_name,
            'description': description,
            'pattern': pattern,
            'expected': expected_match,
            'actual': actual_match
        })

    # Print results
    print(f"\nTest Results: {passed} passed, {failed} failed ({passed + failed} total)\n")

    for result in test_results:
        print(f"{result['status']} {result['test_name']}")
        if result['status'] == '[FAIL]':
            print(f"  Description: {result['description']}")
            print(f"  Pattern: {result['pattern']}")
            print(f"  Expected: {'Match' if result['expected'] else 'No Match'}")
            print(f"  Actual: {'Match' if result['actual'] else 'No Match'}")

    # Summary
    print("\n" + "=" * 80)
    if failed == 0:
        print(f"[SUCCESS] All {passed} tests passed! No regressions detected.")
    else:
        print(f"[WARNING] {failed} test(s) failed. Please review.")
    print("=" * 80 + "\n")

    return failed == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
