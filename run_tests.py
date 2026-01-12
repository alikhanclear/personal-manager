#!/usr/bin/env python3
"""
Quick test runner script for Personal Manager.

Usage:
    python run_tests.py              # Run all tests
    python run_tests.py unit         # Run only unit tests
    python run_tests.py integration  # Run only integration tests
    python run_tests.py coverage     # Run with HTML coverage report
    python run_tests.py fast         # Skip slow tests
"""

import sys
import subprocess


def run_command(cmd: list[str]) -> int:
    """Run a command and return exit code."""
    print(f"Running: {' '.join(cmd)}")
    print("-" * 80)
    result = subprocess.run(cmd)
    return result.returncode


def main():
    if len(sys.argv) < 2:
        # Default: run all tests with basic coverage
        cmd = ["pytest", "-v", "--cov=src", "--cov-report=term-missing"]
    else:
        mode = sys.argv[1].lower()

        if mode == "unit":
            cmd = ["pytest", "-v", "-m", "unit"]
        elif mode == "integration":
            cmd = ["pytest", "-v", "-m", "integration"]
        elif mode == "coverage":
            cmd = ["pytest", "-v", "--cov=src", "--cov-report=html", "--cov-report=term-missing"]
            print("\nHTML coverage report will be generated in htmlcov/index.html")
        elif mode == "fast":
            cmd = ["pytest", "-v", "-m", "not slow"]
        elif mode == "watch":
            try:
                cmd = ["ptw", "--", "-v"]
                print("\nRunning tests in watch mode (auto-rerun on file changes)")
                print("Install pytest-watch if needed: pip install pytest-watch")
            except Exception:
                print("ERROR: pytest-watch not installed")
                print("Install it with: pip install pytest-watch")
                return 1
        else:
            print(f"Unknown mode: {mode}")
            print(__doc__)
            return 1

    exit_code = run_command(cmd)

    if exit_code == 0:
        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED!")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("❌ SOME TESTS FAILED")
        print("=" * 80)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
