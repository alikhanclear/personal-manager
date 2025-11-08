"""
Helper script to URL-encode database password
"""
from urllib.parse import quote_plus

password = input("Enter your database password: ")
encoded = quote_plus(password)

print("\nOriginal:", password)
print("Encoded:", encoded)
print("\nUse this in your .env file:")
print(f"DB_PASSWORD={encoded}")
