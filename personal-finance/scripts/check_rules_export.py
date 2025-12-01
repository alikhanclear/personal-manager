"""
Check if any rules have invalid category_ids that would cause UUIDs to appear in exports.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.database import FinanceDatabase

def check_rules_export():
    """Check rules and their category mappings."""
    db = FinanceDatabase(db_path="data/finance.db")

    # Get all rules
    rules = db.get_rules()
    print(f"Total rules: {len(rules)}")

    # Get all categories
    categories = db.get_categories()
    category_map = {cat.id: cat.name for cat in categories}
    print(f"Total categories: {len(categories)}")
    print()

    # Check for invalid category_ids
    invalid_count = 0
    print("=" * 80)
    print("CHECKING FOR INVALID CATEGORY IDS")
    print("=" * 80)

    for rule in rules:
        if rule.category_id not in category_map:
            invalid_count += 1
            print(f"[ERROR] INVALID RULE:")
            print(f"   Pattern: {rule.pattern}")
            print(f"   Category ID: {rule.category_id}")
            print(f"   Priority: {rule.priority}")
            print()

    if invalid_count == 0:
        print("[OK] All rules have valid category IDs!")
    else:
        print(f"[WARNING] Found {invalid_count} rules with invalid category IDs")

    print()
    print("=" * 80)
    print("SAMPLE EXPORT (First 10 rules)")
    print("=" * 80)

    # Simulate export for first 10 rules
    for idx, rule in enumerate(sorted(rules, key=lambda x: (-x.priority, x.pattern))[:10], 1):
        category_name = category_map.get(rule.category_id, "[UNKNOWN UUID: " + rule.category_id + "]")
        print(f"{idx}. Pattern: {rule.pattern:30s} | Category: {category_name:25s} | Priority: {rule.priority}")

if __name__ == "__main__":
    check_rules_export()
