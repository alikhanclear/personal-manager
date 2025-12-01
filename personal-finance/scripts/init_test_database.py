"""
Initialize a fresh test database for regression testing.
"""
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.database import FinanceDatabase

# Test database path
TEST_DB_PATH = Path(__file__).parent.parent / "data" / "finance_test.db"

def init_test_database():
    """Initialize test database with schema."""

    # Remove existing test database if it exists
    if TEST_DB_PATH.exists():
        print(f"Removing existing test database: {TEST_DB_PATH}")
        TEST_DB_PATH.unlink()

    print(f"Creating fresh test database: {TEST_DB_PATH}")

    # Create database (this initializes schema automatically)
    db = FinanceDatabase(TEST_DB_PATH)

    # Get stats
    categories = db.get_categories()
    rules = db.get_rules()
    transactions = db.get_transactions()

    print(f"\n[OK] Test database initialized successfully!")
    print(f"  - Categories: {len(categories)}")
    print(f"  - Rules: {len(rules)}")
    print(f"  - Transactions: {len(transactions)}")
    print(f"\nDatabase location: {TEST_DB_PATH}")
    print(f"\nNOTE: You may need to copy categories/rules from production database")

if __name__ == "__main__":
    init_test_database()
