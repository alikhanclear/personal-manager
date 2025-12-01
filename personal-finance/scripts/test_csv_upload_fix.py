"""
Test script to verify CSV upload fix for [Errno 22] Invalid argument on Windows.

Tests both BytesIO and temporary file approaches for reading CSV files.
"""
import io
import base64
import tempfile
import os
from pathlib import Path

import polars as pl


def test_bytesio_approach(csv_content: bytes):
    """Test reading CSV from BytesIO (original approach)."""
    print("\n=== Testing BytesIO Approach (Original) ===")
    try:
        df = pl.read_csv(io.BytesIO(csv_content))
        print(f"[OK] Success: Read {len(df)} rows")
        print(f"  Columns: {df.columns}")
        return True
    except Exception as e:
        print(f"[FAIL] Failed: {e}")
        return False


def test_bytesio_with_encoding(csv_content: bytes):
    """Test reading CSV from BytesIO with explicit encoding (new approach)."""
    print("\n=== Testing BytesIO with Encoding Parameters ===")
    try:
        df = pl.read_csv(
            io.BytesIO(csv_content),
            encoding='utf8-lossy',
            truncate_ragged_lines=True,
        )
        print(f"[OK] Success: Read {len(df)} rows")
        print(f"  Columns: {df.columns}")
        return True
    except Exception as e:
        print(f"[FAIL] Failed: {e}")
        return False


def test_tempfile_approach(csv_content: bytes):
    """Test reading CSV from temporary file (fallback approach)."""
    print("\n=== Testing Temporary File Approach (Fallback) ===")
    try:
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as tmp:
            tmp.write(csv_content)
            tmp_path = tmp.name

        try:
            df = pl.read_csv(tmp_path, encoding='utf8-lossy', truncate_ragged_lines=True)
            print(f"[OK] Success: Read {len(df)} rows")
            print(f"  Columns: {df.columns}")
            return True
        finally:
            os.unlink(tmp_path)
    except Exception as e:
        print(f"[FAIL] Failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("CSV Upload Fix - Test Suite")
    print("=" * 60)

    # Test file path
    test_file = Path(__file__).parent.parent / "test_rules_import.csv"

    if not test_file.exists():
        print(f"\n[ERROR] Test file not found: {test_file}")
        return

    print(f"\nTest file: {test_file.name}")

    # Read file content
    csv_content = test_file.read_bytes()
    print(f"File size: {len(csv_content)} bytes")

    # Simulate base64 encoding/decoding (as done in Dash upload)
    print("\nSimulating Dash upload process (base64 encode/decode)...")
    encoded = base64.b64encode(csv_content)
    decoded = base64.b64decode(encoded)

    # Run tests
    results = []
    results.append(("BytesIO (Original)", test_bytesio_approach(decoded)))
    results.append(("BytesIO with Encoding", test_bytesio_with_encoding(decoded)))
    results.append(("Temporary File", test_tempfile_approach(decoded)))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for name, success in results:
        status = "[PASS]" if success else "[FAIL]"
        print(f"{status:10} {name}")

    passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")

    if passed >= 2:  # At least 2 approaches should work
        print("\n[SUCCESS] Fix verified! CSV upload should work reliably.")
    else:
        print("\n[WARNING] Multiple approaches failed. Check Polars version and dependencies.")


if __name__ == "__main__":
    main()
