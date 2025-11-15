"""
Add custom categorization rules for your specific merchants.

Edit this file to add rules for transactions that weren't categorized.
Then run: python add_custom_rules.py
"""
from pathlib import Path
from src.data.database import FinanceDatabase
from src.data.models import Rule

DB_PATH = Path("data/finance.db")
db = FinanceDatabase(DB_PATH)

# Define your custom rules here
# Format: (pattern, category_name, priority)
CUSTOM_RULES = [
    # Financial/Transfers
    ("VIRGIN MONEY", "Transfers", 10),  # Bank transfer to Virgin Money
    ("FROM DADDY", "Transfers", 10),     # Personal transfer from family
    ("FROM AHMED", "Transfers", 10),      # Personal transfer

    # Add more rules here as you discover uncategorized merchants
    # ("MERCHANT_NAME", "Category", 10),
]

print("=" * 80)
print("ADDING CUSTOM RULES")
print("=" * 80)

# Get existing categories
categories = db.get_categories()
category_map = {cat.name: cat.name for cat in categories}

# Add rules
added = 0
for pattern, category_name, priority in CUSTOM_RULES:
    if category_name not in category_map:
        print(f"⚠️  Skipping '{pattern}' - category '{category_name}' doesn't exist")
        continue

    rule = Rule(
        pattern=pattern,
        category_id=category_map[category_name],
        priority=priority,
    )

    try:
        db.insert_rule(rule)
        print(f"✓ Added rule: '{pattern}' → {category_name}")
        added += 1
    except Exception as e:
        print(f"✗ Failed to add rule '{pattern}': {e}")

print(f"\n✓ Added {added} custom rules")
print("\nNow run: python categorize_all.py to re-categorize with new rules")
