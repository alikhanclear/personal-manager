#!/usr/bin/env python3
"""
Debug script to check transaction categorization status.
"""
from pathlib import Path
from src.data.database import FinanceDatabase

DB_PATH = Path("data/finance.db")
db = FinanceDatabase(DB_PATH)

print("=" * 80)
print("TRANSACTION CATEGORIZATION DEBUG")
print("=" * 80)

# Get all transactions
transactions = db.get_transactions()
print(f"\nTotal transactions: {len(transactions)}")

# Check first 10 categorized transactions
categorized = [t for t in transactions if t.category and t.category != "Uncategorized"][:10]

print(f"\nFirst 10 categorized transactions:")
print("-" * 80)

for i, txn in enumerate(categorized, 1):
    print(f"\n{i}. {txn.description[:50]}")
    print(f"   Category: {txn.category}")
    print(f"   Confidence: {txn.category_confidence} (type: {type(txn.category_confidence)})")
    print(f"   Confirmed: {txn.category_confirmed}")
    print(f"   Is 1.0?: {txn.category_confidence == 1.0}")
    print(f"   Is truthy?: {bool(txn.category_confidence)}")

# Count by filter logic
print("\n" + "=" * 80)
print("FILTER COUNTS:")
print("=" * 80)

rule_matched = [t for t in transactions if t.category and t.category_confidence == 1.0 and not t.category_confirmed and t.category != "Uncategorized"]
print(f"Rule Matched (confidence==1.0, not confirmed): {len(rule_matched)}")

ai_suggested = [t for t in transactions if t.category and t.category_confidence and t.category_confidence < 1.0 and not t.category_confirmed and t.category != "Uncategorized"]
print(f"AI Suggested (confidence<1.0, not confirmed): {len(ai_suggested)}")

has_category_no_confirm = [t for t in transactions if t.category and not t.category_confirmed and t.category != "Uncategorized"]
print(f"Has category, not confirmed (any confidence): {len(has_category_no_confirm)}")

confirmed = [t for t in transactions if t.category_confirmed]
print(f"Confirmed: {len(confirmed)}")

uncategorized = [t for t in transactions if not t.category or t.category == "Uncategorized"]
print(f"Uncategorized: {len(uncategorized)}")

# Check confidence values
print("\n" + "=" * 80)
print("CONFIDENCE VALUE ANALYSIS:")
print("=" * 80)

confidence_values = {}
for t in transactions:
    if t.category and t.category != "Uncategorized":
        conf = t.category_confidence
        if conf not in confidence_values:
            confidence_values[conf] = 0
        confidence_values[conf] += 1

for conf, count in sorted(confidence_values.items()):
    print(f"Confidence={conf}: {count} transactions")

print("\n" + "=" * 80)
