"""
Integration tests for database.py

Tests database operations with a real SQLite database.
These are integration tests that use the clean_db fixture.
"""

import pytest
import sqlite3
from datetime import datetime
from src.data.database import (
    get_all_transactions,
    get_transaction_by_id,
    insert_transaction,
    update_transaction_category,
    get_all_categories,
    get_all_rules,
    insert_rule,
    delete_rule,
)


@pytest.mark.integration
class TestDatabaseTransactions:
    """Test transaction database operations."""

    def test_get_all_transactions(self, clean_db, sample_transactions):
        """Test fetching all transactions."""
        transactions = get_all_transactions(clean_db)
        assert len(transactions) == 3

    def test_get_transaction_by_id(self, clean_db, sample_transactions):
        """Test fetching a specific transaction."""
        txn = get_transaction_by_id(clean_db, "txn_001")
        assert txn is not None
        assert txn["description"] == "TESCO STORES 1234"

    def test_get_nonexistent_transaction(self, clean_db):
        """Test fetching a transaction that doesn't exist."""
        txn = get_transaction_by_id(clean_db, "nonexistent")
        assert txn is None

    def test_insert_transaction(self, clean_db, sample_categories):
        """Test inserting a new transaction."""
        new_txn = {
            "id": "txn_999",
            "date": datetime(2025, 1, 10).isoformat(),
            "description": "TEST TRANSACTION",
            "amount": -99.99,
            "balance": 900.00,
            "account_number": "12345678",
            "category": "groceries",
            "category_confidence": 0.95,
            "category_confirmed": False,
        }

        insert_transaction(clean_db, new_txn)

        # Verify it was inserted
        txn = get_transaction_by_id(clean_db, "txn_999")
        assert txn is not None
        assert txn["description"] == "TEST TRANSACTION"

    def test_insert_duplicate_transaction(self, clean_db, sample_transactions):
        """Test that inserting duplicate transaction is ignored."""
        # Try to insert duplicate
        dup_txn = {
            "id": "txn_001",  # Same ID as existing
            "date": datetime(2025, 1, 1).isoformat(),
            "description": "DUPLICATE",
            "amount": -1.00,
            "balance": 1.00,
            "account_number": "12345678",
        }

        insert_transaction(clean_db, dup_txn)

        # Should still be original transaction
        txn = get_transaction_by_id(clean_db, "txn_001")
        assert txn["description"] == "TESCO STORES 1234"  # Original, not "DUPLICATE"

    def test_update_transaction_category(self, clean_db, sample_transactions):
        """Test updating a transaction's category."""
        update_transaction_category(
            clean_db,
            "txn_002",
            category="dining_out",
            confidence=0.85,
            confirmed=True
        )

        txn = get_transaction_by_id(clean_db, "txn_002")
        assert txn["category"] == "dining_out"
        assert txn["category_confidence"] == 0.85
        assert txn["category_confirmed"] == 1  # True stored as 1


@pytest.mark.integration
class TestDatabaseCategories:
    """Test category database operations."""

    def test_get_all_categories(self, clean_db, sample_categories):
        """Test fetching all categories."""
        categories = get_all_categories(clean_db)
        assert len(categories) == 5

    def test_category_hierarchy(self, clean_db):
        """Test parent-child category relationships."""
        conn = sqlite3.connect(clean_db)
        cursor = conn.cursor()

        # Insert parent and child categories
        cursor.execute(
            "INSERT INTO categories (id, name, description) VALUES (?, ?, ?)",
            ("expenses", "Expenses", "All expenses")
        )
        cursor.execute(
            "INSERT INTO categories (id, name, description, parent_id) VALUES (?, ?, ?, ?)",
            ("groceries", "Groceries", "Food shopping", "expenses")
        )
        conn.commit()
        conn.close()

        categories = get_all_categories(clean_db)
        groceries = next(c for c in categories if c["id"] == "groceries")
        assert groceries["parent_id"] == "expenses"


@pytest.mark.integration
class TestDatabaseRules:
    """Test rule database operations."""

    def test_get_all_rules(self, clean_db, sample_rules):
        """Test fetching all rules."""
        rules = get_all_rules(clean_db)
        assert len(rules) == 4

    def test_rules_ordered_by_priority(self, clean_db, sample_rules):
        """Test that rules are returned in priority order."""
        rules = get_all_rules(clean_db)

        # Higher priority rules should come first
        priorities = [r["priority"] for r in rules]
        assert priorities == sorted(priorities, reverse=True)

    def test_insert_rule(self, clean_db, sample_categories):
        """Test inserting a new rule."""
        rule_id = insert_rule(
            clean_db,
            pattern=r"NETFLIX",
            category_id="subscriptions",
            priority=15
        )

        assert rule_id is not None

        rules = get_all_rules(clean_db)
        netflix_rule = next((r for r in rules if r["pattern"] == r"NETFLIX"), None)
        assert netflix_rule is not None
        assert netflix_rule["priority"] == 15

    def test_delete_rule(self, clean_db, sample_rules):
        """Test deleting a rule."""
        # Get first rule ID
        rules = get_all_rules(clean_db)
        rule_id = rules[0]["id"]

        # Delete it
        delete_rule(clean_db, rule_id)

        # Verify it's gone
        rules_after = get_all_rules(clean_db)
        assert len(rules_after) == len(rules) - 1
        assert rule_id not in [r["id"] for r in rules_after]


@pytest.mark.integration
class TestDatabaseFiltering:
    """Test transaction filtering queries."""

    def test_filter_by_category(self, clean_db, sample_transactions):
        """Test filtering transactions by category."""
        conn = sqlite3.connect(clean_db)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM transactions WHERE category = ?",
            ("groceries",)
        )
        results = cursor.fetchall()
        conn.close()

        assert len(results) == 1

    def test_filter_by_confidence(self, clean_db, sample_transactions):
        """Test filtering by confidence level."""
        conn = sqlite3.connect(clean_db)
        cursor = conn.cursor()

        # Get confirmed transactions (confidence = 1.0)
        cursor.execute(
            "SELECT * FROM transactions WHERE category_confidence = 1.0"
        )
        confirmed = cursor.fetchall()

        # Get AI suggestions (confidence < 1.0 and not null)
        cursor.execute(
            "SELECT * FROM transactions WHERE category_confidence < 1.0 AND category_confidence IS NOT NULL"
        )
        suggestions = cursor.fetchall()

        # Get uncategorized (confidence is null)
        cursor.execute(
            "SELECT * FROM transactions WHERE category_confidence IS NULL"
        )
        uncategorized = cursor.fetchall()

        conn.close()

        assert len(confirmed) == 2
        assert len(suggestions) == 0
        assert len(uncategorized) == 1

    def test_filter_by_date_range(self, clean_db, sample_transactions):
        """Test filtering by date range."""
        conn = sqlite3.connect(clean_db)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM transactions WHERE date >= ? AND date <= ?",
            ("2025-01-01", "2025-01-01")
        )
        results = cursor.fetchall()
        conn.close()

        assert len(results) == 1
