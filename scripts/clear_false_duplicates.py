"""Clear false duplicate flags from database."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.database import FinanceDatabase

db = FinanceDatabase('data/finance.db')

print("\n" + "="*80)
print("CLEARING FALSE DUPLICATE FLAGS")
print("="*80)

# Count existing duplicates
duplicates = db.get_potential_duplicates()
print(f"\nCurrent duplicate flags: {len(duplicates)}")

if duplicates:
    # Delete all from potential_duplicates table
    with db._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM potential_duplicates")
        conn.commit()

    print(f"[OK] Cleared all {len(duplicates)} false duplicate flags")

    # Verify
    remaining = db.get_potential_duplicates()
    print(f"[OK] Verified: {len(remaining)} duplicates remain (should be 0)")
else:
    print("[OK] No duplicates to clear")

print("\n" + "="*80)
print("NEXT STEPS:")
print("="*80)
print("1. Restart the app to load new duplicate detection logic")
print("2. Re-import your CSV file")
print("3. Only TRUE duplicates will be flagged (same balance)")
print("="*80 + "\n")
