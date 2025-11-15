"""
Simple script to categorize all transactions in the database.

Run this to categorize your transactions without using the UI.
"""
from pathlib import Path
from src.data.database import FinanceDatabase
from src.core.categorizer import HybridCategorizer
import os

# Load database
DB_PATH = Path("data/finance.db")
db = FinanceDatabase(DB_PATH)

print("=" * 80)
print("CATEGORIZING ALL TRANSACTIONS")
print("=" * 80)

# Get all transactions
all_transactions = db.get_transactions()
print(f"\nTotal transactions in database: {len(all_transactions)}")

# Get uncategorized
uncategorized = [t for t in all_transactions if not t.category or t.category == "Uncategorized"]
print(f"Uncategorized transactions: {len(uncategorized)}")

if len(uncategorized) == 0:
    print("\n✓ All transactions are already categorized!")
    exit(0)

# Get categorizer
api_key = os.getenv("ANTHROPIC_API_KEY")
categorizer = HybridCategorizer(db, ai_api_key=api_key, enable_ai=bool(api_key))

# Check setup
stats = categorizer.get_statistics()
print(f"Rules: {stats['total_rules']}, Categories: {stats['total_categories']}")
print(f"AI enabled: {stats['ai_enabled']}")

# Categorize
print(f"\nCategorizing {len(uncategorized)} transactions...")
results = categorizer.categorize_batch(uncategorized, use_ai_fallback=bool(api_key))

# Save
print("Saving results...")
categorizer.save_transaction_categories(results)

# Show results
print("\n" + "=" * 80)
print("CATEGORIZATION COMPLETE!")
print("=" * 80)
print(f"📋 {results['rule_matched']} matched by rules (FREE)")
print(f"🤖 {results['ai_categorized']} categorized by AI (${results['total_cost_usd']:.4f})")
print(f"❓ {results['uncategorized']} still uncategorized")
print("=" * 80)
