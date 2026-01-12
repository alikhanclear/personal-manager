"""
Fix the NETFLIX rule - update category_id from name to UUID.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.database import FinanceDatabase

DB_PATH = Path(__file__).parent.parent / "data" / "finance.db"

def main():
    db = FinanceDatabase(DB_PATH)

    # Get the NETFLIX rule
    rules = db.get_rules()
    netflix_rule = next((r for r in rules if r.pattern.upper() == 'NETFLIX'), None)

    if not netflix_rule:
        print("ERROR: No NETFLIX rule found!")
        return

    print("=" * 80)
    print("Current NETFLIX Rule:")
    print("=" * 80)
    print(f"Pattern: {netflix_rule.pattern}")
    print(f"Category ID: {netflix_rule.category_id}")
    print(f"Priority: {netflix_rule.priority}")

    # Get the correct Streaming Services category UUID
    categories = db.get_categories()
    streaming_cat = next((c for c in categories if c.name == "Streaming Services"), None)

    if not streaming_cat:
        print("\nERROR: Streaming Services category not found!")
        return

    print("\n" + "=" * 80)
    print("Correct Category:")
    print("=" * 80)
    print(f"Name: {streaming_cat.name}")
    print(f"UUID: {streaming_cat.id}")

    # Check if already correct
    if netflix_rule.category_id == streaming_cat.id:
        print("\n[OK] Rule is already correct!")
        return

    # Update the rule
    print("\n" + "=" * 80)
    print("Fixing Rule...")
    print("=" * 80)

    with db._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE rules
            SET category_id = ?
            WHERE id = ?
        """, (streaming_cat.id, netflix_rule.id))
        conn.commit()

    print(f"[OK] Updated NETFLIX rule category_id from '{netflix_rule.category_id}' to '{streaming_cat.id}'")

    # Verify
    updated_rules = db.get_rules()
    updated_netflix_rule = next((r for r in updated_rules if r.pattern.upper() == 'NETFLIX'), None)

    print("\n" + "=" * 80)
    print("Updated NETFLIX Rule:")
    print("=" * 80)
    print(f"Pattern: {updated_netflix_rule.pattern}")
    print(f"Category ID: {updated_netflix_rule.category_id}")
    print(f"Category Name: {streaming_cat.name}")
    print(f"Priority: {updated_netflix_rule.priority}")
    print("\n[SUCCESS] NETFLIX rule fixed! Now re-categorize all transactions with force mode.")

if __name__ == '__main__':
    main()
