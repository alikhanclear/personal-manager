"""Test RuleEngine with Yahya rule directly."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.database import FinanceDatabase
from src.core.rule_engine import RuleEngine
from src.data.models import Rule

db = FinanceDatabase(Path(__file__).parent.parent / "data" / "finance.db")

print("=" * 60)
print("Testing RuleEngine with Yahya Rule")
print("=" * 60)

# Get the actual rule from database
yahya_rules = [r for r in db.get_rules() if 'yahya' in r.pattern.lower()]
print(f"\nFound {len(yahya_rules)} Yahya rules")

if yahya_rules:
    rule = yahya_rules[0]
    print(f"\nRule details:")
    print(f"  Pattern: '{rule.pattern}'")
    print(f"  Pattern (repr): {rule.pattern!r}")
    print(f"  Pattern (bytes): {rule.pattern.encode('utf-8')}")
    print(f"  Category ID: {rule.category_id}")
    print(f"  Priority: {rule.priority}")

    # Create RuleEngine
    rule_engine = RuleEngine(db)

    # Test description
    description = "YAHYA ALIKHAN , FROM DADDY , VIA MOBILE - LVP , FP 13/11/25 10 , 18211146021841000N"

    print(f"\nTest description: '{description}'")

    # Test _matches_pattern directly
    result = rule_engine._matches_pattern(rule.pattern, description)
    print(f"\n_matches_pattern result: {result}")

    # Debug: Print what's being compared
    import re

    pattern_upper = rule.pattern.upper().strip()
    description_upper = description.upper().strip()

    pattern_tokens = re.split(r'[\s*]+', pattern_upper)
    pattern_tokens = [t for t in pattern_tokens if t]

    description_tokens = re.split(r'[\s*]+', description_upper)
    description_tokens = [t for t in description_tokens if t]

    print(f"\nPattern tokens: {pattern_tokens}")
    print(f"Description tokens (first 5): {description_tokens[:5]}")
    print(f"\nFirst 2 description tokens: {description_tokens[:2]}")
    print(f"Pattern tokens: {pattern_tokens}")
    print(f"Match? {description_tokens[:2] == pattern_tokens}")
