"""Check if transaction category was updated in database."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.database import FinanceDatabase

DB_PATH = Path(__file__).parent.parent / "data" / "finance.db"

def main():
    db = FinanceDatabase(DB_PATH)

    # Check the specific transaction
    txn_id = "1dde2154ff0ed33584a1a2a8a0e9be5a"
    txn = db.get_transaction(txn_id)

    if txn:
        print(f"Transaction ID: {txn.id}")
        print(f"Description: {txn.description}")
        print(f"Category: {txn.category}")
        print(f"Confidence: {txn.category_confidence}")
        print(f"Confirmed: {txn.category_confirmed}")
    else:
        print(f"Transaction {txn_id} not found")

if __name__ == "__main__":
    main()
