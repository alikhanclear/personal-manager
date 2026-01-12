"""
Test how the NEW rule engine tokenizes patterns with special characters.
"""
import re

def tokenize_pattern_old(pattern: str) -> list:
    """OLD tokenization (many delimiters)."""
    tokens = re.split(r'[\s,*\-./\\|()]+', pattern.upper())
    return [t for t in tokens if t]

def tokenize_pattern_new(pattern: str) -> list:
    """NEW tokenization (minimal delimiters - only space and asterisk)."""
    tokens = re.split(r'[\s*]+', pattern.upper())
    return [t for t in tokens if t]


# Test cases
test_patterns = [
    "AMAZON PRIME",
    "M&S",
    "M&S SIMPLY FOOD",
    "APPLE.COM/BILL",
    "CO-OP",
    "PAYPAL *NETFLIX",
    "PRET A MANGER",
    "MARKS & SPENCER",
]

print("=" * 80)
print("PATTERN TOKENIZATION COMPARISON: OLD vs NEW")
print("=" * 80)
print(f"{'Pattern':<25} {'OLD (many delimiters)':<30} {'NEW (space+asterisk only)'}")
print("-" * 80)

for pattern in test_patterns:
    tokens_old = tokenize_pattern_old(pattern)
    tokens_new = tokenize_pattern_new(pattern)
    print(f"{pattern:<25} {str(tokens_old):<30} {str(tokens_new)}")

print("\n" + "=" * 80)
print("KEY IMPROVEMENTS:")
print("=" * 80)
print("NEW tokenization preserves ALL special characters except space and asterisk:")
print("  - Hyphens preserved: 'CO-OP' stays as ['CO-OP'] (not split)")
print("  - Dots preserved: 'APPLE.COM/BILL' stays as ['APPLE.COM/BILL']")
print("  - Commas preserved: 'M&S, LONDON' stays as ['M&S,', 'LONDON']")
print("  - Ampersands preserved: 'M&S' stays as ['M&S']")
print("  - Parentheses preserved: 'BOOTS (UK)' stays as ['BOOTS', '(UK)']")
print("\nAsterisks still split (for bank transaction format):")
print("  - 'PAYPAL *NETFLIX' becomes ['PAYPAL', 'NETFLIX'] (good!)")
print("\n" + "=" * 80)
print("RESULT: You can now use ANY special characters in your patterns!")
print("=" * 80)
