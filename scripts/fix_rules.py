"""
Script to fix invalid rules in database.

Deletes all existing rules (which have invalid category IDs)
and re-creates them with correct category UUIDs.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.database import FinanceDatabase
from src.core.rule_engine import create_default_rules

DB_PATH = Path(__file__).parent.parent / "data" / "finance.db"


def main():
    db = FinanceDatabase(DB_PATH)

    print("=== FIXING INVALID RULES ===\n")

    # Step 1: Get current rule count
    rules = db.get_rules()
    print(f"Current rules in database: {len(rules)}")

    # Step 2: Check how many are invalid
    categories = db.get_categories()
    valid_cat_ids = {cat.id for cat in categories}
    invalid_count = sum(1 for r in rules if r.category_id not in valid_cat_ids)
    print(f"Invalid rules (wrong category IDs): {invalid_count}")

    # Step 3: Delete ALL rules
    print("\nDeleting all rules from database...")
    with db._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM rules")
        conn.commit()
    print("[OK] All rules deleted")

    # Step 4: Create category_map (name -> UUID)
    print("\nCreating category map...")
    category_map = {cat.name: cat.id for cat in categories}
    print(f"[OK] Mapped {len(category_map)} categories")

    # Step 5: Create new rules with correct UUIDs
    print("\nCreating new rules with correct UUIDs...")
    new_rules = create_default_rules(category_map)
    for rule in new_rules:
        db.insert_rule(rule)
    print(f"[OK] Created {len(new_rules)} new rules")

    # Step 6: Verify all rules are valid now
    print("\nVerifying rules...")
    rules = db.get_rules()
    invalid_count = sum(1 for r in rules if r.category_id not in valid_cat_ids)

    if invalid_count == 0:
        print(f"[SUCCESS] All {len(rules)} rules have valid category UUIDs!")
    else:
        print(f"[WARNING] Still have {invalid_count} invalid rules")

    # Step 7: Show sample rules
    print("\n=== SAMPLE RULES (first 5) ===")
    cat_name_map = {cat.id: cat.name for cat in categories}
    for rule in rules[:5]:
        cat_name = cat_name_map.get(rule.category_id, "UNKNOWN")
        print(f"  Pattern: {rule.pattern:20} -> Category: {cat_name} (UUID: {rule.category_id[:8]}...)")

    print("\n[OK] Rule fix complete!")


if __name__ == "__main__":
    main()
