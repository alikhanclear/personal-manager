"""
Fix password encoding in .env file
Reads current password and shows the encoded version
"""
import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

# Load current .env
load_dotenv()

# Get current password
current_password = os.getenv('DB_PASSWORD', '')

if not current_password:
    print("ERROR: DB_PASSWORD not found in .env file")
else:
    # Encode it
    encoded_password = quote_plus(current_password)

    print("=" * 60)
    print("Password Encoding")
    print("=" * 60)
    print(f"\nOriginal password: {current_password}")
    print(f"Encoded password:  {encoded_password}")

    if current_password == encoded_password:
        print("\n✓ Password doesn't need encoding (no special chars)")
    else:
        print("\n✗ Password needs encoding!")
        print("\nUpdate your .env file:")
        print("-" * 60)
        print(f"DB_PASSWORD={encoded_password}")
        print("-" * 60)
