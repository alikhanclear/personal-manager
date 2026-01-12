"""
Pytest configuration and shared fixtures.

This file is automatically loaded by pytest and provides fixtures
that can be used across all test files.
"""

import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Generator

import pytest
from pydantic import BaseModel

# Test database path
TEST_DB_PATH = "data/test_finance.db"


@pytest.fixture(scope="session")
def test_db_path() -> str:
    """Provide path to test database."""
    return TEST_DB_PATH


@pytest.fixture(scope="function")
def clean_db(test_db_path: str) -> Generator[str, None, None]:
    """
    Create a fresh test database for each test.

    This fixture:
    1. Creates a clean database before the test
    2. Yields the path to the test
    3. Cleans up the database after the test

    Usage:
        def test_something(clean_db):
            # clean_db is the path to a fresh database
            conn = sqlite3.connect(clean_db)
            ...
    """
    # Ensure data directory exists
    Path("data").mkdir(exist_ok=True)

    # Remove existing test database
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    # Initialize fresh database schema
    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()

    # Create tables (matching your actual schema)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            parent_id TEXT,
            FOREIGN KEY (parent_id) REFERENCES categories(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id TEXT PRIMARY KEY,
            date TEXT NOT NULL,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            balance REAL NOT NULL,
            account_number TEXT NOT NULL,
            category TEXT,
            category_confidence REAL,
            category_confirmed INTEGER DEFAULT 0,
            FOREIGN KEY (category) REFERENCES categories(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pattern TEXT NOT NULL,
            category_id TEXT NOT NULL,
            priority INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    """)

    conn.commit()
    conn.close()

    # Yield to test
    yield test_db_path

    # Cleanup after test
    if os.path.exists(test_db_path):
        os.remove(test_db_path)


@pytest.fixture
def sample_categories(clean_db: str) -> list[dict]:
    """Insert sample categories into test database."""
    conn = sqlite3.connect(clean_db)
    cursor = conn.cursor()

    categories = [
        {"id": "groceries", "name": "Groceries", "description": "Food and household items"},
        {"id": "dining_out", "name": "Dining Out", "description": "Restaurants and takeaway"},
        {"id": "transportation", "name": "Transportation", "description": "Travel and commute"},
        {"id": "salary", "name": "Salary", "description": "Employment income"},
        {"id": "uncategorized", "name": "Uncategorized", "description": "Unknown transactions"},
    ]

    for cat in categories:
        cursor.execute(
            "INSERT INTO categories (id, name, description) VALUES (?, ?, ?)",
            (cat["id"], cat["name"], cat["description"])
        )

    conn.commit()
    conn.close()

    return categories


@pytest.fixture
def sample_transactions(clean_db: str, sample_categories: list[dict]) -> list[dict]:
    """Insert sample transactions into test database."""
    conn = sqlite3.connect(clean_db)
    cursor = conn.cursor()

    base_date = datetime(2025, 1, 1)
    transactions = [
        {
            "id": "txn_001",
            "date": base_date.isoformat(),
            "description": "TESCO STORES 1234",
            "amount": -45.67,
            "balance": 1000.00,
            "account_number": "12345678",
            "category": "groceries",
            "category_confidence": 1.0,
            "category_confirmed": 1,
        },
        {
            "id": "txn_002",
            "date": (base_date + timedelta(days=1)).isoformat(),
            "description": "AMAZON PRIME",
            "amount": -8.99,
            "balance": 991.01,
            "account_number": "12345678",
            "category": None,
            "category_confidence": None,
            "category_confirmed": 0,
        },
        {
            "id": "txn_003",
            "date": (base_date + timedelta(days=2)).isoformat(),
            "description": "SALARY PAYMENT",
            "amount": 2500.00,
            "balance": 3491.01,
            "account_number": "12345678",
            "category": "salary",
            "category_confidence": 1.0,
            "category_confirmed": 1,
        },
    ]

    for txn in transactions:
        cursor.execute("""
            INSERT INTO transactions
            (id, date, description, amount, balance, account_number,
             category, category_confidence, category_confirmed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            txn["id"], txn["date"], txn["description"], txn["amount"],
            txn["balance"], txn["account_number"], txn["category"],
            txn["category_confidence"], txn["category_confirmed"]
        ))

    conn.commit()
    conn.close()

    return transactions


@pytest.fixture
def sample_rules(clean_db: str, sample_categories: list[dict]) -> list[dict]:
    """Insert sample rules into test database."""
    conn = sqlite3.connect(clean_db)
    cursor = conn.cursor()

    rules = [
        {"pattern": r"TESCO|SAINSBURY|ASDA|MORRISONS", "category_id": "groceries", "priority": 10},
        {"pattern": r"MCDONALD|KFC|PIZZA|NANDO", "category_id": "dining_out", "priority": 10},
        {"pattern": r"UBER|TAXI|BUS|TRAIN", "category_id": "transportation", "priority": 10},
        {"pattern": r"SALARY|WAGES|PAYROLL", "category_id": "salary", "priority": 20},
    ]

    for rule in rules:
        cursor.execute(
            "INSERT INTO rules (pattern, category_id, priority) VALUES (?, ?, ?)",
            (rule["pattern"], rule["category_id"], rule["priority"])
        )

    conn.commit()
    conn.close()

    return rules


@pytest.fixture
def mock_anthropic_client(mocker):
    """Mock Anthropic API client for testing AI categorization."""
    mock_client = mocker.Mock()
    mock_response = mocker.Mock()
    mock_response.content = [mocker.Mock(text='{"category": "groceries", "confidence": 0.95}')]
    mock_client.messages.create.return_value = mock_response
    return mock_client


@pytest.fixture
def sample_csv_content() -> str:
    """Sample NatWest CSV content for testing parser."""
    return """Date,Description,Amount,Balance,Account Number
01/01/2025,TESCO STORES 1234,-45.67,1000.00,12345678
02/01/2025,AMAZON PRIME,-8.99,991.01,12345678
03/01/2025,SALARY PAYMENT,2500.00,3491.01,12345678
"""
