#!/usr/bin/env python3
"""
Manually initialize database with categories and rules.
"""
from pathlib import Path
from src.data.database import FinanceDatabase
from src.data.models import Category
from src.core.rule_engine import create_default_rules
from config.default_categories import DEFAULT_CATEGORIES

DB_PATH = Path("data/finance.db")
db = FinanceDatabase(DB_PATH)

print("=" * 80)
print("INITIALIZING DATABASE")
print("=" * 80)

# Check current state
print(f"\n1. CURRENT STATE:")
categories = db.get_categories()
rules = db.get_rules()
transactions = db.get_transactions()
print(f"   Categories: {len(categories)}")
print(f"   Rules: {len(rules)}")
print(f"   Transactions: {len(transactions)}")

if len(categories) == 0:
    print(f"\n2. ADDING CATEGORIES:")
    category_map = {}
    for name, parent_name, color, icon, budget in DEFAULT_CATEGORIES:
        parent_id = category_map.get(parent_name) if parent_name else None
        category = Category(
            name=name,
            parent_id=parent_id,
            color=color,
            icon=icon,
            budget_monthly=budget,
        )
        try:
            db.insert_category(category)
            category_map[name] = category.name
            print(f"   ✓ Added: {icon} {name}")
        except Exception as e:
            print(f"   ❌ Failed to add {name}: {e}")

    print(f"\n   Total categories added: {len(category_map)}")

    # Add default rules
    print(f"\n3. ADDING DEFAULT RULES:")
    rules = create_default_rules(category_map)
    for rule in rules:
        try:
            db.insert_rule(rule)
            print(f"   ✓ Rule: {rule.pattern} → {rule.category_id}")
        except Exception as e:
            print(f"   ❌ Failed to add rule {rule.pattern}: {e}")

    print(f"\n   Total rules added: {len(rules)}")
else:
    print(f"\n   Categories already exist, skipping initialization")

# Verify
print(f"\n4. FINAL STATE:")
categories = db.get_categories()
rules = db.get_rules()
print(f"   Categories: {len(categories)}")
print(f"   Rules: {len(rules)}")

print("\n" + "=" * 80)
print("✓ Database initialized!")
print("=" * 80)
