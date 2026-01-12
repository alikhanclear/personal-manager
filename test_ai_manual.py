import os
from pathlib import Path
from src.data.database import FinanceDatabase
from src.core.categorizer import HybridCategorizer

# Setup
db = FinanceDatabase(Path('data/finance.db'))
api_key = os.getenv("APP_ANTHROPIC_API_KEY")

print(f"API Key exists: {bool(api_key)}")

# Get uncategorized transactions  
all_txns = db.get_transactions()
uncategorized = [t for t in all_txns if not t.category or t.category == "Uncategorized"]

print(f"Total transactions: {len(all_txns)}")
print(f"Uncategorized: {len(uncategorized)}")

# Try to categorize one transaction
if len(uncategorized) > 0:
    test_txn = uncategorized[0]
    print(f"\nTesting: {test_txn.description} | {test_txn.amount}")

    try:
        categorizer = HybridCategorizer(db, ai_api_key=api_key, enable_ai=True)
        result = categorizer.categorize_batch([test_txn], use_ai_fallback=True, ai_batch_size=1)
        print(f"Result: {result}")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
