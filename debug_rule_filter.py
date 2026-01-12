#!/usr/bin/env python3
"""
Debug rule-matched transactions to see why filter isn't working.
"""
from pathlib import Path
from src.data.database import FinanceDatabase

DB_PATH = Path("data/finance.db")
db = FinanceDatabase(DB_PATH)

print("=" * 80)
print("RULE-MATCHED TRANSACTIONS DEBUG")
print("=" * 80)

# Get all transactions
all_txns = db.get_transactions()
print(f"\nTotal transactions: {len(all_txns)}")

# Find categorized transactions
categorized = [t for t in all_txns if t.category and t.category != "Uncategorized"]
print(f"Categorized (has category): {len(categorized)}")

# Check first 10 categorized transactions
print(f"\nFirst 10 categorized transactions:")
print("-" * 80)

for i, t in enumerate(categorized[:10], 1):
    print(f"\n{i}. {t.description[:50]}")
    print(f"   Category: {t.category}")
    print(f"   Confidence: {t.category_confidence} (type: {type(t.category_confidence)})")
    print(f"   Confirmed: {t.category_confirmed}")
    print(f"   Confidence == 1.0: {t.category_confidence == 1.0}")
    print(f"   Confidence is 1.0 (float check): {float(t.category_confidence) == 1.0 if t.category_confidence else False}")

# Try different filter conditions
print("\n" + "=" * 80)
print("FILTER TEST:")
print("=" * 80)

# Original filter
rule_matched = [t for t in all_txns if t.category and t.category_confidence == 1.0 and not t.category_confirmed and t.category != "Uncategorized"]
print(f"\n1. Rule matched (confidence==1.0): {len(rule_matched)}")

# Try with float conversion
rule_matched_float = [t for t in all_txns if t.category and t.category_confidence and float(t.category_confidence) == 1.0 and not t.category_confirmed and t.category != "Uncategorized"]
print(f"2. Rule matched (float(confidence)==1.0): {len(rule_matched_float)}")

# Try without confidence check
has_category = [t for t in all_txns if t.category and not t.category_confirmed and t.category != "Uncategorized"]
print(f"3. Has category, not confirmed: {len(has_category)}")

# Group by confidence value
print(f"\n4. Confidence value distribution:")
conf_dist = {}
for t in categorized:
    conf = t.category_confidence
    if conf not in conf_dist:
        conf_dist[conf] = 0
    conf_dist[conf] += 1

for conf, count in sorted(conf_dist.items()):
    print(f"   Confidence={conf}: {count} transactions")

print("\n" + "=" * 80)
