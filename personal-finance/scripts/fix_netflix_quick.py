"""
Quick fix for broken NETFLIX rule - update category_id to UUID.
"""
import sys
from pathlib import Path
import sqlite3

sys.path.insert(0, str(Path(__file__).parent.parent))

DB_PATH = Path(__file__).parent.parent / "data" / "finance.db"

def main():
    print("Fixing NETFLIX rule...")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get the Streaming Services category UUID
    cursor.execute("SELECT id FROM categories WHERE name = 'Streaming Services'")
    result = cursor.fetchone()

    if not result:
        print("ERROR: Streaming Services category not found!")
        conn.close()
        return

    streaming_uuid = result[0]
    print(f"Streaming Services UUID: {streaming_uuid}")

    # Update the NETFLIX rule
    cursor.execute("""
        UPDATE rules
        SET category_id = ?
        WHERE pattern = 'NETFLIX'
    """, (streaming_uuid,))

    rows_updated = cursor.rowcount
    conn.commit()
    conn.close()

    if rows_updated > 0:
        print(f"[SUCCESS] Fixed NETFLIX rule! Updated {rows_updated} row(s).")
        print("\nNext steps:")
        print("1. Restart the app: python app.py")
        print("2. Go to Rules tab")
        print("3. Enable 'Force Re-categorize' switch")
        print("4. Click 'Re-categorize ALL with Rules'")
        print("5. All Netflix transactions should now be 'Streaming Services'")
    else:
        print("[WARNING] No rows updated - NETFLIX rule might not exist")

if __name__ == '__main__':
    main()
