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

try:
    # Load database
    DB_PATH = Path("data/finance.db")
    db = FinanceDatabase(DB_PATH)

    # Get uncategorized transactions
    all_transactions = db.get_transactions()
    uncategorized = [t for t in all_transactions if not t.category or t.category == "Uncategorized"]

    if len(uncategorized) == 0:
        # Mark as complete with no work
        tracker = ProgressTracker()
        tracker.complete(0, 0, 0, 0.0, 0.0)
        sys.exit(0)

    # Get categorizer
    api_key = os.getenv("ANTHROPIC_API_KEY")
    categorizer = HybridCategorizer(db, ai_api_key=api_key, enable_ai=bool(api_key))

    # Categorize with progress tracking
    results = categorizer.categorize_batch(
        uncategorized,
        use_ai_fallback=bool(api_key),
        track_progress=True  # Enable progress tracking!
    )

    # Save results
    categorizer.save_transaction_categories(results)

except Exception as e:
    # Mark as error
    tracker = ProgressTracker()
    tracker.error(str(e))
    sys.exit(1)
