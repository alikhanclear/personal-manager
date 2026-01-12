"""
Comprehensive test for smart alphanumeric splitting.
Tests FEDEX tracking numbers AND short codes (O2, F1, U22).
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.rule_engine import RuleEngine
from src.data.models import Rule, Transaction
from datetime import datetime

# Test cases: (transaction_description, pattern, should_match, test_name)
TEST_CASES = [
    # NEW: Smart alphanumeric splitting (4+ letters)
    ("5001 10SEP25 , FEDEX395224543 , T08456 070809 GB", "FEDEX", True, "FEDEX with tracking number (5 letters)"),
    ("AMAZON123456789 PURCHASE", "AMAZON", True, "AMAZON with tracking (6 letters)"),
    ("BOLT123 PAYMENT", "BOLT", True, "BOLT with number (4 letters)"),
    ("UBER1234 TRIP", "UBER", True, "UBER with number (4 letters)"),

    # PRESERVED: Short codes (1-3 letters) NOT split
    ("O2 MOBILE BILL", "O2", True, "O2 short code (1 letter preserved)"),
    ("F1 GRAND PRIX", "F1", True, "F1 short code (1 letter preserved)"),
    ("U22 ON THE WHARF", "U22", True, "U22 short code (1 letter preserved)"),
    ("HIJAZIALAA67 PAYMENT", "HIJAZIALAA67", True, "Full alphanumeric match"),

    # EDGE CASES: 3 letters (not split - below 4 threshold)
    ("EUO2511021744", "EUO", False, "EUO with number (3 letters, NOT split)"),
    ("ABC123", "ABC", False, "ABC with number (3 letters, NOT split)"),

    # PRESERVED: Original functionality (no regressions)
    ("TFL TRAVEL LONDON", "TFL", True, "TFL as whole word"),
    ("NETFLIX SUBSCRIPTION", "TFL", False, "TFL should NOT match NETFLIX"),
    ("CO-OP FOOD STORE", "CO-OP", True, "CO-OP with hyphen preserved"),
    ("M&S SIMPLY FOOD", "M&S", True, "M&S with ampersand"),
    ("PAYPAL *AMAZON PRIME", "AMAZON PRIME", True, "Multi-word pattern"),
    ("BOLT.EUO2511021744", "BOLT", True, "BOLT with dot delimiter"),
    ("APPLE.COM/BILL", "APPLE", True, "APPLE with dot delimiter"),

    # Should NOT match
    ("THUNDERBOLT PAYMENTS", "BOLT", False, "BOLT should NOT match THUNDERBOLT"),
    ("FEDEX", "FEDEX395", False, "Full pattern should NOT match partial"),
]

def run_tests():
    """Run all test cases."""
    print("\n" + "=" * 80)
    print("SMART ALPHANUMERIC SPLITTING TEST SUITE")
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

    # Group results by category
    print("=== NEW FEATURES: Smart Alphanumeric Splitting ===")
    for result in test_results[:4]:
        print(f"{result['status']} {result['test_name']}")
        if result['status'] == '[FAIL]':
            print(f"  Expected: {'Match' if result['expected'] else 'No Match'}, "
                  f"Got: {'Match' if result['actual'] else 'No Match'}")

    print("\n=== PRESERVED: Short Codes (O2, F1, U22) ===")
    for result in test_results[4:8]:
        print(f"{result['status']} {result['test_name']}")
        if result['status'] == '[FAIL]':
            print(f"  Expected: {'Match' if result['expected'] else 'No Match'}, "
                  f"Got: {'Match' if result['actual'] else 'No Match'}")

    print("\n=== EDGE CASES: 3-Letter Codes ===")
    for result in test_results[8:10]:
        print(f"{result['status']} {result['test_name']}")
        if result['status'] == '[FAIL]':
            print(f"  Expected: {'Match' if result['expected'] else 'No Match'}, "
                  f"Got: {'Match' if result['actual'] else 'No Match'}")

    print("\n=== REGRESSIONS: Original Functionality ===")
    for result in test_results[10:]:
        print(f"{result['status']} {result['test_name']}")
        if result['status'] == '[FAIL]':
            print(f"  Expected: {'Match' if result['expected'] else 'No Match'}, "
                  f"Got: {'Match' if result['actual'] else 'No Match'}")

    # Summary
    print("\n" + "=" * 80)
    if failed == 0:
        print(f"[SUCCESS] All {passed} tests passed!")
        print("\nKey Achievements:")
        print("  ✓ FEDEX matches FEDEX395224543 (tracking numbers work)")
        print("  ✓ O2, F1, U22 preserved (short codes work)")
        print("  ✓ BOLT, UBER, AMAZON with tracking numbers work")
        print("  ✓ All original functionality preserved (no regressions)")
    else:
        print(f"[WARNING] {failed} test(s) failed. Review output above.")
    print("=" * 80 + "\n")

    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
