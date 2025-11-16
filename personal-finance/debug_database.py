#!/usr/bin/env python3
"""
Comprehensive database debug script.
"""
import os
import sqlite3
from pathlib import Path
from src.data.database import FinanceDatabase

DB_PATH = Path("data/finance.db")

print("=" * 80)
print("DATABASE DEBUG")
print("=" * 80)

# Check file
print(f"\n1. DATABASE FILE:")
print(f"   Path: {DB_PATH}")
print(f"   Exists: {DB_PATH.exists()}")
if DB_PATH.exists():
    size = DB_PATH.stat().st_size
    print(f"   Size: {size:,} bytes ({size/1024:.1f} KB)")
else:
    print("   ❌ Database file does not exist!")
    exit(1)

# Check tables directly with SQLite
print(f"\n2. DIRECT SQLITE CHECK:")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# List tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print(f"   Tables: {[t[0] for t in tables]}")

# Count rows in each table
for table_name in [t[0] for t in tables]:
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    print(f"   - {table_name}: {count} rows")

# Check transactions table schema
print(f"\n3. TRANSACTIONS TABLE SCHEMA:")
cursor.execute("PRAGMA table_info(transactions);")
columns = cursor.fetchall()
for col in columns:
    print(f"   - {col[1]} ({col[2]})")

# Sample data from transactions
print(f"\n4. SAMPLE TRANSACTIONS (first 5):")
cursor.execute("SELECT id, date, description, amount, category, category_confidence FROM transactions LIMIT 5")
rows = cursor.fetchall()
if rows:
    for row in rows:
        print(f"   ID={row[0]}, Date={row[1]}, Desc={row[2][:30]}, Amount={row[3]}, Cat={row[4]}, Conf={row[5]}")
else:
    print("   ❌ No transactions found in database!")

conn.close()

# Check using FinanceDatabase class
print(f"\n5. FINANCEDATABASE CLASS CHECK:")
db = FinanceDatabase(DB_PATH)

try:
    transactions = db.get_transactions()
    print(f"   Transactions via get_transactions(): {len(transactions)}")

    if len(transactions) > 0:
        print(f"\n   First transaction:")
        t = transactions[0]
        print(f"   - ID: {t.id}")
        print(f"   - Date: {t.date}")
        print(f"   - Description: {t.description}")
        print(f"   - Amount: {t.amount}")
        print(f"   - Category: {t.category}")
        print(f"   - Confidence: {t.category_confidence}")
        print(f"   - Confirmed: {t.category_confirmed}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Check categories and rules
print(f"\n6. CATEGORIES & RULES:")
try:
    categories = db.get_categories()
    print(f"   Categories: {len(categories)}")

    rules = db.get_rules()
    print(f"   Rules: {len(rules)}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Check upload directory
print(f"\n7. UPLOAD DIRECTORY:")
upload_dir = Path("data")
print(f"   Path: {upload_dir}")
print(f"   Exists: {upload_dir.exists()}")
if upload_dir.exists():
    files = list(upload_dir.glob("*"))
    print(f"   Files: {[f.name for f in files]}")

print("\n" + "=" * 80)
