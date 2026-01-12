"""
Restore rules from Nov 29 export file.
This will DELETE all existing rules and import 322 rules from the backup.
"""
import sys
import os
from datetime import datetime
from uuid import uuid4

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from src.data.database import FinanceDatabase

def restore_rules():
    """Restore rules from Nov 29 export."""
    db = FinanceDatabase(db_path="data/finance.db")

    # Load export file
    export_path = "C:/Users/azimu/Downloads/rules_20251129_105930.xlsx"
    print(f"Loading rules from: {export_path}")
    df = pd.read_excel(export_path)
    print(f"Found {len(df)} rules in export file")

    # Get all categories for mapping
    categories = db.get_categories()
    category_map = {cat.name: cat.id for cat in categories}
    print(f"Loaded {len(categories)} categories from database")

    # Check for missing categories
    missing_categories = set()
    for cat_name in df['Category'].unique():
        if cat_name not in category_map:
            missing_categories.add(cat_name)

    if missing_categories:
        print(f"\n[CREATE] {len(missing_categories)} categories not found, creating them:")
        for cat in sorted(missing_categories):
            print(f"   - {cat}")

        # Create missing categories
        with db._get_connection() as conn:
            cursor = conn.cursor()
            for cat_name in sorted(missing_categories):
                cat_id = str(uuid4())
                cursor.execute("""
                    INSERT INTO categories (id, name, parent_id, color, icon)
                    VALUES (?, ?, NULL, '#808080', '?')
                """, (cat_id, cat_name))
                category_map[cat_name] = cat_id
            conn.commit()
        print(f"Created {len(missing_categories)} new categories")

    # Delete all existing rules and import new ones
    with db._get_connection() as conn:
        cursor = conn.cursor()

        # Delete all existing rules
        print("\n[DELETE] Deleting all existing rules...")
        cursor.execute("DELETE FROM rules")
        existing_count = cursor.rowcount
        print(f"Deleted {existing_count} existing rules")

        # Import rules from export
        print(f"\n[IMPORT] Importing {len(df)} rules...")
        imported = 0
        skipped = 0

        for idx, row in df.iterrows():
            pattern = row['Pattern']
            category_name = row['Category']
            priority = int(row['Priority'])

            # Skip if category not found (shouldn't happen now)
            if category_name not in category_map:
                skipped += 1
                continue

            category_id = category_map[category_name]

            # Insert rule
            cursor.execute("""
                INSERT INTO rules (id, pattern, category_id, priority, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                str(uuid4()),
                pattern,
                category_id,
                priority,
                datetime.utcnow().isoformat()
            ))
            imported += 1

            if (imported % 50) == 0:
                print(f"   Imported {imported} rules...")

        conn.commit()

    print(f"\n[SUCCESS] Restore complete!")
    print(f"   Imported: {imported} rules")
    print(f"   Skipped: {skipped} rules (missing categories)")

    # Verify
    rules = db.get_rules()
    print(f"\n[VERIFY] Current database state:")
    print(f"   Total rules: {len(rules)}")

if __name__ == "__main__":
    restore_rules()
