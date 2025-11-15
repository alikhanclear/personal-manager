"""
Test script for hybrid transaction categorization.

Demonstrates:
1. Rule-based categorization (FREE, instant)
2. AI fallback with Claude Haiku (pennies, smart)
3. Learning system that suggests rules
"""
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.categorizer import HybridCategorizer
from src.core.rule_engine import create_default_rules
from src.data.database import FinanceDatabase
from src.data.models import Category, Transaction
from config.default_categories import DEFAULT_CATEGORIES
from datetime import date
from decimal import Decimal


def setup_test_database(db_path: Path) -> FinanceDatabase:
    """Create test database with categories and rules."""
    # Clean up old database
    if db_path.exists():
        db_path.unlink()

    db = FinanceDatabase(db_path)

    # Insert categories
    print("\n[1] Setting up categories...")
    category_map = {}
    for name, parent_name, color, icon, budget in DEFAULT_CATEGORIES:
        # Find parent ID if exists
        parent_id = None
        if parent_name:
            parent_id = category_map.get(parent_name)

        category = Category(
            name=name,
            parent_id=parent_id,
            color=color,
            icon=icon,
            budget_monthly=Decimal(str(budget)) if budget else None,
        )
        db.insert_category(category)
        category_map[name] = category.name

    categories = db.get_categories()
    print(f"✓ Created {len(categories)} categories")

    # Create default rules
    print("\n[2] Creating default rules...")
    rules = create_default_rules(category_map)
    for rule in rules:
        db.insert_rule(rule)

    print(f"✓ Created {len(rules)} default rules")

    return db


def create_test_transactions() -> list[Transaction]:
    """Create test transactions (some match rules, some don't)."""
    return [
        # RULE MATCHES (should be categorized instantly, FREE)
        Transaction(
            date=date(2025, 1, 10),
            description="TESCO STORES 1234",
            amount=Decimal("-45.67"),
            balance=Decimal("1954.33"),
            account_name="ALIKHAN A",
            account_number="75757512344567",
            transaction_type="POS",
        ),
        Transaction(
            date=date(2025, 1, 10),
            description="STARBUCKS LONDON",
            amount=Decimal("-4.50"),
            balance=Decimal("1949.83"),
            account_name="ALIKHAN A",
            account_number="75757512344567",
            transaction_type="POS",
        ),
        Transaction(
            date=date(2025, 1, 11),
            description="NETFLIX.COM",
            amount=Decimal("-15.99"),
            balance=Decimal("1933.84"),
            account_name="ALIKHAN A",
            account_number="75757512344567",
            transaction_type="DPC",
        ),
        Transaction(
            date=date(2025, 1, 11),
            description="UBER TRIP LONDON",
            amount=Decimal("-12.50"),
            balance=Decimal("1921.34"),
            account_name="ALIKHAN A",
            account_number="75757512344567",
            transaction_type="POS",
        ),
        # NO RULE MATCH (need AI fallback)
        Transaction(
            date=date(2025, 1, 12),
            description="WATERSTONES BOOKSHOP",
            amount=Decimal("-24.99"),
            balance=Decimal("1896.35"),
            account_name="ALIKHAN A",
            account_number="75757512344567",
            transaction_type="POS",
        ),
        Transaction(
            date=date(2025, 1, 12),
            description="LEON RESTAURANT",
            amount=Decimal("-18.75"),
            balance=Decimal("1877.60"),
            account_name="ALIKHAN A",
            account_number="75757512344567",
            transaction_type="POS",
        ),
        Transaction(
            date=date(2025, 1, 13),
            description="DELIVEROO",
            amount=Decimal("-32.40"),
            balance=Decimal("1845.20"),
            account_name="ALIKHAN A",
            account_number="75757512344567",
            transaction_type="POS",
        ),
    ]


