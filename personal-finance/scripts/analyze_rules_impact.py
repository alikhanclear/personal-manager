"""
Analyze current rules for impact of adding dot (.) as delimiter.
"""
import pandas as pd

df = pd.read_csv('rules_master.csv')

print(f"Total rules: {len(df)}")
print("\n=== Checking for patterns with dots ===")
dots = df[df['pattern'].str.contains(r'[.]', na=False, regex=True)]
print(f"Rules with dots: {len(dots)}")
if len(dots) > 0:
    print("\nRules that would be affected:")
    print(dots[['pattern', 'category', 'priority']].to_string(index=False))
else:
    print("[NONE] No rules with dots found!")

print("\n=== Checking for BOLT pattern ===")
bolt = df[df['pattern'].str.upper() == 'BOLT']
if len(bolt) > 0:
    print(f"[EXISTS] BOLT pattern found")
    print(f"  Category: {bolt.iloc[0]['category']}")
    print(f"  Priority: {bolt.iloc[0]['priority']}")
else:
    print("[MISSING] BOLT pattern does not exist in rules")
    print("  Recommendation: Add 'BOLT' -> 'Public Transport' rule")

print("\n=== IMPACT SUMMARY ===")
print(f"1. Total rules: {len(df)}")
print(f"2. Rules with dots: {len(dots)} (would need review)")
print(f"3. Net benefit: More flexible matching for:")
print("   - BOLT.EUO2511021744 -> matches 'BOLT'")
print("   - AMAZON.CO.UK -> matches 'AMAZON'")
print("   - NETFLIX.COM -> matches 'NETFLIX'")
print("   - PAYPAL.COM -> matches 'PAYPAL'")
print("   - etc.")
print(f"\n4. Recommendation: {'SAFE TO PROCEED' if len(dots) == 0 else 'REVIEW AFFECTED RULES FIRST'}")
