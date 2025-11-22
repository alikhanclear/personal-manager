"""
Simple script to categorize all transactions in the database.

Run this to categorize your transactions without using the UI.
"""
from pathlib import Path
from src.data.database import FinanceDatabase
from src.core.categorizer import HybridCategorizer
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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
    print("\n[OK] All transactions are already categorized!")
    exit(0)

# Get categorizer
api_key = os.getenv("APP_ANTHROPIC_API_KEY")
categorizer = HybridCategorizer(db, ai_api_key=api_key, enable_ai=bool(api_key))

# Check setup
stats = categorizer.get_statistics()
print(f"Rules: {stats['total_rules']}, Categories: {stats['total_categories']}")
print(f"AI enabled: {stats['ai_enabled']}")

# Estimate time for AI categorization
if api_key and len(uncategorized) > 0:
    # Assume ~80% will need AI (20% matched by rules)
    estimated_ai_calls = int(len(uncategorized) * 0.8)
    # 1.4 seconds per AI call (rate limiting)
    estimated_minutes = (estimated_ai_calls * 1.4) / 60
    print(f"\n[TIME] Estimated time: {estimated_minutes:.1f} minutes")
    print(f"       (Rate limited to 45 requests/minute to avoid API limits)")
    print(f"       Rules will match instantly, AI needs ~1.4s per transaction")

# Categorize
print(f"\nCategorizing {len(uncategorized)} transactions...")
print("=" * 80)
print("Progress updates every 50 transactions...")
print("You can close this window and it will keep running.")
print("Results are saved to database in real-time.")
print("=" * 80)

import time
start_time = time.time()

results = categorizer.categorize_batch(uncategorized, use_ai_fallback=bool(api_key))

elapsed = time.time() - start_time
elapsed_mins = elapsed / 60

# Save
print("Saving results...")
categorizer.save_transaction_categories(results)

# Show results
print("\n" + "=" * 80)
print("CATEGORIZATION COMPLETE!")
print("=" * 80)
print(f"[TIME] Time elapsed: {elapsed_mins:.1f} minutes ({elapsed:.0f} seconds)")
print(f"[RULES] {results['rule_matched']} matched by rules (FREE)")
print(f"[AI] {results['ai_categorized']} categorized by AI (${results['total_cost_usd']:.4f})")
print(f"[UNCAT] {results['uncategorized']} still uncategorized")
print("=" * 80)
print("\n[OK] Refresh your browser to see the updated transactions!")
print("  Go to Review & Correct tab -> Filter: 'AI Suggestions'")
print("=" * 80)
