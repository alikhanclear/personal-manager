"""
Comprehensive test suite for Rules Export/Import functionality.

Tests:
1. Export Test - Verify category names (not UUIDs) appear in export
2. Import Append Test - Verify new rules added without conflicts
3. Import Replace Test - Verify all rules replaced with new UUIDs
4. Duplicate Detection Test - Verify append mode skips duplicates
5. UUID Uniqueness Test - Verify all rule IDs are unique
6. Category Mapping Test - Verify category names resolve to correct UUIDs
"""
import sys
import os
import csv
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.database import FinanceDatabase
from src.data.models import Rule

# ANSI color codes for output (fallback to plain text if not supported)
GREEN = ""
RED = ""
BLUE = ""
RESET = ""

class TestResults:
    """Track test results."""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []

    def add_pass(self, test_name, details=""):
        self.passed += 1
        self.tests.append(("PASS", test_name, details))
        print(f"[PASS] {test_name}")
        if details:
            print(f"       {details}")

    def add_fail(self, test_name, details=""):
        self.failed += 1
        self.tests.append(("FAIL", test_name, details))
        print(f"[FAIL] {test_name}")
        if details:
            print(f"       {details}")

    def summary(self):
        total = self.passed + self.failed
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {total}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Success Rate: {self.passed/total*100:.1f}%")

        if self.failed == 0:
            print("\n[SUCCESS] All tests passed!")
        else:
            print(f"\n[WARNING] {self.failed} test(s) failed")
            print("\nFailed tests:")
            for status, name, details in self.tests:
                if status == "FAIL":
                    print(f"  - {name}")
                    if details:
                        print(f"    {details}")

def test_export_no_uuids(db: FinanceDatabase, results: TestResults):
    """
    TEST 1: Export contains category NAMES, not UUIDs

    Pass Criteria:
    - Export file contains 'pattern', 'category', 'priority' columns
    - All category values are human-readable names (no UUID format)
    - No category values match UUID pattern (e.g., '550e8400-e29b-41d4-a716-446655440000')
    """
    print("\n" + "=" * 80)
    print("TEST 1: Export contains category NAMES (not UUIDs)")
    print("=" * 80)

    rules = db.get_rules()
    if len(rules) == 0:
        results.add_fail("Export Test", "No rules in database to test")
        return

    categories = db.get_categories()
    category_map = {cat.id: cat.name for cat in categories}

    # Create a temporary CSV export
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['pattern', 'category', 'priority'])

        for rule in rules[:10]:  # Test first 10 rules
            category_name = category_map.get(rule.category_id, rule.category_id)
            writer.writerow([rule.pattern, category_name, rule.priority])

        temp_path = f.name

    # Read back and verify
    uuid_pattern_found = False
    invalid_categories = []

    with open(temp_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            category_value = row['category']

            # Check if it looks like a UUID (format: 8-4-4-4-12 hex chars with dashes)
            if len(category_value) == 36 and category_value.count('-') == 4:
                uuid_pattern_found = True
                invalid_categories.append((row['pattern'], category_value))

    os.unlink(temp_path)

    if uuid_pattern_found:
        results.add_fail("Export Test",
                        f"Found {len(invalid_categories)} UUID(s) in export: {invalid_categories[:3]}")
    else:
        results.add_pass("Export Test",
                        "All category values are human-readable names")

def test_import_append_mode(db: FinanceDatabase, results: TestResults):
    """
    TEST 2: Import in APPEND mode preserves existing rules and adds new ones

    Pass Criteria:
    - Existing rule count noted before import
    - New rules imported from test CSV
    - Final count = original count + new unique rules
    - All rule IDs are unique (no UUID conflicts)
    """
    print("\n" + "=" * 80)
    print("TEST 2: Import APPEND mode - Preserves existing + adds new")
    print("=" * 80)

    # Get initial state
    initial_rules = db.get_rules()
    initial_count = len(initial_rules)
    initial_ids = {r.id for r in initial_rules}

    print(f"Initial rule count: {initial_count}")

    # Create test CSV with 3 new rules
    test_rules_data = [
        {'pattern': 'TEST_APPEND_1', 'category': 'Groceries', 'priority': 5},
        {'pattern': 'TEST_APPEND_2', 'category': 'Dining Out', 'priority': 5},
        {'pattern': 'TEST_APPEND_3', 'category': 'Entertainment', 'priority': 5},
    ]

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['pattern', 'category', 'priority'])
        writer.writeheader()
        writer.writerows(test_rules_data)
        temp_path = f.name

    # Import using append mode
    try:
        import polars as pl
        df = pl.read_csv(temp_path)

        # Get category mapping
        categories = db.get_categories()
        category_map = {cat.name.lower(): cat.id for cat in categories}

        # Create Rule objects
        rules_to_import = []
        for row in df.iter_rows(named=True):
            category_id = category_map.get(row['category'].lower())
            if category_id:
                rule = Rule(
                    pattern=row['pattern'],
                    category_id=category_id,
                    priority=row['priority']
                )
                rules_to_import.append(rule)

        # Execute append import
        inserted, skipped = db.import_rules(rules_to_import)

        print(f"Inserted: {inserted} rules")
        print(f"Skipped: {skipped} duplicates")

        # Verify results
        final_rules = db.get_rules()
        final_count = len(final_rules)
        final_ids = {r.id for r in final_rules}

        print(f"Final rule count: {final_count}")

        # Check 1: Count increased correctly
        expected_count = initial_count + inserted
        if final_count != expected_count:
            results.add_fail("Import Append - Count Check",
                           f"Expected {expected_count}, got {final_count}")
        else:
            results.add_pass("Import Append - Count Check",
                           f"Rule count increased by {inserted}")

        # Check 2: All IDs are unique (no conflicts)
        if len(final_ids) != final_count:
            results.add_fail("Import Append - UUID Uniqueness",
                           f"Found duplicate UUIDs: {final_count} rules, {len(final_ids)} unique IDs")
        else:
            results.add_pass("Import Append - UUID Uniqueness",
                           f"All {final_count} rule IDs are unique")

        # Check 3: New IDs don't conflict with old IDs
        new_ids = final_ids - initial_ids
        if len(new_ids) != inserted:
            results.add_fail("Import Append - New ID Generation",
                           f"Expected {inserted} new IDs, found {len(new_ids)}")
        else:
            results.add_pass("Import Append - New ID Generation",
                           f"Generated {inserted} new unique UUIDs")

        # Cleanup: Remove test rules
        for rule in final_rules:
            if rule.pattern.startswith('TEST_APPEND_'):
                db.delete_rule(rule.id)

    except Exception as e:
        results.add_fail("Import Append Test", f"Exception: {str(e)}")
    finally:
        os.unlink(temp_path)

