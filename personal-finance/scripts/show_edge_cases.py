"""
Show remaining one-off edge cases after all new rules are applied.

Excludes:
- Transactions that will match our 27 new rules
- ROYAL BANK C/L (auto-categorized as Cash)
- AHMED ALIKHAN INVESTMENT (user chose to leave uncategorized)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.database import FinanceDatabase

def show_edge_cases():
    """Show remaining one-off uncategorized transactions."""

    db = FinanceDatabase('data/finance.db')

    # Get all transactions and filter for uncategorized
    all_transactions = db.get_transactions()
    uncategorized = [txn for txn in all_transactions if not txn.category]

    print("=" * 80)
    print("REMAINING ONE-OFF EDGE CASES")
    print("=" * 80)
    print(f"\nTotal uncategorized: {len(uncategorized)}")

    # Patterns that will be matched by our new rules
    new_rule_patterns = [
        "SCREWFIX", "PURE MUSCLES GYM", "RISE VAPE", "AMAZON.CO.U",
        "NANDOS", "NANDOS.CO.UK", "UMMAH WELFARE TRUST",
        "LONDON BOROUGH OF WALT", "TESCO-STORES", "BIRKBECK COLLEGE",
        "WASABI_172B", "WASABI_CANARYWHARF", "WASABI_KING",
        "LEGEND BARBER SHOP", "SAINSBURYS S/MKTS", "ZETTLE_*THE SALAD PROJ",
        "CHUFFED.ORG", "ZETTLE_", "SQ *HIGHAM HILL MUSLIM",
        "CHUFFED.OR", "CROWDJUSTICE.COM", "DONATION", "WWW.MAP.OR",
        "SAINSBURY'S", "SAINSBURY'S PETROL", "SAINSBURYS S/MKT",
        "SAINSBURY'S S/MKT", "LONDON BORO OF REDBRID"
    ]

    # Filter out transactions that will be caught by new rules
    edge_cases = []
    for txn in uncategorized:
        desc_upper = txn.description.upper()

        # Skip if will match new rules
        will_match = False
        for pattern in new_rule_patterns:
            if pattern.upper() in desc_upper:
                will_match = True
                break

        if will_match:
            continue

        # Skip ROYAL BANK C/L (auto-categorized as Cash)
        if "ROYAL BANK" in desc_upper and txn.transaction_type == "C/L":
            continue

        # Skip AHMED ALIKHAN INVESTMENT (user chose to leave uncategorized)
        if "AHMED ALIKHAN" in desc_upper and "INVESTMENT" in desc_upper:
            continue

        edge_cases.append(txn)

    print(f"Remaining one-offs after new rules: {len(edge_cases)}\n")

    # Show first 20 examples
    print("Sample of edge cases (showing first 20):")
    print("-" * 80)

    for i, txn in enumerate(edge_cases[:20], 1):
        # Truncate description if too long
        desc = txn.description[:60] + "..." if len(txn.description) > 60 else txn.description
        print(f"{i:2}. £{txn.amount:8.2f} | {txn.transaction_type:5} | {desc}")

    if len(edge_cases) > 20:
        print(f"\n... and {len(edge_cases) - 20} more")

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total uncategorized: {len(uncategorized)}")
    print(f"Will be caught by new rules: {len(uncategorized) - len(edge_cases)}")
    print(f"Remaining one-offs: {len(edge_cases)}")
    print(f"\nThese {len(edge_cases)} transactions are true edge cases:")
    print("- Too specific for general rules")
    print("- One-time or rare merchants")
    print("- May need AI categorization or manual review")

if __name__ == "__main__":
    show_edge_cases()
