"""
Test the new whole-word token matching logic.
"""
import sys
from pathlib import Path
import re

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_matches_pattern(description: str, pattern: str) -> bool:
    """
    Test implementation of whole-word token matching.
    """
    pattern_upper = pattern.upper().strip()

    # Tokenize description into words using common delimiters
    description_tokens = re.split(r'[\s,*\-./\\|()]+', description.upper())
    description_tokens = [t for t in description_tokens if t]

    # Tokenize pattern
    pattern_tokens = re.split(r'[\s,*\-./\\|()]+', pattern_upper)
    pattern_tokens = [t for t in pattern_tokens if t]

    # If single-word pattern, check if it's in description tokens
    if len(pattern_tokens) == 1:
        return pattern_tokens[0] in description_tokens

    # If multi-word pattern, check if sequence appears in description
    for i in range(len(description_tokens) - len(pattern_tokens) + 1):
        if description_tokens[i:i+len(pattern_tokens)] == pattern_tokens:
            return True

    return False

def main():
    print("=" * 80)
    print("Testing New Whole-Word Token Matching Logic")
    print("=" * 80)

    # Test cases
    test_cases = [
        # (description, pattern, should_match, reason)
        ("5001 12OCT25 , PAYPAL *NETFLIX , 35314369001 GB", "NETFLIX", True, "NETFLIX is a whole word"),
        ("5001 12OCT25 , PAYPAL *NETFLIX , 35314369001 GB", "TFL", False, "TFL is inside NETFLIX, not a whole word"),
        ("TFL TRAVEL CARD", "TFL", True, "TFL is a whole word"),
        ("UBER EATS LONDON", "UBER", True, "UBER is a whole word"),
        ("TESCO STORES 1234", "TESCO", True, "TESCO is a whole word"),
        ("AMAZON PRIME SUBSCRIPTION", "AMAZON PRIME", True, "Multi-word pattern matches"),
        ("AMAZON.CO.UK PURCHASE", "AMAZON", True, "AMAZON separated by dot"),
        ("PAYPAL *SPOTIFY", "SPOTIFY", True, "SPOTIFY after asterisk"),
        ("VIZARATH ALIKHAN", "VIZARATH", True, "VIZARATH is first word"),
        ("VIZARATH ALIKHAN", "ALIKHAN", True, "ALIKHAN is second word"),
        ("VIZARATH ALIKHAN", "VIZARATH ALIKHAN", True, "Full name matches"),
        ("NETFLIX.COM SUBSCRIPTION", "NETFLIX", True, "NETFLIX before dot"),
        ("COSTA COFFEE SHOP", "COSTA", True, "COSTA is first word"),
    ]

    print("\nRunning test cases:\n")

    passed = 0
    failed = 0

    for description, pattern, should_match, reason in test_cases:
        result = test_matches_pattern(description, pattern)
        status = "PASS" if result == should_match else "FAIL"

        if result == should_match:
            passed += 1
            icon = "[PASS]"
        else:
            failed += 1
            icon = "[FAIL]"

        print(f"{icon} {status}")
        print(f"  Description: {description}")
        print(f"  Pattern: '{pattern}'")
        print(f"  Expected: {should_match}, Got: {result}")
        print(f"  Reason: {reason}")
        print()

    print("=" * 80)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 80)

    # Now test with actual database
    print("\n" + "=" * 80)
    print("Testing with actual Netflix transactions")
    print("=" * 80)

    from src.data.database import FinanceDatabase
    from src.core.rule_engine import RuleEngine

    DB_PATH = Path(__file__).parent.parent / "data" / "finance.db"
    db = FinanceDatabase(DB_PATH)

    # Get rules
    rules = db.get_rules()
    rule_engine = RuleEngine(rules)

    # Get Netflix transactions
    all_txns = db.get_transactions()
    netflix_txns = [t for t in all_txns if 'netflix' in t.description.lower()]

    print(f"\nFound {len(netflix_txns)} Netflix transactions\n")

    for i, txn in enumerate(netflix_txns[:3], 1):  # Test first 3
        print(f"{i}. {txn.description}")

        # Test what rule matches
        match = rule_engine.match_transaction(txn)

        if match:
            category_id, pattern, priority = match

            # Get category name
            categories = db.get_categories()
            cat = next((c for c in categories if c.id == category_id), None)
            cat_name = cat.name if cat else "UNKNOWN"

            print(f"   Matched: Pattern '{pattern}' -> {cat_name}")
        else:
            print(f"   No match")
        print()

if __name__ == '__main__':
    main()
