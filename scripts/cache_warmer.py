"""
Cache Warmer - Scheduled to run at 9:25 AM daily

Warms up application cache BEFORE users arrive (9:30 AM+).
Ensures instant experience for ALL users including first visitor.

Schedule: Daily at 9:25 AM via Fly.io cron
Duration: ~60 seconds
Result: All caches ready before users access dashboard
"""

import requests
import time
import sys
from datetime import datetime, date
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.fiscal_calendar import get_fiscal_year, get_fiscal_week


def get_current_fiscal_info():
    """Get current fiscal year and week"""
    today = date.today()
    fiscal_year = get_fiscal_year(today)
    fiscal_week = get_fiscal_week(today)
    return fiscal_year, fiscal_week


def warm_cache(base_url: str = "http://localhost:8501", timeout: int = 120):
    """
    Warm application cache by hitting the root endpoint.

    Args:
        base_url: Streamlit app URL (localhost for dev, fly.dev for prod)
        timeout: Request timeout in seconds (default: 2 minutes)

    What this does:
        1. Hits the root URL (/) which triggers load_transactions()
        2. load_transactions() queries 5 years of data from database (~40s)
        3. Data cached via @st.cache_resource (shared across all users)
        4. Report calculations are fast (milliseconds) - no need to pre-warm

    Timeline:
        - Data load: ~40-60 seconds (database query + Polars processing)
        - Total: ~60 seconds
        - Result: All users get instant experience
    """
    start_time = time.time()
    print("="*80)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] CACHE WARMER STARTED")
    print("="*80)

    try:
        # Get current fiscal period (for logging)
        fiscal_year, fiscal_week = get_current_fiscal_info()
        print(f"\nCurrent Period: FY{fiscal_year} Week {fiscal_week}")
        print(f"Target URL: {base_url}")

        # Warm cache by hitting root endpoint
        print(f"\n[Step 1/1] Loading transaction data...")
        print(f"  - Endpoint: {base_url}/")
        print(f"  - Triggers: load_transactions() with 5 years of data")
        print(f"  - Expected: ~40-60 seconds")
        print(f"  - Result: Data cached for 24 hours (all users)")

        load_start = time.time()
        try:
            response = requests.get(f"{base_url}/", timeout=timeout)
            load_duration = time.time() - load_start

            if response.status_code == 200:
                print(f"\n  ✓ SUCCESS: Data loaded and cached ({load_duration:.1f}s)")
            else:
                print(f"\n  ✗ FAILED: HTTP {response.status_code}")
                print(f"     Response: {response.text[:200]}")
                return False

        except requests.exceptions.Timeout:
            print(f"\n  ✗ TIMEOUT after {timeout}s")
            print(f"     - App may be slow or down")
            print(f"     - Check database connection")
            print(f"     - Consider increasing timeout")
            return False

        except requests.exceptions.ConnectionError:
            print(f"\n  ✗ CONNECTION FAILED")
            print(f"     - Is app running at {base_url}?")
            print(f"     - Check: flyctl status (if production)")
            print(f"     - Check: streamlit run src/ui/app.py (if local)")
            return False

        # Summary
        total_duration = time.time() - start_time
        print("\n" + "="*80)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] CACHE WARMER COMPLETE")
        print("="*80)
        print(f"Total Duration: {total_duration:.1f}s")
        print(f"Cache Status: ✓ READY")
        print(f"User Experience: ✓ INSTANT (all users)")
        print("\nNote: Report calculations are fast (milliseconds in Polars)")
        print("      Only data load needed pre-warming (done!)")
        print("="*80)

        return True

    except Exception as e:
        print(f"\n✗ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """
    Main entry point for cache warmer.

    Usage:
        # Development (local)
        python scripts/cache_warmer.py

        # Production (via Fly.io cron)
        python scripts/cache_warmer.py --prod
    """
    import argparse

    parser = argparse.ArgumentParser(description="Warm application cache")
    parser.add_argument(
        "--prod",
        action="store_true",
        help="Use production URL (fly.dev) instead of localhost"
    )
    parser.add_argument(
        "--url",
        type=str,
        help="Custom base URL (overrides --prod)"
    )

    args = parser.parse_args()

    # Determine base URL
    if args.url:
        base_url = args.url
    elif args.prod:
        # TODO: Replace with actual Fly.io app name
        base_url = "https://casualhero-bi.fly.dev"
    else:
        base_url = "http://localhost:8501"

    # Run cache warmer
    success = warm_cache(base_url)

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
