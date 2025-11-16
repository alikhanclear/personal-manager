"""
SQLite database manager for personal finance application.
"""
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import List, Optional

from .models import Category, Rule, Transaction


class FinanceDatabase:
    """SQLite database manager for transactions, categories, and rules."""

    def __init__(self, db_path: str | Path = "finance.db"):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self._init_database()

    def _init_database(self) -> None:
        """Create database tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Transactions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id TEXT PRIMARY KEY,
                    date TEXT NOT NULL,
                    description TEXT NOT NULL,
                    merchant TEXT,
                    amount TEXT NOT NULL,
                    balance TEXT,
                    account_name TEXT NOT NULL,
                    account_number TEXT NOT NULL,
                    transaction_type TEXT,
                    category TEXT,
                    category_confidence REAL,
                    category_confirmed INTEGER DEFAULT 0,
                    tags TEXT,
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            # Create indexes for common queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_transactions_date
                ON transactions(date)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_transactions_account
                ON transactions(account_number)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_transactions_category
                ON transactions(category)
            """)

            # Categories table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    parent_id TEXT,
                    color TEXT NOT NULL,
                    icon TEXT NOT NULL,
                    budget_monthly TEXT,
                    FOREIGN KEY (parent_id) REFERENCES categories(id)
                )
            """)

            # Rules table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rules (
                    id TEXT PRIMARY KEY,
                    pattern TEXT NOT NULL,
                    category_id TEXT NOT NULL,
                    priority INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (category_id) REFERENCES categories(id)
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_rules_priority
                ON rules(priority DESC)
            """)

            conn.commit()

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Access columns by name
        try:
            yield conn
        finally:
            conn.close()

    # ==================== TRANSACTION OPERATIONS ====================

    def insert_transaction(self, transaction: Transaction) -> None:
        """Insert a single transaction into database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO transactions (
                    id, date, description, merchant, amount, balance,
                    account_name, account_number, transaction_type,
                    category, category_confidence, category_confirmed,
                    tags, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                transaction.id,
                transaction.date.isoformat(),
                transaction.description,
                transaction.merchant,
                str(transaction.amount),
                str(transaction.balance) if transaction.balance else None,
                transaction.account_name,
                transaction.account_number,
                transaction.transaction_type,
                transaction.category,
                transaction.category_confidence,
                1 if transaction.category_confirmed else 0,
                ",".join(transaction.tags) if transaction.tags else "",
                transaction.notes,
                transaction.created_at.isoformat(),
                transaction.updated_at.isoformat(),
            ))
            conn.commit()

    def insert_transactions_bulk(self, transactions: List[Transaction]) -> int:
        """
        Insert multiple transactions in bulk.

        Args:
            transactions: List of Transaction objects

        Returns:
            Number of transactions inserted
        """
        inserted = 0
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for txn in transactions:
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO transactions (
                            id, date, description, merchant, amount, balance,
                            account_name, account_number, transaction_type,
                            category, category_confidence, category_confirmed,
                            tags, notes, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        txn.id,
                        txn.date.isoformat(),
                        txn.description,
                        txn.merchant,
                        str(txn.amount),
                        str(txn.balance) if txn.balance else None,
                        txn.account_name,
                        txn.account_number,
                        txn.transaction_type,
                        txn.category,
                        txn.category_confidence,
                        1 if txn.category_confirmed else 0,
                        ",".join(txn.tags) if txn.tags else "",
                        txn.notes,
                        txn.created_at.isoformat(),
                        txn.updated_at.isoformat(),
                    ))
                    if cursor.rowcount > 0:
                        inserted += 1
                except Exception as e:
                    print(f"Warning: Failed to insert transaction {txn.id}: {e}")
                    continue

            conn.commit()

        return inserted

    def get_transaction(self, transaction_id: str) -> Optional[Transaction]:
        """Get a single transaction by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM transactions WHERE id = ?", (transaction_id,))
            row = cursor.fetchone()

            if row is None:
                return None

            return self._row_to_transaction(row)

    def get_transactions(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        account_number: Optional[str] = None,
        category: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Transaction]:
        """
        Query transactions with optional filters.

        Args:
            start_date: Filter transactions on or after this date
            end_date: Filter transactions on or before this date
            account_number: Filter by account number
            category: Filter by category
            limit: Maximum number of results

        Returns:
            List of matching transactions
        """
        query = "SELECT * FROM transactions WHERE 1=1"
        params = []

        if start_date:
            query += " AND date >= ?"
            params.append(start_date.isoformat())

        if end_date:
            query += " AND date <= ?"
            params.append(end_date.isoformat())

        if account_number:
            query += " AND account_number = ?"
            params.append(account_number)

        if category:
            query += " AND category = ?"
            params.append(category)

        query += " ORDER BY date DESC"

        if limit:
            query += f" LIMIT {limit}"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

        return [self._row_to_transaction(row) for row in rows]

    def update_transaction_category(
        self,
        transaction_id: str,
        category: str,
        confirmed: bool = True,
        confidence: float = None
    ) -> None:
        """Update transaction category, confidence, and confirmation status."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE transactions
                SET category = ?, category_confidence = ?, category_confirmed = ?, updated_at = ?
                WHERE id = ?
            """, (category, confidence, 1 if confirmed else 0, datetime.utcnow().isoformat(), transaction_id))
            conn.commit()

    def _row_to_transaction(self, row: sqlite3.Row) -> Transaction:
        """Convert database row to Transaction object."""
        return Transaction(
            id=row["id"],
            date=datetime.fromisoformat(row["date"]).date(),
            description=row["description"],
            merchant=row["merchant"],
            amount=Decimal(row["amount"]),
            balance=Decimal(row["balance"]) if row["balance"] else None,
            account_name=row["account_name"],
            account_number=row["account_number"],
            transaction_type=row["transaction_type"],
            category=row["category"],
            category_confidence=row["category_confidence"],
            category_confirmed=bool(row["category_confirmed"]),
            tags=row["tags"].split(",") if row["tags"] else [],
            notes=row["notes"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    # ==================== CATEGORY OPERATIONS ====================

    def insert_category(self, category: Category) -> None:
        """Insert a category."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO categories (id, name, parent_id, color, icon, budget_monthly)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                category.id,
                category.name,
                category.parent_id,
                category.color,
                category.icon,
                str(category.budget_monthly) if category.budget_monthly else None,
            ))
            conn.commit()

    def get_categories(self) -> List[Category]:
        """Get all categories."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM categories ORDER BY name")
            rows = cursor.fetchall()

        return [self._row_to_category(row) for row in rows]

    def _row_to_category(self, row: sqlite3.Row) -> Category:
        """Convert database row to Category object."""
        return Category(
            id=row["id"],
            name=row["name"],
            parent_id=row["parent_id"],
            color=row["color"],
            icon=row["icon"],
            budget_monthly=Decimal(row["budget_monthly"]) if row["budget_monthly"] else None,
        )

    # ==================== RULE OPERATIONS ====================

    def insert_rule(self, rule: Rule) -> None:
        """Insert a categorization rule."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO rules (id, pattern, category_id, priority, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                rule.id,
                rule.pattern,
                rule.category_id,
                rule.priority,
                rule.created_at.isoformat(),
            ))
            conn.commit()

    def get_rules(self) -> List[Rule]:
        """Get all rules ordered by priority (highest first)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM rules ORDER BY priority DESC")
            rows = cursor.fetchall()

        return [self._row_to_rule(row) for row in rows]

    def _row_to_rule(self, row: sqlite3.Row) -> Rule:
        """Convert database row to Rule object."""
        return Rule(
            id=row["id"],
            pattern=row["pattern"],
            category_id=row["category_id"],
            priority=row["priority"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    # ==================== STATISTICS ====================

    def get_statistics(self) -> dict:
        """Get database statistics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM transactions")
            total_transactions = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM categories")
            total_categories = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM rules")
            total_rules = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COUNT(*) FROM transactions
                WHERE category_confirmed = 1
            """)
            categorized_transactions = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(DISTINCT account_number) FROM transactions")
            total_accounts = cursor.fetchone()[0]

            cursor.execute("""
                SELECT MIN(date), MAX(date) FROM transactions
            """)
            date_range = cursor.fetchone()

        return {
            "total_transactions": total_transactions,
            "total_categories": total_categories,
            "total_rules": total_rules,
            "categorized_transactions": categorized_transactions,
            "total_accounts": total_accounts,
            "earliest_transaction": date_range[0],
            "latest_transaction": date_range[1],
        }
