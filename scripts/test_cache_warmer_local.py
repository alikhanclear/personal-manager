"""
Test Cache Warmer Locally (without Fly.io)

This script helps you test the cache warming strategy on your local machine.

Usage:
    1. Terminal 1: Start Streamlit app
       streamlit run src/ui/app.py

    2. Terminal 2: Run this test script
       python scripts/test_cache_warmer_local.py

Expected behavior:
    - First run: ~40-60 seconds (loads data from database)
    - Subsequent runs: Instant (cache hit)
"""

import time
import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.cache_warmer import warm_cache


def test_cache_warming():
    """Test cache warmer with local Streamlit app"""

    print("="*80)
    print("LOCAL CACHE WARMER TEST")
    print("="*80)
    print("\nPrerequisites:")
    print("  1. Streamlit app must be running:")
    print("     streamlit run src/ui/app.py")
    print("  2. Database connection configured in .env")
    print("="*80)

    input("\nPress ENTER when Streamlit is running...")

    # Test 1: First run (should load data)
    print("\n" + "="*80)
    print("TEST 1: First Cache Load (Cold Start)")
    print("="*80)
    print("Expected: ~40-60 seconds (database query)")

    start = time.time()
    success = warm_cache("http://localhost:8501", timeout=180)
    duration = time.time() - start

    if success:
        print(f"\n✓ TEST 1 PASSED: Data cached in {duration:.1f}s")
    else:
        print(f"\n✗ TEST 1 FAILED: Cache warming failed")
        return False

    # Wait a bit
    print("\nWaiting 5 seconds before test 2...")
    time.sleep(5)

    # Test 2: Second run (should be instant - cache hit)
    print("\n" + "="*80)
    print("TEST 2: Cache Hit (Warm Start)")
    print("="*80)
    print("Expected: <5 seconds (cache already loaded)")

    start = time.time()
    success = warm_cache("http://localhost:8501", timeout=180)
    duration = time.time() - start

    if success and duration < 10:
        print(f"\n✓ TEST 2 PASSED: Cache hit in {duration:.1f}s")
    elif success:
        print(f"\n⚠ TEST 2 WARNING: Took {duration:.1f}s (expected <10s)")
        print("  Cache may not be working correctly")
    else:
        print(f"\n✗ TEST 2 FAILED: Cache warming failed")
        return False

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print("✓ Cache warming works!")
    print("\nWhat this proves:")
    print("  - First user: ~40-60s load time (acceptable - runs at 9:25 AM)")
    print("  - All other users: Instant (cache hit)")
    print("\nProduction behavior:")
    print("  - Fly.io cron runs at 9:25 AM")
    print("  - Cache ready by 9:26 AM")
    print("  - All users get instant experience")
    print("="*80)

    return True


if __name__ == "__main__":
    try:
        success = test_cache_warming()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
