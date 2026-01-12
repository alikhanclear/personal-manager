"""
Show uncategorized transactions to help create rules.

This shows which transactions didn't match any rules,
grouped by similar descriptions to help you create rules.
"""
from pathlib import Path
from collections import Counter
from src.data.database import FinanceDatabase

DB_PATH = Path("data/finance.db")
db = FinanceDatabase(DB_PATH)

print("=" * 80)
print("UNCATEGORIZED TRANSACTIONS")
print("=" * 80)

# Get uncategorized transactions
all_transactions = db.get_transactions()
uncategorized = [t for t in all_transactions if not t.category or t.category == "Uncategorized"]

print(f"\nTotal transactions: {len(all_transactions)}")
print(f"Uncategorized: {len(uncategorized)} ({len(uncategorized)/len(all_transactions)*100:.1f}%)")

if len(uncategorized) == 0:
    print("\n✓ All transactions are categorized!")
    exit(0)

# Extract first word/merchant from description
merchant_patterns = []
for txn in uncategorized:
    # Take first 1-2 words from description as potential pattern
    words = txn.description.split()
    if len(words) >= 2:
        # If second word is numeric, just use first word
        if words[1].replace(',', '').replace('.', '').isdigit():
            pattern = words[0]
        else:
            pattern = f"{words[0]} {words[1]}"
    else:
        pattern = words[0] if words else txn.description[:20]

    merchant_patterns.append((pattern, txn))

# Count patterns
pattern_counts = Counter([p for p, _ in merchant_patterns])

# Show top uncategorized patterns
print("\n" + "=" * 80)
print("TOP UNCATEGORIZED PATTERNS")
print("=" * 80)
print("\nThese patterns appear most often in uncategorized transactions:")
print("(Consider adding rules for these)\n")

for pattern, count in pattern_counts.most_common(20):
    # Find one example transaction
    example = next((t for p, t in merchant_patterns if p == pattern), None)
    if example:
        print(f"{count:4d}x  '{pattern}'")
        print(f"       Example: {example.description[:70]}")
        print(f"       Amount: £{example.amount}")
        print()

print("\n" + "=" * 80)
print("SAMPLE UNCATEGORIZED TRANSACTIONS (First 10)")
print("=" * 80)

for i, txn in enumerate(uncategorized[:10], 1):
    print(f"\n{i}. {txn.description[:70]}")
    print(f"   Amount: £{txn.amount}")
    print(f"   Date: {txn.date}")

print("\n" + "=" * 80)
print("NEXT STEPS")
print("=" * 80)
print("\n1. Add rules for common patterns:")
print("   - Edit: add_custom_rules.py")
print("   - Add patterns like: ('PATTERN', 'Category', 10)")
print("   - Run: python add_custom_rules.py")
print("\n2. Re-categorize with new rules:")
print("   - Run: python categorize_all.py")
print("\n3. Use AI for remaining transactions (if you have API key):")
print("   - Set APP_ANTHROPIC_API_KEY in .env")
print("   - Run: python categorize_all.py")
