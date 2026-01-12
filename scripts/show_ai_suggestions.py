"""
Show AI-suggested transactions (edge cases that didn't match rules).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.database import FinanceDatabase

def show_ai_suggestions():
    """Show AI-suggested transactions."""

    db = FinanceDatabase('data/finance.db')

    # Get all transactions
    all_transactions = db.get_transactions()

    # Filter for AI suggestions (confidence < 1.0)
    ai_suggested = [
        txn for txn in all_transactions
        if txn.category and not txn.category_confirmed and txn.category_confidence < 1.0
    ]

    print("=" * 80)
    print("AI-SUGGESTED TRANSACTIONS (Edge Cases)")
    print("=" * 80)
    print(f"\nTotal: {len(ai_suggested)} transactions\n")
    print("These didn't match any rules and were categorized by AI.\n")

    # Group by category to show patterns
    by_category = {}
    for txn in ai_suggested:
        cat = txn.category or "Unknown"
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(txn)

    print("=" * 80)
    print("BREAKDOWN BY AI-SUGGESTED CATEGORY")
    print("=" * 80)
    for cat in sorted(by_category.keys()):
        print(f"\n{cat}: {len(by_category[cat])} transactions")

    # Show first 25 examples
    print("\n" + "=" * 80)
    print("SAMPLE TRANSACTIONS (First 25)")
    print("=" * 80)
    for i, txn in enumerate(ai_suggested[:25], 1):
        desc = txn.description[:50] + "..." if len(txn.description) > 50 else txn.description
        conf = txn.category_confidence or 0.0
        cat = txn.category or "Unknown"
        print(f"{i:2}. {cat:20} | {conf:4.0%} | £{txn.amount:8.2f} | {desc}")

    if len(ai_suggested) > 25:
        print(f"\n... and {len(ai_suggested) - 25} more")

    # Show unique merchant patterns
    print("\n" + "=" * 80)
    print("UNIQUE MERCHANT PATTERNS (First 30)")
    print("=" * 80)

    # Extract unique starting words/patterns
    patterns = set()
    for txn in ai_suggested:
        # Get first 3 words or first 20 chars
        words = txn.description.split()
        if len(words) >= 3:
            pattern = ' '.join(words[:3])
        else:
            pattern = txn.description[:20]
        patterns.add(pattern.upper())

    for i, pattern in enumerate(sorted(patterns)[:30], 1):
        print(f"{i:2}. {pattern}")

    if len(patterns) > 30:
        print(f"\n... and {len(patterns) - 30} more unique patterns")

    print("\n" + "=" * 80)
    print("ANALYSIS")
    print("=" * 80)
    print(f"Total AI suggestions: {len(ai_suggested)}")
    print(f"Unique patterns: {len(patterns)}")
    print(f"\nThese are true edge cases:")
    print("- One-time or rare merchants")
    print("- Too specific for general rules")
    print("- Good candidates for manual review")
    print("- Create rules only if patterns repeat")

if __name__ == "__main__":
    show_ai_suggestions()
