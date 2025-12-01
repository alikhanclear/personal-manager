"""
Add missing rules for uncategorized transactions.

Rules to add:
- SCREWFIX → Home Maintenance
- PURE MUSCLES GYM → Gym/Fitness
- RISE VAPE → Other
- AMAZON.CO.U → Shopping (additional AMAZON variant)
- NANDOS → Restaurants
- NANDOS.CO.UK → Restaurants
- UMMAH WELFARE TRUST → Charity
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.database import FinanceDatabase
from src.data.models import Rule

def add_missing_rules():
    """Add rules for common uncategorized transactions."""

    db = FinanceDatabase('data/finance.db')

    # Get existing categories
    categories = db.get_categories()
    cat_map = {c.name: c.id for c in categories}

    print("Adding missing rules...")
    print("=" * 70)

    # Define new rules
    new_rules = [
        ("SCREWFIX", "Home Maintenance", 10),
        ("PURE MUSCLES GYM", "Gym/Fitness", 10),
        ("RISE VAPE", "Other", 10),
        ("AMAZON.CO.U", "Shopping", 10),
        ("NANDOS", "Restaurants", 10),
        ("NANDOS.CO.UK", "Restaurants", 10),
        ("UMMAH WELFARE TRUST", "Charity", 10),
    ]

    added = 0
    skipped = 0

    for pattern, category_name, priority in new_rules:
        # Check if category exists
        if category_name not in cat_map:
            print(f"[SKIP] Category '{category_name}' not found for pattern '{pattern}'")
            skipped += 1
            continue

        category_id = cat_map[category_name]

        # Check if rule already exists
        existing_rules = db.get_rules()
        if any(r.pattern.upper() == pattern.upper() for r in existing_rules):
            print(f"[SKIP] Rule '{pattern}' already exists")
            skipped += 1
            continue

        # Create new rule
        rule = Rule(
            pattern=pattern,
            category_id=category_id,
            priority=priority
        )

        # Add to database
        db.insert_rule(rule)
        print(f"[ADD] '{pattern}' -> {category_name}")
        added += 1

    print("=" * 70)
    print(f"Summary: {added} rules added, {skipped} skipped")
    print("\nRun categorization again to apply these rules to transactions.")

if __name__ == "__main__":
    add_missing_rules()
