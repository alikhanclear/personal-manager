"""
Check categorization status of all transactions.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.database import FinanceDatabase

def check_status():
    """Check categorization status."""

    db = FinanceDatabase('data/finance.db')

    # Get all transactions
    all_transactions = db.get_transactions()

    print("=" * 80)
    print("TRANSACTION CATEGORIZATION STATUS")
    print("=" * 80)
    print(f"\nTotal transactions: {len(all_transactions)}\n")

    # Categorize by status
    uncategorized = []
    rule_matched = []
    ai_suggested = []
    confirmed = []

    for txn in all_transactions:
        if not txn.category:
            uncategorized.append(txn)
        elif txn.category_confirmed:
            confirmed.append(txn)
        elif txn.category_confidence == 1.0:
            rule_matched.append(txn)
        else:
            ai_suggested.append(txn)

    print(f"Uncategorized:    {len(uncategorized):4} (no category)")
    print(f"Rule Matched:     {len(rule_matched):4} (confidence=1.0, not confirmed)")
    print(f"AI Suggested:     {len(ai_suggested):4} (confidence<1.0)")
    print(f"Confirmed:        {len(confirmed):4} (user confirmed)")

    if uncategorized:
        print("\n" + "=" * 80)
        print("UNCATEGORIZED TRANSACTIONS (First 20)")
        print("=" * 80)
        for i, txn in enumerate(uncategorized[:20], 1):
            desc = txn.description[:60] + "..." if len(txn.description) > 60 else txn.description
            print(f"{i:2}. £{txn.amount:8.2f} | {txn.transaction_type:5} | {desc}")

        if len(uncategorized) > 20:
            print(f"\n... and {len(uncategorized) - 20} more")
    else:
        print("\n[OK] All transactions are categorized!")

if __name__ == "__main__":
    check_status()
