#!/usr/bin/env python3
"""Verify GitHub App environment variables are set (safe — never prints values).

Usage:
    python scripts/verify_github_app_env.py
"""
import os

REQUIRED_VARS = [
    "GITHUB_APP_ID",
    "GITHUB_APP_SLUG",
    "GITHUB_CLIENT_ID",
    "GITHUB_CLIENT_SECRET",
    "GITHUB_WEBHOOK_SECRET",
    "GITHUB_PRIVATE_KEY_BASE64",
    "GITHUB_CALLBACK_URL",
    "GITHUB_WEBHOOK_URL",
]


def main():
    print("=" * 72)
    print("  GitHub App Environment Check")
    print("=" * 72)
    print()
    print(f"  {'Variable':<30} {'Status':<10}")
    print(f"  {'-'*30} {'-'*10}")
    all_present = True
    for var in REQUIRED_VARS:
        present = bool(os.environ.get(var))
        status = "present" if present else "MISSING"
        if not present:
            all_present = False
        print(f"  {var:<30} {status:<10}")
    print()
    if all_present:
        print("  Result: All required vars present")
    else:
        print("  Result: Some vars are missing")
        print("  Run: python scripts/apply_github_app_env.py --write")
    print()
    print("=" * 72)


if __name__ == "__main__":
    main()
