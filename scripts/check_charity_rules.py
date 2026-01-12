"""Debug script to check Charity rules and test matching."""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.database import FinanceDatabase
from src.core.rule_engine import RuleEngine
from src.data.models import Transaction, Rule
from datetime import datetime

# Initialize database
DB_PATH = Path("data/finance.db")
db = FinanceDatabase(DB_PATH)

# Get all rules
rules_objs = db.get_rules()
categories_objs = db.get_categories()

# Convert to dictionaries for easier printing
rules = [{'id': r.id, 'pattern': r.pattern, 'category_id': r.category_id, 'priority': r.priority} for r in rules_objs]
categories = [{'id': c.id, 'name': c.name} for c in categories_objs]

# Create category lookup
cat_lookup = {c['id']: c['name'] for c in categories}

# Add category names to rules
for r in rules:
    r['category_name'] = cat_lookup.get(r['category_id'], 'Unknown')

# Find Charity rules
charity_rules = [r for r in rules if 'charity' in r.get('category_name', '').lower() or 'donation' in r.get('category_name', '').lower()]

print("=" * 70)
print("CHARITY/DONATION RULES IN DATABASE:")
print("=" * 70)
if charity_rules:
    for r in charity_rules:
        print(f"Pattern: '{r['pattern']}' -> Category: {r['category_name']} (Priority: {r.get('priority', 0)})")
    print(f"\nTotal charity rules: {len(charity_rules)}")
else:
    print("NO CHARITY RULES FOUND!")

print("\n" + "=" * 70)
print("TESTING TRANSACTION:")
print("=" * 70)
test_description = "5001 11NOV25 , FOA PEACE IN , PALESTINE , LEICESTER GB"
print(f"Description: {test_description}")

# Create test transaction
from datetime import date as date_obj
test_txn = Transaction(
    id="test123",
    date=date_obj.today(),
    description=test_description,
    amount=-10.0,
    balance=1000.0,
    account_name="Test Account",
    account_number="12345678"
)

# Test against all rules
engine = RuleEngine(rules_objs)

# Get all matching rules
matches = engine.get_matching_rules(test_txn)

print("\n" + "=" * 70)
print("MATCHING RULES:")
print("=" * 70)
if matches:
    for rule, pattern in matches:
        cat_name = next((c['name'] for c in categories if c['id'] == rule.category_id), 'Unknown')
        print(f"[MATCH] Pattern '{pattern}' -> Category: {cat_name} (Priority: {rule.priority})")
else:
    print("[NO MATCH] NO RULES MATCHED THIS TRANSACTION")

# Test specific patterns manually
print("\n" + "=" * 70)
print("MANUAL TOKEN TESTING:")
print("=" * 70)
description_upper = test_description.upper()
print(f"Description (upper): {description_upper}")

import re
tokens = re.split(r'[\s*]+', description_upper)
tokens = [t for t in tokens if t]
tokens_normalized = [re.sub(r'[,;:.!?()]+$', '', token) for token in tokens]
print(f"Tokens: {tokens_normalized}")

# Test if keywords appear
keywords = ["CHARITY", "DONATION", "PEACE", "PALESTINE", "FOA"]
print(f"\nKeyword search:")
for keyword in keywords:
    if keyword in tokens_normalized:
        print(f"  [YES] '{keyword}' FOUND in tokens")
    else:
        print(f"  [NO] '{keyword}' NOT in tokens")

print("\n" + "=" * 70)
print("SUGGESTED FIX:")
print("=" * 70)
print("Add a rule with pattern: 'PEACE IN PALESTINE' or 'FOA PEACE'")
print("This will match the whole-word tokens in your transaction description.")
