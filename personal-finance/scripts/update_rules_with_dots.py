"""
Update rules with dots to simplified patterns.
After adding dot (.) as delimiter, these rules need to be updated.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.database import FinanceDatabase

# Mapping of old pattern -> new pattern
# Strategy: Extract the most distinctive part (usually the brand name before first dot)
RULE_UPDATES = {
    # Domain-based rules -> Brand name only
    "CREATION.CO.UK": "CREATION",
    "WWW.F1.COM": "F1",
    "WWW.BIKECLUB.COM": "BIKECLUB",
    "WWW.AMAZON": "WWW AMAZON",  # Keep both to avoid conflict with general AMAZON rule
    "SPORTSDIRECT.COM": "SPORTSDIRECT",
    "NIF.ORG": "NIF",
    "CLAUDE.AI": "CLAUDE",
    "CDKEYS.COM": "CDKEYS",
    "APPLE.COM/BILL": "APPLE",
    "WWW.IQBALNASIM.COM": "IQBALNASIM",
    "WWW.ARABIC-  STUDIO.COM": "ARABIC-  STUDIO",
    "BNA.CO.UK": "BNA",

    # Special cases
    "SUMUP *NOVA.SOL": "NOVA",  # Extract the distinctive part
    "AMAZON.CO.UK": "AMAZON CO UK",  # Keep specific to avoid overriding general AMAZON rule
}

def update_rules():
    """Update rules with dots to simplified patterns."""
    db = FinanceDatabase("data/finance.db")

    print("\n=== UPDATING RULES WITH DOTS ===")
    print(f"Total rules to update: {len(RULE_UPDATES)}")

    updated_count = 0
    not_found_count = 0

    with db._get_connection() as conn:
        cursor = conn.cursor()

        for old_pattern, new_pattern in RULE_UPDATES.items():
            # Find rule with old pattern
            cursor.execute(
                "SELECT id, pattern, category_id, priority FROM rules WHERE pattern = ?",
                (old_pattern,)
            )
            result = cursor.fetchone()

            if result:
                rule_id, pattern, category_id, priority = result

                # Get category name for display
                cursor.execute("SELECT name FROM categories WHERE id = ?", (category_id,))
                category_name = cursor.fetchone()[0]

                print(f"\n[UPDATE] {old_pattern} -> {new_pattern}")
                print(f"  Category: {category_name}")
                print(f"  Priority: {priority}")

                # Update pattern
                cursor.execute(
                    "UPDATE rules SET pattern = ? WHERE id = ?",
                    (new_pattern, rule_id)
                )
                updated_count += 1
            else:
                print(f"\n[NOT FOUND] {old_pattern} - Rule doesn't exist (may have been deleted)")
                not_found_count += 1

        conn.commit()

    print(f"\n=== SUMMARY ===")
    print(f"Updated: {updated_count} rules")
    print(f"Not found: {not_found_count} rules")
    print(f"Total: {len(RULE_UPDATES)} rules processed")

    # Verify updates
    print(f"\n=== VERIFICATION ===")
    rules = db.get_rules()
    updated_patterns = [new_pattern for new_pattern in RULE_UPDATES.values()]
    found_patterns = [r.pattern for r in rules if r.pattern in updated_patterns]

    print(f"Rules now using simplified patterns: {len(found_patterns)}")

    return updated_count

if __name__ == "__main__":
    updated = update_rules()
    print(f"\n[SUCCESS] Updated {updated} rules!")
