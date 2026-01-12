"""
Check ALL rules to see which ones have broken category_ids.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.database import FinanceDatabase

DB_PATH = Path(__file__).parent.parent / "data" / "finance.db"

def main():
    db = FinanceDatabase(DB_PATH)

    # Get all rules and categories
    rules = db.get_rules()
    categories = db.get_categories()

    # Create lookup: UUID -> category name
    cat_lookup = {cat.id: cat.name for cat in categories}

    # Create reverse lookup: category name -> UUID
    name_to_uuid = {cat.name: cat.id for cat in categories}

    print("=" * 80)
    print(f"Checking {len(rules)} rules for broken category_ids")
    print("=" * 80)

    broken_rules = []
    working_rules = []

    for rule in rules:
        # Check if category_id is a valid UUID (exists in cat_lookup)
        if rule.category_id in cat_lookup:
            # GOOD: category_id is a valid UUID
            cat_name = cat_lookup[rule.category_id]
            working_rules.append((rule, cat_name))
        else:
            # BAD: category_id is NOT a UUID
            # Check if it's a category name instead
            if rule.category_id in name_to_uuid:
                # It's a category NAME (broken!)
                broken_rules.append((rule, rule.category_id, name_to_uuid[rule.category_id]))
            else:
                # It's neither a UUID nor a name (completely broken)
                broken_rules.append((rule, rule.category_id, None))

    print(f"\n[WORKING RULES: {len(working_rules)}]")
    for rule, cat_name in working_rules[:5]:  # Show first 5
        print(f"  Pattern: '{rule.pattern}' -> {cat_name} (UUID: {rule.category_id[:8]}...)")
    if len(working_rules) > 5:
        print(f"  ... and {len(working_rules) - 5} more")

    print(f"\n[BROKEN RULES: {len(broken_rules)}]")
    if broken_rules:
        for rule, bad_id, correct_uuid in broken_rules:
            print(f"  Pattern: '{rule.pattern}'")
            print(f"    Current (WRONG): {bad_id}")
            if correct_uuid:
                print(f"    Should be: {correct_uuid}")
            else:
                print(f"    ERROR: Category doesn't exist!")
            print()
    else:
        print("  None - all rules are correct!")

    print("=" * 80)
    print("Summary:")
    print("=" * 80)
    print(f"Total rules: {len(rules)}")
    print(f"Working: {len(working_rules)}")
    print(f"Broken: {len(broken_rules)}")

    if broken_rules:
        print("\n[ACTION REQUIRED]")
        print("You need to fix the broken rules by updating their category_ids to UUIDs.")
        print("Options:")
        print("  1. Fix them manually in the database")
        print("  2. Run a fix script to update all broken rules")
        print("  3. Delete all rules and recreate from defaults")
    else:
        print("\n[OK] All rules have valid category_ids!")

if __name__ == '__main__':
    main()
