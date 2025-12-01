"""Add Interest and Charges category if it doesn't exist."""
import sys
sys.path.insert(0, '.')

from src.data.database import FinanceDatabase
from src.data.models import Category
import uuid

db = FinanceDatabase()

# Check if category exists
categories = db.get_categories()
interest_category = next((c for c in categories if c.name == "Interest and Charges"), None)

if interest_category:
    print(f"[OK] 'Interest and Charges' category already exists: {interest_category.id}")
else:
    # Create new category
    new_category = Category(
        id=str(uuid.uuid4()),
        name="Interest and Charges",
        description="Bank interest payments and charges (transaction types: INT, CHG)"
    )

    db.insert_category(new_category)
    print(f"[OK] Created 'Interest and Charges' category: {new_category.id}")
