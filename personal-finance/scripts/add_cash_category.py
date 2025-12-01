"""Add 'Cash' category for C/L transaction types."""
import sys
from pathlib import Path
import uuid

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.database import FinanceDatabase
from src.data.models import Category

db = FinanceDatabase("data/finance.db")

# Check if Cash category already exists
existing_cats = db.get_categories()
cash_exists = any(c.name == "Cash" for c in existing_cats)

if cash_exists:
    print("[OK] Cash category already exists")
else:
    # Create Cash category
    cash_category = Category(
        id=str(uuid.uuid4()),
        name="Cash",
        parent_id=None,
        color="#2E7D32",  # Green (money color)
        icon="money",
        budget_monthly=None
    )

    db.insert_category(cash_category)
    print("[OK] Created 'Cash' category")
    print(f"  ID: {cash_category.id}")
    print(f"  Color: {cash_category.color}")
    print(f"  Icon: {cash_category.icon}")
