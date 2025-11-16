#!/usr/bin/env python3
"""
Background AI categorization script (launched from UI).
Tracks progress to file for UI polling.
"""
import sys
from pathlib import Path
from src.data.database import FinanceDatabase
from src.core.categorizer import HybridCategorizer
from src.core.progress_tracker import ProgressTracker
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize tracker at the top so it's always available for error handling
tracker = ProgressTracker()

try:
    # Load database
    DB_PATH = Path("data/finance.db")
    db = FinanceDatabase(DB_PATH)

    # Get uncategorized transactions
    all_transactions = db.get_transactions()
    uncategorized = [t for t in all_transactions if not t.category or t.category == "Uncategorized"]

    if len(uncategorized) == 0:
        # Mark as complete with no work
        tracker.complete(0, 0, 0, 0.0, 0.0)
        print("No uncategorized transactions found.")
        sys.exit(0)

    print(f"Starting AI categorization for {len(uncategorized)} transactions...")

    # Get categorizer
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        tracker.error("ANTHROPIC_API_KEY not found in environment")
        print("ERROR: ANTHROPIC_API_KEY not found. Please set it in .env file.")
        sys.exit(1)

    categorizer = HybridCategorizer(db, ai_api_key=api_key, enable_ai=True)

    # Categorize with progress tracking
    results = categorizer.categorize_batch(
        uncategorized,
        use_ai_fallback=True,
        track_progress=True  # Enable progress tracking!
    )

    # Save results
    print(f"Saving {len(results['results'])} categorized transactions...")
    categorizer.save_transaction_categories(results)
    print("✓ AI categorization complete!")

except KeyboardInterrupt:
    # User cancelled
    tracker.error("Process cancelled by user")
    print("\n⚠ Process cancelled by user")
    sys.exit(1)

except Exception as e:
    # Mark as error
    import traceback
    error_msg = f"{str(e)}\n{traceback.format_exc()}"
    tracker.error(error_msg)
    print(f"❌ Error: {e}")
    print(traceback.format_exc())
    sys.exit(1)
