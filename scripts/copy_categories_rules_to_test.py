"""
Copy categories and rules from production database to test database.
"""
import sqlite3
from pathlib import Path

# Database paths
PROD_DB = Path(__file__).parent.parent / "data" / "finance.db"
TEST_DB = Path(__file__).parent.parent / "data" / "finance_test.db"

def copy_data():
    """Copy categories and rules from production to test database."""

    # Connect to both databases
    prod_conn = sqlite3.connect(PROD_DB)
    test_conn = sqlite3.connect(TEST_DB)

    prod_cursor = prod_conn.cursor()
    test_cursor = test_conn.cursor()

    # Copy categories
    print("Copying categories...")
    prod_cursor.execute("SELECT * FROM categories")
    categories = prod_cursor.fetchall()

    # Get column names
    category_columns = [desc[0] for desc in prod_cursor.description]
    placeholders = ','.join(['?'] * len(category_columns))
    columns_str = ','.join(category_columns)

    for category in categories:
        test_cursor.execute(
            f"INSERT OR REPLACE INTO categories ({columns_str}) VALUES ({placeholders})",
            category
        )

    print(f"  - Copied {len(categories)} categories")

    # Copy rules
    print("Copying rules...")
    prod_cursor.execute("SELECT * FROM rules")
    rules = prod_cursor.fetchall()

    # Get column names
    rule_columns = [desc[0] for desc in prod_cursor.description]
    placeholders = ','.join(['?'] * len(rule_columns))
    columns_str = ','.join(rule_columns)

    for rule in rules:
        test_cursor.execute(
            f"INSERT OR REPLACE INTO rules ({columns_str}) VALUES ({placeholders})",
            rule
        )

    print(f"  - Copied {len(rules)} rules")

    # Commit and close
    test_conn.commit()
    test_conn.close()
    prod_conn.close()

    print(f"\n[OK] Successfully copied data to test database!")
    print(f"Test database: {TEST_DB}")

if __name__ == "__main__":
    copy_data()
