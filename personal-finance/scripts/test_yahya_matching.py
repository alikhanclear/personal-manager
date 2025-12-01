"""Test Yahya Ali Khan pattern matching in detail."""
import re

pattern = "YAHYA ALIKHAN"
description = "YAHYA ALIKHAN , FROM DADDY , VIA MOBILE - LVP , FP 13/11/25 10 , 18211146021841000N"

print("=" * 60)
print("Testing Pattern Matching")
print("=" * 60)

print(f"\nPattern: '{pattern}'")
print(f"Description: '{description}'")

# Tokenize description
description_upper = description.upper().strip()
description_tokens = re.split(r'[\s*]+', description_upper)
description_tokens = [t for t in description_tokens if t]

print(f"\nDescription tokens ({len(description_tokens)}):")
for i, token in enumerate(description_tokens[:10]):  # Show first 10
    print(f"  [{i}] '{token}'")

# Tokenize pattern
pattern_upper = pattern.upper().strip()
pattern_tokens = re.split(r'[\s*]+', pattern_upper)
pattern_tokens = [t for t in pattern_tokens if t]

print(f"\nPattern tokens ({len(pattern_tokens)}):")
for i, token in enumerate(pattern_tokens):
    print(f"  [{i}] '{token}'")

# Test matching
print("\n" + "=" * 60)
print("Testing Sequence Matching")
print("=" * 60)

if len(pattern_tokens) == 1:
    result = pattern_tokens[0] in description_tokens
    print(f"\nSingle-word pattern check: {result}")
else:
    print(f"\nMulti-word pattern (looking for sequence of {len(pattern_tokens)} tokens)")

    found = False
    for i in range(len(description_tokens) - len(pattern_tokens) + 1):
        window = description_tokens[i:i+len(pattern_tokens)]
        matches = window == pattern_tokens

        if i < 5:  # Show first 5 windows
            print(f"  Window [{i}:{i+len(pattern_tokens)}]: {window} == {pattern_tokens}? {matches}")

        if matches:
            found = True
            print(f"  *** MATCH FOUND at position {i}! ***")

    print(f"\nFinal result: {found}")
