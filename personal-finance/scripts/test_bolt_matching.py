"""
Test if pattern "Bolt" matches "BOLT.EUO2511021744" with current rule engine.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.rule_engine import RuleEngine
from src.data.models import Rule, Transaction
from datetime import datetime

# Create test transaction
test_transaction = Transaction(
    id="test-bolt",
    date=datetime(2025, 11, 2),
    description="8430 02NOV25 D , BOLT.EUO2511021744, LONDON GB",
    amount=-15.50,
    balance=1000.00,
    account_number="12345678",
    account_name="Current Account"
)

# Create rule with pattern "Bolt"
bolt_rule = Rule(
    id="test-rule-1",
    pattern="Bolt",
    category_id="public-transport-id",
    priority=10
)

# Test current matching
engine = RuleEngine([bolt_rule])
result = engine.match_transaction(test_transaction)

print("\n=== CURRENT MATCHING BEHAVIOR ===")
print(f"Transaction: {test_transaction.description}")
print(f"Pattern: {bolt_rule.pattern}")
print(f"Match Result: {result}")
if result:
    print(f"  [MATCH] Category ID: {result[0]}, Pattern: {result[1]}")
else:
    print("  [NO MATCH]")

# Explain why
print("\n=== WHY? ===")
print("Current tokenization (delimiters: space and asterisk ONLY):")
import re
description_upper = test_transaction.description.upper()
tokens = re.split(r'[\s*]+', description_upper)
tokens = [t for t in tokens if t]
tokens_normalized = [re.sub(r'[,;:.!?()]+$', '', t) for t in tokens]
tokens_normalized = [t for t in tokens_normalized if t]

print(f"Tokens: {tokens_normalized}")
print(f"\nPattern 'BOLT' is in tokens? {bolt_rule.pattern.upper() in tokens_normalized}")
print(f"Issue: 'BOLT.EUO2511021744' is ONE token (dot not a delimiter)")

# Test proposed fix
print("\n\n=== PROPOSED FIX: Add dot (.) as delimiter ===")
tokens_with_dot = re.split(r'[\s*\.]+', description_upper)
tokens_with_dot = [t for t in tokens_with_dot if t]
tokens_with_dot_normalized = [re.sub(r'[,;:.!?()]+$', '', t) for t in tokens_with_dot]
tokens_with_dot_normalized = [t for t in tokens_with_dot_normalized if t]

print(f"New Tokens: {tokens_with_dot_normalized}")
print(f"Pattern 'BOLT' is in tokens? {bolt_rule.pattern.upper() in tokens_with_dot_normalized}")
print("  [WOULD MATCH!]")

# Test impact on existing rules
print("\n\n=== IMPACT ON EXISTING RULES ===")

test_cases = [
    ("APPLE.COM/BILL", "APPLE.COM/BILL", "Subscriptions - rule expects dot preserved"),
    ("APPLE.COM/BILL", "APPLE", "Subscriptions - if we change rule to just 'APPLE'"),
    ("PAYPAL *NETFLIX.COM", "NETFLIX", "Streaming - already works"),
    ("CO-OP FOOD STORE", "CO-OP", "Groceries - hyphen preserved (not affected)"),
    ("AMAZON.CO.UK PURCHASE", "AMAZON", "Shopping - would match better"),
]

for description, pattern, category in test_cases:
    # Current behavior
    tokens_current = re.split(r'[\s*]+', description.upper())
    tokens_current = [t for t in tokens_current if t]
    tokens_current = [re.sub(r'[,;:.!?()]+$', '', t) for t in tokens_current]
    tokens_current = [t for t in tokens_current if t]
    matches_current = pattern.upper() in tokens_current

    # With dot delimiter
    tokens_new = re.split(r'[\s*\.]+', description.upper())
    tokens_new = [t for t in tokens_new if t]
    tokens_new = [re.sub(r'[,;:.!?()]+$', '', t) for t in tokens_new]
    tokens_new = [t for t in tokens_new if t]
    matches_new = pattern.upper() in tokens_new

    status = "[SAME]" if matches_current == matches_new else "[CHANGED]"
    print(f"\n{status} | {category}")
    print(f"  Description: {description}")
    print(f"  Pattern: {pattern}")
    print(f"  Current: {'[Match]' if matches_current else '[No Match]'}")
    print(f"  With dot: {'[Match]' if matches_new else '[No Match]'}")

print("\n\n=== RECOMMENDATION ===")
print("1. Add dot (.) to delimiter list: r'[\\s*\\.]+'")
print("2. Update 3 rules that use dots:")
print("   - 'APPLE.COM/BILL' -> 'APPLE' (broader match)")
print("   - 'NETFLIX.COM' -> 'NETFLIX' (already works)")
print("   - 'AMAZON.CO.UK' -> 'AMAZON' (already exists)")
print("3. Impact: More flexible matching, minimal rule breakage")
