"""
Test why pattern "FEDEX" doesn't match "FEDEX395224543".
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.rule_engine import RuleEngine
from src.data.models import Rule, Transaction
from datetime import datetime
import re

# Create test transaction
test_transaction = Transaction(
    id="test-fedex",
    date=datetime(2025, 9, 10),
    description="5001 10SEP25 , FEDEX395224543 , T08456 070809 GB",
    amount=-25.00,
    balance=1000.00,
    account_number="12345678",
    account_name="Current Account"
)

# Create rule with pattern "FEDEX"
fedex_rule = Rule(
    id="test-rule-fedex",
    pattern="FEDEX",
    category_id="shipping-id",
    priority=10
)

# Test current matching
engine = RuleEngine([fedex_rule])
result = engine.match_transaction(test_transaction)

print("\n=== CURRENT MATCHING BEHAVIOR ===")
print(f"Transaction: {test_transaction.description}")
print(f"Pattern: {fedex_rule.pattern}")
print(f"Match Result: {result}")
if result:
    print(f"  [MATCH] Category ID: {result[0]}, Pattern: {result[1]}")
else:
    print("  [NO MATCH]")

# Explain why
print("\n=== WHY NO MATCH? ===")
print("Current tokenization (delimiters: space, asterisk, and dot):")
description_upper = test_transaction.description.upper()
tokens = re.split(r'[\s*\.]+', description_upper)
tokens = [t for t in tokens if t]
tokens_normalized = [re.sub(r'[,;:.!?()]+$', '', t) for t in tokens]
tokens_normalized = [t for t in tokens_normalized if t]

print(f"Tokens: {tokens_normalized}")
print(f"\nPattern 'FEDEX' is in tokens? {fedex_rule.pattern.upper() in tokens_normalized}")
print(f"Issue: 'FEDEX395224543' is ONE token (no delimiter between letters and numbers)")

# Test proposed fix: Split on letter-to-number boundaries
print("\n\n=== PROPOSED FIX: Split on letter-to-number boundaries ===")

def split_alphanumeric_boundaries(tokens):
    """Split tokens on boundaries between letters and numbers."""
    result = []
    for token in tokens:
        # Split on letter-to-digit and digit-to-letter transitions
        # E.g., "FEDEX395224543" -> ["FEDEX", "395224543"]
        # E.g., "T08456" -> ["T", "08456"]
        parts = re.split(r'(?<=[A-Z])(?=[0-9])|(?<=[0-9])(?=[A-Z])', token)
        result.extend([p for p in parts if p])
    return result

tokens_split = split_alphanumeric_boundaries(tokens_normalized)
print(f"New Tokens: {tokens_split}")
print(f"Pattern 'FEDEX' is in tokens? {fedex_rule.pattern.upper() in tokens_split}")
print("  [WOULD MATCH!]")

# Test impact on existing patterns
print("\n\n=== IMPACT ON EXISTING RULES ===")

test_cases = [
    ("FEDEX395224543", "FEDEX", "Shipping - currently doesn't work"),
    ("BOLT.EUO2511021744", "BOLT", "Transport - works with dot delimiter"),
    ("T08456 PAYMENT", "T08456", "Would be split to ['T', '08456']"),
    ("10SEP25 TRANSACTION", "10SEP25", "Would be split to ['10', 'SEP', '25']"),
    ("CO-OP FOOD", "CO-OP", "Groceries - hyphen preserved (not affected)"),
    ("AMAZON123", "AMAZON", "Shopping - would work better"),
]

for description, pattern, notes in test_cases:
    # Current behavior
    tokens_current = re.split(r'[\s*\.]+', description.upper())
    tokens_current = [t for t in tokens_current if t]
    tokens_current = [re.sub(r'[,;:.!?()]+$', '', t) for t in tokens_current]
    tokens_current = [t for t in tokens_current if t]
    matches_current = pattern.upper() in tokens_current

    # With alphanumeric boundary splitting
    tokens_new = split_alphanumeric_boundaries(tokens_current)
    matches_new = pattern.upper() in tokens_new

    status = "[SAME]" if matches_current == matches_new else "[CHANGED]"
    print(f"\n{status} | {notes}")
    print(f"  Description: {description}")
    print(f"  Pattern: {pattern}")
    print(f"  Current tokens: {tokens_current}")
    print(f"  New tokens: {tokens_new}")
    print(f"  Current: {'[Match]' if matches_current else '[No Match]'}")
    print(f"  With split: {'[Match]' if matches_new else '[No Match]'}")

print("\n\n=== RECOMMENDATION ===")
print("1. Add alphanumeric boundary splitting to rule_engine.py")
print("2. Split tokens on letter-to-number and number-to-letter transitions")
print("3. Examples:")
print("   - 'FEDEX395224543' -> ['FEDEX', '395224543']")
print("   - 'BOLT.EUO2511021744' -> ['BOLT', 'EUO', '2511021744'] (dot + alpha boundary)")
print("   - '10SEP25' -> ['10', 'SEP', '25']")
print("4. Impact: Better matching for merchant codes with tracking numbers")
print("5. Trade-off: Patterns like 'T08456' would need to be just 'T' or full '08456'")
