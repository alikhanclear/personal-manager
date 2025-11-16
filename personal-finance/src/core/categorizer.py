"""
Hybrid transaction categorization system.

Combines rule-based matching (free, instant) with AI fallback (pennies, smart).
"""
import time
from typing import List, Optional, Tuple

from ..data.database import FinanceDatabase
from ..data.models import Category, Rule, Transaction
from ..ml.ai_categorizer import ClaudeCategorizationEngine
from .rule_engine import RuleEngine


class HybridCategorizer:
    """
    Hybrid categorization system: Rules first, AI fallback.

    Strategy:
    1. Try rule-based matching (FREE, instant)
    2. If no match, use Claude Haiku AI (pennies, <1 second)
    3. Optionally suggest new rules from AI results (learning system)
    """

    def __init__(
        self,
        database: FinanceDatabase,
        ai_api_key: Optional[str] = None,
        enable_ai: bool = True,
    ):
        """
        Initialize hybrid categorizer.

        Args:
            database: FinanceDatabase instance
            ai_api_key: Anthropic API key (optional, for AI fallback)
            enable_ai: Whether to enable AI fallback (default True)
        """
        self.database = database
        self.enable_ai = enable_ai

        # Load rules and categories from database
        self.rules = database.get_rules()
        self.categories = database.get_categories()

        # Initialize engines
        self.rule_engine = RuleEngine(self.rules)

        if self.enable_ai and ai_api_key:
            self.ai_engine = ClaudeCategorizationEngine(
                categories=self.categories, api_key=ai_api_key
            )
        else:
            self.ai_engine = None

    def categorize_transaction(
        self, transaction: Transaction, use_ai_fallback: bool = True
    ) -> Tuple[Transaction, str, dict]:
        """
        Categorize a single transaction.

        Args:
            transaction: Transaction to categorize
            use_ai_fallback: Whether to use AI if rules don't match

        Returns:
            Tuple of (updated_transaction, method_used, metadata)
            - method_used: "rule", "ai", or "none"
            - metadata: Additional info (pattern matched, confidence, etc.)
        """
        # Skip if already confirmed
        if transaction.category_confirmed:
            return transaction, "already_confirmed", {}

        # Step 1: Try rule matching (FREE)
        rule_match = self.rule_engine.match_transaction(transaction)

        if rule_match:
            category_id, pattern, priority = rule_match
            transaction.category = category_id
            transaction.category_confidence = 1.0  # Rule = 100% confidence
            transaction.category_confirmed = False  # Still needs user review

            metadata = {
                "matched_pattern": pattern,
                "rule_priority": priority,
                "cost_usd": 0.0,  # FREE!
            }

            return transaction, "rule", metadata

        # Step 2: Try AI fallback (if enabled and available)
        if use_ai_fallback and self.ai_engine:
            category, confidence, reasoning = self.ai_engine.categorize_transaction(
                transaction
            )

            transaction.category = category
            transaction.category_confidence = confidence
            transaction.category_confirmed = False  # Needs user review

            metadata = {
                "reasoning": reasoning,
                "confidence": confidence,
                "cost_usd": 0.0001,  # Rough estimate per transaction
            }

            return transaction, "ai", metadata

        # Step 3: No match found
        transaction.category = "Uncategorized"
        transaction.category_confidence = 0.0
        transaction.category_confirmed = False

        return transaction, "none", {}

    def categorize_batch(
        self, transactions: List[Transaction], use_ai_fallback: bool = True
    ) -> dict:
        """
        Categorize a batch of transactions.

        Args:
            transactions: List of transactions to categorize
            use_ai_fallback: Whether to use AI for unmatched transactions

        Returns:
            Dictionary with categorization statistics
        """
        stats = {
            "total": len(transactions),
            "rule_matched": 0,
            "ai_categorized": 0,
            "uncategorized": 0,
            "already_confirmed": 0,
            "total_cost_usd": 0.0,
            "results": [],
        }

        # Rate limiting: 45 requests/minute (buffer for 50/min limit)
        # = 1.33 seconds between requests
        AI_DELAY = 1.4  # seconds between AI requests

        for i, txn in enumerate(transactions, 1):
            # Show progress every 50 transactions
            if i % 50 == 0 or i == 1:
                print(f"Processing {i}/{len(transactions)} transactions... "
                      f"(Rules: {stats['rule_matched']}, AI: {stats['ai_categorized']})")

            updated_txn, method, metadata = self.categorize_transaction(
                txn, use_ai_fallback=use_ai_fallback
            )

            if method == "rule":
                stats["rule_matched"] += 1
            elif method == "ai":
                stats["ai_categorized"] += 1
                stats["total_cost_usd"] += metadata.get("cost_usd", 0.0)
                # Rate limit AI requests to avoid 429 errors
                if use_ai_fallback and i < len(transactions):
                    time.sleep(AI_DELAY)
            elif method == "already_confirmed":
                stats["already_confirmed"] += 1
            else:
                stats["uncategorized"] += 1

            stats["results"].append(
                {
                    "transaction": updated_txn,
                    "method": method,
                    "metadata": metadata,
                }
            )

        return stats

    def suggest_rule_from_transaction(
        self, transaction: Transaction, category: str
    ) -> Rule:
        """
        Suggest a rule based on a categorized transaction.

        Extracts key parts of description to create reusable pattern.

        Args:
            transaction: Transaction that was categorized
            category: Category it was assigned to

        Returns:
            Suggested Rule object (not yet saved to database)
        """
        # Extract key merchant identifier from description
        # Simple approach: Take first word or recognizable pattern
        description = transaction.description.upper()

        # Remove common prefixes/suffixes
        cleaned = description
        for prefix in ["POS ", "DPC ", "BAC ", "TFR "]:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix) :]

        # Take first significant word/phrase
        words = cleaned.split()
        if words:
            # Use first 1-2 words as pattern
            if len(words) == 1:
                pattern = words[0]
            else:
                # Check if second word is numeric (like "TESCO 1234")
                if words[1].isdigit():
                    pattern = words[0]
                else:
                    pattern = " ".join(words[:2])
        else:
            pattern = description[:20]  # Fallback

        # Find category ID
        category_obj = next((c for c in self.categories if c.name == category), None)
        category_id = category_obj.name if category_obj else "Uncategorized"

        return Rule(
            pattern=pattern,
            category_id=category_id,
            priority=5,  # Default medium priority
        )

    def save_transaction_categories(
        self, categorization_results: dict
    ) -> int:
        """
        Save categorization results to database.

        Args:
            categorization_results: Results from categorize_batch()

        Returns:
            Number of transactions updated
        """
        updated = 0

        for result in categorization_results["results"]:
            txn = result["transaction"]
            try:
                self.database.update_transaction_category(
                    transaction_id=txn.id,
                    category=txn.category,
                    confirmed=txn.category_confirmed,
                    confidence=txn.category_confidence,
                )
                updated += 1
            except Exception as e:
                print(f"Failed to update transaction {txn.id}: {e}")

        return updated

    def get_statistics(self) -> dict:
        """Get categorization statistics."""
        db_stats = self.database.get_statistics()

        rule_coverage = 0
        if db_stats["total_transactions"] > 0:
            rule_coverage = (
                db_stats["categorized_transactions"] / db_stats["total_transactions"]
            ) * 100

        return {
            "total_rules": len(self.rules),
            "total_categories": len(self.categories),
            "total_transactions": db_stats["total_transactions"],
            "categorized_transactions": db_stats["categorized_transactions"],
            "rule_coverage_percent": round(rule_coverage, 1),
            "ai_enabled": self.enable_ai and self.ai_engine is not None,
        }


def quick_categorize_file(
    csv_file_path: str,
    db_path: str = "finance.db",
    ai_api_key: Optional[str] = None,
    use_ai: bool = True,
) -> dict:
    """
    Quick helper to import and categorize a CSV file.

    Args:
        csv_file_path: Path to NatWest CSV file
        db_path: Path to SQLite database
        ai_api_key: Anthropic API key for AI categorization
        use_ai: Whether to enable AI fallback

    Returns:
        Categorization statistics
    """
    from ..data.importer import TransactionImporter
    from ..data.csv_parser import NatWestParser

    # Import file
    db = FinanceDatabase(db_path)
    importer = TransactionImporter(db)
    import_result = importer.import_natwest_csv(csv_file_path)

    # Categorize
    categorizer = HybridCategorizer(db, ai_api_key=ai_api_key, enable_ai=use_ai)
    transactions = db.get_transactions(limit=import_result["total_inserted"])
    results = categorizer.categorize_batch(transactions, use_ai_fallback=use_ai)

    # Save
    categorizer.save_transaction_categories(results)

    return {
        "import": import_result,
        "categorization": results,
        "statistics": categorizer.get_statistics(),
    }
