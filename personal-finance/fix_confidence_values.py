#!/usr/bin/env python3
"""
Fix confidence values for existing categorized transactions.
Sets confidence=1.0 for all transactions that have a category but no confidence.
"""
from pathlib import Path
import sqlite3

DB_PATH = Path("data/finance.db")

print("=" * 80)
print("FIXING CONFIDENCE VALUES")
print("=" * 80)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Find transactions with category but no confidence
cursor.execute("""
    SELECT COUNT(*) FROM transactions
    WHERE category IS NOT NULL
    AND category != 'Uncategorized'
    AND category_confidence IS NULL
""")
count = cursor.fetchone()[0]

print(f"\nTransactions with category but no confidence: {count}")

if count == 0:
    print("✓ Nothing to fix!")
    conn.close()
    exit(0)

# Fix them: set confidence=1.0 (assume they were rule-matched)
print(f"Setting confidence=1.0 for {count} transactions...")

cursor.execute("""
    UPDATE transactions
    SET category_confidence = 1.0
    WHERE category IS NOT NULL
    AND category != 'Uncategorized'
    AND category_confidence IS NULL
""")

conn.commit()

# Verify
cursor.execute("""
    SELECT COUNT(*) FROM transactions
    WHERE category IS NOT NULL
    AND category != 'Uncategorized'
    AND category_confidence = 1.0
""")
fixed = cursor.fetchone()[0]

print(f"✓ Fixed {fixed} transactions!")
print("\n" + "=" * 80)
print("DONE!")
print("=" * 80)
print("\nNow refresh the app and check Review & Correct tab.")
print("Filter 'Rule Matched' should show your transactions!")

conn.close()
