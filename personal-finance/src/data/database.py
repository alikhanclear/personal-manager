"""
SQLite database manager for personal finance application.
"""
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import List, Optional, Tuple

from .models import Category, Rule, Transaction, PotentialDuplicate


class FinanceDatabase:
    """SQLite database manager for transactions, categories, and rules."""

    def __init__(self, db_path: str | Path = "finance.db"):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self._cleanup_stale_journals()  # Clean up before init
        self._init_database()
        self._enable_wal_mode()  # Enable WAL for better concurrency

    def _cleanup_stale_journals(self) -> None:
        """
        Clean up stale journal files on startup.

        Journal files can remain if a transaction was interrupted.
        Removing them allows the database to recover properly.
        """
        journal_path = Path(f"{self.db_path}-journal")
        if journal_path.exists():
            try:
                journal_path.unlink()
                print(f"[CLEANUP] Removed stale journal file: {journal_path.name}")
            except Exception as e:
                print(f"[WARNING] Could not remove journal file: {e}")

    def _enable_wal_mode(self) -> None:
        """
        Enable Write-Ahead Logging (WAL) mode for better concurrency.

        Benefits:
        - Readers don't block writers
        - Writers don't block readers
        - Better performance for concurrent access
        - No more "database is locked" errors
        """
        with self._get_connection() as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.commit()
            print("[DATABASE] WAL mode enabled")

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

            # Potential duplicates table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS potential_duplicates (
                    id TEXT PRIMARY KEY,
                    transaction_id TEXT NOT NULL,
                    date TEXT NOT NULL,
                    description TEXT NOT NULL,
                    amount TEXT NOT NULL,
                    balance TEXT,
                    account_name TEXT NOT NULL,
                    account_number TEXT NOT NULL,
                    detected_at TEXT NOT NULL,
                    resolution TEXT,
                    resolved_at TEXT
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_duplicates_resolution
                ON potential_duplicates(resolution)
            """)

            conn.commit()

    @contextmanager
    def _get_connection(self):
        """
        Context manager for database connections with improved error handling.

        Features:
        - 30 second timeout (increased from default 5s)
        - Row factory for column name access
        - Automatic rollback on errors
        - Proper connection cleanup
        """
        conn = sqlite3.connect(
            self.db_path,
            timeout=30.0,  # 30 seconds (up from 5s default)
            isolation_level=None  # Autocommit mode for WAL
        )
        conn.row_factory = sqlite3.Row  # Access columns by name
        try:
            yield conn
        except Exception as e:
            # Rollback on error (even in autocommit, this helps cleanup)
            try:
                conn.rollback()
            except:
                pass
            raise  # Re-raise the original exception
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

    def insert_transactions_bulk(self, transactions: List[Transaction]) -> dict:
        """
        Insert multiple transactions in bulk, flagging duplicates for review.

        Args:
            transactions: List of Transaction objects

        Returns:
            Dictionary with insertion statistics:
            - inserted: Number of new transactions inserted
            - duplicates: Number of potential duplicates flagged
        """
        inserted = 0
        duplicates = 0

        with self._get_connection() as conn:
            cursor = conn.cursor()
            for txn in transactions:
                try:
                    # Check if transaction ID already exists
                    cursor.execute("SELECT COUNT(*) FROM transactions WHERE id = ?", (txn.id,))
                    exists = cursor.fetchone()[0] > 0

                    if exists:
                        # Transaction with same ID exists - flag as potential duplicate
                        duplicate = PotentialDuplicate(
                            transaction_id=txn.id,
                            date=txn.date,
                            description=txn.description,
                            amount=txn.amount,
                            balance=txn.balance,
                            account_name=txn.account_name,
                            account_number=txn.account_number,
                        )
                        self.insert_potential_duplicate(duplicate)
                        duplicates += 1
                    else:
                        # New transaction - insert normally
                        cursor.execute("""
                            INSERT INTO transactions (
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
                        inserted += 1

                except Exception as e:
                    print(f"Warning: Failed to process transaction {txn.id}: {e}")
                    continue

            conn.commit()

        return {"inserted": inserted, "duplicates": duplicates}

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

    def update_rule(self, rule_id: str, pattern: str, category_id: str, priority: int) -> None:
        """Update an existing rule."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE rules
                SET pattern = ?, category_id = ?, priority = ?
                WHERE id = ?
            """, (pattern, category_id, priority, rule_id))
            conn.commit()

    def delete_rule(self, rule_id: str) -> None:
        """Delete a rule by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM rules WHERE id = ?", (rule_id,))
            conn.commit()

    def import_rules(self, rules: List[Rule]) -> tuple[int, int]:
        """
        Import rules in APPEND mode (keep existing rules, add new ones).
        Skips duplicates (same pattern + category).

        Args:
            rules: List of Rule objects to import

        Returns:
            Tuple of (inserted_count, skipped_count)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            inserted = 0
            skipped = 0

            for rule in rules:
                # Check if rule already exists (same pattern + category)
                cursor.execute("""
                    SELECT COUNT(*) FROM rules
                    WHERE pattern = ? AND category_id = ?
                """, (rule.pattern, rule.category_id))

                exists = cursor.fetchone()[0] > 0

                if not exists:
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
                    inserted += 1
                else:
                    skipped += 1

            conn.commit()

        return (inserted, skipped)

    def replace_all_rules(self, rules: List[Rule]) -> int:
        """
        Replace ALL existing rules with new rules.
        WARNING: This deletes all existing rules first.

        Args:
            rules: List of Rule objects to import

        Returns:
            Number of rules inserted
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Delete all existing rules
            cursor.execute("DELETE FROM rules")

            # Insert new rules
            for rule in rules:
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

        return len(rules)

    def delete_all_transactions(self, account_number: Optional[str] = None) -> dict:
        """
        Delete transactions from database (preserves categories and rules).

        Args:
            account_number: Optional account number to filter by.
                           If None, deletes ALL transactions (dangerous!)
                           If provided, only deletes transactions for that account

        Returns:
            Dictionary with deletion counts:
            {
                'transactions': int,  # Number of transactions deleted
                'duplicates': int     # Number of potential duplicates deleted
            }

        Example:
            # Delete transactions for specific account
            result = db.delete_all_transactions('12345678')
            # result = {'transactions': 523, 'duplicates': 12}

            # Delete ALL transactions (use with caution!)
            result = db.delete_all_transactions()
            # result = {'transactions': 5230, 'duplicates': 120}
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Build WHERE clause for account filtering
            where_clause = "WHERE account_number = ?" if account_number else ""
            params = [account_number] if account_number else []

            # Count transactions to be deleted
            cursor.execute(f"SELECT COUNT(*) FROM transactions {where_clause}", params)
            txn_count = cursor.fetchone()[0]

            # Count duplicates to be deleted
            cursor.execute(f"SELECT COUNT(*) FROM potential_duplicates {where_clause}", params)
            dup_count = cursor.fetchone()[0]

            # Delete from both tables
            cursor.execute(f"DELETE FROM transactions {where_clause}", params)
            cursor.execute(f"DELETE FROM potential_duplicates {where_clause}", params)

            conn.commit()

        return {
            'transactions': txn_count,
            'duplicates': dup_count
        }

    # ==================== POTENTIAL DUPLICATE OPERATIONS ====================

    def insert_potential_duplicate(self, duplicate: PotentialDuplicate) -> None:
        """Insert a potential duplicate transaction."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO potential_duplicates (
                    id, transaction_id, date, description, amount, balance,
                    account_name, account_number, detected_at, resolution, resolved_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                duplicate.id,
                duplicate.transaction_id,
                duplicate.date.isoformat(),
                duplicate.description,
                str(duplicate.amount),
                str(duplicate.balance) if duplicate.balance else None,
                duplicate.account_name,
                duplicate.account_number,
                duplicate.detected_at.isoformat(),
                duplicate.resolution,
                duplicate.resolved_at.isoformat() if duplicate.resolved_at else None,
            ))
            conn.commit()

    def get_potential_duplicates(self, include_resolved: bool = False) -> List[PotentialDuplicate]:
        """
        Get all potential duplicates.

        Args:
            include_resolved: If True, include already resolved duplicates

        Returns:
            List of PotentialDuplicate objects
        """
        query = "SELECT * FROM potential_duplicates"
        if not include_resolved:
            query += " WHERE resolution IS NULL"
        query += " ORDER BY detected_at DESC"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()

        return [self._row_to_potential_duplicate(row) for row in rows]

    def resolve_duplicate(self, duplicate_id: str, resolution: str) -> None:
        """
        Mark a potential duplicate as resolved.

        Args:
            duplicate_id: ID of the duplicate record
            resolution: 'keep_both', 'keep_original', or 'dismissed'
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE potential_duplicates
                SET resolution = ?, resolved_at = ?
                WHERE id = ?
            """, (resolution, datetime.utcnow().isoformat(), duplicate_id))
            conn.commit()

    def keep_both_duplicate(self, duplicate_id: str) -> None:
        """
        Keep both transactions - insert the duplicate as a new transaction.

        Args:
            duplicate_id: ID of the duplicate record
        """
        # Get the duplicate record
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM potential_duplicates WHERE id = ?", (duplicate_id,))
            row = cursor.fetchone()

            if not row:
                return

            # Create new transaction with different ID (add timestamp to make unique)
            new_txn = Transaction(
                id="",  # Will be regenerated with different hash
                date=datetime.fromisoformat(row["date"]).date(),
                description=f"{row['description']} [DUPLICATE-{row['id'][:8]}]",  # Modify desc to create unique hash
                amount=Decimal(row["amount"]),
                balance=Decimal(row["balance"]) if row["balance"] else None,
                account_name=row["account_name"],
                account_number=row["account_number"],
            )

            # Insert the new transaction
            self.insert_transaction(new_txn)

            # Mark as resolved
            self.resolve_duplicate(duplicate_id, "keep_both")

    def _row_to_potential_duplicate(self, row: sqlite3.Row) -> PotentialDuplicate:
        """Convert database row to PotentialDuplicate object."""
        return PotentialDuplicate(
            id=row["id"],
            transaction_id=row["transaction_id"],
            date=datetime.fromisoformat(row["date"]).date(),
            description=row["description"],
            amount=Decimal(row["amount"]),
            balance=Decimal(row["balance"]) if row["balance"] else None,
            account_name=row["account_name"],
            account_number=row["account_number"],
            detected_at=datetime.fromisoformat(row["detected_at"]),
            resolution=row["resolution"],
            resolved_at=datetime.fromisoformat(row["resolved_at"]) if row["resolved_at"] else None,
        )

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

    def get_statistics(self, account_number: Optional[str] = None) -> dict:
        """
        Get database statistics, optionally filtered by account.

        Args:
            account_number: Optional account number to filter by (None = all accounts)

        Returns:
            Dictionary of statistics
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Build conditional WHERE clause for account filtering
            where_clause = "WHERE account_number = ?" if account_number else ""
            params = [account_number] if account_number else []

            cursor.execute(f"SELECT COUNT(*) FROM transactions {where_clause}", params)
            total_transactions = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM categories")
            total_categories = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM rules")
            total_rules = cursor.fetchone()[0]

            cursor.execute(f"""
                SELECT COUNT(*) FROM transactions
                {where_clause}{"AND" if account_number else "WHERE"} category_confirmed = 1
            """, params)
            categorized_transactions = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(DISTINCT account_number) FROM transactions")
            total_accounts = cursor.fetchone()[0]

            cursor.execute(f"""
                SELECT MIN(date), MAX(date) FROM transactions
                {where_clause}
            """, params)
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

    def get_unique_accounts(self) -> List[Tuple[str, str]]:
        """
        Get all unique accounts in database, ordered by account name.

        Returns:
            List of (account_number, account_name) tuples
            Example: [('12345678', 'Current Account'), ('87654321', 'Savings Account')]
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT account_number, account_name
                FROM transactions
                WHERE account_number IS NOT NULL
                ORDER BY account_name ASC
            """)
            rows = cursor.fetchall()

        return [(row['account_number'], row['account_name']) for row in rows]

    def get_latest_transaction_per_account(self) -> List[dict]:
        """
        Get earliest and latest transaction dates for each account.

        This helps users understand the full date range of their data
        before importing new CSV files, enabling smarter import workflow
        and minimizing duplicate reviews.

        Returns:
            List of dicts with account info and transaction date range:
            [
                {
                    'account_name': 'Current Account',
                    'account_number': '12345678',
                    'earliest_date': '2024-01-01',  # ISO format date string
                    'latest_date': '2025-01-15',  # ISO format date string
                    'transaction_count': 1523
                },
                ...
            ]

        Example:
            >>> db.get_latest_transaction_per_account()
            [
                {
                    'account_name': 'Current Account',
                    'account_number': '12345678',
                    'earliest_date': '2024-01-01',
                    'latest_date': '2025-01-15',
                    'transaction_count': 1523
                },
                {
                    'account_name': 'Savings Account',
                    'account_number': '87654321',
                    'earliest_date': '2024-01-05',
                    'latest_date': '2025-01-10',
                    'transaction_count': 245
                }
            ]
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    account_name,
                    account_number,
                    MIN(date) as earliest_date,
                    MAX(date) as latest_date,
                    COUNT(*) as transaction_count
                FROM transactions
                WHERE account_number IS NOT NULL
                GROUP BY account_name, account_number
                ORDER BY account_name
            """)

            results = []
            for row in cursor.fetchall():
                results.append({
                    'account_name': row['account_name'],
                    'account_number': row['account_number'],
                    'earliest_date': row['earliest_date'],
                    'latest_date': row['latest_date'],
                    'transaction_count': row['transaction_count']
                })

            return results