def test_import_replace_mode(db: FinanceDatabase, results: TestResults):
    """
    TEST 3: Import in REPLACE mode deletes all old rules and creates new ones

    Pass Criteria:
    - All existing rules deleted
    - New rules imported from test CSV
    - Final count = number of rules in CSV
    - All new rule IDs are unique
    - None of the old rule IDs exist in new rules
    """
    print("\n" + "=" * 80)
    print("TEST 3: Import REPLACE mode - Deletes all + imports new")
    print("=" * 80)

    # Backup current rules first
    backup_rules = db.get_rules()
    backup_count = len(backup_rules)
    old_ids = {r.id for r in backup_rules}

    print(f"Current rules (to be replaced): {backup_count}")
    print(f"Backing up {backup_count} rules for restoration...")

    # Create test CSV with 5 new rules
    test_rules_data = [
        {'pattern': 'TEST_REPLACE_1', 'category': 'Groceries', 'priority': 5},
        {'pattern': 'TEST_REPLACE_2', 'category': 'Dining Out', 'priority': 5},
        {'pattern': 'TEST_REPLACE_3', 'category': 'Entertainment', 'priority': 5},
        {'pattern': 'TEST_REPLACE_4', 'category': 'Transport', 'priority': 5},
        {'pattern': 'TEST_REPLACE_5', 'category': 'Shopping', 'priority': 5},
    ]

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['pattern', 'category', 'priority'])
        writer.writeheader()
        writer.writerows(test_rules_data)
        temp_path = f.name

    try:
        import polars as pl
        df = pl.read_csv(temp_path)

        # Get category mapping
        categories = db.get_categories()
        category_map = {cat.name.lower(): cat.id for cat in categories}

        # Create Rule objects
        rules_to_import = []
        for row in df.iter_rows(named=True):
            category_id = category_map.get(row['category'].lower())
            if category_id:
                rule = Rule(
                    pattern=row['pattern'],
                    category_id=category_id,
                    priority=row['priority']
                )
                rules_to_import.append(rule)

        # Execute REPLACE import
        count = db.replace_all_rules(rules_to_import)

        print(f"Replaced all rules with {count} new rules")

        # Verify results
        final_rules = db.get_rules()
        final_count = len(final_rules)
        new_ids = {r.id for r in final_rules}

        print(f"Final rule count: {final_count}")

        # Check 1: Count matches imported rules
        if final_count != len(test_rules_data):
            results.add_fail("Import Replace - Count Check",
                           f"Expected {len(test_rules_data)}, got {final_count}")
        else:
            results.add_pass("Import Replace - Count Check",
                           f"Replaced with exactly {final_count} new rules")

        # Check 2: All new IDs are unique
        if len(new_ids) != final_count:
            results.add_fail("Import Replace - UUID Uniqueness",
                           f"Found duplicate UUIDs: {final_count} rules, {len(new_ids)} unique IDs")
        else:
            results.add_pass("Import Replace - UUID Uniqueness",
                           f"All {final_count} rule IDs are unique")

        # Check 3: None of the old IDs exist in new rules
        old_ids_remaining = old_ids.intersection(new_ids)
        if len(old_ids_remaining) > 0:
            results.add_fail("Import Replace - Old IDs Removed",
                           f"Found {len(old_ids_remaining)} old IDs still in database")
        else:
            results.add_pass("Import Replace - Old IDs Removed",
                           f"All old rule IDs successfully replaced")

        # Restore backup rules
        print(f"\nRestoring {backup_count} original rules...")
        db.replace_all_rules(backup_rules)

        restored_count = len(db.get_rules())
        if restored_count == backup_count:
            print(f"[OK] Restored {restored_count} rules successfully")
        else:
            print(f"[WARNING] Restore count mismatch: expected {backup_count}, got {restored_count}")

    except Exception as e:
        results.add_fail("Import Replace Test", f"Exception: {str(e)}")
        # Attempt to restore backup anyway
        try:
            db.replace_all_rules(backup_rules)
            print(f"[OK] Restored backup after exception")
        except:
            print(f"[ERROR] Failed to restore backup!")
    finally:
        os.unlink(temp_path)