def main():
    """Run hybrid categorization test."""
    print("=" * 80)
    print("HYBRID TRANSACTION CATEGORIZATION TEST")
    print("=" * 80)

    # Setup
    test_dir = Path(__file__).parent / "test_data"
    test_dir.mkdir(exist_ok=True)
    db_path = test_dir / "test_categorization.db"

    # Initialize database
    db = setup_test_database(db_path)

    # Create test transactions
    print("\n[3] Creating test transactions...")
    transactions = create_test_transactions()
    inserted = db.insert_transactions_bulk(transactions)
    print(f"✓ Created {inserted} test transactions")

    # Load transactions from database
    all_transactions = db.get_transactions()

    print("\n" + "=" * 80)
    print("TEST 1: RULES ONLY (No AI)")
    print("=" * 80)

    # Test rule-based categorization only
    categorizer = HybridCategorizer(db, enable_ai=False)
    results_no_ai = categorizer.categorize_batch(all_transactions, use_ai_fallback=False)

    print(f"\n✓ Categorization complete!")
    print(f"  Total transactions: {results_no_ai['total']}")
    print(f"  Rule matched: {results_no_ai['rule_matched']} (FREE)")
    print(f"  Uncategorized: {results_no_ai['uncategorized']}")
    print(f"  Total cost: ${results_no_ai['total_cost_usd']:.4f}")

    print("\n📋 Results by transaction:")
    for result in results_no_ai["results"]:
        txn = result["transaction"]
        method = result["method"]
        metadata = result["metadata"]

        status = "✓" if method == "rule" else "✗"
        pattern = metadata.get("matched_pattern", "N/A")

        print(
            f"  {status} {txn.description[:30]:30} → {txn.category:20} "
            f"[{method:4}] {pattern if method == 'rule' else ''}"
        )

    # Check if AI API key is available
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if api_key:
        print("\n" + "=" * 80)
        print("TEST 2: HYBRID (Rules + AI Fallback)")
        print("=" * 80)

        # Test with AI fallback
        categorizer_ai = HybridCategorizer(db, ai_api_key=api_key, enable_ai=True)

        # Reload uncategorized transactions
        uncategorized = [
            result["transaction"]
            for result in results_no_ai["results"]
            if result["method"] == "none"
        ]

        if uncategorized:
            print(f"\n🤖 Using Claude Haiku AI for {len(uncategorized)} uncategorized transactions...")

            # Estimate cost
            cost_estimate = categorizer_ai.ai_engine.estimate_cost(len(uncategorized))
            print(f"\n💰 Estimated cost: ${cost_estimate['estimated_total_cost_usd']:.4f}")
            print(f"   Cost per transaction: ${cost_estimate['cost_per_transaction_usd']:.6f}")
            print(f"   Prompt caching savings: ${cost_estimate['savings_vs_no_cache']:.4f}")

            # Categorize with AI
            results_ai = categorizer_ai.categorize_batch(uncategorized, use_ai_fallback=True)

            print(f"\n✓ AI Categorization complete!")
            print(f"  AI categorized: {results_ai['ai_categorized']}")
            print(f"  Still uncategorized: {results_ai['uncategorized']}")
            print(f"  Actual cost: ${results_ai['total_cost_usd']:.4f}")

            print("\n📋 AI Results:")
            for result in results_ai["results"]:
                txn = result["transaction"]
                method = result["method"]
                metadata = result["metadata"]

                confidence = metadata.get("confidence", 0.0)
                reasoning = metadata.get("reasoning", "N/A")

                print(
                    f"  🤖 {txn.description[:30]:30} → {txn.category:20} "
                    f"({confidence:.0%} confidence)"
                )
                print(f"     Reasoning: {reasoning}")

                # Suggest rule
                if method == "ai" and confidence > 0.7:
                    suggested_rule = categorizer_ai.suggest_rule_from_transaction(
                        txn, txn.category
                    )
                    print(f"     💡 Suggested rule: '{suggested_rule.pattern}' → {suggested_rule.category_id}")

        else:
            print("\n✓ All transactions matched rules! No AI needed.")

    else:
        print("\n" + "=" * 80)
        print("⚠️  ANTHROPIC_API_KEY not set - skipping AI test")
        print("=" * 80)
        print("\nTo test AI categorization:")
        print("  1. Get API key from: https://console.anthropic.com/")
        print("  2. Set environment variable:")
        print("     export ANTHROPIC_API_KEY='your-api-key'")
        print("  3. Re-run this script")

    # Final statistics
    print("\n" + "=" * 80)
    print("FINAL STATISTICS")
    print("=" * 80)

    stats = categorizer.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\n" + "=" * 80)
    print("TEST COMPLETE!")
    print("=" * 80)
    print(f"\n✓ Database saved at: {db_path}")
    print("\nKey Takeaways:")
    print("  • Rules handle common transactions (FREE, instant)")
    print("  • AI handles edge cases (pennies, smart)")
    print("  • System learns and improves over time")
    print("  • Estimated cost: $0.10-0.50 per 1000 transactions")


if __name__ == "__main__":
    main()
