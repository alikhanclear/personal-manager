"""
Check how many existing rules have alphanumeric patterns that would be affected.
"""
import pandas as pd
import re

df = pd.read_csv('rules_master.csv')

# Find rules with letter-to-number or number-to-letter transitions
mixed = df[df['pattern'].str.contains(r'[A-Z][0-9]|[0-9][A-Z]', na=False, regex=True)]

print(f"\n=== RULES WITH ALPHANUMERIC PATTERNS ===")
print(f"Total rules: {len(df)}")
print(f"Rules with letter-number transitions: {len(mixed)}")

if len(mixed) > 0:
    print(f"\n{len(mixed)} rules would be affected:")
    print(mixed[['pattern', 'category', 'priority']].to_string(index=False))

    print("\n\n=== IMPACT ANALYSIS ===")
    for idx, row in mixed.iterrows():
        pattern = row['pattern']
        # Simulate the split
        tokens = re.split(r'(?<=[A-Z])(?=[0-9])|(?<=[0-9])(?=[A-Z])', pattern)
        print(f"\nPattern: '{pattern}' -> {tokens}")
        print(f"  Category: {row['category']}")
        print(f"  Would still match if using any sub-token: {', '.join(tokens)}")
else:
    print("\n[GOOD] No rules would be affected!")