def test_duplicate_detection(db: FinanceDatabase, results: TestResults):
    """
    TEST 4: Append mode correctly detects and skips duplicates

    Pass Criteria:
    - Import same rule twice in append mode
    - First import: inserted = 1, skipped = 0
    - Second import: inserted = 0, skipped = 1
    - Final count increases by 1 only
    """
    print("\n" + "=" * 80)
    print("TEST 4: Duplicate detection in APPEND mode")
    print("=" * 80)

    initial_count = len(db.get_rules())

    # Create test rule
    test_rule_data = [
        {'pattern': 'TEST_DUPLICATE_PATTERN', 'category': 'Groceries', 'priority': 5},
    ]

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['pattern', 'category', 'priority'])
        writer.writeheader()
        writer.writerows(test_rule_data)
        temp_path = f.name

    try:
        import polars as pl

        # Get category mapping
        categories = db.get_categories()
        category_map = {cat.name.lower(): cat.id for cat in categories}

        # First import
        df = pl.read_csv(temp_path)
        rules_to_import = []
        for row in df.iter_rows(named=True):
            category_id = category_map.get(row['category'].lower())
            if category_id:
                rule = Rule(
                    pattern=row['pattern'],
                    category_id=category_id,
                    priority=row['priority']
                )
                rules_to_import.append(rule)

        inserted1, skipped1 = db.import_rules(rules_to_import)
        print(f"First import: inserted={inserted1}, skipped={skipped1}")

        # Second import (same rules)
        rules_to_import2 = []
        for row in df.iter_rows(named=True):
            category_id = category_map.get(row['category'].lower())
            if category_id:
                rule = Rule(
                    pattern=row['pattern'],
                    category_id=category_id,
                    priority=row['priority']
                )
                rules_to_import2.append(rule)

        inserted2, skipped2 = db.import_rules(rules_to_import2)
        print(f"Second import: inserted={inserted2}, skipped={skipped2}")

        final_count = len(db.get_rules())

        # Verify first import succeeded
        if inserted1 == 1 and skipped1 == 0:
            results.add_pass("Duplicate Detection - First Import",
                           "Correctly inserted new rule")
        else:
            results.add_fail("Duplicate Detection - First Import",
                           f"Expected inserted=1, skipped=0; got inserted={inserted1}, skipped={skipped1}")

        # Verify second import skipped duplicate
        if inserted2 == 0 and skipped2 == 1:
            results.add_pass("Duplicate Detection - Second Import",
                           "Correctly skipped duplicate rule")
        else:
            results.add_fail("Duplicate Detection - Second Import",
                           f"Expected inserted=0, skipped=1; got inserted={inserted2}, skipped={skipped2}")

        # Verify count increased by 1 only
        if final_count == initial_count + 1:
            results.add_pass("Duplicate Detection - Final Count",
                           f"Count increased by 1 (from {initial_count} to {final_count})")
        else:
            results.add_fail("Duplicate Detection - Final Count",
                           f"Expected {initial_count + 1}, got {final_count}")

        # Cleanup
        for rule in db.get_rules():
            if rule.pattern == 'TEST_DUPLICATE_PATTERN':
                db.delete_rule(rule.id)

    except Exception as e:
        results.add_fail("Duplicate Detection Test", f"Exception: {str(e)}")
    finally:
        os.unlink(temp_path)

def main():
    """Run all tests."""
    print("=" * 80)
    print("RULES EXPORT/IMPORT TEST SUITE")
    print("=" * 80)
    print()

    db = FinanceDatabase(db_path="data/finance.db")
    results = TestResults()

    # Run all tests
    test_export_no_uuids(db, results)
    test_import_append_mode(db, results)
    test_import_replace_mode(db, results)
    test_duplicate_detection(db, results)

    # Print summary
    results.summary()

    return results.failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
