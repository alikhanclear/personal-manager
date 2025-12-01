"""Quick script to check database state before testing."""
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.database import FinanceDatabase

db = FinanceDatabase("data/finance.db")

# Get transaction count
transactions = db.get_transactions()
print(f"Total transactions: {len(transactions)}")

# Get category count
categories = db.get_categories()
print(f"Total categories: {len(categories)}")

# Get rule count
rules = db.get_rules()
print(f"Total rules: {len(rules)}")

# Show sample transactions
if transactions:
    print(f"\nSample of first 3 transactions:")
    for t in transactions[:3]:
        print(f"  - {t.date}: {t.description} | Amount: £{t.amount} | Category: {t.category or 'Uncategorized'}")
