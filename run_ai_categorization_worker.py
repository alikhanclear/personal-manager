"""
Background worker for AI categorization with progress tracking.
This runs independently from the Dash app to enable live progress updates.
"""
import sys
from pathlib import Path
import argparse

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.data.database import FinanceDatabase
from src.core.categorizer import HybridCategorizer
from src.utils.progress_tracker import ProgressTracker
import os

def main():
    """Run AI categorization with progress tracking."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Background AI categorization worker')
    parser.add_argument('--account', type=str, default=None,
                       help='Account number to process (default: all accounts)')
    args = parser.parse_args()

    selected_account = args.account
    account_label = selected_account or "All Accounts"

    # Initialize database
    db = FinanceDatabase("data/finance.db")

    # Get uncategorized transactions FILTERED BY ACCOUNT
    all_transactions = db.get_transactions(account_number=selected_account)
    uncategorized = [
        t for t in all_transactions
        if (not t.category or t.category == "Uncategorized")
        and not (t.category_confidence and t.category_confidence >= 1.0)
        and not t.category_confirmed
    ]

    if len(uncategorized) == 0:
        print(f"No uncategorized transactions found for {account_label}.")
        return

    # Check API key
    api_key = os.getenv("APP_ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: APP_ANTHROPIC_API_KEY not found in environment")
        return

    # Create categorizer and progress tracker
    categorizer = HybridCategorizer(db, api_key=api_key)
    progress_tracker = ProgressTracker()
    progress_tracker.clear()

    print(f"Starting AI categorization for {len(uncategorized)} transactions ({account_label})...")

    try:
        # Run categorization with progress tracking
        results = categorizer.categorize_batch(
            uncategorized,
            use_ai_fallback=True,
            ai_batch_size=30,
            progress_tracker=progress_tracker
        )

        # Save results
        categorizer.save_transaction_categories(results)

        print(f"✓ Categorization complete for {account_label}!")
        print(f"  - Rule matched: {results['rule_matched']}")
        print(f"  - AI categorized: {results['ai_categorized']}")
        print(f"  - Uncategorized: {results['uncategorized']}")

    except Exception as e:
        print(f"ERROR: {e}")
        progress_tracker.error(str(e))
        raise

if __name__ == "__main__":
    main()
