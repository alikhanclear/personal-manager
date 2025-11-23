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

            # Convert category_id (UUID) to category name for display
            category_obj = next((c for c in self.categories if c.id == category_id), None)
            category_name = category_obj.name if category_obj else "Uncategorized"

            transaction.category = category_name
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
        self, transactions: List[Transaction], use_ai_fallback: bool = True,
        ai_batch_size: int = 30, force_recategorize: bool = False
    ) -> dict:
        """
        Categorize a batch of transactions with intelligent batching.

        Args:
            transactions: List of transactions to categorize
            use_ai_fallback: Whether to use AI for unmatched transactions
            ai_batch_size: Number of transactions to send to AI per API call (default: 30)
            force_recategorize: If True, recategorize ALL transactions including confirmed ones (default: False)

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

        import time
        start_time = time.time()

        # STEP 1: Apply rules to all transactions (fast, free)
        mode_msg = "FORCE MODE - Including confirmed" if force_recategorize else "Normal mode - Protecting confirmed"
        print(f"\n=== STEP 1: Applying rules to {len(transactions)} transactions ({mode_msg}) ===")
        uncategorized_for_ai = []

        for i, txn in enumerate(transactions, 1):
            # Skip if already confirmed (unless force mode is enabled)
            if txn.category_confirmed and not force_recategorize:
                stats["already_confirmed"] += 1
                stats["results"].append({
                    "transaction": txn,
                    "method": "already_confirmed",
                    "metadata": {},
                })
                continue

            # Try rule matching
            rule_match = self.rule_engine.match_transaction(txn)

            if rule_match:
                category_id, pattern, priority = rule_match

                # Convert category_id (UUID) to category name for display
                category_obj = next((c for c in self.categories if c.id == category_id), None)
                category_name = category_obj.name if category_obj else "Uncategorized"

                txn.category = category_name
                txn.category_confidence = 1.0
                txn.category_confirmed = False
                stats["rule_matched"] += 1
                stats["results"].append({
                    "transaction": txn,
                    "method": "rule",
                    "metadata": {
                        "matched_pattern": pattern,
                        "rule_priority": priority,
                        "cost_usd": 0.0,
                    },
                })
            else:
                # No rule match - queue for AI
                uncategorized_for_ai.append(txn)

        print(f"[OK] Rules matched: {stats['rule_matched']}")
        print(f"-> Need AI categorization: {len(uncategorized_for_ai)}")

        # STEP 2: Batch AI categorization for unmatched transactions
        if use_ai_fallback and self.ai_engine and len(uncategorized_for_ai) > 0:
            print(f"\n=== STEP 2: AI Categorization (batches of {ai_batch_size}) ===")

            # Split into batches
            num_batches = (len(uncategorized_for_ai) + ai_batch_size - 1) // ai_batch_size

            for batch_idx in range(num_batches):
                batch_start = batch_idx * ai_batch_size
                batch_end = min(batch_start + ai_batch_size, len(uncategorized_for_ai))
                batch_txns = uncategorized_for_ai[batch_start:batch_end]

                print(f"\nBatch {batch_idx + 1}/{num_batches}: Processing {len(batch_txns)} transactions...")

                try:
                    # Call batch AI categorization
                    batch_results = self.ai_engine.categorize_transactions_batch(batch_txns)

                    # Apply results
                    for txn, (category, confidence, reasoning) in zip(batch_txns, batch_results):
                        txn.category = category
                        txn.category_confidence = confidence
                        txn.category_confirmed = False

                        if category != "Uncategorized":
                            stats["ai_categorized"] += 1
                        else:
                            stats["uncategorized"] += 1

                        stats["total_cost_usd"] += 0.0001  # Rough estimate per transaction
                        stats["results"].append({
                            "transaction": txn,
                            "method": "ai",
                            "metadata": {
                                "reasoning": reasoning,
                                "confidence": confidence,
                                "cost_usd": 0.0001,
                            },
                        })

                    print(f"[OK] Batch {batch_idx + 1} complete: {len(batch_txns)} transactions categorized")

                except Exception as e:
                    print(f"[ERROR] Batch {batch_idx + 1} failed: {e}")
                    # Mark all in batch as uncategorized
                    for txn in batch_txns:
                        txn.category = "Uncategorized"
                        txn.category_confidence = 0.0
                        txn.category_confirmed = False
                        stats["uncategorized"] += 1
                        stats["results"].append({
                            "transaction": txn,
                            "method": "error",
                            "metadata": {"error": str(e)},
                        })

                # Rate limit between batches (1.4s delay)
                if batch_idx < num_batches - 1:
                    time.sleep(1.4)

        else:
            # No AI - mark remaining as uncategorized
            for txn in uncategorized_for_ai:
                txn.category = "Uncategorized"
                txn.category_confidence = 0.0
                txn.category_confirmed = False
                stats["uncategorized"] += 1
                stats["results"].append({
                    "transaction": txn,
                    "method": "none",
                    "metadata": {},
                })

        elapsed_secs = time.time() - start_time
        print(f"\n=== COMPLETE ===")
        print(f"Total time: {elapsed_secs:.1f}s")
        print(f"Rule matched: {stats['rule_matched']}")
        print(f"AI categorized: {stats['ai_categorized']}")
        print(f"Uncategorized: {stats['uncategorized']}")
        print(f"Cost: ${stats['total_cost_usd']:.4f}")

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
        category_id = category_obj.id if category_obj else "Uncategorized"

        return Rule(
            pattern=pattern,
            category_id=category_id,
            priority=15,  # Higher than default rules (10) so user rules win
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
