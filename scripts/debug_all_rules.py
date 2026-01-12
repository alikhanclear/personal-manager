"""
Check ALL rules to find what's categorizing PAYPAL *NETFLIX as Public Transport.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.database import FinanceDatabase

DB_PATH = Path(__file__).parent.parent / "data" / "finance.db"

def main():
    db = FinanceDatabase(DB_PATH)

    # Get all rules
    rules = db.get_rules()

    # Get categories for lookup
    categories = db.get_categories()
    cat_lookup = {cat.id: cat.name for cat in categories}

    print("=" * 80)
    print(f"ALL RULES ({len(rules)} total) - Sorted by Priority")
    print("=" * 80)

    # Sort by priority (highest first)
    sorted_rules = sorted(rules, key=lambda r: r.priority, reverse=True)

    for i, rule in enumerate(sorted_rules, 1):
        cat_name = cat_lookup.get(rule.category_id, f"UNKNOWN ({rule.category_id})")
        print(f"{i}. Pattern: '{rule.pattern}' -> {cat_name} (Priority: {rule.priority})")

    # Now test which rule matches "PAYPAL *NETFLIX"
    print("\n" + "=" * 80)
    print("Testing: Which rules match 'PAYPAL *NETFLIX'?")
    print("=" * 80)

    test_description = "5001 12OCT25 , PAYPAL *NETFLIX , 35314369001 GB"
    print(f"\nTest description: {test_description}")
    print(f"Uppercase: {test_description.upper()}\n")

    # Use the rule engine to test
    from src.core.rule_engine import RuleEngine
    rule_engine = RuleEngine(rules)

    # Manually test each rule
    description_upper = test_description.upper()
    matches = []

    for rule in sorted_rules:
        pattern_upper = rule.pattern.upper()

        # Test exact match
        if description_upper == pattern_upper:
            matches.append((rule, "exact match"))
            continue

        # Test substring
        if pattern_upper in description_upper:
            matches.append((rule, "substring match"))
            continue

        # Test regex
        import re
        try:
            if re.search(pattern_upper, description_upper):
                matches.append((rule, "regex match"))
        except:
            pass

    if matches:
        print(f"Found {len(matches)} matching rules:")
        for rule, match_type in matches:
            cat_name = cat_lookup.get(rule.category_id, f"UNKNOWN ({rule.category_id})")
            print(f"  - Pattern: '{rule.pattern}' -> {cat_name} ({match_type}, Priority: {rule.priority})")

        # The first one will win (highest priority)
        winning_rule, match_type = matches[0]
        winning_cat = cat_lookup.get(winning_rule.category_id, "UNKNOWN")
        print(f"\nWINNER (highest priority): Pattern '{winning_rule.pattern}' -> {winning_cat}")
    else:
        print("No rules match this description!")

if __name__ == '__main__':
    main()
