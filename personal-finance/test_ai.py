#!/usr/bin/env python3
"""
Quick test script to verify AI categorization is working.
"""
import os
from dotenv import load_dotenv
from src.data.database import FinanceDatabase
from src.ml.ai_categorizer import ClaudeCategorizationEngine

# Load environment variables
load_dotenv()

def test_ai_categorization():
    """Test AI categorization on a few transactions."""

    # Check API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ERROR: ANTHROPIC_API_KEY not found in environment!")
        print("   Please set it in your .env file")
        return

    print(f"✓ API Key found: {api_key[:8]}...{api_key[-4:]}")

    # Initialize database
    db = FinanceDatabase()

    # Get categories
    categories = db.get_all_categories()
    print(f"✓ Loaded {len(categories)} categories")

    # Get a few uncategorized transactions
    uncategorized = db.get_uncategorized_transactions(limit=3)

    if not uncategorized:
        print("\n⚠️  No uncategorized transactions found in database!")
        print("   Try importing some transactions first.")
        return

    print(f"\n✓ Found {len(uncategorized)} uncategorized transactions to test\n")

    # Initialize AI engine
    print("Initializing Claude AI engine...")
    ai_engine = ClaudeCategorizationEngine(categories=categories, api_key=api_key)
    print(f"✓ Using model: {ai_engine.model}\n")

    # Test categorization
    print("=" * 70)
    print("TESTING AI CATEGORIZATION")
    print("=" * 70)

    for i, txn in enumerate(uncategorized, 1):
        print(f"\n[Test {i}/{len(uncategorized)}]")
        print(f"  Description: {txn.description}")
        print(f"  Amount: £{txn.amount}")
        print(f"  Date: {txn.date}")
        print(f"\n  Categorizing...")

        try:
            category, confidence, reasoning = ai_engine.categorize_transaction(txn)

            print(f"  ✅ SUCCESS!")
            print(f"     Category: {category}")
            print(f"     Confidence: {confidence:.0%}")
            print(f"     Reasoning: {reasoning}")

        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            return

    print("\n" + "=" * 70)
    print("✅ AI CATEGORIZATION TEST PASSED!")
    print("=" * 70)
    print("\nThe AI is working correctly. You can now:")
    print("  1. Run 'python categorize_all.py' to categorize all transactions")
    print("  2. Or use the web UI to categorize interactively")

if __name__ == "__main__":
    test_ai_categorization()
